#!/usr/bin/env python3
"""仲裁协议十二维审计 schema 1；文字扫描只生成候选，不判断法律效力。"""
import argparse
import difflib
import hashlib
import re
import sys
from pathlib import Path

from _matrix_common import (Check, MatrixError, checked_file, cli, filled, question,
                            render_view, resolve_path, unknown)

PROFILES = {'new-clause': 'design', 'review-clause': 'review', 'post-dispute': 'post_dispute',
            'negotiate': 'negotiate', 'compare': 'compare', 'portfolio': 'portfolio'}
DIMENSIONS = {'D01': '机制与商业目标', 'D02': '机构规则与版本', 'D03': '仲裁地',
              'D04': '仲裁庭组成', 'D05': '语言与文本', 'D06': '准据法分层',
              'D07': '争议范围', 'D08': '多合同多方与非签署方', 'D09': '前置程序',
              'D10': '临时措施', 'D11': '裁决权限救济与费用', 'D12': '执行主权与合规'}
STATES = ('green', 'amber', 'red', 'unknown', 'not_applicable')
PROFILE_BLOCKS = {
    'new-clause': {'options': list, 'recommendation': dict, 'rewrite': dict, 'negotiation': dict, 'client_qa': list},
    'review-clause': {'text_lock': list, 'simulations': list, 'enforcement_backtest': dict},
    'post-dispute': {'text_lock': list, 'urgent_actions': list},
    'negotiate': {'negotiation': dict, 'rewrite': dict},
    'compare': {'options': list, 'comparison': dict},
    'portfolio': {'multi_contract': dict, 'renegotiation_calendar': list},
}


def init_data(case='', profile=None):
    profile = profile or 'review-clause'
    if profile not in PROFILES:
        raise MatrixError('PROFILE', 'profile', '不支持的条款 profile', 4)
    data = {'schema': 1, 'audit_id': 'unknown', 'case': case, 'version': 1,
            'mode': PROFILES[profile], 'profile': profile,
            'transaction': {'types': [], 'parties': [], 'posture': 'unknown', 'jurisdictions': []},
            'axes': dict.fromkeys(('validity', 'enforceability', 'administrability'), 'unknown'),
            'dimensions': {key: {'status': 'unknown', 'severity': 'unknown', 'confidence': 'low',
                                 'finding': 'unknown', 'consequence': 'unknown',
                                 'missing_info': ['OQ-%02d' % (i + 4)], 'sources': []}
                           for i, key in enumerate(DIMENSIONS)},
            'pathologies': [], 'neutrality_check': {}, 'sources': [], 'open_questions': []}
    groups = [['audit_id'], ['transaction'], ['axes']]
    groups += [['dimensions.' + key] for key in DIMENSIONS]
    groups += [['neutrality_check']]
    for key, kind in PROFILE_BLOCKS[profile].items():
        data[key] = kind()
        groups.append([key])
    data['open_questions'] = [question(i + 1, paths) for i, paths in enumerate(groups)]
    return data


def _nonempty(c, value, path, critical=True):
    if isinstance(value, dict) and value.get('status') == 'not_applicable':
        c.text(value.get('reason'), path + '.reason')
        c.need(value.get('reason'), path + '.reason', critical)
        return False
    c.need(value, path, critical)
    return filled(value)


def validate(data, stage='draft', profile=None, base_path=None):
    if stage not in ('draft', 'report', 'submission'):
        raise MatrixError('STAGE', 'stage', '不支持的条款校验阶段', 4)
    inferred = next((p for p, mode in PROFILES.items() if mode == data.get('mode')), None)
    profile = profile or data.get('profile') or inferred
    if not isinstance(profile, str) or profile not in PROFILES:
        raise MatrixError('PROFILE', 'profile', '不支持的条款 profile', 4)
    c = Check(data, stage, profile, strict=stage != 'draft')
    c.schema(1)
    c.required(data, ('audit_id', 'case', 'mode', 'transaction', 'dimensions', 'axes', 'open_questions'), '')
    c.load_questions()
    c.enum(data.get('mode'), tuple(PROFILES.values()), 'mode')
    c.text(data.get('audit_id'), 'audit_id')
    c.need(data.get('audit_id'), 'audit_id', False)
    transaction = c.mapping(data.get('transaction'), 'transaction')
    c.enum(transaction.get('posture'), ('likely_claimant', 'likely_respondent', 'balanced', 'unknown'), 'transaction.posture')
    for key in ('types', 'parties', 'jurisdictions'):
        for i, value in enumerate(c.listing(transaction.get(key), 'transaction.' + key)):
            c.text(value, 'transaction.%s.%s' % (key, i))
    axes = c.mapping(data.get('axes'), 'axes')
    c.required(axes, ('validity', 'enforceability', 'administrability'), 'axes')
    for key in ('validity', 'enforceability', 'administrability'):
        value = axes.get(key)
        p = 'axes.' + key
        if isinstance(value, dict):
            c.enum(value.get('status'), STATES, p + '.status')
            if 'verified' in value:
                c.boolean(value['verified'], p + '.verified')
            if value.get('status') == 'not_applicable':
                c.text(value.get('reason'), p + '.reason')
                if not filled(value.get('reason')):
                    c.error('NA_REASON', p + '.reason', '三轴不适用须说明理由')
            elif value.get('status') != 'unknown':
                c.need(value.get('finding'), p + '.finding')
                c.need(value.get('sources'), p + '.sources')
                if value.get('verified') is not True:
                    c.block('AXIS_UNVERIFIED', p, '三轴实质结论须分别有核验依据')
        else:
            c.enum(value, STATES[:-1], p)
            if isinstance(value, str) and value in ('green', 'amber', 'red'):
                c.block('AXIS_UNVERIFIED', p, '三轴结论须使用含 finding/sources/verified 的映射，不能只写颜色')
    dims = c.mapping(data.get('dimensions'), 'dimensions')
    c.required(dims, DIMENSIONS, 'dimensions')
    for key in dims:
        if key not in DIMENSIONS:
            c.error('DIMENSION', 'dimensions.' + key, '仅支持 D01–D12')
    for key in DIMENSIONS:
        p = 'dimensions.' + key
        row = c.mapping(dims.get(key), p)
        c.enum(row.get('status'), STATES, p + '.status')
        if row.get('status') == 'not_applicable':
            c.text(row.get('reason'), p + '.reason')
            if not filled(row.get('reason')):
                c.error('NA_REASON', p + '.reason', '无需项必须说明理由')
            continue
        c.required(row, ('severity', 'confidence', 'finding', 'consequence', 'missing_info', 'sources'), p)
        c.enum(row.get('severity'), STATES[:-1], p + '.severity')
        c.enum(row.get('confidence'), ('high', 'medium', 'low'), p + '.confidence')
        for field in ('finding', 'consequence'):
            c.text(row.get(field), p + '.' + field)
        missing = c.listing(row.get('missing_info'), p + '.missing_info')
        sources = c.listing(row.get('sources'), p + '.sources')
        for i, source in enumerate(sources):
            c.text(source, p + '.sources.%s' % i)
        for i, item in enumerate(missing):
            c.text(item, p + '.missing_info.%s' % i)
        relied = row.get('relied_on', row.get('status') != 'unknown')
        c.boolean(relied, p + '.relied_on')
        if row.get('status') == 'unknown':
            if not missing:
                c.error('MISSING_INFO', p + '.missing_info', 'Unknown 必须列明缺失信息')
            c.gap(p, critical=relied is True)
            if row.get('severity') == 'red' and not filled(row.get('severity_basis')):
                c.error('UNKNOWN_NOT_RED', p + '.severity', '未知不能自动转为 Red；须另有风险依据')
        else:
            c.need(row.get('finding'), p + '.finding', relied is True)
            c.need(row.get('consequence'), p + '.consequence', relied is True)
            if not sources:
                c.gap(p + '.sources', critical=relied is True)
            if row.get('confidence') == 'low' or row.get('verified') is not True:
                if 'verified' in row:
                    c.boolean(row['verified'], p + '.verified')
                c.block('CONCLUSION_UNVERIFIED', p, '实际采用的条款结论须核验来源；词语扫描不能代替法律判断')
        if row.get('status') == 'red' or row.get('severity') == 'red':
            c.need(row.get('remedy', row.get('fix')), p + '.remedy', relied is True)
        if row.get('status') == 'green' and row.get('severity') == 'red':
            c.error('STATE_CONFLICT', p, '同一维度不能同时为 Green 与 Red')
    for i, raw in enumerate(c.listing(data.get('pathologies', []), 'pathologies')):
        p = 'pathologies.%s' % i
        row = c.mapping(raw, p)
        c.boolean(row.get('present'), p + '.present', tristate=True)
        if row.get('present') is True:
            c.need(row.get('evidence'), p + '.evidence', False)
            c.need(row.get('source'), p + '.source', False)
    for key, kind in PROFILE_BLOCKS[profile].items():
        c.required(data, (key,), '')
        value = c.mapping(data.get(key), key) if kind is dict else c.listing(data.get(key), key)
        _nonempty(c, value, key)
    # Validate supplied blocks too, but do not require irrelevant heavy deliverables.
    if 'text_lock' in data:
        for i, raw in enumerate(c.listing(data['text_lock'], 'text_lock')):
            p = 'text_lock.%s' % i
            row = c.mapping(raw, p)
            for key in ('doc', 'version', 'hash', 'source'):
                c.text(row.get(key), p + '.' + key)
                c.need(row.get(key), p + '.' + key, profile in ('review-clause', 'post-dispute'))
            if filled(row.get('hash')) and not re.fullmatch(r'[a-fA-F0-9]{64}', str(row['hash'])):
                c.error('HASH', p + '.hash', '文本锁定须使用 SHA-256')
    if 'options' in data:
        options = c.listing(data['options'], 'options')
        if profile in ('new-clause', 'compare') and len(options) < 2:
            c.gap('options', critical=True)
        ids = set()
        for i, raw in enumerate(options):
            p = 'options.%s' % i
            row = c.mapping(raw, p)
            ident = row.get('id')
            if not isinstance(ident, str) or not ident or ident in ids:
                c.error('OPTION_ID', p + '.id', '方案编号须为唯一字符串')
            else:
                ids.add(ident)
            for key in ('mechanism', 'pros', 'cons', 'cost_time', 'enforceability'):
                c.need(row.get(key), p + '.' + key)
        recommendation = c.mapping(data.get('recommendation', {}), 'recommendation')
        if filled(recommendation.get('option')):
            c.refs(recommendation['option'], ids, 'recommendation.option', many=False)
    if 'negotiation' in data:
        row = c.mapping(data['negotiation'], 'negotiation')
        if row:
            for key in ('ideal', 'acceptable', 'walkaway', 'concessions'):
                c.need(row.get(key), 'negotiation.' + key)
    if 'rewrite' in data:
        row = c.mapping(data['rewrite'], 'rewrite')
        if row and row.get('status') != 'not_applicable':
            if not any(filled(row.get(key)) for key in ('text', 'zh', 'en')):
                c.gap('rewrite.text', critical=True)
            c.need(row.get('field_tradeoffs'), 'rewrite.field_tradeoffs')
            c.need(row.get('baseline_source'), 'rewrite.baseline_source')
            # One language is sufficient unless the assignment explicitly requests both.
            if row.get('bilingual_required') is True:
                for key in ('zh', 'en'):
                    c.need(row.get(key), 'rewrite.' + key)
            if 'bilingual_required' in row:
                c.boolean(row['bilingual_required'], 'rewrite.bilingual_required')
    if 'simulations' in data:
        for i, raw in enumerate(c.listing(data['simulations'], 'simulations')):
            row = c.mapping(raw, 'simulations.%s' % i)
            for key in ('scenario', 'risk', 'clause_fix'):
                c.need(row.get(key), 'simulations.%s.%s' % (i, key))
    if 'client_qa' in data:
        for i, raw in enumerate(c.listing(data['client_qa'], 'client_qa')):
            row = c.mapping(raw, 'client_qa.%s' % i)
            for key in ('q', 'a'):
                c.need(row.get(key), 'client_qa.%s.%s' % (i, key))
    if 'urgent_actions' in data:
        for i, raw in enumerate(c.listing(data['urgent_actions'], 'urgent_actions')):
            row = c.mapping(raw, 'urgent_actions.%s' % i)
            for key in ('action', 'owner', 'due'):
                c.need(row.get(key), 'urgent_actions.%s.%s' % (i, key))
    if 'multi_contract' in data:
        row = c.mapping(data['multi_contract'], 'multi_contract')
        if row and row.get('status') != 'not_applicable':
            c.need(row.get('contracts'), 'multi_contract.contracts')
            c.required(row, ('inconsistencies',), 'multi_contract')
            c.listing(row.get('inconsistencies'), 'multi_contract.inconsistencies')
    neutrality = c.mapping(data.get('neutrality_check', {}), 'neutrality_check')
    _nonempty(c, neutrality, 'neutrality_check')
    c.unknowns()
    return c.result()


def check_file(path, stage='draft', profile=None):
    return checked_file(path, stage, profile, validate)


def summarize(data):
    result = {state: 0 for state in STATES}
    for row in data.get('dimensions', {}).values():
        state = row.get('status')
        if state in result:
            result[state] += 1
    return {'dimensions': result, 'axes': data.get('axes', {}), 'mode': data.get('mode'),
            'note': 'Unknown 不等于 Red；三轴分别报告，不合并成法律效力判断'}


def render(data, result=None, profile=None):
    return render_view(data, result or validate(data), '仲裁协议体检与设计（内部完整阅读版）',
                       'clause-audit', profile or data.get('profile') or 'review-clause')


FEATURES = {
    'institution_terms': r'\b(?:ICC|SIAC|HKIAC|CIETAC|SCIA|LCIA|ICDR|UNCITRAL)\b|仲裁(?:委员会|院|机构)',
    'seat_terms': r'\bseat\b|place of arbitration|仲裁地|开庭地',
    'language_terms': r'\blanguage\b|语言|中文|英文',
    'tribunal_terms': r'\barbitrators?\b|仲裁员|独任|三人',
    'scope_terms': r'arising|in connection with|争议|纠纷',
    'precondition_terms': r'negotiat|mediat|协商|调解|友好解决',
    'court_terms': r'\bcourts?\b|litigation|法院|诉讼',
    'arbitration_terms': r'arbitrat|仲裁',
    'blank_markers': r'\[\[|_{3,}|待填写|待确定',
}


def scan_text(text, source=None):
    candidates = []
    for feature, pattern in FEATURES.items():
        matches = list(re.finditer(pattern, text, re.I))
        if matches:
            candidates.append({'feature': feature, 'occurrences': len(matches),
                               'locators': [{'line': text.count('\n', 0, m.start()) + 1,
                                             'start': m.start(), 'end': m.end()} for m in matches],
                               'status': 'candidate', 'requires_human_review': True})
    if any(x['feature'] == 'court_terms' for x in candidates) and any(x['feature'] == 'arbitration_terms' for x in candidates):
        candidates.append({'feature': 'court_and_arbitration_cooccur', 'status': 'candidate',
                           'requires_human_review': True, 'note': '仅共现；可能是保全、执行、分流或选择，不判断或裁或诉效力'})
    return {'source': source, 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'candidates': candidates, 'fields_inferred': False, 'legal_conclusion': None}


def _text_file(path):
    if Path(path).suffix.lower() not in ('.txt', '.md', '.text'):
        raise MatrixError('INPUT_FORMAT', str(path), '扫描只接受 UTF-8 纯文本或 Markdown', 4)
    try:
        return Path(path).read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        raise MatrixError('INPUT', str(path), '文本不存在或不可读') from None


def extra_parser(commands):
    scan = commands.add_parser('scan')
    compare = commands.add_parser('compare')
    for sub in (scan, compare):
        sub.add_argument('--json', action='store_true', default=argparse.SUPPRESS)
        sub.add_argument('--workdir', default=argparse.SUPPRESS)
    scan.add_argument('--file', required=True)
    scan.add_argument('--lang', choices=('zh', 'en'))
    compare.add_argument('--files', nargs='+', required=True, help='空格或逗号分隔 UTF-8 文本路径')


def extra_command(args):
    c = Check({}, args.command)
    result = c.result()
    result['submission_ready'] = False
    result['warnings'] = [{'code': 'TEXT_CANDIDATES_ONLY', 'path': '$',
                           'message': '仅文字特征／差异候选；不推断字段，不判断法律效力、准据法或冲突'}]
    if args.command == 'scan':
        result.update(scan_text(_text_file(args.file), str(args.file)))
        return result
    paths = [resolve_path(p, getattr(args, 'workdir', None)) for arg in args.files for p in arg.split(',') if p]
    if len(paths) < 2:
        raise MatrixError('ARGUMENTS', 'files', 'compare 至少需要两个文本', 4)
    texts = [_text_file(p) for p in paths]
    result['documents'] = [scan_text(text, str(path)) for path, text in zip(paths, texts)]
    comparisons = []
    for i in range(1, len(texts)):
        changes = [{'operation': op, 'base_lines': [a + 1, b], 'other_lines': [x + 1, y]}
                   for op, a, b, x, y in difflib.SequenceMatcher(None, texts[0].splitlines(), texts[i].splitlines()).get_opcodes()
                   if op != 'equal']
        comparisons.append({'base': str(paths[0]), 'other': str(paths[i]), 'identical_text': texts[0] == texts[i],
                            'text_change_candidates': changes, 'legal_conflict': 'not_determined'})
    result['comparisons'] = comparisons
    result['fields_inferred'] = False
    return result


if __name__ == '__main__':
    sys.exit(cli(sys.modules[__name__]))
