#!/usr/bin/env python3
"""Select user-owned legal research capabilities without installing or calling providers."""
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import json
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
CAPS={'coverage','legislation','case_law','full_text','citation_check','treatment'}

def catalogue():
    data=json.loads((ROOT/'assets/research-sources.json').read_text())
    result={}
    for s in data['sources']:
        capabilities=set(s.get('capabilities',[])) & CAPS
        layers=set(s.get('layers',[]))
        if 'governing_law' in layers or 'lex_arbitri' in layers:capabilities.add('legislation')
        capabilities.update(layers & {'case_law','citation_check'})
        result[s['id']]={'id':s['id'],'title':s['title'],'jurisdictions':s['jurisdictions'],
            'capabilities':sorted(capabilities),'connection':'mcp' if s['kind'].startswith('mcp') else 'web',
            'endpoint':s.get('url'),'status':'unverified','catalogue_only':True}
    return result

def load_profile(path):
    d=json.loads(Path(path).read_text())
    if d.get('schema')!='rulesuite-research-profile/1':raise ValueError('profile schema 无效')
    if not isinstance(d.get('providers',[]),list):raise ValueError('providers 必须是列表')
    providers=catalogue();seen=set()
    for p in d.get('providers',[]):
        pid=p.get('id')
        if not isinstance(pid,str) or not pid or pid in seen:raise ValueError('provider id 缺失或重复')
        seen.add(pid)
        base=dict(providers.get(pid,{}));base.update(p)
        if not base.get('title') or base.get('connection') not in ('mcp','api','web','manual-export'):raise ValueError('需填写 title 和 connection')
        if not isinstance(base.get('jurisdictions'),list) or not base['jurisdictions']:raise ValueError('需填写 jurisdictions')
        if not isinstance(base.get('capabilities'),list) or not set(base['capabilities'])<=CAPS:raise ValueError('未知 capability')
        if base.get('status','unverified') not in ('unverified','ready','auth_required','unavailable','disabled'):raise ValueError('未知 status')
        if any(k.lower() in ('token','password','api_key','secret','authorization','headers') for k in p):raise ValueError('配置不存凭证；使用宿主管理连接或 credential_ref')
        providers[pid]=base
    for block in [d.get('default',{})]+list(d.get('jurisdictions',{}).values())+list(d.get('tasks',{}).values()):
        if not isinstance(block,dict):raise ValueError('选择层必须为对象')
        for cap,ids in block.items():
            if cap not in CAPS or not isinstance(ids,list) or len(ids)!=len(set(ids)):raise ValueError('能力槽或供应商列表无效')
            if any(i not in providers for i in ids):raise ValueError('选择了未登记的 provider；请先加入 providers')
    return d,providers

def select(path,jurisdiction,capability,task=None):
    if capability not in CAPS:raise ValueError('未知 capability')
    d,providers=load_profile(path);jurisdiction=jurisdiction.upper()
    selection=d.get('default',{}).get(capability,[]);level='default'
    for name,block in [('jurisdiction',d.get('jurisdictions',{}).get(jurisdiction,{})),('task',d.get('tasks',{}).get(task,{}))]:
        if capability in block:selection=block[capability];level=name
    rows=[]
    for pid in selection:
        p=providers[pid];reasons=[]
        if capability not in p.get('capabilities',[]):reasons.append('capability_not_declared')
        if jurisdiction not in p.get('jurisdictions',[]) and 'INTL' not in p.get('jurisdictions',[]):reasons.append('jurisdiction_not_declared')
        if p.get('status')!='ready':reasons.append('connection_not_ready')
        evidence=[x for x in p.get('acceptance',[]) if x.get('capability')==capability and x.get('jurisdiction')==jurisdiction and x.get('evidence') and x.get('result')=='passed']
        fresh=False
        for x in evidence:
            try:fresh |= 0 <= (date.today()-date.fromisoformat(x['date'])).days <= 90
            except (ValueError,KeyError):pass
        if not fresh:reasons.append('needs_task_jurisdiction_acceptance')
        rows.append({'id':pid,'title':p['title'],'connection':p['connection'],'eligible':not reasons,'reasons':reasons,
                     'connection_ref':p.get('connection_ref'),'credential_ref':p.get('credential_ref'),
                     'note':'本地验收记录筛选，不证明本案法律结论；web/manual-export 需要宿主或用户操作'})
    return {'decision':'PROFILE_SELECTION','jurisdiction':jurisdiction,'capability':capability,'selection_level':level,
            'providers':rows,'ready':[x['id'] for x in rows if x['eligible']], 'needs_configuration':not any(x['eligible'] for x in rows),
            'action':'按用户顺序使用可用后端；失败保留原因，询问是否切换未选择供应商或使用官方来源。不自动购买/安装。'}

def main():
    require_python(script_name=__file__)
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('catalogue')
    p=sub.add_parser('select');p.add_argument('--config',required=True);p.add_argument('--jurisdiction',required=True);p.add_argument('--capability',choices=sorted(CAPS),required=True);p.add_argument('--task')
    a=ap.parse_args()
    try:
        result=list(catalogue().values()) if a.cmd=='catalogue' else select(a.config,a.jurisdiction,a.capability,a.task)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({'decision':'PROFILE_ERROR','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
