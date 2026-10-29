#!/usr/bin/env python3
"""跨境执行矩阵 schema 1：forecast/plan 可登记未知，filing 才硬核立案条件。"""
import datetime as dt
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from _matrix_common import (Check, MatrixError, checked_file, cli, decimal, filled,
                            iso_date, load_yaml, question, render_view, resolve_path, unknown)

PROFILES = ('forecast', 'plan', 'asset', 'immunity', 'insolvency', 'board', 'counsel')
FILE_ITEMS = ('originals', 'certified_copies', 'arbitration_agreement', 'translation',
              'notarization', 'legalization', 'power_of_attorney', 'corporate_docs',
              'account_info', 'service_evidence')
FORECAST_IDS = tuple('FC-%02d' % i for i in range(1, 13))
SPECIALS = {'immunity': 'applicable', 'insolvency': 'flag', 'sanctions': 'flag', 'public_policy': 'flag'}


def init_data(case='', profile=None):
    profile = profile or 'plan'
    if profile not in PROFILES:
        raise MatrixError('PROFILE', 'profile', '不支持的执行 profile', 4)
    data = {'schema': 1, 'case': case or 'unknown', 'version': 1, 'profile': profile,
            'debtors': [], 'relief': [], 'awards': [], 'targets': [], 'selected_targets': [],
            'file_chain': {}, 'strategy': {}, 'budget': {}, 'timeline': {},
            'sources': [], 'open_questions': []}
    groups = [['case'], ['debtors', 'relief', 'awards'], ['targets', 'selected_targets'],
              ['file_chain'], ['strategy'], ['budget'], ['timeline']]
    if profile == 'forecast':
        data['forecast'] = [{'id': ident, 'status': 'unknown', 'evidence': [],
                             'action': 'unknown', 'owner': 'user', 'due': 'unknown'} for ident in FORECAST_IDS]
        groups.append(['forecast'])
    elif profile == 'board':
        data['board_brief'] = dict.fromkeys(('decision', 'options', 'costs', 'risks', 'recommendation'), 'unknown')
        groups.append(['board_brief'])
    elif profile == 'counsel':
        data['counsel_instructions'] = []
        groups.append(['counsel_instructions'])
    elif profile in ('asset', 'immunity', 'insolvency'):
        data[profile + '_review'] = {}
        groups.append([profile + '_review'])
    data['open_questions'] = [question(i + 1, paths) for i, paths in enumerate(groups)]
    return data


def _date(c, value, path, critical=False):
    if c.need(value, path, critical) and not iso_date(value):
        c.error('DATE', path, '日期须为 ISO 日期，未核验只能写 unknown')


def _verified(c, row, path, critical=True):
    if 'verified' in row:
        c.boolean(row['verified'], path + '.verified')
    if row.get('verified') is not True and critical:
        c.block('LEGAL_UNVERIFIED', path, '立案依赖事项须明确核验，不能把未知当作否')


def _file_chain(c, chain, path, requirements=None):
    chain = c.mapping(chain, path)
    required = list(requirements or FILE_ITEMS)
    for key in required:
        if not isinstance(key, str):
            c.error('TYPE', path, '文件要求必须引用文件链的字符串键')
            continue
        row = c.mapping(chain.get(key), path + '.' + key) if key in chain else {}
        if not row:
            c.block('FILE_CHAIN', path + '.' + key, '选定目标的文件链未备齐')
            continue
        c.enum(row.get('status'), ('have', 'valid', 'pending', 'unknown', 'not_applicable'), path + '.' + key + '.status')
        if row.get('status') == 'not_applicable':
            c.need(row.get('reason'), path + '.' + key + '.reason')
            c.need(row.get('source'), path + '.' + key + '.source')
            _verified(c, row, path + '.' + key)
        elif row.get('status') not in ('have', 'valid'):
            c.block('FILE_CHAIN', path + '.' + key, '选定目标所需文件尚未齐备')
        else:
            c.need(row.get('source', row.get('exhibit')), path + '.' + key + '.source')
            _verified(c, row, path + '.' + key)
        if 'expiry' in row and filled(row['expiry']):
            if not iso_date(row['expiry']):
                c.error('DATE', path + '.' + key + '.expiry', '授权有效期须为 ISO 日期')
            elif str(row['expiry']) < dt.date.today().isoformat():
                c.block('EXPIRED_AUTHORITY', path + '.' + key, '授权或文件已经过期')


def _forecast(c, value):
    rows = c.listing(value, 'forecast')
    ids = set()
    for i, raw in enumerate(rows):
        p = 'forecast.%s' % i
        row = c.mapping(raw, p)
        ident = row.get('id')
        if not isinstance(ident, str) or ident not in FORECAST_IDS or ident in ids:
            c.error('FORECAST_ID', p + '.id', '预判编号须唯一且为 FC-01 至 FC-12')
        else:
            ids.add(ident)
        c.enum(row.get('status'), ('red', 'amber', 'green', 'unknown', 'not_applicable'), p + '.status')
        if row.get('status') == 'not_applicable':
            if not filled(row.get('reason')):
                c.error('NA_REASON', p + '.reason', '不适用项须说明理由')
            continue
        c.required(row, ('evidence', 'action', 'owner', 'due'), p)
        c.listing(row.get('evidence'), p + '.evidence')
        c.need(row.get('action'), p + '.action', False)
        c.need(row.get('owner'), p + '.owner', False)
        if row.get('status') == 'unknown':
            c.gap(p)
        elif row.get('status') in ('green', 'amber', 'red'):
            c.need(row.get('evidence'), p + '.evidence', False)
        _date(c, row.get('due'), p + '.due', False)
    if ids != set(FORECAST_IDS):
        c.error('FORECAST_ITEMS', 'forecast', 'forecast profile 必须覆盖十二项预判；不要求裁决全文')


def _walk_forbidden(c, value, path=''):
    if isinstance(value, dict):
        for key, child in value.items():
            p = path + '.' + key if path else key
            if key in ('success_rate', 'recovery_probability', 'foreign_court_application'):
                c.error('FORBIDDEN_FIELD', p, '不得预测结果概率或自动拟境外法院申请书')
            _walk_forbidden(c, child, p)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _walk_forbidden(c, child, path + '.' + str(i))


def validate(data, stage='draft', profile=None, base_path=None):
    if stage not in ('draft', 'submission', 'plan', 'filing', 'board', 'forecast'):
        raise MatrixError('STAGE', 'stage', '不支持的执行校验阶段', 4)
    profile = profile or (stage if stage in ('board', 'forecast') else data.get('profile', 'plan'))
    if not isinstance(profile, str) or profile not in PROFILES:
        raise MatrixError('PROFILE', 'profile', '不支持的执行 profile', 4)
    filing = stage == 'filing' or (stage == 'submission' and profile == 'plan')
    filing_context = filing or profile == 'plan'
    c = Check(data, stage, profile, strict=filing)
    c.schema(1)
    c.required(data, ('case', 'awards', 'targets', 'open_questions'), '')
    c.load_questions()
    c.text(data.get('case'), 'case')
    c.need(data.get('case'), 'case', False)
    awards = c.index('awards', r'AW-\d{2,}')
    targets = c.index('targets', r'T-\d{2,}')
    # Relief/debtor registries are intentionally independent of the case matrix;
    # case_matrix_ref imports IDs read-only when an existing case file is supplied.
    for key in ('relief', 'debtors'):
        if key not in data:
            c.error('MISSING', key, '须登记救济与债务人，未知可为空并登记 OQ')
    relief = c.index('relief', r'R-\d{2,}')
    debtors = c.index('debtors', r'DTR-\d{2,}')
    if data.get('case_matrix_ref'):
        if not isinstance(data['case_matrix_ref'], str):
            c.error('TYPE', 'case_matrix_ref', '关联案件矩阵须为文件路径')
        else:
            linked = load_yaml(resolve_path(data['case_matrix_ref'], base_path.parent if base_path else None))
            if type(linked.get('schema')) is not int or linked['schema'] != 2:
                c.error('CASE_SCHEMA', 'case_matrix_ref', '关联案件矩阵须为 schema 2')
            linked_relief = linked.get('relief')
            if not isinstance(linked_relief, list) or any(not isinstance(r, dict) for r in linked_relief):
                c.error('TYPE', 'case_matrix_ref.relief', '关联救济结构不合法')
            else:
                for row in linked_relief:
                    ident = row.get('id')
                    if not isinstance(ident, str) or not re.fullmatch(r'R-\d{2,}', ident):
                        c.error('ID', 'case_matrix_ref.relief', '关联救济编号不合法')
                    elif ident in relief and any(relief[ident].get(k) != row.get(k) for k in ('type', 'amount', 'currency')):
                        c.error('RELIEF_CONFLICT', 'relief', '本地与案件矩阵救济口径冲突')
                    else:
                        relief[ident] = row
    selected = c.refs(data.get('selected_targets', []), targets, 'selected_targets')
    # Explicit blockers scoped solely to unselected targets do not stop this filing.
    unselected_paths = {c.entities[t] for t in targets if t not in selected}
    for i, q in enumerate(data.get('open_questions', [])):
        if not isinstance(q, dict):
            continue
        paths = q.get('paths', [q['path']] if 'path' in q else [])
        ids = q.get('targets', [])
        scoped = isinstance(paths, list) and isinstance(ids, list) and bool(paths or ids)
        scoped = scoped and all(isinstance(p, str) and any(p == u or p.startswith(u + '.') for u in unselected_paths) for p in paths)
        scoped = scoped and all(isinstance(t, str) and t in targets and t not in selected for t in ids)
        if scoped:
            c.blocks = [b for b in c.blocks if not (b['code'] == 'OPEN_BLOCKING_QUESTION' and b['path'] == 'open_questions.%s' % i)]
    if filing and not selected:
        c.block('SELECT_TARGET', 'selected_targets', '立案须明确选定目标；不强制未选法域同时就绪')
    if not targets and profile in ('plan', 'asset', 'board'):
        c.gap('targets')
    if profile == 'forecast':
        _forecast(c, data.get('forecast'))
    if filing:
        if not awards:
            c.block('AWARD_REQUIRED', 'awards', '立案须有拟执行裁决')
        if not debtors:
            c.block('DEBTOR_REQUIRED', 'debtors', '立案须核实裁决债务人')
    active_awards = set()
    for ident in selected:
        refs = c.refs(targets[ident].get('awards', []), awards, c.entities[ident] + '.awards')
        if filing_context:
            active_awards.update(refs)
            if not targets[ident].get('awards'):
                c.block('TARGET_AWARD', c.entities[ident] + '.awards', '选定目标须挂接拟执行裁决')
    for ident, row in debtors.items():
        p = c.entities[ident]
        c.text(row.get('name'), p + '.name')
        c.need(row.get('name'), p + '.name', False)
        c.boolean(row.get('state_link', 'unknown'), p + '.state_link', tristate=True)
        if 'verified' in row:
            c.boolean(row['verified'], p + '.verified')
    for ident, row in relief.items():
        p = c.entities.get(ident, 'case_matrix_ref.relief.' + ident)
        c.enum(row.get('type'), ('money', 'costs', 'performance', 'injunction', 'declaration'), p + '.type')
        if row.get('type') in ('money', 'costs'):
            c.number(row.get('amount'), p + '.amount')
            c.text(row.get('currency'), p + '.currency')
            c.need(row.get('currency'), p + '.currency', False)
    for ident, row in awards.items():
        p = c.entities[ident]
        critical = ident in active_awards
        c.enum(row.get('type'), ('partial', 'interim', 'final', 'consent', 'costs', 'supplemental', 'correction'), p + '.type')
        for key in ('date', 'received'):
            _date(c, row.get(key), p + '.' + key, critical)
        for key in ('seat', 'institution', 'rules_version', 'finality', 'source', 'service_evidence'):
            c.need(row.get(key), p + '.' + key, critical)
        referenced = c.refs(row.get('relief', []), relief, p + '.relief')
        c.need(referenced, p + '.relief', critical)
        debtor_refs = c.refs(row.get('debtors', []), debtors, p + '.debtors')
        c.need(debtor_refs, p + '.debtors', critical)
        monetary = [r for r in referenced if relief[r].get('type') in ('money', 'costs')]
        if monetary:
            c.need(row.get('currency'), p + '.currency', critical)
            money = [r for r in monetary if relief[r].get('type') == 'money']
            cost_relief = [r for r in monetary if relief[r].get('type') == 'costs']
            principal = c.number(row.get('principal'), p + '.principal') if money or 'principal' in row else None
            if money:
                c.need(row.get('principal'), p + '.principal', critical)
            c.need(row.get('interest'), p + '.interest', critical)
            c.need(row.get('costs'), p + '.costs', critical)
            allocation = c.mapping(row.get('amount_by_relief', {}), p + '.amount_by_relief')
            if not allocation and len(money) == 1 and not cost_relief:
                allocation = {money[0]: row.get('principal')}
            if critical and set(allocation) != set(monetary):
                c.block('AWARD_ALLOCATION', p + '.amount_by_relief', '金额分配须完整且仅覆盖本裁决的金钱与费用救济')
            amounts = {}
            for rid, amount in allocation.items():
                c.refs(rid, monetary, p + '.amount_by_relief', many=False)
                n = c.number(amount, p + '.amount_by_relief.' + str(rid))
                amounts[rid] = n
                if rid in monetary and critical and (n is None or decimal(relief[rid].get('amount')) != n or
                                                     relief[rid].get('currency') != row.get('currency')):
                    c.block('AWARD_QUANTUM', p + '.amount_by_relief', '执行金额应与裁决及 R- 清偿上限一致，不能沿用未获支持的请求额')
            if critical and money and principal is not None and all(amounts.get(r) is not None for r in money):
                if sum(amounts[r] for r in money) != principal:
                    c.block('AWARD_PRINCIPAL', p + '.principal', '本金须等于本裁决 money 救济分配之和；利息与费用另列')
            if cost_relief:
                costs = c.mapping(row.get('costs'), p + '.costs')
                cost_amounts = [c.number(value, p + '.costs.' + str(key)) for key, value in costs.items()]
                if critical and (not cost_amounts or any(n is None for n in cost_amounts)):
                    c.block('AWARD_COSTS', p + '.costs', '费用救济须有同裁决币种的明确费用明细')
                elif critical and all(amounts.get(r) is not None for r in cost_relief):
                    if sum(cost_amounts) != sum(amounts[r] for r in cost_relief):
                        c.block('AWARD_COSTS', p + '.costs', '费用明细须与 costs 救济分配之和一致，不并入本金')
        if row.get('type') == 'consent':
            basis = c.mapping(row.get('consent_basis', {}), p + '.consent_basis')
            for key in ('tribunal_power', 'procedural_stage', 'party_agreement', 'source'):
                c.need(basis.get(key), p + '.consent_basis.' + key, critical)
            _verified(c, basis, p + '.consent_basis', critical)
        _verified(c, row, p, critical)
    known_oq = {q.get('id') for q in data.get('open_questions', []) if isinstance(q, dict)}
    for ident, row in targets.items():
        p = c.entities[ident]
        critical = ident in selected and filing_context
        c.required(row, ('jurisdiction', 'asset', 'convention', 'procedure', 'deadlines',
                         'immunity', 'insolvency', 'sanctions', 'cost'), p)
        c.text(row.get('jurisdiction'), p + '.jurisdiction')
        c.need(row.get('jurisdiction'), p + '.jurisdiction', critical)
        assets = c.mapping(row.get('asset'), p + '.asset')
        for key in ('type', 'location', 'source', 'locator'):
            c.text(assets.get(key), p + '.asset.' + key)
            c.need(assets.get(key), p + '.asset.' + key, critical)
        if 'value' in assets:
            c.number(assets['value'], p + '.asset.value')
        debtor = row.get('debtor')
        if filled(debtor):
            c.refs(debtor, debtors, p + '.debtor', many=False)
        else:
            c.gap(p + '.debtor', critical)
        if 'awards' in row:
            c.refs(row['awards'], awards, p + '.awards')
        target_relief = c.refs(row.get('relief', []), relief, p + '.relief')
        if critical:
            c.need(target_relief, p + '.relief')
            award_relief = set()
            for aw in row.get('awards', []) if isinstance(row.get('awards'), list) else []:
                if isinstance(aw, str) and aw in awards and isinstance(awards[aw].get('relief'), list):
                    award_relief.update(r for r in awards[aw]['relief'] if isinstance(r, str))
            if any(r not in award_relief for r in target_relief):
                c.block('TARGET_RELIEF', p + '.relief', '执行目标救济须在对应裁决义务范围内')
        if 'open_questions' in row:
            c.refs(row['open_questions'], known_oq, p + '.open_questions')
        convention = c.mapping(row.get('convention'), p + '.convention')
        c.boolean(convention.get('ny'), p + '.convention.ny', tristate=True)
        if convention.get('ny') is False:
            c.need(convention.get('alternatives', row.get('alternatives')), p + '.convention.alternatives', critical)
        c.need(convention.get('source'), p + '.convention.source', critical)
        if critical:
            _verified(c, convention, p + '.convention')
            c.need(convention.get('implementation'), p + '.convention.implementation')
            if unknown(convention.get('ny')):
                c.block('CONVENTION_UNKNOWN', p + '.convention.ny', '立案须核查适用的承认与执行路径')
        if row.get('regime') == 'icsid' and convention.get('ny') is True:
            c.error('REGIME_CONFLICT', p + '.regime', 'ICSID 专门执行机制不能套用纽约公约审查')
        procedure = c.mapping(row.get('procedure'), p + '.procedure')
        for key in ('type', 'court', 'local_counsel', 'service'):
            c.need(procedure.get(key), p + '.procedure.' + key, critical)
        if critical:
            _verified(c, procedure, p + '.procedure')
            if procedure.get('counsel_confirmed') is not True:
                c.block('COUNSEL_CONFIRMATION', p + '.procedure.counsel_confirmed', '选定目标须经本地律师确认')
        if 'counsel_confirmed' in procedure:
            c.boolean(procedure['counsel_confirmed'], p + '.procedure.counsel_confirmed')
        deadlines = c.listing(row.get('deadlines'), p + '.deadlines')
        if critical and not deadlines:
            c.block('DEADLINES_REQUIRED', p + '.deadlines', '选定目标须核实期限或有依据的不适用结论')
        for i, raw in enumerate(deadlines):
            dp = p + '.deadlines.' + str(i)
            deadline = c.mapping(raw, dp)
            c.enum(deadline.get('status'), ('verified', 'unverified', 'unknown', 'not_applicable'), dp + '.status')
            if deadline.get('status') == 'not_applicable':
                c.need(deadline.get('reason'), dp + '.reason', critical)
                c.need(deadline.get('source'), dp + '.source', critical)
                _verified(c, deadline, dp, critical)
            elif deadline.get('status') != 'verified':
                if not unknown(deadline.get('due')):
                    c.error('UNVERIFIED_DEADLINE', dp + '.due', '未核验期限只能写 unknown，不得写日期或天数')
                c.gap(dp, critical)
            else:
                _date(c, deadline.get('due'), dp + '.due', critical)
                for key in ('name', 'start_event', 'source'):
                    c.need(deadline.get(key), dp + '.' + key, critical)
                if critical and iso_date(deadline.get('due')) and str(deadline['due']) < dt.date.today().isoformat():
                    c.block('DEADLINE_PASSED', dp, '所填期限已届满，须重新核实救济路径')
        for name, flag in SPECIALS.items():
            block = c.mapping(row.get(name, {'flag': 'unknown'}), p + '.' + name)
            c.boolean(block.get(flag), p + '.' + name + '.' + flag, tristate=True)
            if unknown(block.get(flag)):
                c.gap(p + '.' + name + '.' + flag, critical)
            if critical:
                _verified(c, block, p + '.' + name)
                c.need(block.get('source'), p + '.' + name + '.source')
            if block.get(flag) is True:
                review = c.mapping(block.get('review', {}), p + '.' + name + '.review')
                if not review:
                    c.gap(p + '.' + name + '.review', critical)
                if name == 'immunity':
                    for key in ('jurisdiction', 'execution', 'asset_character', 'waiver'):
                        c.need(review.get(key), p + '.immunity.review.' + key, critical)
                elif name == 'insolvency':
                    for key in ('stay', 'claim_deadline', 'priority'):
                        c.need(review.get(key), p + '.insolvency.review.' + key, critical)
        debtor_row = debtors.get(debtor, {}) if isinstance(debtor, str) else {}
        state_link = row.get('state_link', debtor_row.get('state_link', 'unknown'))
        c.boolean(state_link, p + '.state_link', tristate=True)
        if unknown(state_link):
            c.gap(p + '.state_link', critical)
        if state_link is True:
            c.warn('STATE_LINK_REVIEW', p + '.immunity', '国家关联只触发核查；国企不自动享有豁免')
            immunity = c.mapping(row.get('immunity'), p + '.immunity')
            c.need(immunity.get('state_link_analysis'), p + '.immunity.state_link_analysis', critical)
        if critical:
            _verified(c, debtor_row, p + '.debtor')
            _verified(c, assets, p + '.asset')
            owner = assets.get('owner')
            c.need(owner, p + '.asset.owner')
            if filled(owner) and owner != debtor:
                c.warn('THIRD_PARTY_ASSET', p + '.asset.owner', '关联或第三方资产不能当然用于清偿裁决债务')
                basis = c.mapping(assets.get('liability_basis', {}), p + '.asset.liability_basis')
                for key in ('instrument', 'source', 'locator', 'scope'):
                    c.need(basis.get(key), p + '.asset.liability_basis.' + key)
                _verified(c, basis, p + '.asset.liability_basis')
            else:
                c.need(assets.get('ownership_source'), p + '.asset.ownership_source')
            for award_id in row.get('awards', []) if isinstance(row.get('awards'), list) else []:
                award = awards.get(award_id, {}) if isinstance(award_id, str) else {}
                if isinstance(award.get('debtors'), list) and debtor not in award['debtors']:
                    c.block('AWARD_DEBTOR', p + '.debtor', '目标债务人不是所选裁决的义务主体')
            requirements = c.listing(row.get('file_requirements', list(FILE_ITEMS)), p + '.file_requirements')
            if not requirements:
                c.block('FILE_REQUIREMENTS', p + '.file_requirements', '文件要求不得空置；不适用须逐项说明')
            # Never let a short per-target list omit the core award/agreement/authority chain.
            _file_chain(c, row.get('file_chain', data.get('file_chain', {})), p + '.file_chain',
                        list(dict.fromkeys(list(FILE_ITEMS) + [r for r in requirements if isinstance(r, str)])))
        c.mapping(row.get('cost'), p + '.cost')
    budget_totals = calculate_budget(data, c)
    recoveries = check_recoveries(data, relief, c)
    if profile in ('plan', 'board'):
        for key in ('strategy', 'budget', 'timeline'):
            value = c.mapping(data.get(key, {}), key)
            c.need(value, key, False)
        strategy = c.mapping(data.get('strategy', {}), 'strategy')
        if 'order' in strategy:
            c.refs(strategy['order'], targets, 'strategy.order')
        timeline = c.mapping(data.get('timeline', {}), 'timeline')
        if timeline:
            c.need(timeline.get('critical_path'), 'timeline.critical_path', False)
    if profile == 'board':
        board = c.mapping(data.get('board_brief'), 'board_brief')
        for key in ('decision', 'options', 'costs', 'risks', 'recommendation'):
            if not filled(board.get(key)):
                c.block('BOARD_SECTION', 'board_brief.' + key, '董事会 profile 必须完成五节简报')
        if not budget_totals:
            c.block('BOARD_BUDGET', 'budget', '董事会 profile 需要可计算的分币种预算')
        # Board report gates its own deliverable, never every target's filing readiness.
        if stage in ('board', 'submission'):
            board_blocks = [b for b in c.blocks if b['code'].startswith('BOARD_')]
            c.errors.extend(board_blocks)
    if profile == 'counsel':
        rows = c.listing(data.get('counsel_instructions'), 'counsel_instructions')
        c.need(rows, 'counsel_instructions', False)
        for i, raw in enumerate(rows):
            p = 'counsel_instructions.%s' % i
            row = c.mapping(raw, p)
            for key in ('jurisdiction', 'question', 'deliverable', 'budget', 'due'):
                c.need(row.get(key), p + '.' + key, False)
            if 'budget' in row:
                c.number(row['budget'], p + '.budget')
    if profile in ('asset', 'immunity', 'insolvency'):
        name = profile + '_review'
        value = c.mapping(data.get(name), name)
        c.need(value, name, False)
    settlement = c.mapping(data.get('settlement', {}), 'settlement')
    if settlement.get('consent_award_requested') is True:
        for key in ('tribunal_power', 'procedural_stage', 'party_agreement', 'source'):
            c.need(settlement.get(key), 'settlement.' + key, filing)
        _verified(c, settlement, 'settlement', filing)
        c.warn('CONSENT_AWARD_LIMIT', 'settlement', '合意裁决取决于权限、程序阶段与合意，不能假设裁决后随时作出')
    _walk_forbidden(c, data)
    c.unknowns()
    # Filing readiness is explicitly separate from internal plan/forecast delivery.
    if not selected or not awards:
        c.block('FILING_NOT_READY', 'selected_targets', '内部方案可交付；尚未达到执行立案条件')
    result = c.result(budget_by_currency=budget_totals, recoveries_by_relief=recoveries,
                      internal_delivery_ready=not c.errors)
    if not filing:
        result['submission_ready'] = False
    return result


def calculate_budget(data, c=None):
    c = c or Check(data)
    totals = defaultdict(Decimal)
    targets = c.listing(data.get('targets', []), 'targets')
    for i, raw in enumerate(targets):
        if not isinstance(raw, dict):
            continue
        p = 'targets.%s.cost' % i
        cost = c.mapping(raw.get('cost', {}), p)
        if not cost:
            continue
        currency = cost.get('currency')
        if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
            if unknown(currency):
                c.gap(p + '.currency')
            else:
                c.error('CURRENCY', p + '.currency', '币种须为三位大写代码或 unknown')
            continue
        for key in ('budget', 'contingency'):
            amount = c.number(cost.get(key, 0), p + '.' + key)
            if amount is not None:
                totals[currency] += amount
    budget = c.mapping(data.get('budget', {}), 'budget')
    extra = budget.get('contingency', {})
    if isinstance(extra, dict):
        for currency, value in extra.items():
            if not re.fullmatch(r'[A-Z]{3}', currency):
                c.error('CURRENCY', 'budget.contingency', '应按币种登记预备费')
                continue
            amount = c.number(value, 'budget.contingency.' + currency)
            if amount is not None:
                totals[currency] += amount
    elif decimal(extra) == 0:
        pass
    elif decimal(extra) is not None and isinstance(budget.get('currency'), str):
        totals[budget['currency']] += c.number(extra, 'budget.contingency') or Decimal(0)
    else:
        c.error('BUDGET_CURRENCY', 'budget.contingency', '预备费须按币种登记')
    total = budget.get('total')
    if total is not None:
        amount = c.number(total, 'budget.total')
        if len(totals) > 1:
            c.error('CROSS_CURRENCY_TOTAL', 'budget.total', '跨币种不得直接相加；使用 by_currency，不接受混币种手写合计')
        elif len(totals) == 1 and amount is not None and amount != next(iter(totals.values())):
            c.error('BUDGET_TOTAL', 'budget.total', '手填预算合计与计算结果不一致')
    if 'by_currency' in budget:
        recorded = c.mapping(budget['by_currency'], 'budget.by_currency')
        for currency, value in recorded.items():
            amount = c.number(value, 'budget.by_currency.' + currency)
            if amount is not None and amount != totals.get(currency, Decimal(0)):
                c.error('BUDGET_TOTAL', 'budget.by_currency.' + currency, '分币种合计与目标预算不一致')
    return {currency: str(value) for currency, value in sorted(totals.items())}


def check_recoveries(data, relief, c):
    """One global receipt ledger; shared R IDs cap satisfaction across all T IDs."""
    totals, converted, receipts = defaultdict(lambda: defaultdict(Decimal)), defaultdict(Decimal), set()
    rows = []
    for i, target in enumerate(data.get('targets', [])):
        if not isinstance(target, dict):
            continue
        for j, receipt in enumerate(c.listing(target.get('collections', []), 'targets.%s.collections' % i)):
            rows.append(('targets.%s.collections.%s' % (i, j), receipt))
    for i, receipt in enumerate(c.listing(data.get('collections', []), 'collections')):
        rows.append(('collections.%s' % i, receipt))
    for p, raw in rows:
        row = c.mapping(raw, p)
        ident = row.get('receipt_id')
        if not isinstance(ident, str) or not ident or ident in receipts:
            c.error('DUPLICATE_RECEIPT', p + '.receipt_id', '回款凭证须全局唯一，不能多目标重复记账')
        else:
            receipts.add(ident)
        rid = row.get('relief')
        refs = c.refs(rid, relief, p + '.relief', many=False)
        currency, amount = row.get('currency'), c.number(row.get('amount'), p + '.amount')
        if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
            c.error('CURRENCY', p + '.currency', '回款必须记录明确币种')
            continue
        c.need(row.get('source'), p + '.source', True)
        if not refs or amount is None:
            continue
        totals[rid][currency] += amount
        obligation = relief[rid]
        if obligation.get('type') not in ('money', 'costs'):
            c.error('NONMONEY_COLLECTION', p + '.relief', '非金钱救济不能直接登记金钱清偿')
            continue
        if currency == obligation.get('currency'):
            converted[rid] += amount
        else:
            fx = c.mapping(row.get('fx', {}), p + '.fx')
            rate = decimal(fx.get('rate'))
            if rate is None or rate <= 0 or fx.get('to') != obligation.get('currency') or fx.get('verified') is not True or not filled(fx.get('source')) or not iso_date(fx.get('date')):
                c.block('RECOVERY_FX', p + '.fx', '异币种回款须有已核验汇率、日期和来源后才能确认未超额清偿')
                c.gap(p + '.fx')
            else:
                converted[rid] += amount * rate
        cap = decimal(obligation.get('amount'))
        for award in data.get('awards', []):
            if not isinstance(award, dict) or award.get('verified') is not True or award.get('currency') != obligation.get('currency'):
                continue
            allocation = award.get('amount_by_relief', {})
            if not allocation and award.get('relief') == [rid] and obligation.get('type') == 'money':
                allocation = {rid: award.get('principal')}
            awarded = decimal(allocation.get(rid)) if isinstance(allocation, dict) else None
            if awarded is not None:
                cap = awarded if cap is None else min(cap, awarded)
        if cap is None:
            c.block('RECOVERY_CAP_UNKNOWN', p + '.relief', '清偿上限未知，不能确认未重复清偿')
        elif converted[rid] > cap:
            c.error('DOUBLE_RECOVERY', p, '所有目标合计清偿超过同一救济上限')
    return {rid: {currency: str(value) for currency, value in sorted(values.items())}
            for rid, values in sorted(totals.items())}


def check_file(path, stage='draft', profile=None):
    return checked_file(path, stage, profile, validate)


def summarize(data):
    return {'targets': len(data.get('targets', [])), 'awards': len(data.get('awards', [])),
            'verified_deadlines': sum(d.get('status') == 'verified' for t in data.get('targets', [])
                                      for d in t.get('deadlines', []) if isinstance(d, dict)),
            'blocking_questions': sum(q.get('status', 'open') == 'open' and q.get('blocking') is True
                                      for q in data.get('open_questions', [])),
            'budget_by_currency': calculate_budget(data)}


def render(data, result=None, profile=None):
    result = result or validate(data, profile=profile)
    return render_view(data, result, '跨境执行方案（内部完整阅读版）',
                       'enforcement', profile or data.get('profile', 'plan'))


if __name__ == '__main__':
    sys.exit(cli(sys.modules[__name__]))
