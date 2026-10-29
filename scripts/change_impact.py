#!/usr/bin/env python3
"""Read-only, conservative change triage for two case snapshots. Not legal advice."""
import argparse
import json
from pathlib import Path

DOMAINS = {
    'jurisdiction_rules': ('arbitr', 'forum', 'seat', 'institution', 'rules', 'venue', 'jurisdiction', 'agreement', 'clause'),
    'deadlines_procedure': ('date', 'deadline', 'service', 'notice', 'receipt', 'procedur', 'order', 'calendar', 'hearing', 'commenc', 'filing', 'time'),
    'claim_evidence': ('party', 'parties', 'claim', 'defence', 'respondent', 'applicant', 'contract', 'fact', 'evidence', 'amount', 'currency', 'relief', 'payment', 'damage', 'interest'),
    'foreign_law': ('governing', 'applicable_law', 'foreign_law', 'choice_of_law'),
    'enforcement': ('asset', 'enforce', 'award', 'bankrupt', 'insolv', 'execution', 'recover', 'security', 'interim'),
}
ACTIONS = {
    'jurisdiction_rules': '复核仲裁协议、机构／规则族及版本、仲裁地和管辖权分析',
    'deadlines_procedure': '核对原始送达／程序令、时区、起算事实及全部相关期限',
    'claim_evidence': '复核请求抗辩、证据锚点、金额计算、案件矩阵、现有文书',
    'foreign_law': '复核各项法律准据法与来源核验，必要时咨询当地律师',
    'enforcement': '复核资产权属、保全可行性、裁决后救济与跨境执行计划',
    'manual_review': '由案件负责人审查未知字段的业务和法律影响',
}

def changes(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result=[]
        for k in sorted(set(a)|set(b)):
            key=prefix+'.'+str(k) if prefix else str(k)
            if k not in a or k not in b: result.append(key)
            else: result.extend(changes(a[k], b[k], key))
        return result
    if isinstance(a, list) and isinstance(b, list):
        # Lists may reorder or contain non-unique IDs; flag as a whole, never assume semantic equivalence.
        return [] if a==b else [prefix]
    return [] if a==b else [prefix or '$']

def assess(before, after):
    paths=changes(before,after)
    domains=set()
    for path in paths:
        hits=[name for name, hints in DOMAINS.items() if any(h in path.lower() for h in hints)]
        domains.update(hits or ['manual_review'])
    return {'schema':'rulesuite-change-impact/1','changed':bool(paths),
            'changed_paths':paths,'review_domains':sorted(domains),
            'actions':[{'domain':x,'review':ACTIONS[x]} for x in sorted(domains)],
            'status':'HUMAN_REVIEW_REQUIRED' if paths else 'NO_STRUCTURAL_CHANGE',
            'limitations':'只比较结构化快照；同内容但底层原始文件发生变化、材料真实有效性、期限计算、法源及既有对外文书均未自动验证。'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',required=True)
    ap.add_argument('--after',required=True)
    ap.add_argument('--json',action='store_true')
    args=ap.parse_args()
    try:
        a=json.loads(Path(args.before).read_text(encoding='utf-8'))
        b=json.loads(Path(args.after).read_text(encoding='utf-8'))
        if not isinstance(a,dict) or not isinstance(b,dict): raise ValueError('快照根必须为 JSON 对象')
        result=assess(a,b)
    except (OSError,ValueError) as exc:
        print(json.dumps({'error':str(exc)},ensure_ascii=False))
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
