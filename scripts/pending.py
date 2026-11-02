"""Explicit, file-scoped pending items; never treats an unregistered blank as intentional."""
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)
import hashlib
import json
import re
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

BANNER_RE = re.compile(r'DRAFT — 审阅草案：含 (\d+) 处待确认项，不可提交')

def banner_text(count):
    return f'DRAFT — 审阅草案：含 {count} 处待确认项，不可提交'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def json_path(json_file, value):
    p = Path(value)
    return (p if p.is_absolute() else Path(json_file).resolve().parent / p).resolve()

def source_path(manifest_file, manifest):
    source = json_path(manifest_file, manifest['source'])
    if not source.is_file():
        raise ValueError(f"无法定位记稿 {manifest['source']}（相对 {Path(manifest_file).resolve().parent}）")
    return source

def load(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != 'rulesuite-pending/1' or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', data.get('case', '')):
        raise ValueError('pending schema 或 case 无效')
    ids, entries = set(), []
    for item in data.get('items', []):
        ident = item.get('id', '')
        if not re.fullmatch(r'Q[1-9][0-9]*', ident) or ident in ids:
            raise ValueError('pending ID 必须唯一且为 Q1、Q2 等')
        ids.add(ident)
        if item.get('status') not in ('open', 'resolved') or not item.get('question') or not item.get('owner'):
            raise ValueError('pending 须填 status、question、owner')
        if item.get('status') == 'resolved' and legal_item(item) and not legal_resolution(item):
            raise ValueError('法律/期限/来源待核项关闭须含核验人、核验日期与来源；用户同意不能代替法律核验')
        token = item.get('placeholder', '')
        if not token.startswith(ident + ':') or any(c in token for c in '[]\r\n'):
            raise ValueError(f'pending {ident} 的 placeholder「{token}」不合规：须以「{ident}:」开头，不能含括号或换行')
        files = item.get('files', [])
        if not files or not all(isinstance(f, str) and f for f in files):
            raise ValueError('pending files 须为非空路径列表')
        item = dict(item, files=[str(json_path(path, f)) for f in files])
        entries.append(item)
    return data, entries

def validate_text(text, relative, entries):
    import difflib
    tokens = re.findall(r'\[\[([^\[\]\r\n]+)\]\]', text)
    allowed = {x['placeholder'] for x in entries if x['status']=='open' and relative in x['files']}
    missing = set(tokens) - allowed
    if missing:
        hints = []
        for m in sorted(missing):
            near = difflib.get_close_matches(m, sorted(allowed), n=1)
            hints.append(m + (f'（与已登记「{near[0]}」相近，Q 编号与冒号后内容须逐字一致）' if near
                              else '（pending.json 无相近登记；先登记或替换为案件事实）'))
        raise ValueError(f'{relative} 存在未登记或已解决占位符: ' + '；'.join(hints))
    if text.count('[[') != len(tokens) or text.count(']]') != len(tokens):
        raise ValueError('占位符不闭合或嵌套')
    return tokens

def validate_docx(path, root, registry):
    data, entries = load(registry)
    manifest = json.loads(path.with_suffix('.paras.json').read_text(encoding='utf-8'))
    if manifest.get('delivery_state') != 'draft' or manifest.get('pending_sha256') != hashlib.sha256(Path(registry).read_bytes()).hexdigest():
        raise ValueError(f'{path.name} 草案状态/待确认清单已变更，须重新渲染')
    if manifest.get('case') != data['case']:
        raise ValueError('草案案件代号与 pending 不一致')
    source = source_path(path.with_suffix('.paras.json'), manifest)
    relative = str(source)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest['source_sha256'] or hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['docx_sha256']:
        raise ValueError('草案、记稿、清单哈希不一致')
    tokens = validate_text(source.read_text(encoding='utf-8'), relative, entries)
    with zipfile.ZipFile(path) as z:
        body = ET.fromstring(z.read('word/document.xml'))
        m = BANNER_RE.search(''.join(body.itertext()))
        if not m:
            raise ValueError('草案缺少状态声明（DRAFT — 审阅草案：含 N 处待确认项，不可提交）')
        if int(m.group(1)) != len(tokens):
            raise ValueError(f'状态声明与实际待确认数不一致：声明 {m.group(1)} 处，记稿实际 {len(tokens)} 处；用 --draft 重新渲染')
        for name in z.namelist():
            if not re.fullmatch(r'word/(document|header\d*|footer\d*)\.xml', name):
                continue
            xml = ET.fromstring(z.read(name))
            for run in xml.findall('.//w:r', NS):
                if run.find('w:rPr/w:highlight', NS) is not None:
                    text = ''.join(t.text or '' for t in run.findall('w:t', NS))
                    if text not in {'['+t+']' for t in tokens}:
                        import difflib
                        near = difflib.get_close_matches(text.strip('[]'), tokens, n=1)
                        hint = f'（与已登记「[{near[0]}]」相近，疑为渲染后手改 docx；请用 --draft 重新渲染）' if near else ''
                        raise ValueError(f'{path.name} 有未映射高亮内容: {text}{hint}')
    return tokens


def legal_item(item):
    return item.get('kind', item.get('category', item.get('type'))) in ('legal','law','source','deadline') or item.get('requires_legal_verification') is True


def legal_resolution(item):
    from datetime import date
    resolution = item.get('resolution', {})
    if not isinstance(resolution, dict) or not all(resolution.get(k) for k in ('verified_by','verified_at','source')):
        return False
    try:
        return date.fromisoformat(str(resolution['verified_at'])) <= date.today()
    except (ValueError, TypeError):
        return False


def oq_links(item):
    value = item.get('oq_ids', item.get('oq_id', item.get('open_question', item.get('oq', []))))
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(v, str) and re.fullmatch(r'OQ-\d+', v) for v in value):
        raise ValueError('oq_ids 须为 OQ-编号列表')
    return value


def cross_check(pending_file, matrix_file, mode='draft', files=None, profile=None):
    from intake import safe_yaml
    data, entries = load(pending_file)
    matrix = safe_yaml(Path(matrix_file).read_text(encoding='utf-8'))
    if not isinstance(matrix, dict):
        raise ValueError('矩阵须为映射')
    if matrix.get('case') and matrix['case'] != data['case']:
        raise ValueError('pending 与矩阵案件代号不一致')
    questions = {}
    def walk(node):
        if isinstance(node, dict):
            ident = node.get('id')
            if isinstance(ident, str) and re.fullmatch(r'OQ-\d+', ident):
                if ident in questions:
                    raise ValueError('矩阵含重复OQ编号')
                questions[ident] = node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(matrix)
    selected = {str(Path(f).resolve()) for f in files} if files is not None else {f for e in entries for f in e['files']}
    relevant = [e for e in entries if selected.intersection(e['files'])]
    errors, warnings, present = [], [], set()
    for file in selected:
        if not Path(file).is_file():
            errors.append('登记记稿不存在：' + Path(file).name)
            continue
        text = Path(file).read_text(encoding='utf-8')
        try:
            tokens = validate_text(text, file, relevant)
            present.update(t.split(':',1)[0] for t in tokens)
            if mode == 'submission' and tokens:
                errors.append('提交态仍有Q占位：' + Path(file).name)
        except ValueError as exc:
            errors.append(str(exc))
    covered = set()
    for entry in relevant:
        links = oq_links(entry)
        if not links:
            warnings.append(entry['id'] + ' 无对应OQ（文书格式性待确认可单列）')
        for ident in links:
            question = questions.get(ident)
            if question is None:
                errors.append(entry['id'] + ' 引用了不存在的 ' + ident)
                continue
            if entry['id'] in present:
                covered.add(ident)
            unresolved = question.get('status','open') not in ('resolved','closed','verified')
            if entry['status'] == 'resolved' and unresolved:
                errors.append(entry['id'] + ' 不能关闭：' + ident + ' 尚未解决；用户同意不等于核验')
            if entry['status'] == 'resolved' and (legal_item(question) or legal_item(entry)) and not legal_resolution(question):
                errors.append(ident + ' 缺法律核验记录，不能以用户同意关闭Q')
            if mode == 'submission' and unresolved:
                errors.append(ident + ' 尚未解决，不得提交相关文书')
    for ident, question in questions.items():
        profiles = question.get('profiles', [])
        if profiles and profile is not None and profile not in profiles:
            continue
        if question.get('status','open') not in ('resolved','closed','verified') and ident not in covered:
            warnings.append(ident + ' 未关闭且本次文书无映射Q')
            if question.get('blocking') is True:
                errors.append(ident + ' 为阻断项，必须补充或在受控草案中映射Q')
    return {'decision':'PENDING_FAILED' if errors else 'PENDING_CHECKED','errors':errors,'warnings':warnings,
            'allowed_to_draft':not errors,'submission_ready':mode == 'submission' and not errors,'checked_stage':mode,
            'exit_code':3 if errors else 0}


def main():
    import argparse
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pending', required=True)
    ap.add_argument('--matrix', required=True, help='与本次交付物关联的矩阵')
    ap.add_argument('--file', action='append', help='限定本次记稿（可重复）')
    ap.add_argument('--mode', choices=['draft','submission'], default='draft')
    ap.add_argument('--profile', help='只核对本任务的OQ阻断项')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    try:
        result = cross_check(args.pending, args.matrix, args.mode, args.file, args.profile)
    except (ValueError, OSError, TypeError) as exc:
        result = {'decision':'INPUT_ERROR','exit_code':4,'errors':[str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
