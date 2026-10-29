#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态规则审计：拦截未绑定官方来源的条号、期限、金额、门槛与机制结论。

用法：
  python3 rule_audit.py                 # 审计当前技能包
  python3 rule_audit.py --root DIR      # 审计指定目录
  python3 rule_audit.py --json          # 机器可读输出

退出码：0 通过 / 2 存在未绑定规则表述或结构错误
"""
from __future__ import annotations

from _pymin import require_python
if __name__ == "__main__":
    require_python(script_name=__file__)

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from _markers import iter_markers, parse_kb_marker, parse_source_marker

SUITE = Path(__file__).resolve().parents[1]
FRESHNESS_CEILING = 90

_CN_DIGIT = "[〇零一二三四五六七八九十百千两]"
LOCATOR = re.compile(
    r"(?<![A-Za-z0-9])("
    r"(?:Art\.?|Article|Rule|Regulation|Reg\.?|Schedule|Section)\s*\d+(?:\.\d+)*(?:[A-Z])?"
    r"|§\s*\d+(?:\.\d+)*"
    r"|第\s*\d+\s*(?:[-–—至]\s*\d+\s*)*条"
    # 中文数字条号与条号区间同样属具体条号引用，不能因为写作"第三十四条"就绕过闸门。
    r"|第\s*" + _CN_DIGIT + r"+\s*条"
    r")",
    re.I,
)
# Permissive locator validator: applied ONLY to curated anchor.locator fields,
# where ranges, Chinese numerals, R-/E- codes and Para./Schedule/Annex pointers are legitimate.
ANCHOR_LOCATOR = re.compile(
    r"(?<![A-Za-z0-9])("
    r"(?:Art\.|Article|Rule|Regulation|Reg\.|Schedule|Section|Para\.|Paragraph|Annex|App\.|Sch\.)"
    r"\s*(?:[A-Z]-)?\d+(?:\.\d+)*(?:[(（][A-Za-z0-9]{1,3}[)）])?(?:[A-Z])?"
    r"|(?:R|E)-\d+"
    r"|§\s*\d+(?:\.\d+)*"
    r"|第\s*\d+\s*(?:[-–—]\s*\d+\s*)?条"
    r"|第\s*" + _CN_DIGIT + r"+\s*条"
    r"|附件\s*" + _CN_DIGIT + r"+\d*"
    r"|(?:First|Second|Third|Fourth|Fifth)\s+Schedule"
    r")",
    re.I,
)
# The anchor table registers "where to look", never "what the rule says". These
# guards keep `via` at hit evidence (date + article number + official heading).
VIA_MAX = 320
VIA_SPAN_MAX = 80
VIA_SPAN = re.compile(r"『([^』]*)』")
VIA_FRAGMENT = re.compile(r"[,，、]")
OPERATIVE_WORD = re.compile(r"\b(?:shall|must|may|should|entitle[sd]?|empower[sd]?)\b", re.I)
CONCLUSION_VERB = ("赋予", "有权", "可作", "规定", "允许", "应当", "意味着")
_CN = r"(?:[0-9][0-9,.]*|[〇零一二三四五六七八九十百千两]+)"
# 期限形态：除"N 日内"外，"答辩期限：30 天""90 天时限""(45天)""组庭后 6 个月""三十日"
# 同样是在陈述规则期限，不得因缺少"内"字而绕过绑定要求。
DAY_LIMIT = re.compile(
    r"\d+\s*(?:个)?(?:工作)?(?:日|天)(?:内|之内)"
    r"|期限(?:为|是|：|:)?\s*" + _CN + r"\s*(?:个)?(?:工作)?(?:日|天|个月)"
    r"|(?:期限|时限|期间|答辩期|答复期|反请求期|裁决期|异议期|更正期)[^。\n哪几何]{0,6}?"
    + _CN + r"\s*(?:个)?(?:工作)?(?:日|天|个月)"
    r"|" + _CN + r"\s*(?:个)?(?:工作)?(?:日|天|个月)\s*(?:时限|期限)"
    r"|[（(]\s*" + _CN + r"\s*(?:个)?(?:工作)?(?:日|天)(?:选定)?\s*[）)]"
    r"|\d+\s*个月(?:内|之内)"
    # 中文数字期限与阿拉伯数字期限等价，不能靠改写数字绕过闸门。
    r"|[〇零一二三四五六七八九十百千两]+\s*(?:个)?(?:工作)?(?:日|天)(?:内|之内)"
)
MONEY = re.compile(
    r"(?:USD|HKD|SGD|SAR|EUR|GBP|CNY|RMB|AED|MYR|KRW|JPY|INR|THB|PHP|VND|IDR)\s*[\d][\d,.]*"
    r"|(?:人民币|美元|令吉|林吉特|迪拉姆|卢比|日元|韩元|新台币|瑞士法郎|欧元|英镑)\s*[\d][\d,.]*"
    r"|(?:[US]\$|S\$|RM|HK\$|₩|€|£|¥|₫|₹|CHF|SEK)\s*[\d][\d,.]*"
    r"|[\d][\d,.]*\s*(?:万元|亿元|元(?![素旦首官音气]))"
)
THRESHOLD = re.compile(r"(?:门槛|上限|下限|费率|收费)(?:为|是|：|:)\s*[^\n]{0,12}\d")
# 国别执行结论：公约成员身份、成员数量与"某国执行便利／某法院友好"式的排序建议，
# 属逐目标核验事项（references/enforcement-jurisdictions.md 声明只提供核查问题）。
# 这一类不看来源标记——登记表的 `ny-convention-status` 是检索入口而非身份证明，
# 因此同行有 [source:...] 也不放行；写法必须改成"须按目标法域现行文本核对"。
JURISDICTION_CLAIM = (
    ("公约成员身份", r"[是为]\s*[《「\"]?纽约公约[」\"》]?[^|\[\n]{0,10}(?:缔约国|缔约方|成员国|成员)"),
    ("公约成员数量", r"\d{2,3}\s*(?:多|余|以上)?\s*(?:个|[+＋])\s*[^|\[\n]{0,6}(?:缔约国|法域|成员)"),
    ("执行友好度排序", r"避风港|执行确定性最高|执行环境良好|执行最为顺畅|执行最为便利|仲裁友好法域|执行便利"),
    ("法域友好度推荐", r"(?:应当|应该|建议|优先|宜|选择)[^。；\n]{0,14}友好[^。；\n]{0,10}(?:法域|国家|法院|仲裁地|环境|度)"),
)
UNBACKED_CLAIM = re.compile(r"sha-?256|哈希|全部锚点|逐条复核|全文已核实|全文本身已核实|取回该版")
PLACEHOLDER = re.compile(r"\[\[.*?\]\]|<[^>\n]{1,30}>|\{\{[^}\n]*\}\}")
BANNED_REGISTRY_KEYS = {
    "procedure_profiles",
    "maintenance_todos",
    "applies_to",
    "matrix_labels",
    "absent_mechanisms",
    "rule_summary",
    "rule_content",
}
BIBLIOGRAPHIC_KEYS = {"title", "name_zh", "id", "juris", "url", "landing", "pdf", "alt",
                      "canonical_url", "pdf_zh", "landing_en", "pdf_en", "download",
                      "download_en", "rules_list", "api"}
MATRIX_HEADINGS = [
    "为什么是清单而不是对照表",
    "单次核验流程",
    "十二维核验问题表",
    "机构差异只有在同一版本内才可比较",
    "来源标记与交付",
    "访问受阻时的降级路径",
]


def _date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def collect_ids(reg):
    out = set()

    def walk(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("id"), str) and obj["id"]:
                out.add(obj["id"])
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(reg)
    return out


def find_banned_keys(obj, loc=""):
    found = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{loc}/{key}"
            if key in BANNED_REGISTRY_KEYS:
                found.append({"path": here, "key": key})
            found.extend(find_banned_keys(value, here))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            found.extend(find_banned_keys(value, f"{loc}/{index}"))
    return found


def rule_like_strings(reg):
    found = []

    def walk(obj, loc, parent_key=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                walk(value, f"{loc}/{key}", key)
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                walk(value, f"{loc}/{index}", parent_key)
        elif isinstance(obj, str):
            if parent_key in BIBLIOGRAPHIC_KEYS:
                return
            masked = PLACEHOLDER.sub("", obj)
            for label, pattern in (
                ("rule_locator", LOCATOR),
                ("day_limit", DAY_LIMIT),
                ("amount", MONEY),
                ("threshold", THRESHOLD),
            ):
                match = pattern.search(masked)
                if match:
                    found.append({"path": loc, "kind": label, "text": match.group(0), "excerpt": obj[:180]})

    walk(reg, "")
    return found


def line_hits(line):
    masked = PLACEHOLDER.sub("", line)
    hits = []
    for label, pattern in (
        ("rule_locator", LOCATOR),
        ("day_limit", DAY_LIMIT),
        ("amount", MONEY),
        ("threshold", THRESHOLD),
    ):
        match = pattern.search(masked)
        if match:
            hits.append((label, match.group(0)))
    return hits


def marker_bound(line, source_ids, today, registry, kind):
    """A kb anchor binds bundled knowledge; a fresh five-field source citation binds prose."""
    for found in iter_markers(line):
        if found.example:
            continue
        if found.kind == "kb":
            if kind != "knowledge":
                continue
            _, issues = parse_kb_marker(found.raw, registry)
            if not issues:
                return True
            continue
        if kind == "knowledge":
            continue
        fields, issues = parse_source_marker(found.raw, source_ids)
        if any(not issue.startswith("WARN ") for issue in issues):
            continue
        when = _date(fields.get("checked_at"))
        if when and when <= today and (today - when).days <= FRESHNESS_CEILING:
            return True
    return False


def scan_content(root, source_ids, today, registry):
    files = [root / "SKILL.md", root / "suite.yaml"]
    files += sorted((root / "references").glob("*.md"))
    files += sorted((root / "skills").glob("*/SKILL.md"))
    files += sorted((root / "assets" / "templates").rglob("*.md"))
    files += sorted((root / "assets" / "institutional-knowledge").glob("*.md"))
    knowledge_dir = (root / "assets" / "institutional-knowledge").resolve()
    template_dir = (root / "assets" / "templates").resolve()
    violations = []
    scanned = 0
    for path in files:
        if not path.exists():
            continue
        scanned += 1
        rel = str(path.relative_to(root))
        resolved = path.resolve()
        in_knowledge = knowledge_dir in resolved.parents
        in_template = template_dir in resolved.parents
        text = path.read_text(encoding="utf-8", errors="ignore")
        by_line = {}
        for found in iter_markers(text):
            by_line.setdefault(found.line, []).append(found)
        for number, line in enumerate(text.splitlines(), 1):
            for found in by_line.get(number, []):
                if found.example:
                    continue
                if in_knowledge and found.kind != "kb":
                    violations.append({
                        "file": rel, "line": number, "kind": "kb_syntax",
                        "text": found.raw[:80],
                        "excerpt": line.strip()[:200],
                        "reason": "包内知识语料只允许三段 [kb:] 锚点；交付引用须在本案核验后另行生成 [source:]",
                    })
                elif in_template and found.kind == "kb":
                    violations.append({
                        "file": rel, "line": number, "kind": "template_syntax",
                        "text": found.raw[:80],
                        "excerpt": line.strip()[:200],
                        "reason": "模板只展示五段 [source:] 示例，不得使用 [kb:]",
                    })
            masked_line = PLACEHOLDER.sub("", line)
            for label, pattern in JURISDICTION_CLAIM:
                hit = re.search(pattern, masked_line)
                if hit:
                    violations.append({
                        "file": rel,
                        "line": number,
                        "kind": "jurisdiction_claim",
                        "text": hit.group(0),
                        "excerpt": line.strip()[:200],
                        "reason": "国别执行结论不属于机制索引内容；须改为指向 references/enforcement-jurisdictions.md 的逐目标核验问题（来源标记不豁免）",
                    })
            hits = line_hits(line)
            if not hits:
                continue
            kind = "knowledge" if in_knowledge else "prose"
            if marker_bound(line, source_ids, today, registry, kind):
                continue
            for label, text_hit in hits:
                violations.append({
                    "file": rel,
                    "line": number,
                    "kind": label,
                    "text": text_hit,
                    "excerpt": line.strip()[:200],
                    "reason": "未绑定官方来源；知识语料须附有效 [kb:] 锚点，其余文件须附已核验的 [source:... | 校验 YYYY-MM-DD] 标记",
                })
    return scanned, violations


def via_problems(via):
    """Return reasons why a `via` note carries rule content instead of hit evidence."""
    text = str(via or "")
    out = []
    if len(text) > VIA_MAX:
        out.append(f"超过 {VIA_MAX} 字符")
    for span in VIA_SPAN.findall(text):
        for frag in VIA_FRAGMENT.split(span):
            frag = frag.strip()
            if len(frag) > VIA_SPAN_MAX:
                out.append(f"引用片段过长（{len(frag)} 字符）")
            elif len(frag.split()) >= 4 and OPERATIVE_WORD.search(frag):
                out.append("引用了操作句而非条号标题")
    if any(verb in VIA_SPAN.sub("", text) for verb in CONCLUSION_VERB):
        out.append("含机制结论")
    return out


def check_anchors(root, reg, today):
    errors = []
    warnings = []
    path = root / "assets" / "rule-anchors.yaml"
    if not path.exists():
        return {"count": 0, "open_questions": 0, "errors": ["rule-anchors.yaml 缺失"]}, warnings
    try:
        import yaml
    except ImportError:
        return {"count": 0, "open_questions": 0, "errors": ["缺 PyYAML，无法读取 rule-anchors.yaml"]}, warnings
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"count": 0, "open_questions": 0, "errors": [f"rule-anchors.yaml 解析失败：{exc}"]}, warnings
    if not isinstance(data, dict):
        return {"count": 0, "open_questions": 0, "errors": ["rule-anchors.yaml 顶层须为 mapping"]}, warnings
    if data.get("version") != 2:
        errors.append("rule-anchors.yaml version 须为 2")
    if "absent_mechanisms" in data:
        errors.append("rule-anchors.yaml 不得保留 absent_mechanisms（否定性断言不属于可保留规则）")
    freshness = data.get("freshness_days", FRESHNESS_CEILING)
    if not isinstance(freshness, int) or not 1 <= freshness <= FRESHNESS_CEILING:
        errors.append(f"freshness_days 须为 1–{FRESHNESS_CEILING} 的整数")
        freshness = FRESHNESS_CEILING
    anchors = data.get("anchors") or {}
    if not isinstance(anchors, dict):
        errors.append("anchors 须为 mapping")
        anchors = {}
    institutions = set((reg.get("institutions") or {}).keys())
    source_ids = collect_ids(reg)
    for key, anchor in anchors.items():
        if not isinstance(anchor, dict):
            errors.append(f"锚点 {key} 须为 mapping")
            continue
        for field in ("institution", "topic", "mechanism", "locator", "basis_source", "status", "checked_at", "via"):
            if not str(anchor.get(field, "")).strip():
                errors.append(f"锚点 {key} 缺字段 {field}")
        if anchor.get("institution") and anchor["institution"] not in institutions:
            errors.append(f"锚点 {key} 的 institution 未登记：{anchor['institution']}")
        if anchor.get("basis_source") and anchor["basis_source"] not in source_ids:
            errors.append(f"锚点 {key} 的 basis_source 未登记：{anchor['basis_source']}")
        if anchor.get("status") != "verified":
            errors.append(f"锚点 {key} 的 status 须为 verified，实际 {anchor.get('status')!r}")
        locator = str(anchor.get("locator", ""))
        if locator and not (ANCHOR_LOCATOR.search(locator) or "Appendix" in locator):
            errors.append(f"锚点 {key} 的 locator 不含可定位的条号或附录：{locator!r}")
        reasons = sorted(set(via_problems(anchor.get("via", ""))))
        if reasons:
            errors.append(f"锚点 {key} 的 via 复现了规则内容：{'；'.join(reasons)}")
        when = _date(anchor.get("checked_at"))
        if anchor.get("checked_at") and when is None:
            errors.append(f"锚点 {key} 的 checked_at 非 ISO 日期：{anchor.get('checked_at')!r}")
        elif when and when > today:
            errors.append(f"锚点 {key} 的 checked_at 晚于今日：{when}")
        elif when and (today - when).days > freshness:
            errors.append(f"锚点 {key} 已超过 {freshness} 天未复核：{when}")
    questions = data.get("open_questions") or []
    if not isinstance(questions, list):
        errors.append("open_questions 须为列表")
        questions = []
    for index, item in enumerate(questions):
        if not isinstance(item, dict):
            errors.append(f"open_questions[{index}] 须为 mapping")
            continue
        for field in ("institution", "question", "action"):
            if not str(item.get(field, "")).strip():
                errors.append(f"open_questions[{index}] 缺字段 {field}")
        if item.get("institution") and item["institution"] not in institutions:
            errors.append(f"open_questions[{index}] 的 institution 未登记：{item['institution']}")
        if item.get("source_id") and item["source_id"] not in source_ids:
            errors.append(f"open_questions[{index}] 的 source_id 未登记：{item['source_id']}")
    if not anchors:
        errors.append("anchors 为空：至少须保留已在官方文本中命中的定位")
    if not questions:
        warnings.append("open_questions 为空：未解决事项应显式登记，而不是凭记忆补答")
    return {"count": len(anchors), "open_questions": len(questions), "errors": errors}, warnings


def check_matrix(root):
    path = root / "references" / "forum-rules-matrix.md"
    if not path.exists():
        return ["references/forum-rules-matrix.md 缺失"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors = []
    for heading in MATRIX_HEADINGS:
        if heading not in text:
            errors.append(f"核验清单缺少必要章节：{heading}")
    for token in ("HIT", "NOT_FOUND", "NO_TEXT", "VERSION_UNKNOWN"):
        if token not in text:
            errors.append(f"核验清单缺少判定：{token}")
    return errors


def check_version_view(root, reg):
    path = root / "references" / "institution-rule-versions.md"
    if not path.exists():
        return ["references/institution-rule-versions.md 缺失"]
    editions = {}
    for node in (reg.get("institutions") or {}).values():
        if not isinstance(node, dict):
            continue
        for entry in node.get("rules") or []:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                editions[entry["id"]] = entry
    rows = re.findall(
        r"^\|\s*`([^`]+)`\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|",
        path.read_text(encoding="utf-8", errors="ignore"),
        re.M,
    )
    errors = []
    listed = []
    for source_id, _title, effective, confidence, fetch in rows:
        source_id = source_id.strip()
        if source_id in listed:
            errors.append(f"版本清单重复登记：{source_id}")
        listed.append(source_id)
        entry = editions.get(source_id)
        if entry is None:
            errors.append(f"版本清单条目不在登记表 rules[] 中：{source_id}")
            continue
        for field, cell in (("effective", effective), ("confidence", confidence), ("fetch", fetch)):
            cell = cell.strip()
            expected = str(entry.get(field) or "")
            if not expected or cell in ("", "—", "-"):
                continue
            if cell != expected:
                errors.append(f"版本清单与登记表不一致：{source_id}.{field} 清单={cell} 登记表={expected}")
    for source_id in sorted(set(editions) - set(listed)):
        errors.append(f"登记表规则版本未进入版本清单：{source_id}")
    errors.extend(check_fetch_model(reg))
    return errors


def check_fetch_model(reg):
    """fetch 只描述自动抓取能力：ok 必须有官方 PDF 下载地址，manual/blocked 必须有 landing。"""
    errors = []
    for inst, node in (reg.get("institutions") or {}).items():
        if not isinstance(node, dict):
            continue
        for entry in node.get("rules") or []:
            if not isinstance(entry, dict) or not entry.get("id"):
                continue
            sid, fetch = entry["id"], str(entry.get("fetch") or "ok").lower()
            if fetch not in ("ok", "blocked", "manual"):
                errors.append(f"登记表 fetch 取值非法：{sid}.fetch={fetch!r}")
                continue
            for key in ("url", "landing", "download", "pdf"):
                value = str(entry.get(key) or "")
                if value.lower().startswith("http://"):
                    errors.append(f"登记表规则 URL 须为 https：{sid}.{key}")
            if fetch == "ok" and not str(entry.get("download") or "").startswith("https://"):
                errors.append(f"fetch=ok 但缺官方 PDF 下载地址：{sid}.download")
            if fetch in ("manual", "blocked"):
                if not str(entry.get("landing") or "").startswith("https://"):
                    errors.append(f"fetch={fetch} 但缺人工查看页：{sid}.landing")
                note = str(entry.get("note") or "")
                if re.search(r"(?:可|支持)自动抓取", note):
                    errors.append(f"fetch={fetch} 的备注却宣称可自动抓取：{sid}")
            note = str(entry.get("note") or "")
            claims = sorted(set(UNBACKED_CLAIM.findall(note)))
            if claims:
                backed = (entry.get("verified_at")
                          and any(entry.get(k) for k in ("sha256", "verified_hashes", "verified_locators")))
                if not backed:
                    errors.append(f"登记表核验断言无哈希/逐条核验记录支撑：{sid}（{'、'.join(claims)}）")
    return errors


def audit(root=SUITE, today=None):
    root = Path(root).resolve()
    today = today or date.today()
    reg_path = root / "assets" / "sources-registry.json"
    registry_errors = []
    try:
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        reg = {}
        registry_errors.append(f"sources-registry.json 解析失败：{exc}")
    source_ids = collect_ids(reg)
    banned = find_banned_keys(reg)
    rule_strings = rule_like_strings(reg)
    scanned, violations = scan_content(root, source_ids, today, reg)
    anchor_report, warnings = check_anchors(root, reg, today)
    matrix_errors = check_matrix(root)
    version_errors = check_version_view(root, reg)
    errors = registry_errors + anchor_report["errors"] + matrix_errors + version_errors
    ok = not (violations or banned or rule_strings or errors)
    return {
        "decision": "RULE_AUDIT_PASS" if ok else "RULE_AUDIT_FAIL",
        "policy": "交付物只允许五段 [source:]（含 URL 与校验日期）；包内知识语料只允许三段 [kb:]（id、登记表 title、定位）；assets/rule-anchors.yaml 的已登记锚点继续按 basis_source 与 checked_at 校验。其余条号、天数、金额、门槛一律视为未绑定。",
        "scanned": {"files": scanned, "source_ids": len(source_ids), "anchors": anchor_report["count"], "open_questions": anchor_report["open_questions"]},
        "violations": violations,
        "registry": {"banned_keys": banned, "rule_like_strings": rule_strings},
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(SUITE))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['decision']}｜文件 {result['scanned']['files']}｜锚点 {result['scanned']['anchors']}｜"
              f"未绑定表述 {len(result['violations'])}｜登记表问题 {len(result['registry']['banned_keys']) + len(result['registry']['rule_like_strings'])}｜"
              f"结构错误 {len(result['errors'])}")
        for item in result["violations"][:20]:
            print(f"  {item['file']}:{item['line']} [{item['kind']}] {item['text']} -> {item['excerpt']}")
        for item in result["registry"]["banned_keys"]:
            print(f"  登记表禁用字段：{item['path']}")
        for item in result["registry"]["rule_like_strings"]:
            print(f"  登记表规则性文本：{item['path']} [{item['kind']}] {item['text']}")
        for item in result["errors"]:
            print(f"  错误：{item}")
        for item in result["warnings"]:
            print(f"  提示：{item}")
    return 0 if result["decision"] == "RULE_AUDIT_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
