#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""套件确定性路由器：范围闸门 / 冷启动检测 / 意图匹配 / 材料闸门。

用法：
  python3 route.py --scope <案件要素文件或目录>   # 涉外因素判定（先于一切）
  python3 route.py --detect  [--workdir DIR]      # 冷启动闸门（.arbitration-config.md）
  python3 route.py --match "用户原话 + 案件要素"   # 意图 -> 子技能候选 + 缺口
  python3 route.py --gate <子技能id> [--provided <案件目录>/case.json]  # 材料闸门（唯一台账）
  python3 route.py --list                          # 子技能清单

退出码：0 通过 / 2 闸门未通过（禁止起草）/ 3 范围不符（转交）
"""
from __future__ import annotations

from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("需要 PyYAML：pip install pyyaml 或 uv run --with pyyaml python3 scripts/route.py ...")

SUITE = Path(__file__).resolve().parent.parent
CONFIG_NAME = ".arbitration-config.md"
REQUIRED_SLOTS = ["official_rules_fetch", "law_retrieval", "docx_render", "local_corpus", "party_data"]
UNFILLED_VALUES = {"", "UNBOUND", "PENDING"}

STRONG_FOREIGN = [
    "涉外", "foreign-related", "international arbitration", "跨境", "出海", "境外",
    "外商投资", "外资", "外国", "离岸", "出口", "进口", "海外",
    "icc", "siac", "hkiac", "lcia", "scc", "icdr", "kcab", "aiac",
    "acica", "diac", "crcica", "mcia", "qicca", "arbitratead", "lmaa", "gafta", "fosfa",
    "vienna", "stockholm", "新加坡国际仲裁", "香港国际仲裁",
    "new york convention", "纽约公约",

    "foreign law", "境外法", "适用外国法", "境外执行",
    "新加坡", "singapore", "香港", "hong kong", "英国", "united kingdom", "伦敦", "london",
    "德国", "germany", "美国", "united states", "日本", "japan", "韩国", "korea",
]
STRONG_FOREIGN_PHRASES = []
AMBIGUOUS_INSTITUTIONS = ["cietac", "中国国际经济贸易仲裁", "贸仲", "cmac", "海事仲裁",
                          "北仲", "bjac", "biac", "深国仲", "scia", "上国仲", "shiac",
                          "广州仲裁", "gac", "天津仲裁", "tjac", "华南国际仲裁"]
HARD_EXCLUDE_ZH = [
    "劳动争议", "劳动仲裁", "劳动合同", "解除劳动合同", "工伤", "工资拖欠", "经济补偿金",
    "员工投诉", "工会", "集体合同", "社保",
]
HARD_EXCLUDE_EN = [
    "employment arbitration", "employment dispute", "employment contract",
    "unpaid wages", "work injury", "labour dispute", "labor dispute",
]
NEGATIONS_ZH = [
    "无涉外因素", "不涉外", "没有涉外因素", "不涉及境外", "无境外因素",
    "纯国内", "纯境内", "不涉及外国主体", "无境外履行", "不需要境外执行",
    "不涉及劳动争议", "不是劳动合同",
]
NEGATIONS_EN = [
    "no foreign-related", "not international arbitration", "no cross-border",
    "not employment", "no foreign element",
]
DOMESTIC_ONLY = ["国内两家公司", "双方均为境内公司", "境内公司之间", "双方均在境内", "国内纠纷", "纯境内"]
TEMPLATE_MARKERS = re.compile(r"\[\[.*?\]\]")
SLOT_PATTERN = re.compile(r"^-\s*slot\(\w+\)\s*:", re.M)
TRAILING_NOTE = re.compile(r"\s*[（(][^）)]*[）)]\s*$")
VALID_SLOT_PATTERNS = [
    re.compile(r"^bound\b", re.I),
    re.compile(r"^degraded\b", re.I),
    re.compile(r"^skipped$", re.I),
    re.compile(r"^user-materials-only$", re.I),
    re.compile(r"^refused\b", re.I),
]
INVESTMENT_ONLY = ["icsid", "bit", "双边投资协定", "投资条约仲裁", "征收"]


def load_suite() -> dict:
    from intake import safe_yaml, validate_suite
    return validate_suite(safe_yaml((SUITE / 'suite.yaml').read_text(encoding='utf-8')))


def _error(msg: str) -> dict:
    print(json.dumps({"error": msg}, ensure_ascii=False, indent=2))
    return {}


def read_case(path: Path) -> str:
    from intake import extract, load_case
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.is_dir():
        chunks = []
        for f in sorted(p.rglob("*")):
            if f.is_file() and not f.is_symlink() and f.suffix.lower() in (".md", ".txt", ".json", ".docx", ".pdf", ".yaml", ".yml"):
                try:
                    chunks.append(read_case(f))
                except Exception as e:
                    chunks.append(f"[UNPARSED {f.name}: {type(e).__name__}]")
        return "\n".join(chunks)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("schema") == "rulesuite-case/1":
            case = load_case(p)
            return "case: " + case["case"] + "\n" + "\n".join(str(v["value"]) for v in case["facts"].values() if v["status"] == "confirmed")
        if isinstance(data, dict) and data.get("schema") == "rulesuite-extract/1":
            docs = data.get("documents")
            if not isinstance(docs, list):
                raise ValueError('rulesuite-extract/1 输入须含 documents 数组；请用 intake.py extract 生成，'
                                 '或提供 {"documents":[{"file":"...","status":"parsed","text":"..."}]}')
            return "\n".join(x.get("text", "") for x in docs if isinstance(x, dict) and x.get("status") == "parsed")
        if isinstance(data, dict) and isinstance(data.get("confirmed"), list):
            return "case: " + str(data.get("case", "")) + "\n" + "\n".join("- [x] " + x for x in data["confirmed"])
    return extract(p)


def _strip_negations(text: str) -> str:
    result = text.lower()
    for n in NEGATIONS_ZH + NEGATIONS_EN:
        result = result.replace(n.lower(), "")
    # A negative location statement is not affirmative evidence of foreign scope.
    result = re.sub(r'(?:未|不|没有|并非|无)(?:曾|有|在|位于|发生于|涉及|需要|属于|到|向|于|属|需|可)*[^，。；;\n]{0,12}(?:境外|海外|外国|涉外|跨境)[^，。；;\n]*', '', result)
    result = re.sub(r'\b(?:not|never|no)\b[^,;.\n]{0,30}\b(?:overseas|abroad|foreign|cross-border)\b[^,;.\n]*', '', result)
    return result


def _strip_template_lines(text: str) -> str:
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if TEMPLATE_MARKERS.search(line):
            continue
        if SLOT_PATTERN.match(stripped):
            continue
        if stripped.startswith("~ ") and any(k in stripped for k in [
            "机构", "仲裁地", "工作目录", "规则版本", "仲裁启动", "仲裁语言", "准据法",
            "我方地位", "争议金额", "涉外因素", "slot", "降级", "bound", "degraded",
            "UNBOUND", "适用规则", "案件代号"]):
            continue
        if stripped.startswith("case:") or stripped.startswith("case: "):
            continue
        if "待用户确认" in line or "待核" in line:
            continue
        if stripped.startswith("# ") and any(k in stripped for k in ["冷启动", "材料补充", "配置"]):
            continue
        if "本轮不产出" in line:
            continue
        if stripped.startswith("## ") and ("涉外范围" in stripped or "专用" in stripped):
            continue
        lines.append(line)
    return "\n".join(lines)


def _has_word_boundary(term: str, text: str) -> bool:
    if len(term) <= 3 and term.isascii():
        return bool(re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", text))
    return term in text


def structured_scope(path):
    from intake import safe_yaml, SchemaError
    data = safe_yaml(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema', 'rulesuite-scope/1') != 'rulesuite-scope/1':
        raise SchemaError('scope schema 须为 rulesuite-scope/1')
    records = [data.get(k, {}) for k in ('parties', 'performance', 'legal_facts', 'seat', 'law', 'enforcement')]
    if any(not isinstance(r, dict) for r in records):
        raise SchemaError('scope 各要素须为 {status, foreign, evidence} 记录')
    confirmed = [r for r in records if r.get('status') == 'confirmed' and r.get('evidence')]
    labor = data.get('labor', {})
    if not isinstance(labor, dict):
        raise SchemaError('labor 须为 {status, value, evidence} 记录')
    if labor.get('status') == 'confirmed' and labor.get('value') is True and labor.get('evidence'):
        decision = 'OUT_OF_SCOPE'
    elif any(r.get('foreign') is True for r in confirmed):
        decision = 'IN_SCOPE'
    elif len(confirmed) == len(records) and all(r.get('foreign') is False for r in confirmed):
        decision = 'OUT_OF_SCOPE'
    else:
        decision = 'REVIEW_REQUIRED'
    out = {'decision': decision, 'basis': 'structured-records', 'limitations': '仅检查显式确认记录，不判定法律上的涉外性质'}
    if decision == 'REVIEW_REQUIRED':
        out['mandatory_question'] = _scope_question()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if decision == 'IN_SCOPE' else (3 if decision == 'OUT_OF_SCOPE' else 2)


def cmd_scope(args, suite: dict) -> int:
    if getattr(args, 'scope_file', None):
        return structured_scope(args.scope_file)
    try:
        raw = re.sub(r"\[UNPARSED[^\]]*\]", "", read_case(args.scope))
    except (OSError, ValueError) as e:
        print(json.dumps({"decision": "INPUT_ERROR", "error": str(e)}, ensure_ascii=False, indent=2))
        return 2
    if not raw.strip():
        print(json.dumps({"decision": "UNKNOWN",
                          "mandatory_question": "案件要素为空。" + _scope_question()},
                         ensure_ascii=False, indent=2))
        return 2

    cleaned = _strip_negations(raw)
    cleaned = _strip_template_lines(cleaned)
    text = cleaned.lower()

    hard_zh = [m for m in HARD_EXCLUDE_ZH if _has_word_boundary(m, text)]
    hard_en = [m for m in HARD_EXCLUDE_EN if _has_word_boundary(m.lower(), text)]
    hard = sorted(set(hard_zh + hard_en))

    negated_text = _strip_negations(raw).lower()
    negated_text = _strip_template_lines(negated_text).lower()
    has_hard_negation = False  # 否定仅移除相应短语，不能抵销其他肯定用工事实

    if hard and not has_hard_negation:
        out = {"decision": "OUT_OF_SCOPE", "reason": "属劳动争议或用工争议，本套件只处理涉外商事仲裁。",
               "exclude_markers": hard, "action": "终止本轮并转交：建议使用劳动争议专门技能/工具；如案件同时含商事与劳动两个独立争议，须由用户拆案后分别处理。"}
    else:
        strong = sorted({m for m in STRONG_FOREIGN if _has_word_boundary(m, text)})
        phrase_hits = []
        for phrase in STRONG_FOREIGN_PHRASES:
            if phrase in text:
                ctx_start = max(0, text.index(phrase) - 30)
                ctx_end = min(len(text), text.index(phrase) + len(phrase) + 30)
                context = text[ctx_start:ctx_end]
                if any(d in context for d in ["国内", "domestic", "北京", "beijing", "中国", "china"]):
                    continue
                phrase_hits.append(phrase)
        strong = sorted(set(strong + phrase_hits))

        for amb_name in AMBIGUOUS_INSTITUTIONS:
            amb_lower = amb_name.lower()
            if amb_lower in text:
                strong = [s for s in strong if s not in amb_lower]
                if amb_lower in ["biac", "beijing international arbitration center", "北仲"]:
                    strong = [s for s in strong if s != "international arbitration"]
        strong = sorted(set(strong))

        dom = sorted({m for m in DOMESTIC_ONLY if m in text})

        inv = sorted({m for m in INVESTMENT_ONLY if _has_word_boundary(m, text)})
        has_negated_contract = any(neg in text for neg in ["不基于合同", "不基于商事合同", "not based on contract", "not a commercial contract", "非合同"])
        commercial_context = (any(w in text for w in ["合同", "contract", "买卖", "sale", "采购", "purchase", "设备", "货物", "goods", "服务", "service", "合作", "joint"])
                              and not has_negated_contract)
        if inv and not commercial_context:
            out = {"decision": "REVIEW_REQUIRED",
                   "investment_markers": inv,
                   "mandatory_question": "案件可能属于投资条约争端而非商事仲裁。" + _scope_question()}
        else:
            amb = sorted({m for m in AMBIGUOUS_INSTITUTIONS if _has_word_boundary(m, text)})
            dom = sorted({m for m in DOMESTIC_ONLY if m in text})
            if strong and dom:
                out = {"decision": "REVIEW_REQUIRED", "strong_markers": strong, "domestic_only_markers": dom,
                       "mandatory_question": "案件描述同时含跨境与纯境内表述。" + _scope_question()}
            elif strong:
                out = {"decision": "IN_SCOPE", "strong_markers": strong, "ambiguous_institution": amb}
            elif dom or any(x in raw for x in ("无涉外因素", "没有涉外因素", "纯国内", "纯境内")):
                out = {"decision": "OUT_OF_SCOPE", "reason": "已明确无涉外因素", "action": "转交国内商事争议工具"}
            elif amb:
                out = {"decision": "REVIEW_REQUIRED", "ambiguous_institution": amb,
                       "mandatory_question": f"出现双轨机构（{'、'.join(amb)}），该类机构同时受理境内与涉外案件。" + _scope_question()}
            else:
                out = {"decision": "UNKNOWN", "mandatory_question": "未检出涉外要素线索。" + _scope_question()}

    out["rule"] = "本套件只处理涉外商事仲裁；纯境内（无涉外因素）商事案件与劳动争议一律转交。"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if out["decision"] == "IN_SCOPE":
        return 0
    return 3 if out["decision"] == "OUT_OF_SCOPE" else 2


def _scope_question() -> str:
    return ("请用户确认其一是否存在（不得由助手推断）：①当事人一方为境外主体或境外注册实体；"
            "②履行地／标的物在境外；③引发争议的法律事实发生在境外；"
            "④约定境外仲裁地或外国准据法；⑤需在境外承认与执行。")


def config_status(workdir, required_slots=()) -> dict:
    """Shared, side-effect-free config gate for detect, routing and delivery."""
    wd = Path(workdir or ".").expanduser()
    cfg = wd / CONFIG_NAME
    if cfg.is_symlink() or (cfg.exists() and not cfg.is_file()):
        return {"decision": "INPUT_ERROR", "error": f"配置须为案件根普通文件，不得为目录或符号链接：{cfg}"}
    if not cfg.exists():
        return {"decision": "NO_CONFIG", "action": "必须先执行 skills/00-cold-start/SKILL.md："
                "向用户提问并获得真实回答后写入 " + str(cfg), "hard_gate": True}
    try:
        raw = cfg.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        return {"decision": "INPUT_ERROR", "error": f"无法读取配置：{e}"}
    if not raw.strip():
        return {"decision": "CONFIG_INCOMPLETE", "error": "配置文件为空", "unfilled": REQUIRED_SLOTS}

    slot_lines = re.findall(r"^-\s*slot\((\w+)\)\s*:[ \t]*(.*)$", raw, re.M)
    if not slot_lines and required_slots:
        return {"decision": "CONFIG_INCOMPLETE", "error": "配置文件中未找到任何 slot() 条目",
                "unfilled": list(required_slots)}
    slots = {}
    duplicates = []
    for key, value in slot_lines:
        if key in slots:
            duplicates.append(key)
        slots[key] = value.strip()

    missing_required = [s for s in required_slots if s not in slots]
    invalid_values = []
    unfilled = []
    for k, v in slots.items():
        # Optional capabilities are requested by the actual task/filing gate, not every cold start.
        if k not in REQUIRED_SLOTS and k not in {"company_research","certified_translation","notarization","local_counsel"}:
            invalid_values.append(k)
            continue
        core = TRAILING_NOTE.sub("", v).strip()
        if not v or v in UNFILLED_VALUES:
            unfilled.append(k)
        elif v.startswith("[["):
            invalid_values.append(k)
        elif not any(p.match(core) for p in VALID_SLOT_PATTERNS):
            invalid_values.append(k)
        elif core.lower().startswith("refused") and len(v) < 15:
            invalid_values.append(k)
    all_unfilled = sorted(set(missing_required + unfilled + invalid_values))
    if duplicates:
        return {"decision": "CONFIG_INCOMPLETE", "error": f"检测到重复配置槽（须解决冲突）：{duplicates}",
                "duplicate_slots": duplicates, "unfilled": all_unfilled}
    if all_unfilled:
        return {"decision": "CONFIG_INCOMPLETE", "config": str(cfg), "slots": slots, "unfilled": all_unfilled,
                "accepted_values": "bound (…) / degraded (…) / skipped / "
                "user-materials-only / refused (<15 字符视为未说明理由)",
                "hint": "槽位值须以这些词之一开头；照抄模板 slot(party_data): user-materials-only 即可。"
                "仍以 [[…]] 或 UNBOUND 占位表示尚未确认。"}

    config_workdir_match = re.search(r"^~[ \t]*工作目录[：:][ \t]*(.*)$", raw, re.M)
    case_match = re.search(r"^case:[ \t]*(.*)$", raw, re.M)
    if (not case_match or not case_match.group(1).strip() or "[[" in case_match.group(1)
            or not config_workdir_match or not config_workdir_match.group(1).strip()):
        return {"decision": "CONFIG_INCOMPLETE", "error": "配置须含 case 案件代号及 ~ 工作目录：绝对路径"}
    config_workdir = Path(config_workdir_match.group(1).strip()).expanduser()
    if not config_workdir.is_absolute():
        config_workdir = wd / config_workdir
    actual_workdir = wd.resolve()
    if config_workdir.resolve() != actual_workdir:
        return {"decision": "CONFIG_MISMATCH",
                "error": f"配置绑定的工作目录 {config_workdir} 与当前工作目录 {actual_workdir} 不一致",
                "config_workdir": str(config_workdir), "actual_workdir": str(actual_workdir),
                "action": "请确认配置是否属于当前案件；如属不同案件，须重新执行冷启动。"}
    return {"decision": "CONFIGURED", "config": str(cfg), "slots": slots, "unfilled": [],
            "case": case_match.group(1).strip()}


def cmd_detect(args, suite: dict) -> int:
    result = config_status(args.workdir, getattr(args, 'required_slots', ()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['decision'] == 'CONFIGURED' else 2


def stage_matches(value, stage):
    if not stage or value == 'cross':
        return True
    match = re.fullmatch(r'P([0-7])(?:-P([0-7]))?', str(value))
    return bool(match and int(match[1]) <= int(stage[1]) <= int(match[2] or match[1]))


PROFILE_HINTS = {
    '02-clause-diagnosis': {
        'portfolio': ['多合同', '合同组合', 'portfolio'], 'post-dispute': ['争议后', '争议已发生', '补充仲裁协议'],
        'negotiate': ['谈判', '红线'], 'compare': ['比较', '对比', 'vs'],
        'new-clause': ['设计', '新拟', '起草条款'], 'review-clause': ['体检', '审查', '病态', '审阅']},
    '05-defence': {'answer': ['答辩', '答复', 'answer', 'response'],
        'counterclaim': ['反请求', '反诉', 'counterclaim'], 'jurisdiction': ['管辖异议', 'challenge jurisdiction']},
    '06-tribunal': {'nomination': ['提名', '指定', 'nomination', 'appointment'],
        'disclosure': ['披露', '独立性', 'disclosure', 'independence'],
        'challenge': ['挑战', '回避', 'challenge', 'recusal']},
    '07-measures-costs': {'interim': ['临时措施', '保全', 'interim', 'conservatory'],
        'security': ['费用担保', 'security for costs'], 'advance': ['预缴', '押金', 'advance', 'deposit']},
    '08-evidence': {'production': ['文件披露', '文件生产', 'production', 'disclosure'],
        'witness': ['证人', 'witness', '事实证人'], 'expert': ['专家', 'expert', '鉴定']},
    '09-hearing': {'hearing': ['庭审', '开庭', 'hearing', 'oral'],
        'post-hearing': ['庭后', 'post-hearing', '补充书状']},
    '10-award-post': {'finality': ['终局性', '部分裁决'], 'settlement': ['和解', '合意裁决'],
        'enforcement-triage': ['执行分流'], 'correction': ['更正', '解释裁决', '补充裁决'],
        'set-aside': ['撤销', 'set aside'], 'matrix': ['期限', '动作矩阵']},
    '14-cross-border-enforcement': {'forecast': ['预判', '裁决前'], 'counsel': ['律师', '报价'],
        'board': ['董事会', '管理层'], 'immunity': ['豁免', '主权'], 'insolvency': ['破产', '重整'],
        'asset': ['调查', '海外资产'], 'plan': ['执行', '纽约公约']}}


def suggest_profile(sid, query):
    return next((p for p, words in PROFILE_HINTS.get(sid, {}).items() if any(w in query for w in words)), None)


def cmd_match(args, suite: dict) -> int:
    q = args.match.lower()
    stage = getattr(args, 'stage', None)

    # Exclusion patterns for common false positives
    exclusions = {
        'award': ['award-winning', 'award ceremony', 'award winner', 'award winning'],
        'closing': ['closing bracket', 'closing date', 'closing time'],
        '解释': ['解释合同', '解释条款', '解释协议'],
    }

    # Context requirements for ambiguous triggers
    context_required = {
        '解释': ['裁决', 'award', '仲裁'],
        'closing': ['statement', 'brief', 'argument', '庭审', '结案'],
    }

    scored = []
    for sid, meta in suite.get("subskills", {}).items():
        if not stage_matches(meta.get('stage'), stage):
            continue
        score = 0
        for t in (meta.get("triggers") or []):
            tl = str(t).lower()
            if tl == '保全':
                post_award = stage == 'P7' or any(w in q for w in ('裁决后', '执行阶段', '执行保全', '承认与执行'))
                if sid == '14-cross-border-enforcement' and not post_award:
                    continue
                if sid == '07-measures-costs' and post_award:
                    continue

            # Check exclusions first
            if tl in exclusions:
                if any(exc in q for exc in exclusions[tl]):
                    continue

            # Check context requirements
            if tl in context_required:
                if not any(ctx in q for ctx in context_required[tl]):
                    continue

            if len(tl) <= 3:
                if _has_word_boundary(tl, q):
                    score += 1
            else:
                if tl in q:
                    score += 1
        if score:
            scored.append((score, sid))
    scored.sort(reverse=True)
    top = [s for n, s in scored[:4]]
    need_cfg = not (Path(args.workdir or ".") / CONFIG_NAME).exists()
    details = []
    from intake import load_case, evaluate
    fact_file = Path(getattr(args, 'provided', None) or Path(args.workdir or '.') / 'case.json')
    facts = load_case(fact_file) if fact_file.is_file() and fact_file.suffix == '.json' else None
    for sid in top:
        meta = suite['subskills'][sid]
        profile = suggest_profile(sid, q)
        spec = meta.get('profiles', {}).get(profile, meta)
        detail = {'subskill': sid, 'profile': profile, 'profile_options': list(meta.get('profiles', {})),
                  'required': list(zip(spec.get('gate_ids', []), spec.get('gate', []))),
                  'gate_any': list(zip(spec.get('gate_any_ids', []), spec.get('gate_any', [])))}
        if facts and (profile or not meta.get('profiles')):
            assessment = evaluate(facts, sid, profile, getattr(args, 'mode', 'submission'))
            detail.update({k: assessment.get(k, []) for k in ('missing', 'pending', 'unknown', 'reused')})
        details.append(detail)
    result = {
        "candidates": top,
        "stage": stage,
        "details": details,
        "score": {sid: score for score, sid in scored[:6]},
        "must_run_cold_start_first": need_cfg,
        "next_action": ("运行 route.py --gate <id> 取材料缺项；缺项不为空则只出《补充材料与信息确认清单》"
                        if top else "意图不明确：向用户确认本轮目标文书或目标程序环节，不得自行选择"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if top else 2


def cmd_gate(args, suite: dict) -> int:
    meta = (suite.get("subskills") or {}).get(args.gate)
    if not meta:
        print(json.dumps({"error": f"未知子技能 {args.gate}", "known": list(suite.get("subskills", {}))},
                         ensure_ascii=False, indent=2))
        return 2
    profile = getattr(args, "profile", None)
    profiles = meta.get("profiles") or {}
    if profiles and profile not in profiles:
        print(json.dumps({"decision": "PROFILE_INVALID" if profile else "PROFILE_REQUIRED", "profiles": profiles,
                          "allowed_to_draft": False, "action": "按本轮目标选择 --profile；不要合并不同文书的材料要求"}, ensure_ascii=False, indent=2))
        return 4 if profile else 2
    if profile and not profiles:
        print(json.dumps({"decision": "PROFILE_INVALID", "error": "该子技能没有 profile", "allowed_to_draft": False}, ensure_ascii=False))
        return 4
    effective = dict(meta, **profiles.get(profile, {}))
    from intake import validate_gate_spec, SchemaError, load_case, evaluate
    try:
        validate_gate_spec(effective)
    except SchemaError as exc:
        print(json.dumps({'decision':'PROFILE_INVALID','error':str(exc),'allowed_to_draft':False},ensure_ascii=False))
        return 4
    if effective.get('redirect'):
        print(json.dumps({'decision':'REDIRECT_REQUIRED','redirect':effective['redirect'],
                          'redirect_profile':effective.get('redirect_profile'),'allowed_to_draft':False,
                          'action':'旧 enforcement 入口仅分流；请显式选择14任务并重跑材料闸门'},ensure_ascii=False))
        return 2
    required = list(effective.get("gate") or [])
    gate_any = list(effective.get("gate_any_ids") or [])
    gate_any_labels = list(effective.get("gate_any") or [])
    configured = None
    if args.gate != "00-cold-start":
        configured = config_status(args.workdir, effective.get('requires', []))
        if configured['decision'] != 'CONFIGURED':
            print(json.dumps({"decision": "CONFIG_REQUIRED", "allowed_to_draft": False,
                              "detail": configured}, ensure_ascii=False, indent=2))
            return 2

    if not required and not gate_any:
        print(json.dumps({'decision': 'NO_GATE', 'subskill': args.gate, 'profile': profile,
                          'allowed_to_draft': True, 'submission_ready': True,
                          'action': '本任务无材料闸门；仍须按技能正文与 references 核验事实、来源与交付契约'},
                         ensure_ascii=False, indent=2))
        return 0

    workdir = Path(args.workdir or '.').expanduser().resolve()
    supplied = Path(args.provided).expanduser() if args.provided else workdir / 'case.json'
    if supplied.is_dir():
        supplied = supplied / 'case.json'
    symlink = supplied.is_symlink()
    ledger_path = supplied.resolve()
    ledger_ok = (ledger_path == workdir / 'case.json' and not symlink and ledger_path.is_file())
    if not ledger_ok:
        reason = ('缺少案件材料台账 case.json' if not ledger_path.is_file()
                  else '材料台账必须是不越界的案件根 case.json，不接受 Markdown 清单、其他文件名或符号链接')
        print(json.dumps({'decision': 'MATERIALS_REQUIRED', 'subskill': args.gate, 'profile': profile,
                          'missing': required + gate_any_labels, 'gate_ids': effective.get('gate_ids', []),
                          'gate_any_ids': effective.get('gate_any_ids', []),
                          'allowed_to_draft': False, 'submission_ready': False, 'error': reason,
                          'action': '在案件根建立 case.json（schema rulesuite-case/1），按 gate_ids 与 gate_any_ids 登记已核事实与证据；不要把 Markdown 清单勾成已确认'},
                         ensure_ascii=False, indent=2))
        return 2
    try:
        case = load_case(ledger_path)
    except (OSError, ValueError, KeyError, TypeError, SchemaError) as exc:
        print(json.dumps({'decision': 'INVALID_INPUT', 'subskill': args.gate, 'profile': profile,
                          'allowed_to_draft': False, 'submission_ready': False,
                          'error': 'case.json 无效：' + str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if configured is not None and configured['case'] != case['case']:
        print(json.dumps({"decision": "CASE_MISMATCH", "allowed_to_draft": False,
                          "submission_ready": False,
                          "error": "case.json 的 case 必须与 .arbitration-config.md 一致"},
                         ensure_ascii=False))
        return 2
    mode = getattr(args, "mode", "submission")
    result = evaluate(case, args.gate, profile, mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    passed = result["submission_ready"] if mode == "submission" else result["allowed_to_draft"]
    return 0 if passed else 2


def main() -> int:
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", type=Path, help="案件要素文件或目录，做涉外因素判定")
    ap.add_argument('--scope-file', type=Path, help='结构化范围记录 YAML/JSON')
    ap.add_argument('--stage', choices=['P0','P1','P2','P3','P4','P5','P6','P7'])
    ap.add_argument('--json', action='store_true', help='清单输出机器可读JSON')
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--require-slot", action="append", default=[], help="detect 时仅要求本任务依赖的能力槽")
    ap.add_argument("--match")
    ap.add_argument("--gate")
    ap.add_argument("--mode", choices=["draft", "submission"], default="submission")
    ap.add_argument("--profile", help="该子技能下的具体文书类型，见 suite.yaml profiles")
    ap.add_argument("--provided", help="案件材料台账路径，必须是案件根 case.json；默认 <workdir>/case.json")
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if sum(bool(x) for x in (a.scope, a.scope_file, a.detect, a.match, a.gate, a.list)) > 1:
        ap.error("一次只选 --scope / --scope-file / --detect / --match / --gate / --list 中一个动作")

    from intake import SchemaError
    try:
        suite = load_suite()
    except SchemaError as e:
        print(json.dumps({'decision':'SCHEMA_INVALID','error':str(e)},ensure_ascii=False))
        return 4
    except Exception as e:
        print(json.dumps({"error": f"加载套件失败：{e}"}, ensure_ascii=False, indent=2))
        return 2

    if a.list:
        subs = {sid:m for sid,m in suite['subskills'].items() if stage_matches(m.get('stage'),a.stage)}
        if a.json:
            print(json.dumps({'version':suite['version'],'name':suite.get('name'),'display_name':suite.get('display_name'),
                              'stage_default':suite.get('stage_default',{}),'subskills':subs},ensure_ascii=False,indent=2))
        else:
            for sid, m in subs.items():
                print(f"{sid}\t{m.get('stage')}\t{m.get('entry')}\tprofiles={','.join(m.get('profiles',{}))}\tgate_ids={len(m.get('gate_ids',[]))}")
        return 0
    try:
        if a.scope or a.scope_file:
            return cmd_scope(a, suite)
        if a.detect:
            a.required_slots = a.require_slot
            return cmd_detect(a, suite)
        if a.match:
            return cmd_match(a, suite)
        if a.gate:
            return cmd_gate(a, suite)
    except SchemaError as e:
        print(json.dumps({'decision':'SCHEMA_INVALID','error':str(e),'allowed_to_draft':False},ensure_ascii=False))
        return 4
    except Exception as e:
        print(json.dumps({"error": f"执行失败：{e}"}, ensure_ascii=False, indent=2))
        return 2
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
