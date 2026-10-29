#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""官方规则与指引的实时调取、版本适用判定与来源凭证维护。

数据源：assets/sources-registry.json（可由用户或维护者追加条目）
本地缓存：data/official/<id>.pdf 或 .html 为原始件，<id>.md 为派生文本；旧 .txt 仅读兼容。
凭证：data/_provenance/<id>.json。干净安装先用 install_suite.py --seed-official 获取取文指引。

用法：
  python3 fetch_official.py applicable --inst icc --commencement 2026-07-01 [--ruleset <族名或 source-id>]
  python3 fetch_official.py anchor [--inst icc] [--stale-days 90]
  python3 fetch_official.py check [--inst siac] [--source-id <id>] [--timeout 20]
  python3 fetch_official.py fetch <source_id> [--to-md]
  python3 fetch_official.py import <source_id> --file <path> --origin <url> --kind <official|mirror|browser> --retrieved <YYYY-MM-DD>
  python3 fetch_official.py verify <source_id> --by <核验人> --scope <范围> --edition <版本> [--locator <定位> ...]
  python3 fetch_official.py cite <source_id> --locator <定位> [--edition <版本>] [--date <verified_at>] [--workdir <案件目录>]
  python3 fetch_official.py lookup <source_id> --pattern "Rule 5" [--max 12]
  python3 fetch_official.py report
退出码：0 = 根据登记表得到候选版本；不代表适用性或条文已经核验；其中"官网抓不动"仅披露不阻断（decision=APPLICABLE_EDITION、citation_ready=false）。
       2 = 硬闸门，继续即会写错东西：适用版本按日期定不了（NO_DATED_EDITIONS 无任何生效日期、NO_ELIGIBLE_EDITION 启动日落在全部版本窗口之外）、
         命中版本置信度低须人工核对（LOW_CONFIDENCE_MANUAL_CHECK）、输入非法、注册表本身坏了、同机构并行规则族未指明（一个 --ruleset 即可解开）、
         引用条件不满足（CITATION_BLOCKED）。
原则：抓不到最新文本不是停止工作的理由，而是必须向用户披露的理由；但连"适用哪一版"都定不了或版本可信度低时，宁可停手向机构/官网确证，绝不臆定版本号或回填未来生效规则、绝不引用未逐字核对的条号。
取文政策：正文下载前先按目标站 robots.txt 判定本 UA 可否抓取，禁止时输出 NEEDS_MANUAL 转人工取文与 import 登记，不绕过站点限制；robots.txt 本身取不到时按通行做法放行。
引用：cite 是唯一生成 [source:] 标记的入口；它要求 legal_verified、正文缓存、核验版本与定位覆盖同时成立，日期一律取 verified_at。
"""
from __future__ import annotations

from _safe_http import public_urlopen, validate_public_url, UnsafeURL
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import tempfile
import collections
import hashlib
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import urllib.parse
import urllib.robotparser
from datetime import date, datetime
from pathlib import Path

SUITE = Path(__file__).resolve().parent.parent
REG = SUITE / "assets" / "sources-registry.json"
DATA = Path(os.environ.get("RULESUITE_DATA_DIR", str(SUITE / "data"))).expanduser().resolve()
OFFICIAL = DATA / "official"
PROV = DATA / "_provenance"
# UA 必须以产品 token 开头：robots.txt 的 user-agent 行按前缀匹配 UA，
# 写成 "Mozilla/5.0 (compatible; RulesuiteBot/...)" 会让站点针对本 bot 的允许与禁止行全部失效。
UA = os.environ.get("RULESUITE_USER_AGENT", "RulesuiteBot/2.0 (rulesuite fetch_official)")

SAFE_ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]*$')
MAX_ID_LEN = 128

FLAT_LAYERS = [
    ("statutes", "statute"),
    ("treaties", "treaty"),
    ("soft_law", "soft_law"),
    ("open_data", "open_data"),
    ("community_and_guidance", "guidance"),
    ("drafting_instruments", "drafting"),
    ("model_clauses", "model_clause"),
    ("china_judicial_review", "cn_review"),
    ("benchmarks", "benchmark"),
]


def load() -> dict:
    return json.loads(REG.read_text(encoding="utf-8")) or {}


def safe_id(sid: str) -> bool:
    if not isinstance(sid, str) or len(sid) > MAX_ID_LEN or len(sid) == 0:
        return False
    if not SAFE_ID_RE.match(sid):
        return False
    if any(c in sid for c in '\x00\n\r\t\\'):
        return False
    return True


def validate_date(s: str):
    try:
        return date.fromisoformat(s) if isinstance(s, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else None
    except (ValueError, TypeError):
        return None


def is_file_safe(path: Path) -> bool:
    try:
        if not path.exists():
            return False
        if not path.is_file():
            return False
        resolved = path.resolve()
        official_resolved = OFFICIAL.resolve()
        try:
            resolved.relative_to(official_resolved)
            return not path.is_symlink()
        except ValueError:
            return False
    except (OSError, ValueError):
        return False


def verify_cache(sid: str) -> bool:
    if not safe_id(sid):return False
    prov=read_prov(sid)
    expected=prov.get('sha256')
    if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):return False
    for suffix in ('.pdf','.html','.md','.txt'):
        p=OFFICIAL/(sid+suffix)
        if not is_file_safe(p):continue
        try:
            data=p.read_bytes()
            if not data:continue
            if suffix=='.pdf' and not data.startswith(b'%PDF-'):return False
            if hashlib.sha256(data).hexdigest()==expected:return True
        except OSError:return False
    return False


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".download-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_prov(source_id: str, data: dict) -> Path:
    if not safe_id(source_id):
        raise ValueError("invalid source id")
    p = PROV / f"{source_id}.json"
    data = dict(data)
    data.setdefault("_checked_at", date.today().isoformat())
    atomic_write(p, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    return p


def read_prov(source_id: str) -> dict:
    p = PROV / f"{source_id}.json"
    if not safe_id(source_id) or not p.exists() or p.is_symlink():
        return {}
    try:
        p.resolve().relative_to(PROV.resolve())
        value = json.loads(p.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def iter_sources(reg: dict):
    """产出 (institution_id, source_id, kind, obj)。"""
    for inst, meta in (reg.get("institutions") or {}).items():
        for bucket in ("rules", "companions", "fees", "statute"):
            v = meta.get(bucket)
            if isinstance(v, dict):
                v = [dict(v, _bucket=bucket)]
            for item in (v or []):
                if isinstance(item, dict) and item.get("id"):
                    yield inst, item["id"], bucket, item
        for bucket in ("filing", "_watch", "watch", "note"):
            v = meta.get(bucket)
            if isinstance(v, dict) and (v.get("url") or v.get("landing")):
                yield inst, f"{inst}-{bucket.strip('_')}", "filing", v
    for key, label in FLAT_LAYERS:
        for item in (reg.get(key) or []):
            if isinstance(item, dict) and item.get("id"):
                yield item.get("juris", label), item["id"], label, item


def urls_of(item: dict) -> dict:
    out = {}
    for k, v in item.items():
        if isinstance(v, str) and v.startswith("http"):
            out[k] = v
    return out


def download_target(item: dict) -> str:
    """自动下载目标：只认规范 download 或旧的 PDF 字段；绝不回退 landing/url。

    landing 是人工查看页，把它当自动下载目标会把 HTML 落盘成“规则正文”。
    """
    value = item.get("download")
    if isinstance(value, str) and value.startswith("https://"):
        return value
    for key in ("pdf", "pdf_zh", "pdf_en", "pdf_url"):
        value = item.get(key)
        if not isinstance(value, str) or not value.startswith("https://"):
            continue
        path = value.split("?", 1)[0].lower()
        if path.endswith(".pdf") or str(item.get("content_type", "")).lower() == "application/pdf":
            return value
    return ""


def canonical_url(item: dict) -> str:
    """引用使用的登记地址：优先可下载正文，其次落地页；绝不回退到 alt/mirror。"""
    for key in ("download", "download_en", "pdf", "pdf_zh", "pdf_en", "landing", "landing_en", "url"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            return value
    return ""


def http_probe(url: str, timeout: int = 20, download: bool = False):
    if not url.startswith("https://"):
        return {"url": url, "status": 0, "error": "URL 须为 https://"}
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with public_urlopen(req, timeout=timeout, context=ctx) as r:
            body = r.read(32 * 1024 * 1024 + 1) if download else r.read(2048)
            if len(body) > 32 * 1024 * 1024:
                raise ValueError("响应超过 32 MiB 限额")
            head = {k.lower(): v for k, v in r.headers.items()}
            return {"url": url, "status": r.status, "final_url": r.geturl(),
                    "last_modified": head.get("last-modified"), "etag": head.get("etag"),
                    "content_type": head.get("content-type"), "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest() if download else None,
                    "_body": body if download else None}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "error": f"HTTPError {e.code}"}
    except Exception as e:
        return {"url": url, "status": 0, "error": f"{type(e).__name__}: {e}"}


_ROBOTS_CACHE: dict = {}


def robots_allowed(url: str, timeout: int = 20):
    """下载正文前遵守目标站 robots.txt。

    返回 (allowed, robots_url)。robots.txt 取不到、非 200 或解析失败时按通行做法放行——
    把"读不到政策"当成"禁止"会让大量官方站点整体转人工，反而降低取文质量。
    """
    if not url.startswith("https://"):
        return True, ""
    parts = urllib.parse.urlsplit(url)
    root = f"{parts.scheme}://{parts.netloc}/"
    robots_url = root + "robots.txt"
    parser = _ROBOTS_CACHE.get(root)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        try:
            probe = http_probe(robots_url, timeout=timeout, download=True)
        except Exception:
            probe = {}
        body = probe.get("_body")
        if probe.get("status") == 200 and isinstance(body, bytes):
            try:
                parser.parse(body.decode("utf-8", "replace").splitlines())
            except Exception:
                parser.allow_all = True
        else:
            parser.allow_all = True
        _ROBOTS_CACHE[root] = parser
    try:
        return bool(parser.can_fetch(UA, url)), robots_url
    except Exception:
        return True, robots_url


def _rule_family(sid: str) -> str:
    return re.sub(r"-\d{4}$", "", sid)


def rule_set_of(r: dict) -> str:
    """规则族：优先用登记时显式声明的 rule_set，缺失才从 source-id 前两段推断。
    注意与机构级 family（地域分组）无关。"""
    return str(r.get("rule_set") or _rule_family(r["id"]))


def group_rule_sets(rules: list) -> dict:
    """同族多版本＝按生效日排序的历史；附属文书不参与族的竞争。

    只有"当事人要在其间择一适用"的记录才参加竞争：无 role、role=primary、role=alternative。
    其余 role（supplementary／annex／companion／foundation 等）一律视为随主规则集一并适用之附属文书。
    """
    families, supplements = {}, []
    for r in rules:
        if str(r.get("role", "")).lower() not in ("", "primary", "alternative"):
            supplements.append(r)
            continue
        families.setdefault(rule_set_of(r), []).append(r)
    return {"families": families, "supplements": supplements}


UNVERIFIED_DISCLOSURE = "未核验最新仲裁规则的可适用性"


def source_state(sid: str, item: dict) -> dict:
    """分层来源状态：抓取策略、抓取新鲜度、正文缓存、法律核验、引用资格。

    抓取可达或缓存新鲜都不等于法律核验；只有 legal_verified 且正文缓存与
    verified_at 齐备时 citation_ready 才为真。具体定位是否覆盖由 cite 复核。
    """
    prov = read_prov(sid)
    cached = verify_cache(sid)
    policy = str(item.get("fetch") or prov.get("fetch_policy") or "ok").lower()
    if policy not in ("ok", "blocked", "manual"):
        policy = "manual"
    fetch_state = str(prov.get("state") or "UNCHECKED")
    checked = validate_date(prov.get("_checked_at"))
    fetch_fresh = bool(checked and 0 <= (date.today() - checked).days <= 90)
    legal = legal_status(sid)
    verified_at = legal.get("verified_at") or None
    verified_by = legal.get("verified_by") or None
    verified_scope = legal.get("verified_scope") or None
    edition = str(prov.get("verified_edition") or "").strip() or None
    raw_locators = prov.get("verified_locators")
    locators = ([x.strip() for x in raw_locators if isinstance(x, str) and x.strip()]
                if isinstance(raw_locators, list) else [])
    hashes = prov.get("verified_hashes")
    legal_verified = bool(legal.get("legal_verified") and verified_by and verified_scope
                          and validate_date(verified_at) and edition
                          and isinstance(hashes, dict) and hashes)
    citation_ready = bool(legal_verified and cached and verified_at)
    if citation_ready:
        reason = "已有通过哈希校验的核验正文；具体定位须由 cite 在核验范围内复核"
    elif not cached:
        if policy in ("blocked", "manual"):
            reason = (f"该站点仅允许人工取文（fetch={policy}）；已导入并核验的正文仍可引用，"
                      "当前尚无通过哈希校验的正文缓存")
        elif not download_target(item):
            reason = "登记条目无官方 PDF 下载地址，须人工取文并导入后核验"
        else:
            reason = "尚无通过哈希校验的正文缓存：先 fetch 或导入正文并取得文本层"
    else:
        missing = []
        if legal.get("legal_verified") is not True:
            missing.append("凭证未标记 legal_verified")
        if not verified_by:
            missing.append("缺核验人")
        if not verified_scope:
            missing.append("缺核验范围")
        if not validate_date(verified_at):
            missing.append("缺有效核验日期")
        if not edition:
            missing.append("缺核验版本（重做 verify --edition）")
        if not (isinstance(hashes, dict) and hashes):
            missing.append("缺核验哈希")
        reason = "已有正文缓存但未完成法律核验：" + "；".join(missing or ["核验凭证不完整"])
    return {
        "fetch_policy": policy,
        "fetch_state": fetch_state,
        "text_cached": bool(cached),
        "fetch_fresh": fetch_fresh,
        "fetch_checked_at": prov.get("_checked_at") or None,
        "legal_verified": legal_verified,
        "verified_at": verified_at if legal_verified else None,
        "verified_by": verified_by if legal_verified else None,
        "verified_scope": verified_scope if legal_verified else None,
        "verified_edition": edition if legal_verified else None,
        "verified_locators": locators if legal_verified else [],
        "citation_ready": citation_ready,
        "reason": reason,
    }


def emit_unverified(decision: str, reason: str, action: str, **extra) -> int:
    """适用版本无法按启动日确证：这是硬闸门（退出码 2），必须向机构/官网确证后方可继续。
    与"官网抓不动"不同——后者是版本已定、仅文本未核验（见 APPLICABLE_EDITION + citation_ready=false，仍退出 0）；
    此处连适用哪一版都定不了，继续就会臆定版本号或回填未来生效规则，故阻断。不输出 edition。"""
    out = {"decision": decision,
           "blocking": True,
           "disclosure": UNVERIFIED_DISCLOSURE,
           "must_disclose_to_user": True,
           "citation_ready": False,
           "source_state": {"fetch_policy": None, "fetch_state": "UNCHECKED",
                            "text_cached": False, "fetch_fresh": False, "fetch_checked_at": None,
                            "legal_verified": False, "verified_at": None, "verified_by": None,
                            "verified_scope": None, "verified_edition": None,
                            "verified_locators": [], "citation_ready": False, "reason": reason},
           "citation_instruction": "适用版本未确证：不得生成 [source:] 标记，条号一律写 [[适用规则条号待官方文本核对]]。",
           "reason": reason,
           "action": action,
           "drafting_rule": "适用版本未确证：文书中所有条号与天数写 [[适用规则条号待官方文本核对]] 占位，"
                            "不得引用具体条文号；《中文审阅说明》风险节须原样写出 disclosure 与 reason。"}
    out.update(extra)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2


# ── applicable ──
def selection_date(rule):
    """A consolidated edition cannot be auto-selected before its own lower bound."""
    effective=validate_date(str(rule.get('effective')))
    lower=validate_date(str(rule.get('selection_from',rule.get('effective'))))
    return max(effective,lower) if effective and lower else None


def cmd_applicable(a, reg) -> int:
    meta = (reg.get("institutions") or {}).get(a.inst)
    if not meta:
        print(json.dumps({"error": f"注册表无该机构 {a.inst}",
                          "known": list((reg.get('institutions') or {}).keys())}, ensure_ascii=False))
        return 2
    raw_rules = meta.get("rules") or []
    if isinstance(raw_rules, dict):
        raw_rules = [raw_rules]
    no_id = [i for i, r in enumerate(raw_rules) if isinstance(r, dict) and not r.get("id")]
    if no_id:
        print(json.dumps({"decision": "REGISTRY_SCHEMA",
                          "error": f"机构 {a.inst} 的 rules 第 {no_id} 项缺 id：注册表本身坏了，须先修 assets/sources-registry.json",
                          "action": "这不是时效问题，不能降级引用：补全 source-id 后重跑"}, ensure_ascii=False, indent=2))
        return 2
    all_rules = [r for r in raw_rules if isinstance(r, dict) and r.get("id") and r.get("effective")]
    if not all_rules:
        return emit_unverified(
            "NO_DATED_EDITIONS",
            f"机构 {a.inst} 登记的规则条目均无生效日期，无法按启动日判版",
            "向机构秘书处/官网确认适用版本；确证前按用户提供的材料起草，条号一律占位",
            institution=a.inst,
            registered_ids=[r.get("id") for r in raw_rules if isinstance(r, dict)])
    groups = group_rule_sets(all_rules)
    families = groups["families"]
    want = getattr(a, "ruleset", None)
    if want:
        hit = {k: v for k, v in families.items()
               if k == want or any(r.get("id") == want for r in v)}
        if not hit:
            print(json.dumps({"decision": "RULESET_UNKNOWN", "asked": want,
                              "known_rule_sets": sorted(families),
                              "action": f"用 --ruleset 指定下列之一：{sorted(families)}（取自条款指向的规则页）"},
                             ensure_ascii=False, indent=2))
            return 2
        chosen_set, dated = list(hit.items())[0]
        alternatives = sorted(set(families) - {chosen_set})
    elif len(families) == 1:
        chosen_set, dated = list(families.items())[0]
        alternatives = []
    else:
        defaults = [k for k, v in families.items() if any(r.get("default") for r in v)]
        if len(defaults) != 1:
            print(json.dumps({"decision": "AMBIGUOUS_RULE_SET",
                              "action": "该机构并行登记多套规则（如国际／境内、普通／简易），条款指向哪套只能读条款或问用户；"
                                        "确证后直接重跑并加 --ruleset <下列族名或 source-id>",
                              "ask_for": "仲裁条款约定由该机构适用哪一套规则？",
                              "ruleset_flags": {k: [r["id"] for r in v] for k, v in sorted(families.items())},
                              "all_dated_editions": [{"id": r["id"], "effective": str(r["effective"])} for r in all_rules]},
                             ensure_ascii=False, indent=2))
            return 2
        chosen_set, dated = defaults[0], families[defaults[0]]
        alternatives = sorted(set(families) - {chosen_set})
    d = validate_date(a.commencement)
    if d is None:
        print(json.dumps({"error": f"非法启动日期 {a.commencement}",
                          "action": "日期须为 YYYY-MM-DD 格式且为有效日历日"}, ensure_ascii=False))
        return 2
    bad_dates = [{"id": r["id"], "effective": str(r["effective"]), "selection_from": str(selection_date(r))} for r in dated
                 if selection_date(r) is None]
    eligible = [r for r in dated if selection_date(r) is not None and selection_date(r) <= d]
    if not eligible:
        return emit_unverified(
            "NO_ELIGIBLE_EDITION",
            f"启动日 {a.commencement} 早于规则族 {chosen_set} 全部已登记版本的可自动筛选下界（历史版本覆盖不足）"
            + (f"；另有条目生效日期非法：{bad_dates}" if bad_dates else ""),
            "历史案件须由机构秘书处/官网确认当时适用版本；确证前不得回填现行版本，条号一律占位",
            institution=a.inst, commencement=a.commencement, rule_set=chosen_set,
            all_dated_editions=[{"id": r["id"], "effective": str(r["effective"]), "selection_from": str(selection_date(r))} for r in dated],
            invalid_date_entries=bad_dates,
            other_rule_sets=alternatives)
    if bad_dates:
        return emit_unverified("REGISTRY_SCHEMA", "规则族含非法日期", "修正登记表后重试", invalid_date_entries=bad_dates)
    chosen = max(eligible, key=selection_date)
    agreed = getattr(a, "agreed_edition", None)
    if agreed:
        matches = [r for r in dated if r["id"] == agreed]
        if len(matches) != 1 or selection_date(matches[0]) is None or selection_date(matches[0]) > d:
            return emit_unverified("AGREED_EDITION_INVALID", "约定版本不属选定规则族或尚未生效", "核对条款、规则族与启动日")
        chosen = matches[0]
    st = source_state(chosen["id"], chosen)
    citation_url = canonical_url(chosen)
    citation_fields = {
        "source_id": chosen["id"],
        "version": chosen.get("title") or chosen["id"],
        "locator": None,
        "url": citation_url or None,
        "verified_at": st["verified_at"],
        "ready": False,
        "blocked_reason": ("尚未在本案取得并核验正文" if not st["citation_ready"]
                           else "定位未指定：先在已核验正文中定位条号，再运行 cite"),
    }
    out = {
        "decision": "APPLICABLE_EDITION",
        "selection_basis": "express-agreement" if agreed else "registered-effective-date",
        "applicability_requires_review": True,
        "institution": a.inst,
        "commencement": a.commencement,
        "rule_set": chosen_set,
        "edition": chosen["id"],
        "title": chosen.get("title"),
        "effective": str(chosen["effective"]),
        "selection_from": str(selection_date(chosen)),
        "components": chosen.get("components", []),
        "applies_to_note": chosen.get("applies_to") or "适用条件须按所选版本官方文本的过渡条款核验；本工具不预载结论。",
        "other_editions": [{"id": r["id"], "effective": str(r["effective"]), "selection_from": str(selection_date(r))} for r in dated if r is not chosen],
        "other_rule_sets": alternatives,
        "supplementary_rule_sets": [{"id": r["id"], "title": r.get("title")} for r in groups["supplements"]],
        "confidence": chosen.get("confidence", "medium"),
        "fetch_policy": st["fetch_policy"],
        "source_state": st,
        "citation_ready": st["citation_ready"],
        "citation_fields": citation_fields,
        "citation_instruction": ("定位核对后运行 fetch_official.py cite <source-id> --locator <定位>；"
                                 "ready=false 时不得生成 [source:] 标记，改用 [[待官方文本核对]]。"),
        "reminder": "条文号必须在该版本文本中逐字核对；若该 source 尚无 data/official 缓存，先运行 fetch。",
    }
    if not st["citation_ready"]:
        out["disclosure"] = UNVERIFIED_DISCLOSURE
        out["must_disclose_to_user"] = True
        out["reason"] = st["reason"]
    if chosen.get("confidence") == "low":
        out["decision"] = "LOW_CONFIDENCE_MANUAL_CHECK"
        out["blocking"] = True
        out["citation_ready"] = False
        out["citation_fields"]["ready"] = False
        out["citation_fields"]["blocked_reason"] = "登记置信度低：取得机构官网文本逐字核对后方可引用"
        out["must_disclose_to_user"] = True
        out["action"] = (f"该版本登记置信度低（{chosen.get('note', '来源冲突或未逐字核对')}）："
                         "硬闸门：取得机构官网文本逐字核对后方可引用具体条号，确证前条号一律占位")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


# ── anchor ──
ANCHORS_FILE = SUITE / "assets" / "rule-anchors.yaml"


def load_anchors():
    """条文锚定表读取：PyYAML 缺失或解析失败都返回结构化错误，不抛异常。"""
    if not ANCHORS_FILE.exists():
        return None, "锚定表缺失：assets/rule-anchors.yaml"
    try:
        import yaml
    except ImportError:
        return None, "缺 PyYAML，无法读取锚定表：pip install pyyaml"
    try:
        data = yaml.safe_load(ANCHORS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"锚定表解析失败：{type(e).__name__}: {e}"
    if not isinstance(data, dict) or not isinstance(data.get("anchors"), dict):
        return None, "锚定表顶层结构错误：须含 anchors 映射"
    return data, None


def build_source_index(reg) -> dict:
    """source-id → (归属, 桶, 记录)。含 flat layers，使准据法/软法锚点也能解析出依据版本。"""
    idx = {}
    for owner, sid, bucket, item in iter_sources(reg):
        idx.setdefault(sid, (owner, bucket, item))
    return idx


def newer_in_family(idx: dict, basis_id: str) -> dict | None:
    """同族内是否已有更晚生效的版本——这是"机构修订了规则"的机器可检信号。
    只与同一归属、同一桶（即同一套规则）的条目比较：费率表与指引不能冒充规则新版。"""
    owner, bucket, rec = idx[basis_id]
    fam = rule_set_of(rec)
    peers = [r for (o, b, r) in idx.values()
             if o == owner and b == bucket and rule_set_of(r) == fam
             and validate_date(str(r.get("effective") or "")) is not None]
    if not peers:
        return None
    newest = max(peers, key=lambda r: validate_date(str(r["effective"])))
    if newest["id"] == basis_id:
        return None
    return {"id": newest["id"], "title": newest.get("title"), "effective": str(newest.get("effective"))}


def cmd_anchor(a, reg) -> int:
    data, err = load_anchors()
    if err:
        print(json.dumps({"decision": "ANCHORS_UNREADABLE", "error": err,
                          "action": "锚定表不可用时，所有条号一律按未核处理并写占位；不得引用具体条号"},
                         ensure_ascii=False, indent=2))
        return 2
    idx = build_source_index(reg)
    freshness = int(data.get("freshness_days") or 90)
    if a.stale_days:
        freshness = int(a.stale_days)
    today = date.today()
    kept = {k: v for k, v in data["anchors"].items()
            if not a.inst or str(v.get("institution")) == a.inst}
    if a.inst and not kept:
        print(json.dumps({"decision": "ANCHORS_NO_MATCH", "inst": a.inst,
                          "known": sorted({str(v.get('institution')) for v in data['anchors'].values()})},
                         ensure_ascii=False, indent=2))
        return 2
    revision, warn, verified = [], [], []
    for key in sorted(kept):
        v = kept[key] or {}
        basis = v.get("basis_source")
        status = str(v.get("status") or "")
        item = {"anchor": key, "institution": v.get("institution"), "locator": v.get("locator"),
                "basis_source": basis, "status": status, "in_matrix": v.get("in_matrix"), **(legal_status(basis) if basis else {})}
        vd=validate_date(item.get('verified_at'))
        item['legal_stale']=bool(vd and (today-vd).days>freshness)
        if not basis:
            item["verdict"] = "UNANCHORED"
            item["action"] = "线索未归版：按未核处理，现查 applicable 取现行版本后补 basis_source"
            warn.append(item)
            continue
        if basis not in idx:
            item["verdict"] = "ORPHAN_BASIS"
            item["action"] = f"basis_source={basis} 已不在注册表中：该锚点依据的版本记录丢失，须整体重核本机构"
            revision.append(item)
            continue
        newer = newer_in_family(idx, basis)
        if newer:
            item["verdict"] = "SUPERSEDED"
            item["current_edition"] = newer
            item["action"] = (f"注册表显示 {basis} 已被 {newer['id']}（生效 {newer['effective']}）取代："
                              f"本机构全部相关条号线索、核验问题与模板占位须一并重核")
            revision.append(item)
            continue
        if status != "verified":
            st = source_state(basis, idx[basis][2])
            item["verdict"] = "UNVERIFIED"
            item["citation_ready"] = st["citation_ready"]
            item["disclosure"] = UNVERIFIED_DISCLOSURE
            item["action"] = ("用 lookup 在 " + basis + " 文本中命中原文后方可写入文书；"
                              "抓不到官网文本就按降级处理并向用户披露" + UNVERIFIED_DISCLOSURE)
            if not st["legal_verified"]:
                item["why"] = st["reason"]
            warn.append(item)
            continue
        checked = validate_date(str(v.get("checked_at") or ""))
        if not v.get("via"):
            item["verdict"] = "VERIFIED_WITHOUT_VIA"
            item["action"] = "status=verified 必须写明 via（在哪一版文本的哪一处命中），否则视为未核"
            warn.append(item)
            continue
        if checked is None or (today - checked).days > freshness:
            item["verdict"] = "STALE_VERIFIED"
            item["age_days"] = (today - checked).days if checked else None
            item["action"] = f"核验已超 {freshness} 天：重跑 lookup 后方可引用"
            warn.append(item)
            continue
        item["verdict"] = "VERIFIED"
        verified.append(item)
    out = {"decision": "ANCHORS_OK" if not revision else "ANCHORS_REVISION_REQUIRED",
           "anchors_total": len(kept),
           "verified": len(verified),
           "unverified_or_stale": len(warn),
           "revision_required": revision,
           "revision_instructions": {
               "trigger": "注册表出现比 basis_source 更晚生效的同族版本＝机构修订了规则",
               "scope": "整机构修订：该机构全部锚点 + 受影响的核验问题、模板与子技能中的定位表述",
               "steps": ["1. applicable 取现行版本 source-id", "2. fetch 取官方正文文本层",
                         "3. lookup 逐条重锚 locator，改 rule-anchors.yaml 的 locator/basis_source/status/checked_at/via",
                         "4. 按 anchors 的 topic/mechanism 更新核验问题与模板占位；数值一律重查不回填",
                         "5. 跑 install_suite.py 的 RULE 闸门确认无残留"]},
           "warn": warn,
           "blocking": bool(revision or warn),
           "note": "本命令是诊断；锚点表不允许 unverified/absent 条目，过期或未命中锚点由 rule_audit.py 在安装时阻断。"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


# ── check ──
def check_filing(a, reg):
    rows=[]
    for inst,meta in reg.get('institutions',{}).items():
        if a.inst and inst!=a.inst:continue
        if a.source_id and a.source_id!=inst+'-filing':continue
        f=meta.get('filing',{});url=f.get('url')
        if not url:
            rows.append({'id':inst+'-filing','fetch':'unknown','checked_at':f.get('checked_at'),'reason':'无登记入口，未发请求'});continue
        try:probe=http_probe(url,timeout=a.timeout)
        except Exception as e:probe={'status':None,'error':str(e)}
        status=probe.get('status');ok=isinstance(status,int) and 200<=status<300
        f.update(fetch='ok' if ok else 'blocked',checked_at=date.today().isoformat())
        f['portal_check']={'http_status':status,'error':probe.get('error'),'scope':'入口 HTTP 可达性；未验证登录、上传、支付或完整立案流程'}
        rows.append({'id':inst+'-filing','fetch':f['fetch'],'checked_at':f['checked_at'],'probe':probe,'email_verified':False})
    if not rows:
        print(json.dumps({'error':'无匹配立案入口'},ensure_ascii=False));return 2
    # 探针结果写 DATA 侧车，不回写随包发布的 sources-registry.json：
    # REG 不受 RULESUITE_DATA_DIR 重定向，回写会让只读安装失败，并使磁盘内容与已审计的发布内容不一致
    side = DATA / "filing_portal_check.json"
    atomic_write(side, (json.dumps({'checked_at': date.today().isoformat(),
                                    'scope': '入口 HTTP 可达性；未验证登录、上传、支付或完整立案流程',
                                    'filing': [{k: v for k, v in x.items() if k != 'probe'} for x in rows]},
                                   ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'filing': rows, 'result_file': str(side),
                      'registry_write': 'skipped（随包登记表保持不可变）',
                      'note': '邮箱未通过网络探活核验，须人工核对官方收件说明'}, ensure_ascii=False, indent=2))
    return 0 if all(x['fetch'] == 'ok' for x in rows) else 2

def cmd_check(a, reg) -> int:
    if getattr(a,"kind",None)=="filing":return check_filing(a,reg)
    needs_human = []
    processed = 0
    seen_ids = collections.Counter()
    for inst, sid, bucket, item in iter_sources(reg):
        if a.inst and inst != a.inst:
            continue
        if a.source_id and sid != a.source_id:
            continue
        if not safe_id(sid):
            rec = {"source_id": sid, "state": "UNSAFE_ID", "action": "source-id 含不安全字符"}
            needs_human.append(sid)
            print(f"{'UNSAFE_ID':<14} {sid}")
            continue
        if seen_ids[sid] > 0:
            rec = {"source_id": sid, "state": "DUPLICATE_ID", "action": "重复 source-id，须人工澄清"}
            needs_human.append(sid)
            continue
        seen_ids[sid] += 1
        processed += 1
        fetch = str(item.get("fetch") or "ok").lower()
        u = urls_of(item)
        target = download_target(item)
        rec = {"source_id": sid, "institution": inst, "bucket": bucket,
               "title": item.get("title"), "fetch_policy": fetch,
               "download_target": target or None,
               "landing": item.get("landing") or item.get("url"),
               "targets": u}
        if item.get("note"):
            rec["note"] = item["note"]
        if fetch in ("blocked", "manual") or not target:
            rec["state"] = "NEEDS_MANUAL"
            rec["reason"] = ("登记站点仅允许人工取文" if fetch in ("blocked", "manual")
                             else "登记条目无官方 PDF 下载地址")
            rec["manual"] = manual_steps(sid, item)
            needs_human.append(sid)
        else:
            probe = http_probe(target, timeout=a.timeout)
            rec["probe"] = probe
            ok_status = isinstance(probe.get("status"), int) and 0 < probe["status"] < 400
            is_pdf = "pdf" in (probe.get("content_type") or "").lower()
            if ok_status and is_pdf:
                rec["state"] = "REACHABLE"
            elif ok_status:
                # landing 可达或返回 HTML 不等于规则正文可达；绝不把页面当 PDF 正文。
                rec["state"] = "NEEDS_MANUAL"
                rec["reason"] = "下载地址返回非 PDF（可能是 HTML 页面），须人工下载 PDF 后 import"
                rec["manual"] = manual_steps(sid, item)
                needs_human.append(sid)
            else:
                rec["state"] = "UNREACHABLE"
                needs_human.append(sid)
        cache_valid = verify_cache(sid)
        rec["cached"] = cache_valid
        if not cache_valid and (OFFICIAL / f"{sid}.pdf").exists():
            needs_human.append(sid)
        old_prov = read_prov(sid)
        for k in ("sha256", "downloaded", "bytes", "origin", "source_kind", "retrieved_at", "derived_hashes", "legal_verified", "verified_by", "verified_at", "verified_scope", "verified_hashes", "verified_locators", "verified_edition", "provenance_missing"):
            if k in old_prov:
                rec[k] = old_prov[k]
        write_prov(sid, rec)
        print(f"{rec['state']:<14} cached={str(cache_valid):<5} {sid}")
    if a.source_id and processed == 0:
        print(json.dumps({"error": f"未找到 source_id={a.source_id}"}))
        return 2
    if a.inst and processed == 0:
        print(json.dumps({"error": f"机构 {a.inst} 无匹配条目"}))
        return 2
    if processed == 0 and not a.source_id and not a.inst:
        has_items_without_id = False
        for inst_k, meta in (reg.get("institutions") or {}).items():
            for bucket in ("rules", "companions", "fees", "statute"):
                v = meta.get(bucket)
                if isinstance(v, dict):
                    v = [v]
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and not item.get("id"):
                            has_items_without_id = True
        if has_items_without_id:
            print(json.dumps({"error": "注册表含缺 id 条目，须补全后方可继续"}))
            return 2
    print(json.dumps({"summary": {"needs_human": needs_human,
                                 "count_needs_human": len(needs_human)},
                      "cadence_days": reg.get("refresh_cadence_days", 90)}, ensure_ascii=False, indent=2))
    return 2 if needs_human else 0


# ── fetch ──
def manual_steps(sid, item):
    return {"official_url": item.get('landing') or item.get('url'),
            "landing": item.get('landing') or item.get('url'),
            "download_target": download_target(item) or None,
            "fallback": item.get('fallback_sources', []),
            "destination": str(OFFICIAL / (sid + '.pdf')),
            "steps": ["打开当前官方规则/费用页面；浏览器只读查看，遇登录或验证码遵循宿主流程，不绕过",
                      "保存 PDF 或浏览器所见正文为 UTF-8 txt/md，同时保存 URL、访问日期、版本及截图证据",
                      "使用 import 登记来源性质；镜像不是官方实时来源，导入不等于条文已核验",
                      "用 lookup 定位，再核对完整条文、版本、币种、税费和适用日期"],
            "import_example": f"python3 scripts/fetch_official.py import {sid} --file <local-file> --origin <actual-url> --kind <official|mirror|browser> --retrieved <YYYY-MM-DD>"}


def ensure_text(sid):
    pdf = OFFICIAL / (sid + '.pdf')
    prov = read_prov(sid)
    md = OFFICIAL / (sid + '.md')
    if is_file_safe(md) and prov.get('derived_hashes', {}).get('.md') == hashlib.sha256(md.read_bytes()).hexdigest():
        return {'decision':'TEXT_LAYER', 'file':str(md)}
    if not is_file_safe(pdf) or not verify_cache(sid):
        return {'decision':'TEXT_UNAVAILABLE', 'action':'导入正文或安装本地 PDF 解析器；扫描件需 OCR 后核对'}
    result = extract_text_layer(pdf, sid)
    if result.get('decision') == 'TEXT_LAYER':
        txt = Path(result['file'])
        atomic_write(md, txt.read_bytes())
        write_prov(sid, dict(prov, sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                   provenance_missing=not bool(prov.get('origin')), legal_verified=False,
                   derived_hashes={'.md':hashlib.sha256(md.read_bytes()).hexdigest()}))
    return result


def visible_html(body):
    from html.parser import HTMLParser
    text=body.decode('utf-8')
    if re.search(r'just a moment|checking your browser|access denied|cf-chl-|captcha',text,re.I):
        raise ValueError('拒绝反爬/验证码页面作为正文')
    class Text(HTMLParser):
        def __init__(self):super().__init__();self.hidden=0;self.parts=[]
        def handle_starttag(self,tag,attrs):
            if tag in ('script','style','noscript'):self.hidden+=1
            elif tag in ('p','div','br','h1','h2','h3','li','tr'):self.parts.append('\n')
        def handle_endtag(self,tag):
            if tag in ('script','style','noscript'):self.hidden=max(0,self.hidden-1)
        def handle_data(self,data):
            if not self.hidden:self.parts.append(data)
    parser=Text();parser.feed(text);result='\n'.join(x.strip() for x in ''.join(parser.parts).splitlines() if x.strip())
    if len(result)<30:raise ValueError('HTML 可见正文过短；请人工导出并核对')
    return result.encode('utf-8')

def cmd_import(a, reg):
    try:
        if not safe_id(a.source_id) or a.source_id not in build_source_index(reg):
            raise ValueError('未知或不安全的 source-id')
        if validate_date(a.retrieved) is None or validate_date(a.retrieved)>date.today():
            raise ValueError('retrieved 必须为非未来的 ISO 日期')
        if not re.match(r'^https://[^/]+', a.origin):
            raise ValueError('origin 必须为实际 HTTPS 来源 URL')
        source = Path(a.file)
        if source.is_symlink() or source.suffix.lower() not in ('.pdf','.html','.md','.txt'):
            raise ValueError('仅接受非符号链接 PDF/HTML/md/txt；网页快照须人工确认可见正文')
        body = source.read_bytes()
        if not body or len(body)>32*1024*1024:
            raise ValueError('文件为空或超过 32 MiB')
        ext = '.md' if source.suffix.lower()=='.txt' else source.suffix.lower()
        if ext=='.pdf' and not body.startswith(b'%PDF-'):
            raise ValueError('不是有效 PDF 字节')
        html_md = visible_html(body) if ext=='.html' else None
        if ext not in ('.pdf','.html'):
            text = body.decode('utf-8')
            if re.search(r'<(?:html|!doctype)|just a moment|checking your browser', text, re.I):
                raise ValueError('拒绝 HTML/反爬页面冒充正文')
        dest = OFFICIAL / (a.source_id + ext)
        if source.resolve()==dest.resolve():
            raise ValueError('请将导入原件放在缓存目录外')
        atomic_write(dest, body)
        for other in ('.pdf','.html','.txt','.md'):
            f=OFFICIAL/(a.source_id+other)
            if other!=ext and f.exists(): f.unlink()
        sha=hashlib.sha256(body).hexdigest()
        write_prov(a.source_id, {'source_id':a.source_id,'origin':a.origin,'source_kind':a.kind,
             'retrieved_at':a.retrieved,'sha256':sha,'downloaded':str(dest),'state':'IMPORTED',
             'legal_verified':False,'derived_hashes':{ext:sha} if ext!='.pdf' else {}})
        if html_md is not None:
            md=OFFICIAL/(a.source_id+'.md');atomic_write(md,html_md)
            write_prov(a.source_id,dict(read_prov(a.source_id),derived_hashes={'.md':hashlib.sha256(html_md).hexdigest()}))
        result=ensure_text(a.source_id) if ext in ('.pdf','.html') else {'decision':'TEXT_LAYER','file':str(dest)}
        print(json.dumps({'decision':'IMPORTED','source_id':a.source_id,'legal_verified':False,'text':result},ensure_ascii=False))
        return 0
    except (ValueError,OSError) as e:
        print(json.dumps({'decision':'IMPORT_FAILED','error':str(e)},ensure_ascii=False)); return 2


def cmd_fetch(a, reg) -> int:
    if not safe_id(a.source_id):
        print(json.dumps({"decision": "UNSAFE_ID", "action": "source-id 含不安全字符，拒绝操作"}))
        return 2
    hit = None
    for inst, sid, bucket, item in iter_sources(reg):
        if sid == a.source_id:
            hit = (inst, sid, bucket, item)
            break
    if not hit:
        print(f"未找到 source_id={a.source_id}（见 report）")
        return 2
    dup_count = sum(1 for inst, sid, bucket, item in iter_sources(reg) if sid == a.source_id)
    if dup_count > 1:
        print(json.dumps({"decision": "DUPLICATE_ID",
                          "action": f"source_id={a.source_id} 在注册表中出现 {dup_count} 次，须先消除重复"},
                         ensure_ascii=False, indent=2))
        return 2
    _, sid, _, item = hit
    if verify_cache(sid) and item.get('fetch') in ('blocked','manual'):
        result = ensure_text(sid) if a.to_md else {'decision':'CACHED', 'source_id':sid}
        print(json.dumps(dict(result, **legal_status(sid)), ensure_ascii=False))
        return 0 if result['decision'] in ('CACHED','TEXT_LAYER') else 2
    if str(item.get("fetch") or "ok").lower() in ("blocked", "manual"):
        print(json.dumps({"decision": "NEEDS_MANUAL",
                          "instruction": f"该站点仅允许人工取文。请从官方页面 {item.get('landing') or item.get('url') or ''} 下载 PDF，"
                                         f"另存为 {OFFICIAL}/{sid}.pdf，或用 import 登记已取得的官方文本，然后重跑 check。",
                          "manual": manual_steps(sid, item), "mirror_if_emergency": item.get("mirror")}, ensure_ascii=False, indent=2))
        return 2
    target = download_target(item)
    if not target:
        print(json.dumps({"decision": "NEEDS_MANUAL",
                          "instruction": "登记条目无官方 PDF 下载地址；请人工从官网下载 PDF 后 import，不以 landing 页面冒充正文",
                          "manual": manual_steps(sid, item)}, ensure_ascii=False, indent=2))
        return 2
    allowed, robots_url = robots_allowed(target)
    if not allowed:
        print(json.dumps({"decision": "NEEDS_MANUAL",
                          "instruction": f"目标站 robots.txt 不允许本 UA 抓取该正文（{robots_url}）。"
                                         f"请人工从官方页面下载 PDF 后用 import 登记已取得的官方文本；"
                                         f"如机构已授权自动取文，可用 RULESUITE_USER_AGENT 配置该授权 UA。",
                          "robots": robots_url, "download_target": target,
                          "manual": manual_steps(sid, item)}, ensure_ascii=False, indent=2))
        return 2
    OFFICIAL.mkdir(parents=True, exist_ok=True)
    # Phase 1：廉价头部探测（download=False，仅读 ≤2048 字节），只判可达性与状态，取得预期类型。
    try:
        probe = http_probe(target, timeout=30, download=False)
    except Exception as e:
        print(json.dumps({"decision": "FAILED", "error": str(e)}))
        return 2
    if not probe.get("status") or probe["status"] >= 400:
        print(json.dumps({"decision": "FAILED", "probe": probe}, ensure_ascii=False, indent=2))
        return 2
    probe_ct = (probe.get("content_type") or "").lower()
    # Phase 2：真正落盘用这一次响应，并对"这一份字节"作类型/魔数校验——绝不沿用探测阶段的结论。
    # 探测报 PDF、下载却回 HTML 或中途失败，都属"探测与落盘脱节"，必须阻断而非把 HTML 当规则正文存下。
    try:
        req = urllib.request.Request(target, headers={"User-Agent": UA})
        with public_urlopen(req, timeout=30) as dl:
            body = dl.read(32 * 1024 * 1024 + 1)
            if len(body) > 32 * 1024 * 1024:
                raise ValueError("响应超过 32 MiB 限额")
            dl_ct = ({k.lower(): v for k, v in dl.headers.items()}.get("content-type") or "").lower()
            final_url = dl.geturl()
    except urllib.error.HTTPError as e:
        print(json.dumps({"decision": "FAILED", "error": f"下载请求失败：HTTPError {e.code}",
                          "probe_status": probe.get("status")}, ensure_ascii=False))
        return 2
    except Exception as e:
        print(json.dumps({"decision": "FAILED", "error": str(e)}))
        return 2
    ct = dl_ct or probe_ct
    if not body:
        print(json.dumps({"decision": "FAILED", "error": "空内容响应"}))
        return 2
    # HTML 或非 PDF 不是网络故障：站点把下载地址重定向到页面/验证页，只能人工取 PDF 后 import。
    if "html" in ct or "html" in probe_ct or not body[:5].startswith(b'%PDF-'):
        print(json.dumps({"decision": "NEEDS_MANUAL",
                          "error": "站点返回 HTML 或非 PDF 响应，须人工从官网下载 PDF 后用 import 登记；未写入缓存",
                          "content_type": ct, "probe_content_type": probe_ct,
                          "download_target": target, "landing": item.get("landing") or item.get("url"),
                          "manual": manual_steps(sid, item)}, ensure_ascii=False, indent=2))
        return 2
    dest = OFFICIAL / f"{sid}.pdf"
    atomic_write(dest, body)
    for old_suffix in (".md", ".txt"):
        old_p = OFFICIAL / f"{sid}{old_suffix}"
        if old_p.exists():
            old_p.unlink()
    file_sha = hashlib.sha256(body).hexdigest()
    prov_data = dict(read_prov(sid),
                     source_id=sid, title=item.get("title"),
                     downloaded=str(dest), bytes=len(body),
                     sha256=file_sha, origin=target, final_url=final_url,
                     state="REACHABLE", legal_verified=False, verified_hashes={},
                     fetch_policy=item.get("fetch", "ok"),
                     confidence=item.get("confidence", "medium"),
                     _checked_at=date.today().isoformat())
    if item.get("confidence") == "low":
        prov_data["needs_manual_verify"] = True
    write_prov(sid, prov_data)
    print(f"saved {dest} ({len(body)} bytes)")
    tl = extract_text_layer(dest, sid)
    print(json.dumps(tl, ensure_ascii=False))
    if tl.get("decision") == "TEXT_LAYER":
        write_prov(sid, dict(read_prov(sid), text_layer=tl["file"],
                             text_layer_backend=tl["backend"], derived_hashes={".md": hashlib.sha256(Path(tl["file"]).read_bytes()).hexdigest()}))
    if a.to_md:
        if tl.get("decision") == "TEXT_LAYER":
            return 0
        return _to_md(dest, OFFICIAL / f"{sid}.md", sid)
    return 0


def find_parse_backend():
    """解析后端是外部可插拔依赖，不绑定某个技能的绝对路径：环境变量 → 同级技能 → 默认技能目录。"""
    roots = []
    env = os.environ.get("ARBITRATION_PARSE_BACKEND")
    if env:
        roots.append(Path(env))
    roots.append(SUITE.parent)
    roots.append(Path.home() / ".qoder" / "skills")
    for root in roots:
        if not root.is_dir():
            continue
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            be = d / "scripts" / "mineru_backend.py"
            cfg = d / "assets" / "parser-backends.yaml"
            if be.exists() and cfg.exists():
                return be, cfg
    return None


def extract_text_layer(pdf: Path, sid: str) -> dict:
    """PDF → 纯文本层（data/official/<sid>.md），供 lookup 逐字核对条号。
    依赖本地可选库，先 PyMuPDF 后 pypdf；都没有则明确降级，不抛异常。"""
    text, backend = None, None
    try:
        import fitz  # PyMuPDF
        with fitz.open(str(pdf)) as doc:
            text = "\n".join(page.get_text() for page in doc)
        backend = "pymupdf"
    except ImportError:
        pass
    except Exception as e:
        return {"decision": "TEXT_LAYER_FAILED", "error": f"pymupdf：{type(e).__name__}: {e}"}
    if text is None:
        try:
            from pypdf import PdfReader
        except ImportError:
            return {"decision": "NO_PDF_TEXT_LIB",
                    "action": "本机无 PyMuPDF/pypdf：条号核对须用 --to-md 的解析后端，"
                              "或用浏览器工具打开官网条文页（引用仍需官方 PDF 复核）"}
        try:
            text = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(pdf)).pages)
            backend = "pypdf"
        except Exception as e:
            return {"decision": "TEXT_LAYER_FAILED", "error": f"pypdf：{type(e).__name__}: {e}"}
    body = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(body.strip()) < 30:
        return {"decision": "TEXT_LAYER_THIN",
                "action": "文本层过短，疑为扫描件无 OCR：条号核对须改用 --to-md 解析后端或人工阅读原文",
                "chars": len(body)}
    out = OFFICIAL / f"{sid}.md"
    out.write_text(body, encoding="utf-8")
    return {"decision": "TEXT_LAYER", "backend": backend, "file": str(out), "chars": len(body)}


def _to_md(pdf: Path, out_md: Path, sid: str) -> int:
    if not safe_id(sid):
        return 2
    be = find_parse_backend()
    if not be:
        print(json.dumps({"decision": "NO_PARSE_BACKEND",
                          "searched": [str(SUITE.parent), str(Path.home() / ".qoder" / "skills")],
                          "instruction": "未找到 PDF 解析后端。可选项：①安装带 scripts/mineru_backend.py 与 "
                                         "assets/parser-backends.yaml 的解析技能，或用 ARBITRATION_PARSE_BACKEND "
                                         "指向其所在目录；②使用 MinerU/其他工具人工转换后放入 data/official/<id>.md；"
                                         "③暂时用浏览器工具打开官网条文页定位（引用仍需官方 PDF 复核）。"},
                         ensure_ascii=False, indent=2))
        return 2
    be, backends = be
    if out_md.exists():
        out_md.unlink()
    argv = ["python3", str(be),
            "--input", str(pdf),
            "--output-md", str(out_md),
            "--outdir", str(out_md.parent),
            "--language", "en",
            "--timeout", "2400"]
    try:
        r = subprocess.run(argv, capture_output=True, timeout=2500)
    except Exception as e:
        print(json.dumps({"decision": "PARSE_FAILED", "error": str(e)}))
        return 2
    if r.returncode != 0:
        return 2
    if not out_md.exists() or out_md.stat().st_size == 0:
        out_md.unlink(missing_ok=True)
        print(json.dumps({"decision": "PARSE_NO_OUTPUT",
                          "error": "解析器返回成功但未生成 Markdown 产物"}))
        return 2
    return 0


# ── lookup ──
def cmd_lookup(a, reg) -> int:
    if not safe_id(a.source_id):
        print(json.dumps({"decision": "UNSAFE_ID", "action": "source-id 含不安全字符"}))
        return 2
    if a.max is not None and a.max < 1:
        print(json.dumps({"decision": "INVALID_MAX", "action": "max 须为正整数"}))
        return 2
    if not verify_cache(a.source_id):
        print(json.dumps({"decision": "CACHE_UNVERIFIED", "action": "缓存缺失或哈希不匹配，请重新取得正文"}, ensure_ascii=False))
        return 2
    if (OFFICIAL / f"{a.source_id}.pdf").exists():
        result = ensure_text(a.source_id)
        if result.get("decision") != "TEXT_LAYER":
            print(json.dumps(result, ensure_ascii=False)); return 2
    for suffix in (".md", ".txt"):
        p = OFFICIAL / f"{a.source_id}{suffix}"
        if p.exists():
            if not is_file_safe(p):
                print(json.dumps({"decision": "UNSAFE_CACHE", "action": "缓存文件不在 official 目录内或为符号链接"}))
                return 2
            expected = read_prov(a.source_id).get("derived_hashes", {}).get(suffix)
            if not expected or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                print(json.dumps({"decision": "TEXT_LAYER_UNVERIFIED", "action": "文本层需从对应 PDF 重新提取并登记哈希"}, ensure_ascii=False))
                return 2
            text = p.read_text(encoding="utf-8", errors="ignore")
            try:
                pat = re.compile(a.pattern, re.I)
            except re.error as e:
                print(json.dumps({"decision": "BAD_PATTERN", "error": str(e)}))
                return 2
            hits = []
            for i, line in enumerate(text.splitlines(), 1):
                if pat.search(line):
                    hits.append({"line": i, "text": line.strip()[:400]})
                if len(hits) >= a.max:
                    break
            print(json.dumps({"source_id": a.source_id, "file": str(p), "hits": hits, **legal_status(a.source_id), "provenance": read_prov(a.source_id),
                              "note": "命中为文本层定位；起草引用前须在同一文本中确认条文完整表述与小节编号"},
                             ensure_ascii=False, indent=2))
            return 0 if hits else 2
    print(json.dumps({"decision": "NOT_CACHED", "source_id": a.source_id,
                      "action": f"python3 scripts/fetch_official.py fetch {a.source_id} --to-md，或人工下载"},
                     ensure_ascii=False, indent=2))
    return 2


# ── report ──
def legal_status(sid):
    empty={'legal_verified':False,'legal_state':'未取文本','verified_by':None,'verified_at':None,'verified_scope':None}
    if not safe_id(sid): return empty
    prov=read_prov(sid)
    hashes=prov.get('verified_hashes',{})
    texts=[ext for ext in ('.md','.txt') if is_file_safe(OFFICIAL/(sid+ext))]
    verified=bool(texts and verify_cache(sid) and prov.get('legal_verified') is True and
        isinstance(hashes,dict) and hashes and all(ext in hashes for ext in texts))
    if verified:
        verified=all(ext in ('.md','.txt','.pdf','.html') and is_file_safe(OFFICIAL/(sid+ext)) and
            hashlib.sha256((OFFICIAL/(sid+ext)).read_bytes()).hexdigest()==digest for ext,digest in hashes.items())
    return {'legal_verified':verified,'legal_state':'已核验' if verified else ('已取文本未核验' if texts else '未取文本'),
            'verified_by':prov.get('verified_by') if verified else None,
            'verified_at':prov.get('verified_at') if verified else None,
            'verified_scope':prov.get('verified_scope') if verified else None}


def cmd_verify(a, reg):
    try:
        if not safe_id(a.source_id) or a.source_id not in build_source_index(reg):raise ValueError('来源 ID 未登记')
        when = getattr(a,'date',None) or date.today().isoformat()
        if not str(a.by).strip() or not str(a.scope).strip() or not str(getattr(a,'edition',None) or '').strip() or not validate_date(when) or validate_date(when)>date.today():raise ValueError('须填写核验人、范围、--edition 及有效核验日期')
        if not verify_cache(a.source_id):raise ValueError('缓存缺失或哈希不匹配')
        prov=read_prov(a.source_id);hashes={}
        for ext in ('.md','.txt'):
            p=OFFICIAL/(a.source_id+ext)
            if is_file_safe(p):
                digest=hashlib.sha256(p.read_bytes()).hexdigest()
                if prov.get('derived_hashes',{}).get(ext)!=digest:raise ValueError('文本哈希未登记或已变化')
                hashes[ext]=digest
        if not hashes:raise ValueError('尚无可核验文本，请先 lookup 或导入文本')
        prov.update(legal_verified=True,verified_by=a.by.strip(),verified_scope=a.scope.strip(),verified_at=when,verified_hashes=hashes,verified_locators=getattr(a,'locator',None) or [],verified_edition=getattr(a,'edition',None))
        write_prov(a.source_id,prov)
        print(json.dumps(dict(source_id=a.source_id,**legal_status(a.source_id)),ensure_ascii=False));return 0
    except (ValueError,OSError,TypeError) as e:
        print(json.dumps({'decision':'CACHE_UNVERIFIED','error':str(e)},ensure_ascii=False));return 2


# ── cite ──
def cite_record(sid: str, workdir):
    """引用凭证：案件来源读 case-sources.json，否则读注册表来源的 data/_provenance。
    返回 (record, kind, source_item, error)。"""
    from _source_evidence import load_local
    if workdir:
        try:
            local = load_local(workdir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return None, None, None, f"案件来源登记无效：{exc}"
        if sid in local:
            record = local[sid]
            if not isinstance(record, dict):
                return None, None, None, "案件来源记录须为对象"
            return record, "case", None, None
    item = build_source_index(load()).get(sid)
    if item is None:
        return None, None, None, "来源未登记：注册表无此 id；案件本地来源须先写入 case-sources.json"
    return None, "registry", item[2], None


def cmd_cite(a, reg) -> int:
    from _markers import format_source_marker, source_marker_issues as marker_issues
    from _source_evidence import normalized, scope_covers, source_evidence
    from verify_suite import citation_url_issue, registry_ids

    sid = a.source_id
    locator = str(a.locator or "").strip()
    reasons = []

    def blocked():
        print(json.dumps({"decision": "CITATION_BLOCKED", "source_id": sid,
                          "blocking": True, "reasons": reasons,
                          "action": "补齐核验凭证与定位后重跑 cite；不得手工拼接 [source:] 标记"},
                         ensure_ascii=False, indent=2))
        return 2

    if not safe_id(sid):
        reasons.append("source-id 含不安全字符")
        return blocked()
    workdir = None
    if getattr(a, "workdir", None):
        workdir = Path(a.workdir).expanduser().resolve()
        if not workdir.is_dir():
            reasons.append("--workdir 不是有效目录")
            return blocked()
    record, kind, item, err = cite_record(sid, workdir)
    if err:
        reasons.append(err)
        return blocked()
    if not locator:
        reasons.append("缺 --locator：引用必须写明条号/条款/章节定位")

    if kind == "registry":
        st = source_state(sid, item)
        if not st["legal_verified"]:
            reasons.append(st["reason"])
        if not st["text_cached"]:
            reasons.append("尚未取得通过哈希校验的正文缓存")
        edition = st["verified_edition"]
        verified_at = st["verified_at"]
        locators = st["verified_locators"]
        scope = st["verified_scope"] or ""
        url = canonical_url(item)
        fetch_policy = st["fetch_policy"]
    else:
        edition = str(record.get("edition") or "").strip()
        verified_at = str(record.get("verified_at") or "").strip()
        locators = record.get("verified_locators") if isinstance(record.get("verified_locators"), list) else []
        scope = str(record.get("verified_scope") or "")
        url = str(record.get("origin") or "")
        fetch_policy = None
        if record.get("legal_verified") is not True:
            reasons.append("案件来源未标记 legal_verified")
        if not record.get("verified_by") or not scope:
            reasons.append("案件来源缺核验人或核验范围")
        if validate_date(verified_at) is None:
            reasons.append("案件来源缺有效核验日期")

    if not edition:
        reasons.append("核验凭证缺版本标签：重做 verify --edition（案件来源须登记 edition）")
    if not validate_date(verified_at):
        reasons.append("核验日期缺失或无效")
    if not url:
        reasons.append("来源无可引用 URL：先补 download/landing 并重新取文核验")
    if locator and not scope_covers(locator, locators, scope):
        reasons.append(f"核验范围未覆盖定位 {locator!r}")
    requested_edition = str(getattr(a, "edition", None) or "").strip()
    if requested_edition and edition and normalized(requested_edition) != normalized(edition):
        reasons.append(f"指定版本与核验版本不符：{requested_edition!r} != {edition!r}")
    requested_date = str(getattr(a, "date", None) or "").strip()
    if requested_date and requested_date != verified_at:
        reasons.append(f"指定日期与核验日期不符：{requested_date!r} != {verified_at!r}")
    if reasons:
        return blocked()

    try:
        marker = format_source_marker(sid, edition, locator, url, verified_at)
        table_marker = format_source_marker(sid, edition, locator, url, verified_at, table_cell=True)
    except ValueError as exc:
        reasons.append(f"引用字段无法生成合法标记：{exc}")
        return blocked()
    syntax = marker_issues(marker, registry_ids(), citation_url_issue)
    reasons.extend(x for x in syntax if not x.startswith("WARN "))
    evidence, _ = source_evidence(sid, workdir, locator=locator, edition=edition,
                                  url=url, checked_at=verified_at)
    reasons.extend(evidence)
    if reasons:
        return blocked()
    print(json.dumps({
        "decision": "CITATION_READY",
        "citation": marker,
        "citation_table_cell": table_marker,
        "fields": {"source_id": sid, "version": edition, "locator": locator, "url": url,
                   "checked_at": verified_at, "verified_at": verified_at,
                   "verified_by": (record or {}).get("verified_by") if kind == "case" else source_state(sid, item)["verified_by"],
                   "verified_scope": scope, "origin": kind, "fetch_policy": fetch_policy},
        "note": "本命令只证明核验凭证覆盖该定位；不证明条文内容适用于本案，也不写入任何文件。"
    }, ensure_ascii=False, indent=2))
    return 0

def matrix_audit(reg):
    """审计核验清单、来源登记表与锚点的一致性；不判断任何机构规则结论。"""
    matrix_path = SUITE / 'references/forum-rules-matrix.md'
    headings = ['为什么是清单而不是对照表', '单次核验流程', '十二维核验问题表',
                '机构差异只有在同一版本内才可比较', '来源标记与交付', '访问受阻时的降级路径']
    text = matrix_path.read_text(encoding='utf-8') if matrix_path.exists() else ''
    missing_headings = [h for h in headings if h not in text]
    missing_decisions = [d for d in ('HIT', 'NOT_FOUND', 'NO_TEXT', 'VERSION_UNKNOWN') if d not in text]
    institutions = reg.get('institutions', {})
    rules = [x for v in institutions.values() for x in v.get('rules', [])]
    anchors, err = load_anchors()
    anchor_errors = []
    anchor_count = 0
    open_questions = 0
    if err:
        anchor_errors.append(err)
    else:
        anchor_count = len(anchors.get('anchors') or {})
        open_questions = len(anchors.get('open_questions') or [])
        for key, item in (anchors.get('anchors') or {}).items():
            inst = item.get('institution')
            if inst not in institutions:
                anchor_errors.append(f"{key}: institution 未登记（{inst}）")
            for field in ('locator', 'basis_source', 'checked_at', 'via'):
                if not str(item.get(field, '')).strip():
                    anchor_errors.append(f"{key}: 缺 {field}")
            if item.get('status') != 'verified':
                anchor_errors.append(f"{key}: status 不是 verified")
    static = None
    try:
        from rule_audit import audit as static_audit
        result = static_audit(SUITE)
        static = {'decision': result['decision'], 'violations': len(result['violations']),
                  'registry_issues': len(result['registry']['banned_keys']) + len(result['registry']['rule_like_strings']),
                  'errors': result['errors']}
    except Exception as exc:  # noqa: BLE001
        static = {'decision': 'UNAVAILABLE', 'error': str(exc)}
    return {
        'institution_nodes': len(institutions),
        'rule_entries': len(rules),
        'fetch_distribution': dict(collections.Counter(x.get('fetch', 'unknown') for x in rules)),
        'confidence_distribution': dict(collections.Counter(x.get('confidence', 'unknown') for x in rules)),
        'matrix_checklist': {'file': str(matrix_path.relative_to(SUITE)),
                             'missing_headings': missing_headings,
                             'missing_decisions': missing_decisions},
        'anchors': {'count': anchor_count, 'open_questions': open_questions, 'errors': anchor_errors},
        'static_rule_audit': static,
        'note': '本清单不保存机构规则答案；锚点只提供条号级定位，引用前须按本案适用版本重新取文命中。'
    }

def cmd_report(a, reg) -> int:
    if getattr(a, "matrix_audit", False):
        print(json.dumps(matrix_audit(reg),ensure_ascii=False,indent=2));return 0
    rows = []
    today = date.today()
    cadence = int(reg.get("refresh_cadence_days", 90))
    unreachable_ids = []
    manual_ids = []
    invalid_prov_ids = []
    for inst, sid, bucket, item in iter_sources(reg):
        prov = read_prov(sid)
        checked = prov.get("_checked_at")
        age = None
        stale = False
        is_invalid = False
        if checked:
            d = validate_date(checked)
            if d is None:
                is_invalid = True
            else:
                age = (today - d).days
                if age < 0:
                    is_invalid = True
                else:
                    stale = age > cadence
        if is_invalid:
            invalid_prov_ids.append(sid)
        cached = verify_cache(sid)
        note = prov.get("note") or item.get("note") or ""
        state = prov.get("state", "MISSING")
        if state == "UNREACHABLE":
            unreachable_ids.append(sid)
        if state == "NEEDS_MANUAL":
            manual_ids.append(sid)
        rows.append({"id": sid, "inst": inst, "bucket": bucket,
                     "fetch": item.get("fetch", "ok"), "conf": item.get("confidence", "medium"),
                     "checked": checked or "NEVER", "age_d": age, "stale": stale,
                     "invalid_prov": is_invalid,
                     "cached": cached, "note": note, "state": state, **legal_status(sid)})
    stale = [r["id"] for r in rows if r["stale"]]
    never = [r["id"] for r in rows if r["checked"] == "NEVER"]
    uncached_manual = [r["id"] for r in rows
                       if r["fetch"] in ("blocked", "manual") and not r["cached"]]
    idx = ["# 官方数据源状态索引", "",
           f"生成：{today.isoformat()}｜刷新周期：{cadence} 天｜条目数：{len(rows)}", "",
           f"- 从未核验：{len(never)}", f"- 已过期需重核：{len(stale)}",
           f"- 需人工下载：{len(uncached_manual)}", "",
           "| source_id | 机构 | 类别 | 抓取 | 置信 | 最近核验 | 已缓存 | 备注 |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        note = r["note"] if len(r["note"]) <= 70 else r["note"][:70] + "…"
        idx.append(f"| {r['id']} | {r['inst']} | {r['bucket']} | {r['fetch']} | {r['conf']} | "
                   f"{r['checked']} | {'是' if r['cached'] else '否'} | {note} |")
    (DATA / "_index.md").parent.mkdir(parents=True, exist_ok=True)
    (DATA / "_index.md").write_text("\n".join(idx), encoding="utf-8")
    print("\n".join(idx[:12]))
    has_issues = bool(stale or never or unreachable_ids or manual_ids or invalid_prov_ids or uncached_manual)
    print(json.dumps({"stale": stale, "never_checked": never,
                      "needs_manual_download": uncached_manual,
                      "unreachable": unreachable_ids, "invalid_provenance": invalid_prov_ids,
                      "legal_status": [{k:r.get(k) for k in ("id","legal_state","legal_verified","verified_at","verified_scope","verified_by")} for r in rows],
                      "legacy_txt": [{"id":sid,"action":"旧 .txt 可继续读取；建议用 import 将外部原件重新导入为 .md，不自动改名"} for _,sid,_,_ in iter_sources(reg) if (OFFICIAL/(sid+".txt")).is_file()],
                      "missing_canonical_url_count": sum(not item.get("canonical_url") for _,_,_,item in iter_sources(reg))},
                     ensure_ascii=False, indent=2))
    return 2 if has_issues else 0


def main() -> int:
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suggest-id", help="离线建议最接近的真实来源 ID，不修改文本")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("applicable"); p.add_argument("--inst", required=True); p.add_argument("--commencement", required=True)
    p.add_argument("--ruleset", help="同一机构并行多套规则时指定规则族名或族内任一 source-id")
    p.add_argument("--agreed-edition", help="条款明确约定的 source-id；仍需人工核对过渡与强制适用条款")
    p = sub.add_parser("anchor"); p.add_argument("--inst"); p.add_argument("--stale-days", dest="stale_days", type=int)
    p = sub.add_parser("check"); p.add_argument("--inst"); p.add_argument("--source-id", dest="source_id")
    p.add_argument("--kind", choices=["filing"], help="探测立案入口可达性，结果写入 data 侧车文件（不回写随包登记表）")
    p.add_argument("--timeout", type=int, default=20)
    p = sub.add_parser("fetch"); p.add_argument("source_id"); p.add_argument("--to-md", action="store_true")
    p = sub.add_parser("lookup"); p.add_argument("source_id"); p.add_argument("--pattern", required=True); p.add_argument("--max", type=int, default=12)
    p = sub.add_parser('import'); p.add_argument('source_id'); p.add_argument('--file', required=True)
    p.add_argument('--origin', required=True); p.add_argument('--kind', choices=['official','mirror','browser'], required=True)
    p.add_argument('--retrieved', required=True)
    p = sub.add_parser('verify'); p.add_argument('source_id'); p.add_argument('--by', required=True); p.add_argument('--scope', required=True); p.add_argument('--date')
    p.add_argument('--locator', action='append', help='已逐条核验的定位，可重复；旧 --scope 须明确写定位')
    p.add_argument('--edition', help='本次核验的精确版本标签，与 source 标记一致')
    p = sub.add_parser('cite'); p.add_argument('source_id'); p.add_argument('--locator', required=True)
    p.add_argument('--edition', help='须与核验凭证的版本一致；缺省用凭证版本')
    p.add_argument('--date', help='须等于核验凭证的 verified_at；缺省用凭证日期')
    p.add_argument('--workdir', help='案件目录：先查 case-sources.json，再查注册表来源')
    p = sub.add_parser("report"); p.add_argument("--matrix-audit", action="store_true")
    a = ap.parse_args()
    reg = load()
    if a.suggest_id:
        import difflib
        ids = build_source_index(reg)
        print(json.dumps({'query': a.suggest_id, 'suggestions': [{'id': sid, 'registry': 'assets/sources-registry.json'} for sid in difflib.get_close_matches(a.suggest_id, sorted(ids), n=3)]}, ensure_ascii=False))
        return 0
    if not a.cmd:
        ap.error('需要子命令或 --suggest-id')
    if a.cmd == 'fetch':
        result = cmd_fetch(a, reg)
        if result:
            item = build_source_index(reg).get(a.source_id)
            if item:
                print(json.dumps({'decision':'MANUAL_RECOVERY','manual':manual_steps(a.source_id,item[2])},ensure_ascii=False))
        return result
    return {"applicable": cmd_applicable, "anchor": cmd_anchor, "check": cmd_check, "fetch": cmd_fetch,
            "lookup": cmd_lookup, "report": cmd_report, "import": cmd_import, "verify": cmd_verify,
            "cite": cmd_cite}[a.cmd](a, reg)


if __name__ == "__main__":
    sys.exit(main())
