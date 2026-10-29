"""Shared CLI interpreter requirement; kept compatible with Python 3.9."""
import json
import sys

def require_python(minor=(3, 9), script_name=None):
    if sys.version_info[:2] < minor:
        print(json.dumps({'decision': 'PY_TOO_OLD', 'need': '.'.join(map(str, minor)),
                          'found': '.'.join(map(str, sys.version_info[:3])), 'script': script_name,
                          'action': '请用 Python 3.9+ 解释器重新运行；不要使用系统旧版 python3'}, ensure_ascii=False))
        raise SystemExit(3)
