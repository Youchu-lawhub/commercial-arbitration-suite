#!/usr/bin/env python3
"""Case-local foreign-law evidence card audit. No case data written into suite.

Input JSON: {"claims":[{"id":"C1","statement":"...","sources":[{"url":"https://...", "publisher":"...", "document_title":"...", "pinpoint":"s. 3", "text_sha256":"64 hex", "retrieved_at":"2026-10-29", "effective_on":"2026-01-01", "scope":"SG", "verified_by":"human or agent", "verification_method":"official-text-checked"}]}]}
Audit validates traceability completeness, NOT legal correctness. Exit 2 when
substantive claims lack verifiable source cards, 0 when structurally complete.
"""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from datetime import date
FIELDS=('url','publisher','document_title','pinpoint','text_sha256','retrieved_at','effective_on','scope','verified_by','verification_method')

def audit(obj):
    problems=[];seen=set();claims=obj.get('claims')
    if not isinstance(claims,list) or not claims:return ['claims must be a nonempty list']
    for i,c in enumerate(claims):
        label=f'claims[{i}]'
        if not isinstance(c,dict):problems.append(label+': not an object');continue
        ident=c.get('id')
        if not isinstance(ident,str) or not ident.strip() or ident in seen:problems.append(label+': missing/duplicate id')
        seen.add(ident)
        if not isinstance(c.get('statement'),str) or not c['statement'].strip():problems.append(label+': missing statement')
        sources=c.get('sources')
        if not isinstance(sources,list) or not sources:problems.append(label+': no sources');continue
        for j,s in enumerate(sources):
            x=f'{label}.sources[{j}]'
            if not isinstance(s,dict):problems.append(x+': not an object');continue
            for f in FIELDS:
                if not isinstance(s.get(f),str) or not s[f].strip():problems.append(x+': missing '+f)
            if s.get('text_sha256') and not re.fullmatch(r'[a-fA-F0-9]{64}',str(s['text_sha256'])):problems.append(x+': invalid sha256')
            if s.get('url') and not str(s['url']).startswith('https://'):problems.append(x+': evidence URL must use HTTPS')
            for field in ('retrieved_at','effective_on'):
                if s.get(field):
                    try:date.fromisoformat(s[field])
                    except (ValueError,TypeError):problems.append(x+': invalid '+field)
            if s.get('verification_method') == 'navigation-only':problems.append(x+': navigation not legal text')
    return problems

def main():
    p=argparse.ArgumentParser();p.add_argument('--file',required=True);a=p.parse_args()
    path=Path(a.file)
    try:obj=json.loads(path.read_text(encoding='utf-8'));issues=audit(obj)
    except (OSError,ValueError,TypeError) as e:issues=[f'invalid input: {e}']
    print(json.dumps({'decision':'CITATION_BLOCKED' if issues else 'EVIDENCE_CARD_COMPLETE','verified_law':False,'checks':'structure_only','issues':issues},ensure_ascii=False,indent=2))
    return 2 if issues else 0
if __name__=='__main__':sys.exit(main())
