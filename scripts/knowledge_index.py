#!/usr/bin/env python3
"""Offline, bounded knowledge locator; returns FILE REFERENCES, never asserted law.

Usage: python3 scripts/knowledge_index.py --query 'SIAC emergency' --limit 5
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
ROOTS=('skills','references','assets/institutional-knowledge')
STOP={'the','and','for','with','法律','仲裁','规则','案件','相关','如何'}

def tokens(s):
    return [w for w in re.findall(r'[a-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}',s.lower()) if w not in STOP]

def locate(q,limit=5):
    ts=tokens(q)
    if not ts:return []
    out=[]
    for root in ROOTS:
        for p in sorted((BASE/root).rglob('*.md')):
            if p.is_symlink() or not p.is_file():continue
            rel=p.relative_to(BASE).as_posix()
            body=p.read_text(encoding='utf-8',errors='replace')
            head='\n'.join(body.splitlines()[:25]); hay=(rel+' '+head).lower()
            score=sum(8 if t in rel.lower() else 4 if t in head.lower() else 1 if t in body.lower() else 0 for t in ts)
            if score:out.append((score,rel,len(body),[t for t in ts if t in (rel+' '+body).lower()]))
    out.sort(key=lambda x:(-x[0],x[2],x[1]))
    return [{'path':p,'score':s,'bytes':n,'matched':m,'instruction':'Open only the relevant headings/paragraphs. This locator does not establish current legal validity.'} for s,p,n,m in out[:max(1,min(limit,12))]]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--query',required=True);ap.add_argument('--limit',type=int,default=5);a=ap.parse_args()
    print(json.dumps({'decision':'KNOWLEDGE_LOCATOR','query':a.query,'candidates':locate(a.query,a.limit),'verified_law':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
