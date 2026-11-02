#!/usr/bin/env python3
"""交付清单生成与人工复核回执：build 计算哈希与页数、attest 由人工复核后签字。

本脚本不替人做视觉验收：build 产出的每份文件复核状态一律 pending，
只有经办人在 Word 中逐页看过并运行 attest，状态才会变 passed。
"""
import argparse
import hashlib
import json
import math
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
DELIVERY_DIRS = ('交付', 'deliverables')


def fail(message):
    print(json.dumps({'decision': 'INPUT_ERROR', 'detail': message}, ensure_ascii=False))
    return 2


def delivery_dir(workdir):
    for name in DELIVERY_DIRS:
        d = workdir / name
        if d.is_dir():
            return d
    raise ValueError('案件目录下无 交付/ 或 deliverables/ 目录')


def para_count(docx):
    try:
        with zipfile.ZipFile(docx) as z:
            return len(list(ET.fromstring(z.read('word/document.xml')).iter(W + 'p')))
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile):
        return 0


def receipt_for(path, root):
    n = para_count(path)
    return {'status': 'pending',
            'pages': max(1, math.ceil(n / 24)) if n else 1,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def build(workdir, round_label):
    root = Path(workdir).resolve()
    folder = delivery_dir(root)
    docs, notes, attachments, files = [], [], [], {}
    guide = next((p for p in sorted(folder.glob('*立案申请指引*.md')) if p.is_file()), None)
    for docx in sorted(folder.glob('*.docx')):
        rel = docx.relative_to(root).as_posix()
        if '中文审阅说明' in docx.stem or '审阅说明' in docx.stem:
            notes.append(docx)
            continue
        docs.append({'document': rel})
        files[rel] = receipt_for(docx, root)
        for suffix in ('.md', '.docx.md'):
            src = docx.with_suffix(suffix)
            if src.is_file():
                attachments.append(src.relative_to(root).as_posix())
                break
    if not docs:
        raise ValueError('交付目录内没有可作为主文书的 .docx（说明件不计入）')
    for note in notes:
        stem = note.stem.replace('-中文审阅说明', '').replace('-审阅说明', '')
        for row in docs:
            if row['document'].endswith(stem + '.docx'):
                row['review_note'] = note.relative_to(root).as_posix()
                files[row['review_note']] = receipt_for(note, root)
    if guide:
        attachments.append(guide.relative_to(root).as_posix())
    manifest = {
        'schema': 'rulesuite-delivery/1',
        'round': round_label or '',
        'documents': docs,
        'attachments': sorted(set(attachments)),
        'visual_review': {
            'reviewer': '',
            'date': '',
            'note': 'build 只计算哈希与页数，不做视觉验收：请经办人在 Word 中逐页复核后运行 '
                    'delivery.py attest --reviewer <姓名>，状态才会从 pending 变 passed。'
                    'pages 为按 docx 段落元素数估算（每页约 24 段），请复核时一并订正。',
            'files': files,
        },
    }
    if guide:
        manifest['filing_guide'] = guide.relative_to(root).as_posix()
    out = root / 'delivery.json'
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'decision': 'BUILT', 'file': str(out), 'documents': len(docs),
                      'with_review_note': sum(1 for d in docs if 'review_note' in d),
                      'attachments': len(manifest['attachments']),
                      'filing_guide': manifest.get('filing_guide'),
                      'visual_status': 'pending（需人工 attest）'}, ensure_ascii=False, indent=2))
    return 0


def attest(workdir, reviewer, when):
    root = Path(workdir).resolve()
    manifest = root / 'delivery.json'
    if not manifest.is_file():
        return fail('案件目录下无 delivery.json，请先运行 delivery.py build')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    review = data.get('visual_review', {})
    if not isinstance(review.get('files'), dict) or not review['files']:
        return fail('delivery.json 缺少 visual_review.files，请先运行 build')
    for key, rec in review['files'].items():
        f = root / key
        if not f.is_file():
            return fail('清单中的文件不存在：%s' % f)
        rec['sha256'] = hashlib.sha256(f.read_bytes()).hexdigest()
        rec['status'] = 'passed'
    review['reviewer'] = reviewer
    review['date'] = when
    review['note'] = ('人工回执：经办人声明已在 Word 中逐页复核上述文件（含分页、字体与占位残留），'
                      '并已将本清单 sha256 固定到复核时的文件版本；此后任何再渲染都必须重新 build 并复核。')
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'decision': 'ATTESTED', 'reviewer': reviewer, 'date': when,
                      'files': len(review['files']),
                      'next': 'python3 scripts/verify_suite.py --workdir <案件目录> --mode submission'},
                     ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build', help='扫描交付目录，生成/刷新 delivery.json（复核状态 pending）')
    b.add_argument('--workdir', required=True)
    b.add_argument('--round', default='')
    a = sub.add_parser('attest', help='人工逐页复核后签收回执（状态改 passed，并刷新哈希）')
    a.add_argument('--workdir', required=True)
    a.add_argument('--reviewer', required=True)
    a.add_argument('--date', default=date.today().isoformat())
    args = ap.parse_args()
    try:
        if args.cmd == 'build':
            return build(args.workdir, args.round)
        return attest(args.workdir, args.reviewer, args.date)
    except (OSError, ValueError, KeyError) as exc:
        return fail(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
