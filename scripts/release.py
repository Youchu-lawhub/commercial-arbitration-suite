#!/usr/bin/env python3
"""可复现发布打包：先跑闸门，再打包，最后解包复验。

- 排除 .git/、.gitignore、__pycache__、.DS_Store、运行时 data/ 缓存（README 声明不随包分发）。
- zip 内时间戳与权限位固定，同一份输入产出同一 sha256。
- 打包后解到临时目录重跑 install_suite 与 verify_suite --selftest，失败即不交付。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SUITE = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {'.git', '__pycache__', 'data'}
EXCLUDE_FILES = {'.gitignore', '.DS_Store'}
EPOCH = (2026, 1, 1, 0, 0, 0)


def run(cmd, cwd, env):
    p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def checks(root, data_dir):
    env = dict(os.environ, RULESUITE_DATA_DIR=str(data_dir))
    results = []
    for label, cmd in (
            ('install', [sys.executable, str(root / 'scripts/install_suite.py')]),
            ('selftest', [sys.executable, str(root / 'scripts/verify_suite.py'), '--selftest']),
            ('templates', [sys.executable, str(root / 'scripts/verify_suite.py'), '--templates'])):
        rc, out = run(cmd, root, env)
        results.append({'check': label, 'exit': rc, 'tail': out.strip().splitlines()[-1:]})
        if rc:
            return results, False
    return results, True


def iter_files(root):
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_FILES or path.suffix == '.pyc':
            continue
        yield path, rel.as_posix()


def build(out_path, do_verify=True):
    root = SUITE
    out_path = Path(out_path).expanduser().resolve()
    tmp = Path(tempfile.mkdtemp(prefix='arb-release-'))
    env = dict(os.environ)
    results, ok = checks(root, tmp / 'precheck-data')
    if not ok:
        print(json.dumps({'decision': 'GATE_FAILED', 'checks': results}, ensure_ascii=False, indent=2))
        return 2
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for path, rel in iter_files(root):
            info = zipfile.ZipInfo('commercial-arbitration-suite/' + rel, date_time=EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ((0o755 if rel.startswith('scripts/') and rel.endswith('.py') else 0o644) << 16)
            z.writestr(info, path.read_bytes())
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    (out_path.with_suffix(out_path.suffix + '.sha256')).write_text(digest + '  ' + out_path.name + '\n', encoding='utf-8')
    if do_verify:
        target = tmp / 'unpacked'
        with zipfile.ZipFile(out_path) as z:
            z.extractall(target)
            for info in z.infolist():
                mode = (info.external_attr >> 16) & 0o777
                if mode:
                    (target / info.filename).chmod(mode)
        results, ok = checks(target / 'commercial-arbitration-suite', tmp / 'verify-data')
        if not ok:
            print(json.dumps({'decision': 'EXTRACTED_CHECK_FAILED', 'checks': results}, ensure_ascii=False, indent=2))
            return 2
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({'decision': 'RELEASED', 'zip': str(out_path),
                      'bytes': out_path.stat().st_size, 'sha256': digest,
                      'checks': results,
                      'note': '排除 .git 与运行时 data/ 缓存；zip 内时间戳固定为 2026-01-01，同输入同哈希。'},
                     ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    version = re.search(r'version:\s*"?([\w.\-]+)"?', (SUITE / 'suite.yaml').read_text(encoding='utf-8'))
    default = Path.home() / 'Desktop' / ('commercial-arbitration-suite-%s.zip' % (version.group(1) if version else 'dev'))
    ap.add_argument('--out', default=str(default))
    ap.add_argument('--no-verify', action='store_true', help='跳过解包复验（不建议）')
    a = ap.parse_args()
    return build(a.out, not a.no_verify)


if __name__ == '__main__':
    raise SystemExit(main())
