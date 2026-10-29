#!/usr/bin/env python3
"""Register reviewed sources in a case directory without editing shared registries."""
from __future__ import annotations
from _pymin import require_python
if __name__ == '__main__': require_python(script_name=__file__)
import argparse
import json
from datetime import date
from pathlib import Path
from _source_evidence import digest,load_local,valid_url,within
from fetch_official import atomic_write,safe_id,SUITE,DATA


def register(root, sid, text_file, origin, edition, locators, by, scope, verified_at, original_file=None):
    root=Path(root).resolve()
    if root == SUITE or SUITE in root.parents or root == DATA or DATA in root.parents:
        raise ValueError('案件来源不能写入技能包或共享缓存')
    if not safe_id(sid) or not valid_url(origin): raise ValueError('ID 或 HTTPS 原始地址无效')
    if not all(isinstance(x,str) and x.strip() for x in (edition,by,scope)) or not locators or not all(isinstance(x,str) and x.strip() for x in locators):
        raise ValueError('须填写版本、定位、核验人和核验范围')
    if date.fromisoformat(verified_at)>date.today(): raise ValueError('核验日期不得在未来')
    text=within(root,text_file)
    if text.suffix not in ('.md','.txt') or not text.read_text(encoding='utf-8').strip(): raise ValueError('须为非空 UTF-8 md/txt 正文')
    record={'edition':edition,'origin':origin,'text_file':text_file,'text_sha256':digest(text),'legal_verified':True,'verified_by':by,'verified_scope':scope,'verified_locators':locators,'verified_at':verified_at}
    if original_file:
        original=within(root,original_file);record.update(original_file=original_file,original_sha256=digest(original))
    sources=load_local(root);sources[sid]=record
    atomic_write(root/'case-sources.json',json.dumps({'schema':'rulesuite-case-sources/1','sources':sources},ensure_ascii=False,indent=2).encode())
    return record


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workdir',required=True);ap.add_argument('--id',required=True);ap.add_argument('--text',required=True)
    ap.add_argument('--origin',required=True);ap.add_argument('--edition',required=True);ap.add_argument('--locator',action='append',required=True)
    ap.add_argument('--by',required=True);ap.add_argument('--scope',required=True);ap.add_argument('--date',default=date.today().isoformat());ap.add_argument('--original')
    a=ap.parse_args()
    try:
        register(a.workdir,a.id,a.text,a.origin,a.edition,a.locator,a.by,a.scope,a.date,a.original)
        print(json.dumps({'decision':'REGISTERED','source_id':a.id,'limitation':'仅登记已完成的人工核验，不自动证明法源真实或本案适用'},ensure_ascii=False));return 0
    except (ValueError,TypeError,OSError) as exc:
        print(json.dumps({'decision':'INVALID_INPUT','error':str(exc)},ensure_ascii=False));return 2
if __name__=='__main__': raise SystemExit(main())
