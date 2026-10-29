"""Detect local font capability and validate version-bound visual review receipts."""
from __future__ import annotations
from datetime import date
import os
from pathlib import Path
import shutil
import subprocess
import sys
from _source_evidence import digest

MACOS_CJK_FONTS = (
    ('/System/Library/Fonts', 'PingFang.ttc'),
    ('/System/Library/Fonts', 'STHeiti Light.ttc'),
    ('/System/Library/Fonts', 'Hiragino Sans GB.ttc'),
    ('/Library/Fonts', 'Arial Unicode.ttf'),
)
WINDOWS_CJK_FONTS = ('msyh.ttc', 'simsun.ttc')


def candidate_fonts(platform_name=None):
    """Known CJK font files outside fontconfig; used only when fc-list is absent."""
    platform_name = platform_name or sys.platform
    if platform_name == 'darwin':
        return [Path(directory) / name for directory, name in MACOS_CJK_FONTS]
    if platform_name.startswith('win'):
        base = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
        return [base / name for name in WINDOWS_CJK_FONTS]
    return []


def font_environment(candidates=None, platform_name=None):
    if shutil.which('fc-list'):
        try:
            r=subprocess.run(['fc-list',':lang=zh','family'],capture_output=True,text=True,timeout=5)
            families=sorted(set(x.strip() for x in r.stdout.splitlines() if x.strip()))
            if r.returncode or not families:
                return {'cjk':'missing','message':'本机未检测到中文字体；转PDF可能缺字，完成字体配置及逐页检查前不得称视觉验收通过'}
            return {'cjk':'available','families':families,'message':'检测到中文字体；仍须逐页验证实际渲染结果'}
        except (OSError,subprocess.TimeoutExpired):
            return {'cjk':'unknown','message':'字体检测不可用；须实际查看渲染页面'}
    if candidates is None:
        candidates = candidate_fonts(platform_name)
    found = [str(path) for path in candidates if Path(path).is_file()]
    if found:
        return {'cjk':'available','fonts':found,'message':'检测到系统中文字体文件；仍须逐页验证实际渲染结果'}
    if candidates:
        return {'cjk':'unknown','message':'已知路径未检测到中文字体文件；须在实际查看环境验证中文字体和分页'}
    return {'cjk':'unknown','message':'未检测到 fontconfig；须在实际查看环境验证中文字体和分页'}


def visual_receipt(manifest, files, root):
    """A receipt records review of exact DOCX versions; cannot perform review itself."""
    review=manifest.get('visual_review')
    if not isinstance(review,dict) or not isinstance(review.get('reviewer'),str) or not review['reviewer'].strip():
        return False,['未登记本轮逐页视觉复核记录']
    try:
        if date.fromisoformat(str(review.get('date')))>date.today():raise ValueError('future')
    except (ValueError,TypeError): return False,['视觉复核日期无效']
    records=review.get('files')
    if not isinstance(records,dict):return False,['视觉复核须逐文件记录哈希和页数']
    issues=[]
    for path in files:
        key=Path(path).relative_to(root).as_posix();r=records.get(key,{})
        if not isinstance(r,dict) or r.get('status')!='passed' or type(r.get('pages')) is not int or r['pages']<1 or r.get('sha256')!=digest(path):
            issues.append(key+' 缺有效视觉复核记录或文件版本已变化')
    return not issues,issues
