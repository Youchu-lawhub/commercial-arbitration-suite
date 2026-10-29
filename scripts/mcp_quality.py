#!/usr/bin/env python3
"""Offline, case-local MCP capability acceptance and route evidence.

No network access, no keys, no public cache. The CLI cannot assert legal truth:
it only checks whether a current session's recorded tool call contains the
required provenance metadata. Readiness is deliberately scoped to a task.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

KINDS={'legislation','case_law','full_text','citation_check','coverage','treatment'}
STATUSES={'READY','PARTIAL','AUTH_REQUIRED','UNAVAILABLE'}
ID=re.compile(r'^[a-z0-9][a-z0-9_-]{0,127}$')
JUR=re.compile(r'^[A-Z]{2,6}$')

def status(record, jurisdiction, capability, now=None, max_age_hours=24):
    """Conservative status for a single capability within a single case."""
    if not isinstance(record,dict) or record.get('jurisdiction')!=jurisdiction or record.get('capability')!=capability:
        return 'UNAVAILABLE','task or jurisdiction mismatch'
    if record.get('auth_required') is True:
        return 'AUTH_REQUIRED','user authentication required'
    if not record.get('connected') or not record.get('tool_discovered'):
        return 'UNAVAILABLE','no current connection and tool discovery evidence'
    try:
        t=datetime.fromisoformat(record['checked_at'].replace('Z','+00:00'))
        if t.tzinfo is None:raise ValueError('timezone required')
        current=now or datetime.now(timezone.utc)
        if t>current+timedelta(minutes=5) or current-t>timedelta(hours=max_age_hours):
            return 'PARTIAL','probe is stale or from future'
    except (KeyError,TypeError,ValueError,AttributeError):
        return 'PARTIAL','missing or invalid probe time'
    if not record.get('query_succeeded'):
        return 'PARTIAL','query acceptance missing'
    if capability in {'legislation','case_law','full_text','citation_check','treatment'}:
        if not (record.get('full_text_returned') and record.get('official_origin_url') and record.get('pinpoint') and record.get('version_checked')):
            return 'PARTIAL','original text, pinpoint, official origin or version check missing'
    return 'READY','capability acceptance recorded; legal correctness not established'

def evaluate(registry, observations, jurisdiction, capability, max_age_hours=24, now=None):
    if not JUR.fullmatch(jurisdiction):raise ValueError('invalid jurisdiction')
    if capability not in KINDS:raise ValueError('invalid capability')
    sources=[s for s in registry.get('sources',[]) if s.get('kind','').startswith('mcp')]
    obs=observations.get('observations',{}) if isinstance(observations,dict) else {}
    results=[]
    for src in sources:
        js={str(x).upper() for x in src.get('jurisdictions',[])}
        if jurisdiction not in js:continue  # INTL is background, not evidence of country coverage
        sid=src.get('id','')
        if not ID.fullmatch(sid):continue
        cap=src.get('capabilities',[])
        supports=capability in cap or (capability=='full_text' and src.get('layers'))
        if not supports:continue
        record=obs.get(sid,{})
        s,reason=status(record,jurisdiction,capability,now,max_age_hours)
        if not record and src.get('auth') not in (None,'none','keyless','public'):
            s,reason='AUTH_REQUIRED','requires authorization; not attempted'
        results.append({'id':sid,'status':s,'reason':reason,'historical_state':src.get('state'),
                        'current_case_accepted':s=='READY'})
    ranking={'READY':0,'PARTIAL':1,'AUTH_REQUIRED':2,'UNAVAILABLE':3}
    results.sort(key=lambda x:(ranking[x['status']],x['id']))
    return {'decision':'MCP_CAPABILITY_ROUTE','jurisdiction':jurisdiction,'capability':capability,
            'verified_law':False,'candidates':results,
            'next':'Use accepted MCP when available; verify original law independently. Otherwise use research_sources.py web and host browser/search, never fabricate a citation.',
            'note':'Case-local observation is self-attested task evidence, not proof of legal correctness. No probing or network requests performed.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jurisdiction',required=True);p.add_argument('--capability',required=True,choices=sorted(KINDS))
    p.add_argument('--observations',help='Case-owned JSON file; never in the Skill folder')
    p.add_argument('--max-age-hours',type=int,default=24)
    a=p.parse_args()
    try:
        if not 1<=a.max_age_hours<=168:raise ValueError('max-age-hours must be 1..168')
        root=Path(__file__).resolve().parent.parent
        registry=json.loads((root/'assets/research-sources.json').read_text(encoding='utf-8'))
        observations={}
        if a.observations:
            filepath=Path(a.observations).expanduser().resolve()
            if filepath.is_relative_to(root):raise ValueError('case observations must not be stored in Skill folder')
            observations=json.loads(filepath.read_text(encoding='utf-8'))
        print(json.dumps(evaluate(registry,observations,a.jurisdiction.upper(),a.capability,a.max_age_hours),ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,TypeError) as e:
        print(json.dumps({'decision':'INVALID_INPUT','reason':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
