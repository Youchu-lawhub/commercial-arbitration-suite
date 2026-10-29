"""Shared source evidence for official cache and case-local sources (no network)."""
from __future__ import annotations
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(value):
    return re.sub(r'\s+', ' ', str(value).strip()).casefold()


def valid_url(url):
    if not isinstance(url, str): return False
    try:
        u = urlsplit(url)
        return u.scheme == 'https' and bool(u.hostname) and not (u.username or u.password or u.fragment) and u.hostname not in ('example.com','example.org','example.net','localhost') and not u.hostname.endswith(('.invalid','.test','.example'))
    except ValueError:
        return False


def within(root, value):
    root = Path(root).resolve()
    value = Path(value)
    if value.is_absolute() or '..' in value.parts:
        raise ValueError('案件来源须使用目录内相对路径')
    p = root / value
    p.resolve().relative_to(root)
    if any(x.is_symlink() for x in [p, *p.parents] if x != root):
        raise ValueError('案件来源不接受符号链接')
    if not p.is_file(): raise ValueError('案件来源文件不存在')
    return p


def scope_covers(locator, locators, scope=''):
    if not normalized(locator): return False
    if locators:
        return normalized(locator) in {normalized(x) for x in locators if isinstance(x,str)}
    # Backward compatibility: a legacy free-text scope must name the exact locator.
    return bool(re.search(r'(?<![\w.])' + re.escape(normalized(locator)) + r'(?![\w.])', normalized(scope)))


def load_local(root):
    path = Path(root) / 'case-sources.json'
    if not path.exists(): return {}
    if path.is_symlink(): raise ValueError('案件来源登记不接受符号链接')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema') != 'rulesuite-case-sources/1' or not isinstance(data.get('sources'),dict):
        raise ValueError('case-sources.json 结构无效')
    return data['sources']


def source_evidence(sid, root=None, locator=None, edition=None, url=None, quote=None, max_age=None, checked_at=None):
    """Return (issues, text). Attests recorded review, never independently proves law."""
    import fetch_official as f
    if not f.safe_id(sid): return ['来源 ID 非法'], None
    local = load_local(root).get(sid) if root else None
    errors = []
    text = None
    if local is not None:
        if not isinstance(local,dict): return ['案件来源记录须为对象'], None
        record = local
        try:
            p = within(root, record.get('text_file',''))
            if p.suffix not in ('.md','.txt'): raise ValueError('来源文本须为 md/txt')
            if digest(p) != record.get('text_sha256'): errors.append('案件来源文本哈希不匹配')
            text = p.read_text(encoding='utf-8')
            if record.get('original_file'):
                original = within(root,record['original_file'])
                if digest(original) != record.get('original_sha256'): errors.append('案件来源原件哈希不匹配')
        except (OSError,ValueError,TypeError) as exc:
            errors.append('案件来源文件无效：'+str(exc))
        if not valid_url(record.get('origin')): errors.append('案件来源缺有效 HTTPS 原始地址')
        if url and url.rstrip('/') != str(record.get('origin','')).rstrip('/'):
            errors.append('案件来源 URL 与核验记录不符')
        expected_edition = record.get('edition')
        if edition and normalized(edition) != normalized(expected_edition): errors.append('案件来源版本与核验记录不符')
        verified = record.get('legal_verified') is True
    else:
        indexed = f.build_source_index(f.load())
        if sid not in indexed: return ['来源未登记：请登记到本案 case-sources.json'], None
        record = f.read_prov(sid)
        status = f.legal_status(sid)
        verified = status['legal_verified']
        for ext in ('.md','.txt'):
            p = f.OFFICIAL / (sid + ext)
            if f.is_file_safe(p):
                text = p.read_text(encoding='utf-8'); break
        if url:
            from verify_suite import citation_url_issue
            mismatch = citation_url_issue(sid,url)
            if mismatch: errors.append(mismatch.removeprefix('WARN '))
        expected_edition = record.get('verified_edition')
        if edition:
            if not expected_edition:
                errors.append('来源核验记录未绑定版本；请重新 verify 并指定 --edition')
            elif normalized(edition) != normalized(expected_edition):
                errors.append('引用版本与来源核验版本不符')
    if text is None: errors.append('未取得可核验正文')
    if checked_at and checked_at != str(record.get('verified_at')): errors.append('引用校验日期与核验凭证不符')
    if not verified: errors.append('来源尚未完成有效哈希及法律核验')
    if not record.get('verified_by') or not record.get('verified_scope'): errors.append('缺核验人或核验范围')
    try:
        when = date.fromisoformat(str(record.get('verified_at')))
        if when > date.today(): errors.append('核验日期在未来')
        if max_age is not None and (date.today()-when).days > max_age: errors.append('核验已超过刷新周期')
    except (ValueError,TypeError): errors.append('核验日期缺失或无效')
    if locator and not scope_covers(locator,record.get('verified_locators',[]),record.get('verified_scope','')):
        errors.append('核验范围未覆盖定位 '+str(locator))
    if quote and (text is None or normalized(quote) not in normalized(text)):
        errors.append('核验引文未在正文命中')
    return errors,text
