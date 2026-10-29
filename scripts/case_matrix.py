#!/usr/bin/env python3
"""案件构建矩阵 schema 2；init/check/render/summary/anchors/migrate，无网络。"""
import argparse
import re
import sys
from pathlib import Path

from _matrix_common import (ANCHOR_RE, ID_RE, Check, MatrixError, checked_file, cli,
                            dump_yaml, failure, filled, iso_date, load_yaml, question,
                            render_view, resolve_path, safe_write, unknown)

FAMILIES = ('common_law', 'civil_germanic', 'civil_french', 'latin_iberian',
            'chinese_law', 'mixed', 'uniform_law', 'islamic_law', 'unknown')
COLLECTIONS = {'claims': r'CL-\d{2,}', 'defences': r'DF-\d{2,}',
               'elements': r'E-(?:CL|DF)\d{2,}-\d{2,}', 'facts': r'F-\d{3,}',
               'evidence': r'EV-\d{3,}', 'relief': r'R-\d{2,}', 'authorities': r'A-\d{2,}'}
COLD_READ = ('what_case_is_about', 'three_issues', 'strongest_point',
             'weakest_point', 'missing', 'what_would_persuade')


def init_data(case='', profile=None):
    data = {'schema': 2, 'case': case or 'unknown', 'version': 1, 'complexity': 'standard',
            'posture': 'unknown', 'stage': 'P0',
            'forum': dict.fromkeys(('institution', 'seat', 'language'), 'unknown'),
            'governing_law': {'contract': 'unknown', 'arbitration_agreement': 'unknown',
                              'family': 'unknown', 'confidence': 'low'},
            'theory': {'one_sentence': 'unknown', 'tribunal_questions': [], 'must_prove': [],
                       'opponent_best_case': 'unknown', 'predictions': [], 'falsifiers': []},
            **{key: [] for key in COLLECTIONS},
            'enforcement': {'targets': [], 'awards': [], 'budget': {}},
            'adversarial_review': {}, 'documents': [], 'open_questions': []}
    blocks = [['case', 'posture'], ['forum'], ['governing_law'], ['theory'],
              ['claims', 'defences', 'elements'], ['adversarial_review'], ['documents']]
    data['open_questions'] = [question(i + 1, paths) for i, paths in enumerate(blocks)]
    return data


def _source(c, source, path, evidence=None, critical=False):
    source = c.mapping(source, path)
    c.required(source, ('document_id', 'locator'), path)
    for key in ('document_id', 'locator'):
        c.text(source.get(key), path + '.' + key)
        c.need(source.get(key), path + '.' + key, critical)
    if evidence is not None and filled(source.get('document_id')):
        c.refs(source['document_id'], evidence, path + '.document_id', many=False)


def _legal(c, rows, path, authorities, critical):
    rows = c.listing(rows, path)
    c.need(rows, path, critical)
    used = set()
    for i, raw in enumerate(rows):
        p = path + '.' + str(i)
        row = c.mapping(raw, p)
        c.required(row, ('instrument', 'provision', 'authority_id', 'confidence'), p)
        for key in ('instrument', 'provision'):
            c.text(row.get(key), p + '.' + key)
            c.need(row.get(key), p + '.' + key, critical)
        if filled(row.get('authority_id')):
            used.update(c.refs(row['authority_id'], authorities, p + '.authority_id', many=False))
        else:
            c.need(row.get('authority_id'), p + '.authority_id', critical)
        c.enum(row.get('confidence'), ('high', 'medium', 'low'), p + '.confidence')
        if row.get('confidence') == 'low':
            c.gap(p, critical)
    return used


def validate(data, stage='draft', profile=None, base_path=None):
    if stage not in ('draft', 'submission', 'enforcement'):
        raise MatrixError('STAGE', 'stage', '不支持的案件校验阶段', 4)
    c = Check(data, stage, profile, strict=stage != 'draft')
    c.schema(2)
    c.required(data, ('case', 'complexity', 'posture', 'stage', 'forum', 'governing_law',
                      'theory', 'open_questions', *COLLECTIONS), '')
    indexes = {key: c.index(key, pattern) for key, pattern in COLLECTIONS.items()}
    c.load_questions()
    c.enum(data.get('complexity'), ('light', 'standard', 'complex'), 'complexity')
    c.enum(data.get('posture'), ('claimant', 'respondent', 'both', 'unknown'), 'posture')
    c.enum(data.get('stage'), tuple('P%s' % i for i in range(8)), 'stage')
    c.text(data.get('case'), 'case')
    c.need(data.get('case'), 'case')
    c.need(data.get('posture'), 'posture')
    for name, keys in (('forum', ('institution', 'seat', 'language')),
                       ('governing_law', ('contract', 'arbitration_agreement', 'family', 'confidence'))):
        obj = c.mapping(data.get(name), name)
        c.required(obj, keys, name)
        for key in keys:
            c.text(obj.get(key), name + '.' + key)
        if name == 'governing_law':
            c.enum(obj.get('family'), FAMILIES, name + '.family')
            c.enum(obj.get('confidence'), ('high', 'medium', 'low'), name + '.confidence')
            c.warn('METHOD_ONLY', name + '.family', '法律家族仅为论证方法，不决定准据法或证明标准')
    owners = dict(indexes['claims'], **indexes['defences'])
    if not owners:
        c.gap('claims', critical=True)
    elements, facts, evidence = indexes['elements'], indexes['facts'], indexes['evidence']
    used_authorities, active_elements, owner_links = set(), set(), {}
    for ident, row in owners.items():
        p = c.entities[ident]
        defence = ident.startswith('DF-')
        kinds = ('denial', 'positive_defence', 'legal_defence', 'jurisdictional_objection') if defence else ('claim', 'counterclaim', 'alternative')
        c.required(row, ('kind', 'label', 'elements'), p)
        c.enum(row.get('kind'), kinds, p + '.kind')
        c.text(row.get('label'), p + '.label')
        c.need(row.get('label'), p + '.label')
        relied = row.get('relied_on', True)
        c.boolean(relied, p + '.relied_on')
        linked = c.refs(row.get('elements'), elements, p + '.elements')
        owner_links[ident] = linked
        if relied is True:
            active_elements.update(linked)
        denial = row.get('kind') == 'denial'
        if not linked:
            if denial:
                for key in ('opponent_reference', 'response'):
                    c.text(row.get(key), p + '.' + key)
                    c.need(row.get(key), p + '.' + key, relied is True)
            else:
                c.need(linked, p + '.elements', relied is True)
        for eid in linked:
            if elements[eid].get('claim') != ident:
                c.error('OWNER_LINK', p + '.elements', '主张引用了归属其他主张的要件')
        authority_refs = set()
        if not denial:
            if 'legal_basis' not in row:
                c.error('MISSING', p + '.legal_basis', '非否认型主张须登记法律基础')
            authority_refs = _legal(c, row.get('legal_basis'), p + '.legal_basis', indexes['authorities'], relied is True)
        elif 'legal_basis' in row:
            authority_refs = _legal(c, row['legal_basis'], p + '.legal_basis', indexes['authorities'], relied is True)
        if relied is True:
            used_authorities.update(authority_refs)
        relief = c.refs(row.get('relief', []), indexes['relief'], p + '.relief')
        if not defence:
            c.required(row, ('relief',), p)
            c.need(relief, p + '.relief', relied is True)
    theory = c.mapping(data.get('theory'), 'theory')
    c.required(theory, ('one_sentence', 'tribunal_questions', 'must_prove', 'opponent_best_case', 'predictions', 'falsifiers'), 'theory')
    for key in ('one_sentence', 'opponent_best_case'):
        c.text(theory.get(key), 'theory.' + key)
        c.need(theory.get(key), 'theory.' + key)
    must_prove = c.refs(theory.get('must_prove'), elements, 'theory.must_prove')
    if elements:
        c.need(must_prove, 'theory.must_prove')
    active_elements.update(must_prove)
    for key, minimum in (('tribunal_questions', 2), ('predictions', 2), ('falsifiers', 1)):
        rows = c.listing(theory.get(key), 'theory.' + key)
        if len(rows) < minimum:
            c.gap('theory.' + key, critical=True)
        for i, row in enumerate(rows):
            p = 'theory.%s.%s' % (key, i)
            if key == 'tribunal_questions':
                row = c.mapping(row, p)
                for field in ('question', 'our_answer', 'opponent_answer'):
                    c.text(row.get(field), p + '.' + field)
                    c.need(row.get(field), p + '.' + field)
            else:
                c.text(row, p)
                c.need(row, p)
    document_ids = _check_documents(c, data, base_path)
    active_elements.update(eid for eid in document_ids if eid in elements)
    for rid in document_ids:
        if rid in indexes['relief']:
            active_elements.update(eid for eid in indexes['relief'][rid].get('elements', []) if isinstance(eid, str))
    used_authorities.update(aid for aid in document_ids if aid in indexes['authorities'])
    for owner_id, linked in owner_links.items():
        if any(eid in active_elements for eid in linked) and owners[owner_id].get('relied_on') is False:
            row = owners[owner_id]
            if row.get('kind') != 'denial' or 'legal_basis' in row:
                used_authorities.update(_legal(c, row.get('legal_basis'), c.entities[owner_id] + '.legal_basis', indexes['authorities'], True))
    active_facts = {ident for ident in document_ids if ident in facts}
    active_evidence = {ident for ident in document_ids if ident in evidence}
    fact_refs, evidence_refs = set(), set()
    for ident, row in elements.items():
        p = c.entities[ident]
        c.required(row, ('claim', 'statement', 'burden', 'standard', 'facts', 'evidence', 'witnesses',
                         'strength', 'gap', 'opponent_attack', 'response', 'fallback'), p)
        owner_id = row.get('claim')
        c.refs(owner_id, owners, p + '.claim', many=False)
        owner = owners.get(owner_id, {}) if isinstance(owner_id, str) else {}
        if isinstance(owner_id, str) and owner_id in owners:
            expected = 'E-' + owner_id.replace('-', '') + '-'
            if not ident.startswith(expected) or ident not in owner_links.get(owner_id, []):
                c.error('OWNER_LINK', p, '要件编号、归属与主张 elements 必须一致')
        critical = ident in active_elements
        denial = owner.get('kind') == 'denial'
        for key in ('statement', 'burden', 'standard', 'gap', 'opponent_attack', 'response', 'fallback'):
            c.text(row.get(key), p + '.' + key)
        for key in ('statement', 'burden', 'opponent_attack', 'response', 'fallback'):
            c.need(row.get(key), p + '.' + key, critical)
        c.need(row.get('standard'), p + '.standard', critical and not denial)
        c.enum(row.get('strength'), ('strong', 'partial', 'missing'), p + '.strength')
        fs = c.refs(row.get('facts'), facts, p + '.facts')
        es = c.refs(row.get('evidence'), evidence, p + '.evidence')
        witnesses = {k: v for k, v in evidence.items() if v.get('type') in ('witness', 'expert')}
        es += c.refs(row.get('witnesses'), witnesses, p + '.witnesses')
        fact_refs.update(fs)
        evidence_refs.update(es)
        if critical:
            active_facts.update(fs)
            active_evidence.update(es)
        if not denial:
            c.need(fs, p + '.facts', critical)
            if not es:
                if not filled(row.get('gap')):
                    c.gap(p + '.evidence', critical)
                else:
                    c.gap(p + '.gap', critical)
            if row.get('strength') == 'missing':
                c.gap(p + '.strength', critical)
        if 'authorities' in row:
            refs = c.refs(row['authorities'], indexes['authorities'], p + '.authorities')
            if critical:
                used_authorities.update(refs)
    for ident, row in facts.items():
        p = c.entities[ident]
        c.required(row, ('actor', 'act', 'source', 'status', 'elements', 'adverse', 'background'), p)
        critical = ident in active_facts
        if 'date' not in row and 'period' not in row:
            c.error('MISSING', p + '.date', '事实须有 date 或 period')
        when = row.get('date', row.get('period'))
        c.need(when, p + ('.date' if 'date' in row else '.period'), critical)
        if 'date' in row and filled(when) and not iso_date(when):
            c.error('DATE', p + '.date', '具体日期须为 ISO 日期；模糊期间请使用 period')
        elif 'date' not in row:
            c.text(when, p + '.period')
        for key in ('actor', 'act'):
            c.text(row.get(key), p + '.' + key)
            c.need(row.get(key), p + '.' + key, critical)
        _source(c, row.get('source'), p + '.source', evidence, critical)
        source_id = row.get('source', {}).get('document_id') if isinstance(row.get('source'), dict) else None
        if isinstance(source_id, str) and source_id in evidence:
            evidence_refs.add(source_id)
            if critical:
                active_evidence.add(source_id)
        c.enum(row.get('status'), ('undisputed', 'disputed', 'unverified'), p + '.status')
        if row.get('status') == 'unverified':
            c.gap(p + '.status', critical)
        for key in ('adverse', 'background'):
            c.boolean(row.get(key), p + '.' + key)
        linked = c.refs(row.get('elements'), elements, p + '.elements')
        if row.get('background') is not True and (not linked or ident not in fact_refs):
            c.error('ORPHAN_FACT', p, '非背景事实必须被要件引用并反向挂接')
    for ident, row in evidence.items():
        p = c.entities[ident]
        critical = ident in active_evidence
        c.required(row, ('type', 'exhibit_no', 'source', 'facts', 'elements'), p)
        c.enum(row.get('type'), ('document', 'witness', 'expert', 'electronic', 'physical'), p + '.type')
        c.text(row.get('exhibit_no'), p + '.exhibit_no')
        c.need(row.get('exhibit_no'), p + '.exhibit_no', critical)
        _source(c, row.get('source'), p + '.source', critical=critical)
        c.need(c.refs(row.get('facts'), facts, p + '.facts'), p + '.facts', critical)
        c.need(c.refs(row.get('elements'), elements, p + '.elements'), p + '.elements', critical)
        if ident not in evidence_refs:
            c.error('ORPHAN_EVIDENCE', p, '证据未被事实或要件引用')
        if 'verified' in row:
            c.boolean(row['verified'], p + '.verified')
        if critical and row.get('verified') is not True:
            c.block('EVIDENCE_UNVERIFIED', p, '实际依赖证据须声明已核验来源和定位')
    active_relief = {r for owner in owners.values() if owner.get('relied_on', True) is True
                     for r in (owner.get('relief') if isinstance(owner.get('relief'), list) else []) if isinstance(r, str)}
    active_relief.update(r for r in document_ids if r in indexes['relief'])
    if data.get('documents') and active_relief - document_ids:
        c.block('RELIEF_ANCHOR', 'documents', '实际请求救济须在正文中有对应 R- 锚点')
    for ident, row in indexes['relief'].items():
        p = c.entities[ident]
        critical = ident in active_relief
        c.required(row, ('type', 'elements'), p)
        c.enum(row.get('type'), ('money', 'performance', 'injunction', 'declaration', 'costs'), p + '.type')
        c.need(c.refs(row.get('elements'), elements, p + '.elements'), p + '.elements', critical)
        if row.get('type') in ('money', 'costs'):
            c.required(row, ('currency', 'amount', 'calculation_ref', 'interest'), p)
            c.text(row.get('currency'), p + '.currency')
            c.need(row.get('currency'), p + '.currency', critical)
            c.number(row.get('amount'), p + '.amount')
            c.need(row.get('amount'), p + '.amount', critical)
            c.need(row.get('calculation_ref'), p + '.calculation_ref', critical)
            interest = c.mapping(row.get('interest'), p + '.interest')
            if interest.get('status') == 'not_applicable':
                c.need(interest.get('reason'), p + '.interest.reason', critical)
            else:
                for key in ('basis', 'rate', 'from', 'method'):
                    c.need(interest.get(key), p + '.interest.' + key, critical)
    for ident, row in indexes['authorities'].items():
        p = c.entities[ident]
        critical = ident in used_authorities
        c.required(row, ('type', 'citation', 'forum', 'date', 'status', 'proposition', 'weight', 'source'), p)
        c.enum(row.get('type'), ('statute', 'case', 'treaty', 'soft_law', 'commentary', 'contract'), p + '.type')
        c.enum(row.get('status'), ('good_law', 'questioned', 'overruled', 'superseded', 'unknown'), p + '.status')
        c.enum(row.get('weight'), ('binding', 'persuasive', 'weak'), p + '.weight')
        if 'use' in row:
            c.enum(row['use'], ('support', 'distinguish', 'attack', 'background'), p + '.use')
        for key in ('citation', 'forum', 'date', 'proposition', 'source'):
            if key != 'date':
                c.text(row.get(key), p + '.' + key)
            c.need(row.get(key), p + '.' + key, critical)
        if filled(row.get('date')) and not iso_date(row['date']):
            c.error('DATE', p + '.date', '权威日期须为 ISO 日期')
        if 'verified' in row:
            c.boolean(row['verified'], p + '.verified')
        if critical and row.get('verified') is not True:
            c.block('AUTHORITY_UNVERIFIED', p, '实际依赖权威须阅原文并声明核验')
        if critical and (row.get('status') == 'unknown' or row.get('confidence') == 'low'):
            c.gap(p, critical=True)
        if critical and row.get('status') in ('overruled', 'superseded') and row.get('use', 'support') == 'support':
            c.block('AUTHORITY_STATUS', p, '已推翻或替代权威不能直接支持现行法命题')
    _review(c, data, c.entities, must_prove)
    enforcement = c.mapping(data.get('enforcement', {}), 'enforcement')
    target_ids = c.listing(enforcement.get('targets', []), 'enforcement.targets')
    for i, target in enumerate(target_ids):
        if not isinstance(target, str) or not re.fullmatch(r'T-\d{2,}', target):
            c.error('ID', 'enforcement.targets.%s' % i, '执行目标仅引用 T- 编号')
    reference = enforcement.get('plan_ref') or enforcement.get('forecast')
    if stage == 'enforcement' and not reference:
        c.block('ENFORCEMENT_REQUIRED', 'enforcement.plan_ref', '执行阶段须关联执行矩阵')
    if reference:
        if not isinstance(reference, str):
            c.error('TYPE', 'enforcement', 'plan_ref/forecast 必须为文件路径')
        else:
            from enforcement_matrix import check_file as check_enforcement
            target_path = resolve_path(reference, base_path.parent if base_path else None)
            external = check_enforcement(target_path, stage='filing' if stage == 'enforcement' else 'draft',
                                         profile='plan' if stage == 'enforcement' else 'forecast')
            if external['exit_code']:
                c.error('ENFORCEMENT_INVALID', 'enforcement', '关联执行矩阵未通过结构或执行闸门') if external['exit_code'] in (2, 4) else c.block('ENFORCEMENT_BLOCKED', 'enforcement', '关联执行矩阵被阻断')
            else:
                external_data = load_yaml(target_path)
                available = {r['id'] for r in external_data.get('targets', [])}
                c.refs(target_ids, available, 'enforcement.targets')
    elif target_ids:
        c.error('ENFORCEMENT_REFERENCE', 'enforcement', 'T- 由执行矩阵管理，须提供 plan_ref 或 forecast 文件路径')
    if 'migration' in data:
        migration = c.mapping(data['migration'], 'migration')
        if migration.get('reviewed') is not True:
            c.block('MIGRATION_REVIEW', 'migration', '迁移未完成字段映射与人工复核')
    c.unknowns()
    return c.result()


def _check_documents(c, data, base_path):
    documents = c.listing(data.get('documents', []), 'documents')
    c.need(documents, 'documents')
    ids = set()
    for i, doc in enumerate(documents):
        p = 'documents.%s' % i
        if not isinstance(doc, str):
            c.error('TYPE', p, '文书路径必须为字符串')
            continue
        path = resolve_path(doc, base_path.parent if base_path else None)
        try:
            result = anchors(data, path.read_text(encoding='utf-8'))
            ids.update(result['anchored_ids'])
            for err in result['errors']:
                if err['code'] in ('ANCHOR_UNKNOWN', 'ANCHOR_SYNTAX'):
                    c.errors.append(err)
                else:
                    c.blocks.append(err)
        except (OSError, UnicodeError):
            c.error('DOCUMENT', p, '锚点文书不存在或不可读')
    return ids


def _review(c, data, targets, must_prove):
    review = c.mapping(data.get('adversarial_review', {}), 'adversarial_review')
    if not review:
        c.gap('adversarial_review', critical=True)
        return
    for key in ('reviewer', 'date', 'opponent_best_case'):
        c.need(review.get(key), 'adversarial_review.' + key)
    if filled(review.get('date')) and not iso_date(review['date']):
        c.error('DATE', 'adversarial_review.date', '审查日期须为 ISO 日期')
    c.boolean(review.get('self_review'), 'adversarial_review.self_review')
    if review.get('self_review') is True:
        c.warn('SELF_REVIEW', 'adversarial_review', '自审；未做独立冷读，不得称独立审查')
    cold = c.mapping(review.get('cold_read'), 'adversarial_review.cold_read')
    for key in COLD_READ:
        c.need(cold.get(key), 'adversarial_review.cold_read.' + key)
    count = {'light': 2, 'standard': 3, 'complex': 5}.get(data.get('complexity'), 3)
    attacked = set()
    for key in ('attack_lines', 'premortem'):
        rows = c.listing(review.get(key), 'adversarial_review.' + key)
        if len(rows) < count:
            c.block('REVIEW_COUNT', 'adversarial_review.' + key, '未满足复杂度对应的 2/3/5 条审查记录')
        for i, row in enumerate(rows):
            p = 'adversarial_review.%s.%s' % (key, i)
            if key == 'attack_lines':
                row = c.mapping(row, p)
                attacked.update(c.refs(row.get('target'), targets, p + '.target', many=False))
                for field in ('attack', 'response', 'fallback'):
                    c.need(row.get(field), p + '.' + field)
            else:
                c.need(row, p)
    if any(target not in attacked for target in must_prove):
        c.block('REVIEW_COVERAGE', 'adversarial_review.attack_lines', '核心要件未被攻击线覆盖')
    c.need(review.get('unresolved_risks'), 'adversarial_review.unresolved_risks')
    # Explicit record avoids guessing whether narrative prose really admits a weakness.
    if review.get('own_weakness_reviewed') is not True:
        c.block('OWN_WEAKNESS', 'adversarial_review.own_weakness_reviewed', '须确认预演失败包含本方论证弱点')


def check_file(path, stage='draft', profile=None):
    return checked_file(path, stage, profile, validate)


def summarize(data):
    return {**{key: len(data.get(key, [])) for key in COLLECTIONS},
            'open_questions': sum(q.get('status', 'open') == 'open' for q in data.get('open_questions', []))}


def render(data, result=None, profile=None):
    return render_view(data, result or validate(data), '案件构建矩阵（内部完整阅读版）',
                       'case-construction', profile or 'case')


def anchors(data, text):
    """Check IDs everywhere and coverage only in substantive sections/explicit scope.

Use `#! 锚点范围：facts|argument|relief|none` for unrecognised headings.
Heading/table/quote/letter furniture are exempt; every prose paragraph in a
substantive section needs an adjacent anchor of the matching family.
"""
    c = Check(data, 'anchors', strict=True)
    known = {r.get('id') for name in COLLECTIONS for r in data.get(name, []) if isinstance(r, dict)}
    denials = {r.get('id') for r in data.get('defences', []) if isinstance(r, dict) and r.get('kind') == 'denial'}
    if isinstance(data.get('enforcement'), dict):
        known.update(t for t in data['enforcement'].get('targets', []) if isinstance(t, str))
    errors, used, pending = [], set(), []
    scope, paragraph, paragraph_ids, paragraph_line = None, [], [], 0
    fence = None
    substantive, prose = 0, 0
    ordinary_letter = bool(re.search(r'^(Dear\b|敬启|致[^\n]*[:：])', text, re.I | re.M))
    scope_stack = []
    frontmatter = text.startswith('---\n')
    def flush():
        nonlocal paragraph, paragraph_ids, substantive, prose
        if paragraph:
            prose += 1
            if scope:
                substantive += 1
                expected = {'facts': ('F-',), 'argument': ('E-', 'A-'), 'relief': ('R-', 'DF-')}[scope]
                denial_anchor = scope == 'argument' and any(v in denials for v in paragraph_ids)
                if not denial_anchor and not any(any(v.startswith(prefix) for prefix in expected) for v in paragraph_ids):
                    errors.append({'code': 'ANCHOR_COVERAGE', 'path': 'line.%s' % paragraph_line,
                                   'message': '事实／论证／救济正文段缺少对应类型的相邻锚点'})
            used.update(paragraph_ids)
        paragraph, paragraph_ids = [], []
    for number, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if frontmatter:
            if number > 1 and s == '---':
                frontmatter = False
            continue
        match = ANCHOR_RE.match(line)
        if match:
            flush()
            pending = [v for v in re.split(r'[,，/\s]+', match.group(1)) if v]
            if not pending or any(not ID_RE.fullmatch(v) for v in pending):
                errors.append({'code': 'ANCHOR_SYNTAX', 'path': 'line.%s' % number, 'message': '锚点须为规范主键，不能用占位符'})
            if any(v not in known for v in pending):
                errors.append({'code': 'ANCHOR_UNKNOWN', 'path': 'line.%s' % number, 'message': '锚点引用未登记编号'})
            continue
        if s.startswith('```') or s.startswith('~~~'):
            flush()
            marker = s[:3]
            fence = None if fence == marker else marker
            pending = []
            continue
        if fence:
            continue
        if s.startswith('#! 锚点范围：') or s.startswith('#! 锚点范围:'):
            flush()
            selected = re.split('[:：]', s, maxsplit=1)[1].strip()
            if selected not in ('facts', 'argument', 'relief', 'none'):
                errors.append({'code': 'ANCHOR_SYNTAX', 'path': 'line.%s' % number, 'message': '不支持的锚点范围'})
            scope = selected if selected in ('facts', 'argument', 'relief') else None
            pending = []
            continue
        heading = re.match(r'^(#{1,6})\s+(.*)', s)
        if heading:
            flush()
            level, title = len(heading.group(1)), heading.group(2).lower()
            while scope_stack and scope_stack[-1][0] >= level:
                scope_stack.pop()
            inherited = scope_stack[-1][1] if scope_stack else None
            if re.search(r'事实|背景|facts|factual|background', title):
                scope = 'facts'
            elif re.search(r'救济|请求事项|relief|remed', title):
                scope = 'relief'
            elif re.search(r'法律|论证|管辖|紧迫|不可弥补|利益衡量|legal|law|argument|jurisdiction|merits|urgency', title):
                scope = 'argument'
            else:
                scope = inherited
            scope_stack.append((level, scope))
            pending = []
            continue
        if not s:
            flush()
            continue
        if s.startswith(('|', '>', '~', '#!')) or s in ('---', '***'):
            flush()
            pending = []
            continue
        if re.match(r'^(Dear\b|Yours\b|Sincerely\b|敬启|此致|日期[:：]|Date:|To:|From:)', s, re.I):
            flush()
            pending = []
            continue
        if re.match(r'^\d+[.)]\s', s) and paragraph:
            flush()
        if not paragraph:
            paragraph_line, paragraph_ids = number, pending
            pending = []
        paragraph.append(s)
    flush()
    c.errors.extend(e for e in errors if e['code'] != 'ANCHOR_COVERAGE')
    c.blocks.extend(e for e in errors if e['code'] == 'ANCHOR_COVERAGE')
    if not text.strip():
        c.block('ANCHOR_EMPTY', '$', '空文书不能通过提交锚点闸门')
    elif substantive == 0 and prose and not ordinary_letter:
        c.block('ANCHOR_SCOPE', '$', '未识别正文范围；请明确标注 facts/argument/relief，而不是免除全部正文')
    elif substantive == 0:
        c.warn('ANCHOR_SCOPE', '$', '常规信函或标题表格免除正文锚定；仍检查所有显式锚点编号')
    return c.result(anchored_ids=sorted(v for v in used if isinstance(v, str)), substantive_paragraphs=substantive)


def check_anchors(matrix_path, draft_path, stage='submission'):
    try:
        data = load_yaml(matrix_path)
        structural = check_file(matrix_path, stage='draft')
        if structural['exit_code']:
            return structural
        return anchors(data, Path(draft_path).read_text(encoding='utf-8'))
    except MatrixError as exc:
        return failure(exc, 'anchors')
    except (OSError, UnicodeError):
        return failure(MatrixError('DOCUMENT', str(draft_path), '文书不存在或不可读'), 'anchors')


def extra_parser(commands):
    for name in ('anchors', 'migrate'):
        sub = commands.add_parser(name)
        sub.add_argument('--json', action='store_true', default=argparse.SUPPRESS)
        sub.add_argument('--workdir', default=argparse.SUPPRESS)
        sub.add_argument('--in', dest='input', required=True)
        if name == 'anchors':
            sub.add_argument('--draft', required=True)
            sub.add_argument('--fix-anchors', action='store_true', help='仅报告，不修改文书')
        else:
            sub.add_argument('--from', dest='old_schema', type=int, required=True)
            sub.add_argument('--to', dest='new_schema', type=int, required=True)
            sub.add_argument('--out', required=True)
            sub.add_argument('--force', action='store_true')


def extra_command(args):
    if args.command == 'anchors':
        return check_anchors(args.input, args.draft)
    old = load_yaml(args.input)
    if args.old_schema != 1 or args.new_schema != 2 or type(old.get('schema')) is not int or old['schema'] != 1:
        raise MatrixError('MIGRATION_SCHEMA', 'schema', '仅支持真实 schema 1 显式迁移到 2', 4)
    if args.input.resolve() == args.out.resolve():
        raise MatrixError('MIGRATION_OUTPUT', str(args.out), '迁移必须写入新文件，不修改旧案')
    data = init_data(old.get('case') if isinstance(old.get('case'), str) else '')
    data['migration'] = {'from_schema': 1, 'source': str(args.input), 'reviewed': False,
                         'note': '旧字段及来源完整保存在 legacy_payload；未猜测主键或证据映射，须人工复核后填入 schema 2。'}
    data['legacy_payload'] = old
    data['open_questions'].append(question(8, ['migration'], '核对旧案字段、主键和来源；完成迁移人工复核', blocking=True))
    out = safe_write(args.out, dump_yaml(data), args.force)
    result = check_file(out)
    result['output'] = out
    return result


if __name__ == '__main__':
    sys.exit(cli(sys.modules[__name__]))
