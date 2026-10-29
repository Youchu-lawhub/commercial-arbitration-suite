#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""套件自检与安装校验：不联网、不写案件材料，只判定"这个包装上机器后能不能跑"。

用法：
  python3 install_suite.py                 # 安装自检
  python3 install_suite.py --fix           # 顺带补 scripts/*.py 可执行位
  python3 install_suite.py --workdir DIR   # 附带检查该目录是否已放 .arbitration-config.md
  python3 install_suite.py --json          # 机器可读输出

退出码：0 全部通过（允许 WARN）/ 2 存在 FAIL / 3 依赖缺失（先装依赖再重跑）
"""
from __future__ import annotations

from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SUITE = Path(__file__).resolve().parent.parent
SLOTS = {"official_rules_fetch", "law_retrieval", "docx_render", "local_corpus", "party_data",
         "company_research", "certified_translation", "notarization", "local_counsel"}
DOCX_PARTS = ["word/document.xml", "word/styles.xml", "word/numbering.xml", "[Content_Types].xml"]

results: list = []


def add(code: str, state: str, msg: str) -> None:
    results.append({"check": code, "state": state, "msg": msg})


def fail(code: str, msg: str) -> None:
    add(code, "FAIL", msg)


def warn(code: str, msg: str) -> None:
    add(code, "WARN", msg)


def ok(code: str, msg: str) -> None:
    add(code, "OK", msg)


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    meta, cur = {}, None
    for line in block.split("\n"):
        if re.match(r"^\S", line) and ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip().strip('"\'')
            if v == "":
                meta[k] = {}
                cur = k
            else:
                meta[k] = v
                cur = None
        elif cur and line.startswith("  ") and ":" in line:
            k, v = line.strip().split(":", 1)
            meta[cur][k.strip()] = v.strip().strip('"\'')
    return meta


# ── DEPS ────────────────────────────────────────────────────────────────
def check_deps() -> bool:
    if sys.version_info < (3, 9):
        fail("DEPS", f"Python {sys.version.split()[0]} 过低，需 ≥3.9")
        return False
    ok("DEPS", f"Python {sys.version.split()[0]}")
    try:
        import yaml  # noqa: F401
        ok("DEPS", "PyYAML 可用（route.py 依赖）")
    except ImportError:
        fail("DEPS", "缺 PyYAML：pip install pyyaml，或 uv run --with pyyaml python3 scripts/route.py ...")
        return False
    ok("DEPS", "xmllint " + ("可用" if shutil.which("xmllint") else "缺失（DOCX 校验降级为部件完整性检查）"))
    return True


# ── TREE ────────────────────────────────────────────────────────────────
def load_suite_yaml():
    try:
        from intake import safe_yaml, validate_suite
        data = validate_suite(safe_yaml((SUITE / "suite.yaml").read_text(encoding="utf-8")))
        if not isinstance(data, dict):
            fail("TREE", f"suite.yaml 顶层结构错误：期望 mapping，实际 {type(data).__name__}")
            return None
        return data or {}
    except Exception as e:  # noqa: BLE001
        fail("TREE", f"suite.yaml 解析失败：{type(e).__name__}: {e}")
        return None


def check_tree(data) -> list:
    subs = (data or {}).get("subskills") or {}
    if not subs:
        fail("TREE", "suite.yaml 无 subskills 节点")
        return []
    ids = sorted(subs)
    bad_shape = [sid for sid in ids if not isinstance(subs[sid], dict)]
    if bad_shape:
        fail("TREE", f"subskills 条目不是映射：{bad_shape}")
        return ids
    # 无前置槽位的子技能＝收集配置的入口，本身不设闸门；其余子技能闸门必须非空
    entry_ids = {sid for sid in ids if not (subs[sid].get("requires") or [])}
    on_disk = sorted(p.name for p in (SUITE / "skills").iterdir() if (p / "SKILL.md").exists())
    for sid in ids:
        entry = subs[sid].get("entry")
        if not entry or not (SUITE / entry).exists():
            fail("TREE", f"{sid} entry 不存在：{entry}")
        # Validate entry points to the correct SKILL.md for this subskill
        if entry:
            expected_entry = f"skills/{sid}/SKILL.md"
            if entry != expected_entry and (SUITE / expected_entry).exists():
                fail("TREE", f"{sid} entry 指向错误：{entry}（应为 {expected_entry}）")
        gate = subs[sid].get("gate")
        if not isinstance(gate, list):
            fail("TREE", f"{sid} 缺少 gate 字段或格式不是列表（每个子技能必须声明资料闸门）")
        elif not gate and sid not in entry_ids and not subs[sid].get("profiles"):
            fail("TREE", f"{sid} gate 为空：仅无前置槽位的入口子技能可不设闸门")
        for req in (subs[sid].get("requires") or []):
            if req not in SLOTS:
                fail("TREE", f"{sid} requires 出现未登记槽位 {req}")
        for nxt in (subs[sid].get("next") or []):
            if nxt not in subs:
                fail("TREE", f"{sid} next 指向不存在子技能 {nxt}")
    for sid in set(ids) ^ set(on_disk):
        if sid in ids:
            fail("TREE", f"{sid} 在 suite.yaml 但 skills/{sid}/SKILL.md 缺失")
        else:
            fail("TREE", f"skills/{sid}/SKILL.md 存在但未登记进 suite.yaml")
    for stage, tgts in ((data or {}).get("stage_default") or {}).items():
        for t in (tgts or []):
            if t not in subs:
                fail("TREE", f"stage_default[{stage}] 指向不存在子技能 {t}")
    from intake import validate_suite, SchemaError
    try:
        validate_suite(data)
    except SchemaError as exc:
        fail('SCHEMA', str(exc))
    for sid in ids:
        profiles = subs[sid].get("profiles", {})
        if not isinstance(profiles, dict):
            fail("TREE", f"{sid} profiles 须为映射")
        else:
            for profile, spec in profiles.items():
                if not isinstance(spec, dict) or not isinstance(spec.get("gate"), list) or not spec["gate"]:
                    fail("TREE", f"{sid}/{profile} 缺少非空 gate 列表")
    ok("TREE", f"suite.yaml 与 skills/ 一一对应（{len(ids)} 个子技能）")
    return ids


# ── FRONT ───────────────────────────────────────────────────────────────
def check_frontmatter(ids):
    # The source/release directory may be renamed by any host; the internal slug is stable.
    data = load_suite_yaml() or {}
    files = [(SUITE / "SKILL.md", data.get('name', 'commercial-arbitration-suite'))] + [(SUITE / "skills" / i / "SKILL.md", i) for i in ids]
    for p, expect in files:
        if not p.exists():
            fail("FRONT", f"{p} 不存在")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        yaml_meta = None
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                block = text[3:end].strip("\n")
                try:
                    import yaml
                    yaml_meta = yaml.safe_load(block)
                    if not isinstance(yaml_meta, dict):
                        fail("FRONT", f"{expect}: frontmatter 解析结果非 mapping")
                        continue
                except Exception as e:
                    fail("FRONT", f"{expect}: frontmatter YAML 解析失败：{e}")
                    continue
        m = yaml_meta if yaml_meta is not None else parse_frontmatter(text)
        if m is None:
            fail("FRONT", f"{p.name} frontmatter 未按 --- 包裹")
            continue
        if m.get("name") != expect:
            fail("FRONT", f"{expect}: name={m.get('name')!r} 与目录名不一致")
        desc = m.get("description")
        if not isinstance(desc, str) or not desc.strip():
            fail("FRONT", f"{expect}: description 缺失")
        elif len(desc) > 1024:
            fail("FRONT", f"{expect}: description {len(desc)} 字符，超 1024")
        elif "\n" in desc:
            fail("FRONT", f"{expect}: description 非单行")
        body_lines = len(text.split("\n"))
        if body_lines > 500:
            warn("FRONT", f"{expect}: 正文 {body_lines} 行，超 500 行建议拆分")
    ok("FRONT", f"{len(files)} 份 SKILL.md frontmatter 合规")


# ── REFS ────────────────────────────────────────────────────────────────
REF_RE = re.compile(r"(?:assets|references|scripts|skills|data/official)/(?:[\w\u4e00-\u9fff、\-./]+(?=`)|[\w\u4e00-\u9fff\-./]*)")


def check_refs(ids):
    files = [SUITE / "SKILL.md"] + [SUITE / "skills" / i / "SKILL.md" for i in ids]
    files += list((SUITE / "references").glob("*.md")) + list((SUITE / "assets/templates").glob("*.md"))
    files += [SUITE / "suite.yaml"]
    bad, n = [], 0
    for p in files:
        if not p.exists():
            continue
        for m in REF_RE.finditer(p.read_text(encoding="utf-8", errors="ignore")):
            rel = m.group(0).rstrip("，。；、):（")
            if "<" in rel or rel.endswith(("/", ".")) or rel.startswith('data/official/'):
                # Official caches are created on demand and excluded from runtime packages.
                continue
            n += 1
            q = SUITE / rel
            if not q.exists() and not q.parent.joinpath(Path(rel).name).exists():
                bad.append(f"{p.relative_to(SUITE)} -> {rel}")
    if bad:
        for b in bad[:12]:
            fail("REFS", f"内部路径失效：{b}")
    else:
        ok("REFS", f"{n} 处内部路径全部可解析")


# ── REG ─────────────────────────────────────────────────────────────────
def load_registry():
    try:
        data = json.loads((SUITE / "assets" / "sources-registry.json").read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            fail("REG", f"sources-registry.json 顶层结构错误：期望 mapping，实际 {type(data).__name__}")
            return None
        return data
    except Exception as e:  # noqa: BLE001
        fail("REG", f"sources-registry.json 解析失败：{type(e).__name__}: {e}")
        return None


def reg_ids(reg) -> set:
    out = set()
    for inst, meta in (reg.get("institutions") or {}).items():
        for b in ("rules", "companions", "fees", "statute"):
            v = meta.get(b)
            for it in (v if isinstance(v, list) else ([v] if isinstance(v, dict) else [])):
                if isinstance(it, dict) and it.get("id"):
                    out.add(it["id"])
        for b in ("filing", "_watch", "watch", "note"):
            v = meta.get(b)
            if isinstance(v, dict) and (v.get("url") or v.get("landing")):
                out.add(f"{inst}-{b.strip('_')}")
    for k, v in reg.items():
        if k == "institutions" or not isinstance(v, list):
            continue
        out |= {i["id"] for i in v if isinstance(i, dict) and i.get("id")}
    return out


def check_reg(reg, ids):
    if reg is None:
        return
    if 'treaties' in reg:
        treaties = reg['treaties']
        if not isinstance(treaties, list) or not all(isinstance(t,dict) and t.get('id') and any(str(t.get(k,'')).startswith('https://') for k in ('url','landing','pdf')) for t in treaties):
            fail('REG', 'treaties 须为含 id 与官方 https 地址的记录列表')
    sids = reg_ids(reg)
    if not sids:
        fail("REG", "注册表无 source id")
        return
    # Check for duplicate source-ids
    all_ids = []
    for inst, meta in (reg.get("institutions") or {}).items():
        for b in ("rules", "companions", "fees", "statute"):
            v = meta.get(b)
            for it in (v if isinstance(v, list) else ([v] if isinstance(v, dict) else [])):
                if isinstance(it, dict) and it.get("id"):
                    all_ids.append(it["id"])
        for b in ("filing", "_watch", "watch", "note"):
            v = meta.get(b)
            if isinstance(v, dict) and (v.get("url") or v.get("landing")):
                all_ids.append(f"{inst}-{b.strip('_')}")
    for k, v in reg.items():
        if k == "institutions" or not isinstance(v, list):
            continue
        for i in v:
            if isinstance(i, dict) and i.get("id"):
                all_ids.append(i["id"])
    dupes = [x for x in all_ids if all_ids.count(x) > 1]
    if dupes:
        fail("REG", f"注册表含重复 source-id：{list(set(dupes))[:5]}")
        return
    for inst, meta in (reg.get("institutions") or {}).items():
        for r in (meta.get("rules") or []):
            if r.get("id") and r.get("effective"):
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r["effective"])):
                    fail("REG", f"{r['id']} effective 非 ISO 日期：{r['effective']}（applicable 判定会失败）")
                else:
                    # Validate date is real (e.g., not 2026-02-31)
                    try:
                        from datetime import datetime
                        datetime.fromisoformat(str(r["effective"]))
                    except ValueError:
                        fail("REG", f"{r['id']} effective 日期不存在：{r['effective']}")
        if not (meta.get("rules") or meta.get("statute")):
            warn("REG", f"机构 {inst} 未登记任何规则文本来源")
    cited = set()
    for p in [SUITE / "SKILL.md"] + [SUITE / "skills" / i / "SKILL.md" for i in ids] + \
             list((SUITE / "references").glob("*.md")) + list((SUITE / "assets/templates").glob("*.md")):
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"\[source:([a-z0-9\-]+)\]", txt):
            cited.add(m.group(1))
        for m in re.finditer(r"\[source:([a-z0-9\-]+)\s*\|", txt):
            cited.add(m.group(1))
    ghost = sorted(c for c in cited if c not in sids)
    if ghost:
        fail("REG", f"来源标记引用了未登记 id：{ghost[:8]}")
    else:
        ok("REG", f"{len(sids)} 个来源已登记；包内 {len(cited)} 处实引 id 均可解析")
    never = [s for s in sids if not (SUITE / "data" / "_provenance" / f"{s}.json").exists()]
    if never:
        ok("REG", f"{len(never)} 个来源未作本机核验（信息提示；仅按本案所需 source-id 检查，不必全库抓取）")


# ── SRC（境外法检索通道登记表）─────────────────────────────────────────
SRC_PATH = SUITE / "assets" / "research-sources.json"
SRC_KINDS = {"mcp-npm", "mcp-pypi", "mcp-git", "mcp-remote", "api", "site", "dataset"}
SRC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
SRC_JUR_RE = re.compile(r"^[A-Z]{2,6}$")
# 非 ISO 3166-1 别码：混用会让 plan --jurisdiction <标准码> 查不到对应 blocked_path
SRC_JUR_ALIASES = {"UK": "GB", "EU": None}  # 值为 None 表示该码合法（欧盟属约定用法）
SRC_JUR_BANNED = {k: v for k, v in SRC_JUR_ALIASES.items() if v}
SRC_RUNTIMES = {"python3", "node", "npx", "uvx", "uv", "pipx", "docker"}
SRC_REQUIRED = ("id", "title", "kind", "jurisdictions", "layers", "relevance", "state",
                "auth", "checked", "acceptance", "caveat", "provider", "upstream", "role")
SRC_ROLES = {"primary", "mirror", "cross-check"}


def src_module_symbols():
    """取 research_sources.py 里定义的分层与状态口径，用于与登记表对表。"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_rs", SUITE / "scripts" / "research_sources.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return set(getattr(mod, "LAYERS", set())), set(getattr(mod, "STATE_RANK", {})), \
            set(getattr(mod, "BOUND_OK", set())) | set(getattr(mod, "CONDITIONAL", set())), \
            set(getattr(mod, "RUNTIME_TOOLS", set()))
    except Exception as e:  # noqa: BLE001
        fail("SRC", f"无法载入 research_sources.py 对表：{type(e).__name__}: {e}")
        return set(), set(), set(), set()


def check_research_sources():
    if not SRC_PATH.exists():
        fail("SRC", "缺少 assets/research-sources.json：law_retrieval 层没有通道登记表")
        return
    try:
        reg = json.loads(SRC_PATH.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail("SRC", f"research-sources.json 解析失败：{type(e).__name__}: {e}（plan 会据此误报闸门）")
        return
    if not isinstance(reg, dict):
        fail("SRC", f"research-sources.json 顶层须为 mapping，实际 {type(reg).__name__}")
        return
    layers, ranks, known_states, rt_tools = src_module_symbols()
    bad = []
    for k in ("schema", "generated", "refresh_cadence_days", "disclosure", "state_legend",
              "sources", "discovery", "blocked_paths", "dead_claims",
              "official_hosts", "non_official_hosts"):
        if k not in reg:
            bad.append(f"缺顶层字段 {k}")
    if not str(reg.get("schema", "")).startswith("research-sources/"):
        bad.append(f"schema 非 research-sources/N：{reg.get('schema')}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(reg.get("generated") or "")):
        bad.append(f"generated 非 ISO 日期：{reg.get('generated')}")
    cad = reg.get("refresh_cadence_days")
    if not isinstance(cad, int) or not (1 <= cad <= 365):
        bad.append(f"refresh_cadence_days 须为 1–365：{cad}")
    for d in ("degraded", "single_source", "stale"):
        if not str((reg.get("disclosure") or {}).get(d) or "").strip():
            bad.append(f"disclosure.{d} 缺失（降级话术无出处）")
    legend = set((reg.get("state_legend") or {}).keys())
    if not legend:
        bad.append("state_legend 为空")
    miss_rank = sorted(legend - ranks)
    if miss_rank:
        bad.append(f"脚本 STATE_RANK 未登记这些状态，plan 排序会退化：{miss_rank}")
    miss_leg = sorted(ranks - legend)
    if miss_leg:
        bad.append(f"脚本认识但这些状态不在 state_legend：{miss_leg}")
    seen = set()
    for s in reg.get("sources") or []:
        sid = str(s.get("id") or "")
        if not SRC_ID_RE.fullmatch(sid):
            bad.append(f"通道 id 非法：{sid!r}")
            continue
        if sid in seen:
            bad.append(f"通道 id 重复：{sid}")
        seen.add(sid)
        for f in SRC_REQUIRED:
            if f == "checked" and s.get("checked") is None and s.get("documentation_checked"):
                continue
            if not str(s.get(f) or "").strip() and not isinstance(s.get(f), list):
                bad.append(f"{sid} 缺 {f}")
        if s.get("kind") not in SRC_KINDS:
            bad.append(f"{sid} kind 未登记：{s.get('kind')}")
        if s.get("relevance") not in ("high", "medium", "low"):
            bad.append(f"{sid} relevance 须 high/medium/low：{s.get('relevance')}")
        if s.get("role") not in SRC_ROLES:
            bad.append(f"{sid} role 须 primary/mirror/cross-check：{s.get('role')}")
        if s.get("state") not in legend:
            bad.append(f"{sid} state 不在 state_legend：{s.get('state')}")
        # 声称"已实测可用"就必须留下带日期的实测记录，否则状态无法证伪
        stt = str(s.get("state") or "")
        evd = str(s.get("evidence") or "")
        dated = bool(re.search(r"20\d\d-\d\d-\d\d", evd))
        if stt in ("VERIFIED_KEYLESS", "VERIFIED_REMOTE_MCP", "PACKAGE_OK_LOCAL_BLOCKED",
                   "LIVE_CLIENT", "PARTIAL") and not dated:
            bad.append(f"{sid} 状态为 {stt}（声称已实测）但 evidence 缺带日期的实测记录")
        caps = [str(x) for x in (s.get("capabilities") or [])]
        # 声称的工具数必须与记录的工具面一致，否则说明有一边是抄来的
        claimed = re.findall(r"共\s*(\d+)\s*个工具", str((s.get("corpus") or {}).get("stats") or ""))
        for cnum in claimed:
            if caps and int(cnum) != len(caps):
                bad.append(f"{sid} corpus 声称 {cnum} 个工具，capabilities 实为 {len(caps)} 个：数字不一致说明其中一处未核对")
        if s.get("kind") == "mcp-remote" and stt == "VERIFIED_REMOTE_MCP" and not caps:
            bad.append(f"{sid} 远端 MCP 声称已验证，但 capabilities 为空："
                       f"没记录实测工具面，无法发现它改名、缩容或本来只是问答机器人")
        if caps:
            named = set(re.findall(r"`([a-z][a-z0-9_.]{3,60})`", str(s.get("acceptance") or "")))
            ghost = sorted(t for t in named if t not in caps)
            if ghost:
                bad.append(f"{sid} acceptance 点名了不存在的工具 {ghost}："
                           f"按此验收会把可用通道误判为坏通道，或诱导模型编造结果来凑")
        if s.get("kind") in ("mcp-npm", "mcp-pypi") and not str(s.get("version_known") or "").strip():
            bad.append(f"{sid} {s.get('kind')} 缺 version_known：无法发现包改名或下架")
        if s.get("kind") == "mcp-remote" and stt == "VERIFIED_REMOTE_MCP" and not dated:
            bad.append(f"{sid} 远端 MCP 声称 tools/list 实测通过，但没有带日期的证据")
        if s.get("state") in ("SECONDARY_ONLY", "BLOCKED", "DEAD"):
            bad.append(f"{sid} 登记状态为 {s.get('state')}：不产正文的站点不得留在 sources 里，"
                       f"应删除本条并把官方入口移入 blocked_paths（人工取文路径）")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s.get("checked") or s.get("documentation_checked") or "")):
            bad.append(f"{sid} checked 非 ISO 日期")
        jur = s.get("jurisdictions") or []
        if not jur or not all(SRC_JUR_RE.fullmatch(str(x)) for x in jur):
            bad.append(f"{sid} jurisdictions 须为 2–6 位大写代码列表：{jur}")
        for alias, std in SRC_JUR_BANNED.items():
            if alias in [str(x) for x in jur]:
                bad.append(f"{sid} jurisdictions 用了非 ISO 别码 {alias}，应为 {std}")
        lyr = set(s.get("layers") or [])
        if not lyr:
            bad.append(f"{sid} 未标注 layers")
        elif layers and not lyr <= layers:
            bad.append(f"{sid} layers 含脚本未定义值：{sorted(lyr - layers)}")
        ins = s.get("install") or {}
        rq = [str(r).split(">=")[0].split(">")[0].strip() for r in (ins.get("requires") or [])]
        unknown_rt = sorted({r for r in rq if r not in SRC_RUNTIMES})
        if unknown_rt:
            bad.append(f"{sid} install.requires 含未登记运行时：{unknown_rt}")
        if s.get("kind") == "mcp-remote" and not str(s.get("url") or "").startswith("https://"):
            bad.append(f"{sid} mcp-remote 缺 https url")
        if s.get("kind") in ("mcp-npm", "mcp-pypi") and not s.get("pkg"):
            bad.append(f"{sid} {s.get('kind')} 缺 pkg 包名，check 无法核对版本")
        if s.get("kind") == "mcp-git" and not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+",
                                                           str(s.get("repo") or "")):
            bad.append(f"{sid} mcp-git 缺 repo（https://github.com/<owner>/<repo>），check 无法探活")
        for f in ("corpus", "install", "endpoint"):
            if s.get(f) is not None and not isinstance(s.get(f), dict):
                bad.append(f"{sid} {f} 须为对象（plan 按键读取，字符串会导致崩溃）")
        if s.get("subdivision") is not None and not re.fullmatch(r"[A-Z]{2,6}", str(s.get("subdivision"))):
            bad.append(f"{sid} subdivision 须为 2–6 位大写州省／自由区代码：{s.get('subdivision')}")
        ep = s.get("endpoint") or {}
        tpl = str(ep.get("url_template") or "")
        if s.get("kind") in ("api", "site") and not tpl.startswith("https://"):
            bad.append(f"{sid} api/site 缺 https endpoint.url_template")
        if tpl.startswith("https://"):
            ph = set(re.findall(r"\{(\w+)\}", tpl))
            decl = set((ep.get("params") or {}).keys())
            if ph - decl:
                bad.append(f"{sid} 模板占位未声明参数：{sorted(ph - decl)}")
            if decl - ph:
                bad.append(f"{sid} 声明了模板用不到的参数：{sorted(decl - ph)}")
            host = tpl.split("//", 1)[1].split("/", 1)[0]
            if ep.get("allow_host") and ep["allow_host"] != host:
                bad.append(f"{sid} allow_host({ep['allow_host']}) 与模板主机({host}) 不一致")
            if tpl.count("://") != 1:
                bad.append(f"{sid} url_template 出现多重 scheme，疑似拼接错误")
            path = tpl.split("//", 1)[1]
            path = path.split("/", 1)[1] if "/" in path else ""
            last = path.split("?")[0].rstrip("/").split("/")[-1].lower()
            portal_words = ("", "index", "home", "start", "beranda", "welcome", "search",
                            "suche", "find", "query", "sindex", "main")
            is_portal = last in portal_words or "search" in last or last.endswith(".do")
            bindable = s.get("state") in ("VERIFIED_KEYLESS", "VERIFIED_REMOTE_MCP")
            if bindable and not ph and is_portal:
                bad.append(f"{sid} 状态声称免密可取正文，但 url_template 指向站点根／检索页（末段 {last!r}）："
                           f"门户只能定位文件，state 应改 SECONDARY_ONLY，或把模板改指带占位的文件路径")
            for k, v in (ep.get("params") or {}).items():
                val = str(v)
                if val in ("required", "optional"):
                    continue
                if re.search(r"[　-〿一-鿿＀-￯]", val):
                    bad.append(f"{sid} endpoint.params.{k} 是中文说明而非可用默认值："
                               f"get 会把它拼进 URL；应改为 \"required\" 或给出真实取值")
    host_re = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$")
    chan_ids = {str(s0.get("id")) for s0 in reg.get("sources") or []}
    path_ids = {str(b0.get("id")) for b0 in reg.get("blocked_paths") or []}
    seen_h = set()
    for e in reg.get("official_hosts") or []:
        h = str(e.get("host") or "").lower()
        if not host_re.fullmatch(h):
            bad.append(f"official_hosts host 非法：{h!r}")
        if h in seen_h:
            bad.append(f"official_hosts host 重复：{h}")
        seen_h.add(h)
        for f in ("jurisdictions", "authority", "status", "via", "note"):
            if not e.get(f) and not isinstance(e.get(f), list):
                bad.append(f"official_hosts {h} 缺 {f}")
        if e.get("status") not in ("verified_text", "official_pending"):
            bad.append(f"official_hosts {h} status 须 verified_text/official_pending：{e.get('status')}")
        if e.get("authority") not in ("state", "court", "supranational", "statutory_body", "institution"):
            bad.append(f"official_hosts {h} authority 未登记：{e.get('authority')}")
        if not all(SRC_JUR_RE.fullmatch(str(x)) for x in (e.get("jurisdictions") or [])):
            bad.append(f"official_hosts {h} jurisdictions 代码非法：{e.get('jurisdictions')}")
        # 台账必须挂在真实条目上，否则无法追溯取证来源
        if str(e.get("via")) not in chan_ids | path_ids:
            bad.append(f"official_hosts {h} 的 via={e.get('via')!r} 不是已登记通道或人工路径")
    def _hk(u):
        h = str(u or "").split("//", 1)[-1].split("/")[0].lower()
        return h[4:] if h.startswith("www.") else h
    non_off = [_hk(e.get("host")) for e in reg.get("non_official_hosts") or [] if e.get("host")]
    for s2 in reg.get("sources") or []:
        h = _hk(str((s2.get("endpoint") or {}).get("url_template") or s2.get("url") or ""))
        if not h:
            continue
        if any(h == b or h.endswith("." + b) for b in non_off if b):
            cav = str(s2.get("caveat") or "")
            if not re.search(r"不是官方|非官方|商业|社区镜像|私营|聚合|不得.*官方原文|须回.*官方", cav):
                bad.append(f"{s2.get('id')} 架在官方域名台账已判为非官方的主机 {h} 上，"
                           f"但 caveat 未声明其非官方身份——plan 会把它当可用通道呈现，使用者无从知道它不是一手来源")

    for e in reg.get("non_official_hosts") or []:
        h = str(e.get("host") or "").lower()
        if not host_re.fullmatch(h):
            bad.append(f"non_official_hosts host 非法：{h!r}")
        if h in seen_h:
            bad.append(f"同一主机既列官方又列非官方：{h}")
        for f in ("why", "evidence"):
            if not str(e.get(f) or "").strip():
                bad.append(f"non_official_hosts {h} 缺 {f}（判非官方同样要留证据）")

    # 已删除的通道不得再被任何条目的文字引用：删除时若忘了同步 caveat／evidence，
    # 使用者会照着一条不存在的通道去配置。只比对 dead_claims 里明确记录的退役 id，
    # 不做泛化分词——否则会把 serverInfo 名、URL 片段和包名误当成通道引用，校验就会变成噪声
    retired = {str(d.get("id"))[len("channel-"):] for d in (reg.get("dead_claims") or [])
               if str(d.get("id") or "").startswith("channel-")}
    retired |= {str(d.get("id"))[len("portal-"):] for d in (reg.get("dead_claims") or [])
                if str(d.get("id") or "").startswith("portal-")}
    live_ids = {str(x.get("id")) for x in (reg.get("sources") or [])}
    live_ids |= {str(x.get("id")) for x in (reg.get("blocked_paths") or [])}
    for x in ((reg.get("sources") or []) + (reg.get("blocked_paths") or [])):
        blob = " ".join(str(x.get(f) or "") for f in
                        ("caveat", "evidence", "acceptance", "reason", "disclose", "title"))
        for rid in sorted(retired):
            if rid in live_ids:
                continue
            if re.search(r'(?:见|参见|走|改用|替代|同|和|与)\\s*[`"]?' + re.escape(rid) + r'[`"]?\\b', blob):
                bad.append(f"{x.get('id')} 的文字把已退役通道 {rid} 当作可参考对象："
                           f"该通道已删除，须改掉这段文字或换指向仍存在的条目")
            elif "`" + rid + "`" in blob:
                bad.append(f"{x.get('id')} 引用了已退役通道 `{rid}`：它已不在登记表，不能继续作为指引目标")

    ids_bp = set()
    for b in reg.get("blocked_paths") or []:
        bid = str(b.get("id") or "")
        if not SRC_ID_RE.fullmatch(bid) or bid in ids_bp:
            bad.append(f"blocked_paths id 非法或重复：{bid!r}")
        ids_bp.add(bid)
        for f in ("title", "reason", "action", "disclose", "checked"):
            if not str(b.get(f) or "").strip():
                bad.append(f"blocked_path {bid} 缺 {f}")
        if not b.get("browser_url") and not str(b.get("action") or "").strip():
            bad.append(f"blocked_path {bid} 既无 browser_url 也无 action，用户无从人工取文")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(b.get("checked") or "")):
            bad.append(f"blocked_path {bid} checked 非 ISO 日期")
        if not b.get("jurisdictions") or not all(SRC_JUR_RE.fullmatch(str(x)) for x in b["jurisdictions"]):
            bad.append(f"blocked_path {bid} jurisdictions 非法：{b.get('jurisdictions')}")
        for alias, std in SRC_JUR_BANNED.items():
            if alias in [str(x) for x in (b.get("jurisdictions") or [])]:
                bad.append(f"blocked_path {bid} 用了非 ISO 别码 {alias}，应为 {std}"
                           f"（否则 plan --jurisdiction {std} 查不到本条人工取文指引）")
        if layers and not set(b.get("layers") or []) <= layers:
            bad.append(f"blocked_path {bid} layers 含未定义值：{sorted(set(b.get('layers') or []) - layers)}")
    ids_dc = set()
    for d in reg.get("dead_claims") or []:
        did = str(d.get("id") or "")
        if not SRC_ID_RE.fullmatch(did) or did in ids_dc:
            bad.append(f"dead_claims id 非法或重复：{did!r}")
        ids_dc.add(did)
        for f in ("claim", "state", "evidence", "checked"):
            if not str(d.get(f) or "").strip():
                bad.append(f"dead_claim {did} 缺 {f}（宣称失效必须留下证据）")
        if d.get("state") not in legend:
            bad.append(f"dead_claim {did} state 不在 state_legend：{d.get('state')}")
    for d in reg.get("discovery") or []:
        did = str(d.get("id") or "")
        if not SRC_ID_RE.fullmatch(did):
            bad.append(f"discovery id 非法：{did!r}")
        if not str(d.get("url_template") or "").startswith("https://"):
            bad.append(f"discovery {did} 缺 https url_template")
        if not str(d.get("note") or "").strip():
            bad.append(f"discovery {did} 缺 note（未记录参数形态就无法复用）")
    overlap = sorted(seen & ids_dc)
    if overlap:
        bad.append(f"同一 id 既是可用通道又被登记为失效宣称：{overlap}")
    live = seen | ids_bp
    for s in (reg.get("sources") or []) + (reg.get("blocked_paths") or []):
        for f in s.get("fallback") or []:
            if f not in live:
                bad.append(f"{s.get('id')} fallback 指向不存在或已失效的通道：{f}（plan 会把用户引向死路）")
    for b in bad[:20]:
        fail("SRC", b)
    if not bad:
        ok("SRC", f"research-sources.json：{len(seen)} 条通道 / {len(ids_bp)} 条人工路径 / "
                  f"{len(ids_dc)} 条失效宣称；layers 与状态口径与脚本一致")


# ── DOCS ────────────────────────────────────────────────────────────────
CMD_RE = re.compile(
    r"python3\s+(?:<suite>/)?scripts/(\w+)\.py((?:(?!python3|[；;。\n]).)*)")


def script_cli():
    import ast
    info = {}
    for sp in (SUITE / 'scripts').glob('*.py'):
        tree = ast.parse(sp.read_text(encoding='utf-8'))
        opts, subs = set(), set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            values = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if node.func.attr == 'add_argument':
                opts.update(v for v in values if v.startswith('--'))
            if node.func.attr == 'add_parser' and values:
                subs.add(values[0])
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and isinstance(node.iter, (ast.Tuple, ast.List)):
                if any(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'add_parser'
                       and call.args and isinstance(call.args[0], ast.Name) and call.args[0].id == node.target.id for call in ast.walk(node)):
                    subs.update(value.value for value in node.iter.elts if isinstance(value, ast.Constant) and isinstance(value.value, str))
        info[sp.stem] = dict(opts=opts, subs=subs)
    # Matrix CLIs delegate shared arguments to the local parser factory.
    common = info.get('_matrix_common')
    if common:
        for sp in (SUITE / 'scripts').glob('*.py'):
            tree = ast.parse(sp.read_text(encoding='utf-8'))
            delegates = any(isinstance(node, ast.ImportFrom) and node.module == '_matrix_common'
                            and any(alias.name == 'cli' for alias in node.names) for node in ast.walk(tree))
            if delegates:
                info[sp.stem]['opts'].update(common['opts'])
                info[sp.stem]['subs'].update(common['subs'])
    return info


def check_docs(ids):
    info = script_cli()
    files = [SUITE / "SKILL.md"] + [SUITE / "skills" / i / "SKILL.md" for i in ids] + \
            list((SUITE / "references").glob("*.md")) + list((SUITE / "assets/templates").glob("*.md"))
    bad, n = [], 0
    for p in files:
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8", errors="ignore")
        joined = re.sub(r'\\\n\s*', ' ', raw)
        for i, line in enumerate(joined.split("\n"), 1):
            for m in CMD_RE.finditer(line):
                script, rest = m.group(1), m.group(2)
                n += 1
                if script not in info:
                    bad.append(f"{p.relative_to(SUITE)}:{i} 脚本不存在 {script}.py")
                    continue
                unk = sorted(f for f in set(re.findall(r"(--[a-z][a-z\-]+)", rest)) if f not in info[script]["opts"])
                if unk:
                    bad.append(f"{p.relative_to(SUITE)}:{i} {script} 无此参数 {unk}")
                sub = next((w for w in rest.split() if not w.startswith("-")), None)
                if sub and info[script]["subs"] and sub not in info[script]["subs"] and not sub.startswith(("<", "[")):
                    bad.append(f"{p.relative_to(SUITE)}:{i} {script} 无此子命令 {sub!r}")
                if script == "fetch_official" and sub in ("lookup", "report"):
                    wrong_flags = [f for f in re.findall(r"(--[a-z][a-z\-]+)", rest) if f in ("--inst", "--commencement")]
                    if wrong_flags:
                        bad.append(f"{p.relative_to(SUITE)}:{i} {script} {sub} 不应使用 {wrong_flags}（属于 applicable/check）")
                if script == "fetch_official" and sub == "applicable":
                    if "--commencement" not in rest and "--inst" in rest:
                        bad.append(f"{p.relative_to(SUITE)}:{i} applicable 缺必需参数 --commencement")
    for b in bad:
        fail("DOCS", f"文档命令与脚本 CLI 不符：{b}")
    if not bad:
        ok("DOCS", f"{n} 处文档内命令行与脚本 argparse 完全一致")


# ── CLEAN ───────────────────────────────────────────────────────────────
def check_clean():
    stray = [str(p.relative_to(SUITE)) for p in SUITE.rglob("*.docx") if not p.name.startswith("~$")]
    if stray:
        fail("CLEAN", f"技能包内出现交付文件（违反铁律 8）：{stray[:5]}")
    else:
        ok("CLEAN", "技能包内无 .docx 交付物")
    cache = [p.name for p in (SUITE / "data" / "official").glob("*") if p.is_file() and not p.name.startswith(".")]
    unproven = [n for n in cache if not (SUITE / "data" / "_provenance" / f"{Path(n).stem}.json").exists()]
    if unproven:
        warn("CLEAN", f"data/official 缓存缺凭证：{unproven[:5]}")
    else:
        ok("CLEAN", f"data/official 缓存 {len(cache)} 件，均有来源凭证")
    # 反向核对：凭证文件指向的通道必须仍在登记表内，否则是历史残留或已删除通道的孤儿记录
    try:
        known = {str(s.get("id")) for s in (json.loads(
            (SUITE / "assets" / "research-sources.json").read_text(encoding="utf-8"))
            .get("sources") or [])}
    except Exception:
        known = set()
    prov_dir = SUITE / "data" / "_provenance"
    orphans = []
    if known and prov_dir.is_dir():
        for p in prov_dir.glob("research-*.json"):
            cid = p.name[len("research-"):-len(".json")]
            if cid not in known:
                orphans.append(p.name)
    if orphans:
        fail("CLEAN", f"data/_provenance 存在孤儿凭证（通道已不在登记表）：{sorted(orphans)[:5]}"
                       f"，共 {len(orphans)} 件；本机实测记录不得随包发布")
    n_data = len([p for p in SUITE.glob("data/**/*") if p.is_file()]) if (SUITE / "data").is_dir() else 0
    if n_data:
        warn("CLEAN", f"包内含 {n_data} 件本机运行数据（data/），发布前须清空："
                      f"这些是 check／fetch_official 在本机的实测记录，不属于发布内容")
    else:
        ok("CLEAN", "包内无本机运行数据（data/ 为空或不存在），符合发布口径")
    leak, marks = [], ("素材称", "素材口径", "素材未载", "素材转述", "原始素材",
                       "整理稿", "整理时", "整理期",
                       "corpus/mined", "[forms-", "[regime-", "[asia-", "[research-")
    scan = [p for p in list(SUITE.rglob("*.md")) + list(SUITE.rglob("*.yaml")) +
            list(SUITE.rglob("*.json")) + list(SUITE.rglob("*.py"))
            if p.resolve() != Path(__file__).resolve()]  # 本文件必然含标记字面量，自证清白的例外
    for p in scan:
        low = p.read_text(encoding="utf-8", errors="ignore")
        if any(k in low for k in marks):
            leak.append(str(p.relative_to(SUITE)))
    if leak:
        fail("CLEAN", f"出现内部编制词汇/私有语料溯源标记：{leak[:5]}")
    else:
        ok("CLEAN", f"无内部编制词汇与私有语料溯源标记残留（扫描 {len(scan)} 个文件）")
    # Check for TODO markers in entry instructions and references
    todos = []
    for p in [SUITE / "SKILL.md"] + list(SUITE.rglob("skills/*/SKILL.md")) + \
             list((SUITE / "references").glob("*.md")) + list((SUITE / "assets/templates").glob("*.md")):
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "TODO:" in text or "TODO " in text:
            todos.append(str(p.relative_to(SUITE)))
    if todos:
        fail("CLEAN", f"入口指令含未完成 TODO 标记：{todos[:5]}")


# ── RUNTIME ─────────────────────────────────────────────────────────────
def run(cmd, timeout=5):
    try:
        r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, cwd=str(SUITE), timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 2, f"子脚本超时（{timeout}秒）"


def check_runtime(fix: bool, workdir):
    scripts = sorted((SUITE / "scripts").glob("*.py"))
    nonexec = [p.name for p in scripts if not p.stat().st_mode & 0o111]
    if nonexec and fix:
        for p in scripts:
            p.chmod(0o755)
        ok("RUN", "已补 scripts/*.py 可执行位")
    elif nonexec:
        warn("RUN", f"脚本无可执行位（--fix 自动补）：{nonexec}")
    else:
        ok("RUN", "scripts/*.py 权限正常")

    code, out = run([str(SUITE / "scripts" / "route.py"), "--list", '--json'], timeout=5)
    if code != 0:
        fail("RUN", f"route.py --list 失败：{out[:200]}")
        return
    try:
        discovered = json.loads(out)['subskills']
        ok('RUN', f'route.py --list --json 正常（{len(discovered)} 个子技能）')
    except (ValueError, KeyError, TypeError):
        fail('RUN', 'route --list --json 未返回合法清单')
    # Discover every CLI rather than hard-code a fictitious script count.
    for script in scripts:
        if script.name.startswith('_') or 'ArgumentParser' not in script.read_text(encoding='utf-8'):
            continue
        code, out = run([str(script), '--help'])
        if code:
            fail('RUN', f'{script.name} --help 失败：{out[:180]}')
    from verify_suite import MATRIX_FILES
    with tempfile.TemporaryDirectory() as td:
        sample = Path(td) / 'invalid.yaml'
        sample.write_text('schema: 999\n', encoding='utf-8')
        for module, _ in MATRIX_FILES.values():
            script = SUITE / 'scripts' / (module + '.py')
            if not script.exists():
                fail('RUN', f'缺少矩阵运行模块 {script.name}')
                continue
            stage = {'case_matrix':'draft','clause_audit':'report','enforcement_matrix':'forecast'}[module]
            code, out = run([str(script), 'check', '--in', str(sample), '--stage', stage, '--json'])
            try:
                result = json.loads(out)
                if code != 4 or not isinstance(result.get('errors'),list):
                    raise ValueError('schema拒绝不符合约定')
                ok('RUN', f'{script.name} CLI schema拒绝冒烟通过')
            except (ValueError, AttributeError):
                fail('RUN', f'{script.name} CLI schema冒烟失败：exit={code}')

    code, out = run([str(SUITE / "scripts" / "fetch_official.py"), "applicable", "--inst", "siac",
                     "--commencement", "2026-07-01"], timeout=5)
    if code != 0:
        warn("RUN", f"版本判定示例未通过（需人工确认版本口径）：{out[:160]}")
    else:
        try:
            ok("RUN", "applicable 按启动日定版本可用：" + json.loads(out)["edition"])
        except Exception:  # noqa: BLE001
            ok("RUN", "applicable 退出码 0")

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        legal = d / "t.md"
        legal.write_text(
            "---\ntitle: Smoke\ncase: smoke\ntoc: true\n---\n# Request\nIntro line.\n"
            "~ unnumbered\n- bullet\n| a | b |\n|---|---|\n| c | d\\|e |\n"
            "Rule 5 says so. [source:siac-2025 | x | Rule 5 | https://e | 校验 2026-01-01]\n",
            encoding="utf-8")
        memo = d / "m.md"
        memo.write_text("---\ntitle: 说明\nmode: memo\n---\n## 一、作用\n"
                        "Rule 5 says so. [source:siac-2025 | x | Rule 5 | https://e | 校验 2026-01-01]\n", encoding="utf-8")
        outs = []
        for src, mode in ((legal, "legal"), (memo, "memo")):
            o = d / (src.stem + ".docx")
            code, out = run([str(SUITE / "scripts" / "render_docx.py"), "--in", str(src), "--out", str(o),
                             "--mode", mode], timeout=5)
            if code not in (0, 3):
                fail("RUN", f"render_docx {mode} 失败 exit={code}：{out[:200]}")
                continue
            with zipfile.ZipFile(o) as z:
                names = set(z.namelist())
                doc = z.read("word/document.xml").decode("utf-8", "ignore") if "word/document.xml" in names else ""
            missing = [q for q in DOCX_PARTS if q not in names]
            has_src = "source:siac-2025" in doc
            if missing:
                fail("RUN", f"{mode} 渲染产物缺部件：{missing}")
            elif mode == "legal" and has_src:
                fail("RUN", "legal 模式未剥离 [source:…] 标记")
            elif mode == "memo" and not has_src:
                fail("RUN", "memo 模式不应剥离 [source:…] 标记")
            else:
                outs.append(mode)
        if len(outs) == 2:
            ok("RUN", "渲染冒烟通过：legal 剥离来源标记、memo 保留，部件齐备（含转义竖线表格）")

    code, out = run([str(SUITE / "scripts" / "verify_suite.py"), "--templates"])
    if code != 0:
        fail("RUN", f"模板体检失败：{out[:240]}")
    else:
        try:
            j = json.loads(out)
            ok("RUN", f"verify_suite --templates：{j.get('decision', '?')}，扫描 {j.get('scanned', '?')} 份模板")
        except json.JSONDecodeError:
            ok("RUN", "verify_suite --templates 通过")

    code, out = run([str(SUITE / "scripts" / "verify_suite.py"), "--selftest"])
    if code != 0:
        fail("RUN", f"核验器自检失败：{out[:240]}")
    else:
        ok("RUN", "verify_suite --selftest 通过（PAIR/FILL/CITE/XREF/DIALECT/DOCX 均在跑）")

    from _visual import font_environment
    fonts=font_environment()
    if fonts['cjk']!='available':
        warn('FONT', fonts['message'])
    else:
        ok('FONT', fonts['message'])

    cfg = None
    for base in [workdir] if workdir else []:
        if base and (base / ".arbitration-config.md").exists():
            cfg = base / ".arbitration-config.md"
            break
    if cfg:
        txt = cfg.read_text(encoding="utf-8", errors="ignore")
        slots_found = re.findall(r"^-\s*slot\((\w+)\)", txt, re.M)
        if not slots_found:
            warn("CFG", f"{cfg} 无任何 slot 配置（配置为空或格式无效）")
        else:
            unset = re.findall(r"^-\s*slot\((\w+)\)\s*:\s*(\[\[.*|UNBOUND|PENDING|)$", txt, re.M)
            if unset:
                warn("CFG", f"{cfg} 仍有未绑定槽位：{[s[0] for s in unset]}")
            else:
                ok("CFG", f"能力槽配置已存在：{cfg}")
    else:
        ok("CFG", "安装检查不要求客户案件配置；实际办案时用 --workdir 检查对应案件")


def check_rule_audit():
    """静态规则闸门：条号、天数、金额、门槛必须绑定官方来源，否则不得安装。"""
    try:
        from rule_audit import audit
    except ImportError as exc:  # noqa: BLE001
        fail("RULE", f"无法加载 rule_audit.py：{exc}")
        return
    result = audit(SUITE)
    if result["decision"] == "RULE_AUDIT_PASS":
        ok("RULE", f"静态规则审计通过：{result['scanned']['files']} 个文件、{result['scanned']['anchors']} 条已核验锚点、0 处未绑定表述")
        return
    parts = []
    if result["violations"]:
        first = result["violations"][0]
        parts.append(f"{len(result['violations'])} 处未绑定规则表述（首处 {first['file']}:{first['line']}）")
    if result["registry"]["banned_keys"]:
        parts.append(f"{len(result['registry']['banned_keys'])} 个登记表禁用字段")
    if result["registry"]["rule_like_strings"]:
        parts.append(f"{len(result['registry']['rule_like_strings'])} 处登记表规则性文本")
    if result["errors"]:
        parts.append(f"{len(result['errors'])} 个结构错误（{result['errors'][0]}）")
    fail("RULE", "静态规则审计未通过：" + "；".join(parts))


def main() -> int:
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-official", action="store_true", help="仅输出首次取文指引，不联网")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--workdir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument('--check', action='store_true', help='只读全量安装检查，输出JSON，不修改权限')
    a = ap.parse_args()
    if a.check and a.fix:
        ap.error('--check 不可与 --fix 同时使用')
    a.json = a.json or a.check
    results.clear()

    if a.seed_official:
        from fetch_official import load, iter_sources, manual_steps
        print(json.dumps({'network_accessed':False,'instructions':'按本案所需 source-id 选择取文；fetch 或人工 import 后再 lookup。缓存不随发布包分发。',
                          'sources':[{'id':sid,**manual_steps(sid,item)} for _,sid,bucket,item in iter_sources(load()) if bucket=='rules']},ensure_ascii=False,indent=2))
        return 0
    deps_ok = check_deps()
    if not deps_ok:
        emit(a.json, 3)
        return 3
    data = load_suite_yaml()
    ids = check_tree(data)
    check_frontmatter(ids)
    check_refs(ids)
    check_reg(load_registry(), ids)
    check_rule_audit()
    check_research_sources()
    check_docs(ids)
    check_clean()
    check_runtime(a.fix, Path(a.workdir).expanduser() if a.workdir else None)
    emit(a.json, 2 if any(r["state"] == "FAIL" for r in results) else 0)
    return 2 if any(r["state"] == "FAIL" for r in results) else 0


def emit(as_json: bool, exit_code: int) -> None:
    counts = {}
    for r in results:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    if as_json:
        print(json.dumps({"suite": SUITE.name, "counts": counts, "exit": exit_code, "checks": results},
                         ensure_ascii=False, indent=2))
        return
    width = max(len(r["check"]) for r in results)
    for r in results:
        print(f"{r['state']:<5} {r['check']:<{width}}  {r['msg']}")
    print(f"\n合计：OK {counts.get('OK', 0)}｜WARN {counts.get('WARN', 0)}｜FAIL {counts.get('FAIL', 0)}"
          f"｜exit {exit_code}（{'可安装' if exit_code == 0 else '不可安装'}）")


if __name__ == "__main__":
    sys.exit(main())
