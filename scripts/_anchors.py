"""锚点校验唯一实现：语法、家族排序、紧邻正文、悬空与范围覆盖由本模块统一承担。

verify_suite（交付闸门）与 case_matrix（范围+家族覆盖语义层）此前各自维护一套
行走与判定规则，对同一份记稿可能给出相反结论。本模块合并为一遍扫描：
各调用方只保留消息格式与闸门级别（error/block/require）的差异。
"""
import re

ANCHOR_ID = re.compile(r'(?:F-\d+|CL-\d+|DF-\d+|E-[A-Z0-9]+-\d+|EV-\d+|R-\d+|A-\d+)')
MATRIX_ID = re.compile(r'(?:F-\d{3,}|E-(?:CL|DF)\d{2,}-\d{2,}|CL-\d{2,}|DF-\d{2,}|EV-\d{3,}|R-\d{2,}|A-\d{2,}|T-\d{2,})')
ANCHOR_LINE_RE = re.compile(r'#!\s*锚点\s*[:：]\s*(.*)$')
SCOPE_LINE_RE = re.compile(r'^#!\s*锚点范围\s*[:：]\s*(.*)$')
FENCE_PREFIXES = ('```', '~~~')
LETTER_FURNITURE_RE = re.compile(r'^(Dear\b|Yours\b|Sincerely\b|敬启|此致|日期[:：]|Date:|To:|From:)', re.I)
NUMBERED_RE = re.compile(r'^\d+[.)]?\s+')
FAMILY_RANK = {'F': 0, 'CL': 1, 'DF': 2, 'E': 3, 'EV': 4, 'R': 5, 'A': 6}
SCOPE_FAMILIES = {'facts': ('F-',), 'argument': ('E-', 'A-'), 'relief': ('R-', 'DF-')}
SCOPES = ('facts', 'argument', 'relief', 'none')
SCOPE_TITLE_RES = (
    ('facts', re.compile(r'事实|背景|facts|factual|background', re.I)),
    ('relief', re.compile(r'救济|请求事项|relief|remed', re.I)),
    ('argument', re.compile(r'法律|论证|管辖|紧迫|不可弥补|利益衡量|legal|law|argument|jurisdiction|merits|urgency', re.I)),
)


def scan(text, *, require=False, list_exempt=True, id_pattern=ANCHOR_ID,
         known=frozenset(), scopes=False, denials=frozenset()):
    """对文书正文做单遍锚点行走，返回结构化发现。

    issues: line -> [{kind, ...}]；kind 取 syntax/order/unknown/not_attached/
      not_adjacent/missing/dangling/scope_invalid/coverage。
    paragraphs: [{line, ids, scope}] 逐段列表（ids 为挂接到的锚点）。
    counts: {'prose': 全部正文段数, 'substantive': facts/argument/relief 段数}。
    anchored_ids: 实际挂接到正文的锚点（排序去重）。

    统一规则（两端同一条）：锚点行必须紧跟正文段，中间的空行、标题、表格、
    围栏、信函套语都算不紧邻；列表行是否算正文由 list_exempt 决定
    （verify 豁免、case_matrix 计入）。
    """
    issues = {}
    paragraphs = []

    def add(line, kind, **kw):
        issues.setdefault(line, []).append(dict(kind=kind, **kw))

    pending_tokens, pending_line = None, 0
    scope, scope_stack = None, []
    fence = None
    in_frontmatter = text.startswith('---\n')
    para_ids, para_line, para_scope, para_lines = [], 0, None, 0
    prose = substantive = 0

    def flush():
        nonlocal para_ids, para_line, para_scope, para_lines, prose, substantive
        if para_lines:
            prose += 1
            if para_scope:
                substantive += 1
                expected = SCOPE_FAMILIES[para_scope]
                denial_hit = para_scope == 'argument' and any(v in denials for v in para_ids)
                if not denial_hit and not any(v.startswith(p) for p in expected for v in para_ids):
                    add(para_line, 'coverage', scope=para_scope)
            paragraphs.append({'line': para_line, 'ids': list(para_ids), 'scope': para_scope})
        para_ids, para_line, para_scope, para_lines = [], 0, None, 0

    def drop_pending():
        nonlocal pending_tokens, pending_line
        if pending_tokens is not None:
            add(pending_line, 'not_adjacent')
            pending_tokens, pending_line = None, 0

    for number, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if in_frontmatter:
            if number > 1 and s == '---':
                in_frontmatter = False
            continue
        m = ANCHOR_LINE_RE.match(raw)
        if m:
            flush()
            if pending_tokens is not None:
                add(pending_line, 'not_attached')
                pending_tokens, pending_line = None, 0
            tokens = [v for v in re.split(r'[,，/\s]+', m.group(1).strip()) if v]
            if not tokens or len(tokens) != len(set(tokens)) or any(not id_pattern.fullmatch(v) for v in tokens):
                add(number, 'syntax')
            else:
                ranks = [FAMILY_RANK.get(t.split('-')[0]) for t in tokens]
                if all(r is not None for r in ranks) and ranks != sorted(ranks):
                    add(number, 'order')
                unknown = sorted(set(tokens) - set(known))
                if unknown:
                    add(number, 'unknown', ids=unknown)
            pending_tokens, pending_line = tokens, number
            continue
        if scopes:
            sm = SCOPE_LINE_RE.match(raw)
            if sm:
                flush()
                drop_pending()
                value = sm.group(1).strip()
                if value not in SCOPES:
                    add(number, 'scope_invalid', value=value)
                scope = value if value in ('facts', 'argument', 'relief') else None
                continue
        if s.startswith(FENCE_PREFIXES):
            flush()
            drop_pending()
            marker = s[:3]
            fence = None if fence == marker else marker
            continue
        if fence:
            continue
        heading = re.match(r'^(#{1,6})\s+(.*)', s)
        if heading:
            flush()
            drop_pending()
            if scopes:
                level, title = len(heading.group(1)), heading.group(2).lower()
                while scope_stack and scope_stack[-1][0] >= level:
                    scope_stack.pop()
                inherited = scope_stack[-1][1] if scope_stack else None
                scope = inherited
                for name, rx in SCOPE_TITLE_RES:
                    if rx.search(title):
                        scope = name
                        break
                scope_stack.append((level, scope))
            continue
        if not s:
            drop_pending()
            flush()
            continue
        is_list = s.startswith(('- ', '* '))
        furniture = ((not is_list or list_exempt)
                     and (s.startswith(('#', '|', '>', '~')) or is_list
                          or s in ('---', '***') or s == '<pagebreak>'
                          or bool(LETTER_FURNITURE_RE.match(s))))
        if furniture:
            drop_pending()
            flush()
            continue
        if NUMBERED_RE.match(s) and para_lines:
            flush()
            start = True
        else:
            start = not para_lines
        if start:
            if pending_tokens is not None:
                para_ids, pending_tokens, pending_line = list(pending_tokens), None, 0
            elif require:
                add(number, 'missing')
            para_line, para_scope = number, scope
        para_lines += 1
    flush()
    if pending_tokens is not None:
        add(pending_line, 'dangling')
    return {'issues': issues, 'paragraphs': paragraphs, 'counts': {'prose': prose, 'substantive': substantive},
            'anchored_ids': sorted({v for p in paragraphs for v in p['ids']})}
