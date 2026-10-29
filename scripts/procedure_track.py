#!/usr/bin/env python3
"""Data-driven procedure screening from a case-local, source-verified profile."""
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fetch_official import SUITE, OFFICIAL
from _source_evidence import source_evidence, valid_url
FRESHNESS_DAYS = 90
PROFILE_SCHEMA = 'rulesuite-procedure-profile/1'


def evaluate(expression, facts, depth=0):
    """Small data-only predicate language; never evals code or imports registry functions."""
    if depth>40: raise ValueError('条件图嵌套超限')
    if isinstance(expression,(bool,str,int)) and not isinstance(expression,float):return expression
    if not isinstance(expression,dict) or len(expression)!=1:raise ValueError('程序条件须为单一运算节点')
    op,args=next(iter(expression.items()))
    if op=='fact':
        if not isinstance(args,str): raise ValueError('fact 须引用字段名')
        return facts[args]
    if op in ('all','any'):
        if not isinstance(args,list) or not args: raise ValueError('all/any 须为非空条件数组')
        values=[evaluate(x,facts,depth+1) for x in args]
        if any(type(x) is not bool for x in values):raise ValueError('布尔条件须返回 true/false')
        return all(values) if op=='all' else any(values)
    if op=='not':
        value=evaluate(args,facts,depth+1)
        if type(value) is not bool:raise ValueError('not 条件须为布尔值')
        return not value
    if op in ('lte','lt','gte','gt','eq'):
        if not isinstance(args,list) or len(args)!=2:raise ValueError('比较条件须为两个操作数')
        left,right=(evaluate(x,facts,depth+1) for x in args)
        if op=='eq':return left==right
        if isinstance(left,bool) or isinstance(right,bool):raise ValueError('金额条件不得使用布尔值')
        left,right=Decimal(str(left)),Decimal(str(right))
        if not left.is_finite() or not right.is_finite():raise ValueError('金额必须有限')
        return {'lte':left<=right,'lt':left<right,'gte':left>=right,'gt':left>right}[op]
    raise ValueError('不支持的程序条件运算：'+str(op))


def load_profile(d):
    if isinstance(d.get('profile'),dict):return d['profile'],None
    path=d.get('profile_file')
    if not path:return None,'缺少 profile：请提供从本案适用官方文本核验后生成的案件本地 profile'
    try:
        return json.loads(Path(path).read_text(encoding='utf-8')),None
    except (OSError,ValueError) as e:
        return None,'profile 无法读取：'+str(e)


def profile_errors(p):
    if not isinstance(p,dict):return ['profile 须为 JSON 对象']
    errs=[]
    if p.get('schema')!=PROFILE_SCHEMA:errs.append('schema 须为 '+PROFILE_SCHEMA)
    for key in ('institution','rules_version','basis_source','source_url','source_locator','source_quote','verified_at'):
        if not isinstance(p.get(key),str) or not p[key].strip():errs.append('缺少或为空：'+key)
    for key in ('required','outcomes'):
        if not isinstance(p.get(key),dict if key=='required' else list) or not p[key]:errs.append(key+' 须为非空对象或数组')
    if not isinstance(p.get('confirmations',[]),list):errs.append('confirmations 须为数组')
    if not isinstance(p.get('references',[]),list):errs.append('references 须为数组')
    url=p.get('source_url')
    if not valid_url(url):
        errs.append('source_url 须为 https 官方地址')
    quote=p.get('source_quote')
    if isinstance(quote,str) and quote.strip() and len(quote.strip())<12:
        errs.append('source_quote 过短，无法作为命中凭证')
    try:
        verified=date.fromisoformat(str(p.get('verified_at')))
        if verified>date.today():errs.append('verified_at 不得晚于今日')
    except ValueError:
        errs.append('verified_at 须为 YYYY-MM-DD')
    outcomes=p.get('outcomes')
    if isinstance(outcomes,list):
        for row in outcomes:
            if not isinstance(row,dict) or 'when' not in row or not isinstance(row.get('result',{}),dict) or not isinstance(row.get('computed',{}),dict):
                errs.append('outcomes 项须含 when，result/computed 须为对象')
    if isinstance(p.get('required'),dict) and any(not isinstance(k,str) or v not in ('boolean','decimal','text') for k,v in p['required'].items()):
        errs.append('required 字段名或类型无效')
    if isinstance(p.get('confirmations'),list) and any(not isinstance(x,str) or not x.strip() for x in p['confirmations']):
        errs.append('confirmations 须为非空字段名')
    return errs


def profile_fingerprint(p):
    body={k:v for k,v in p.items() if k!='review'}
    return hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def source_marker(p):
    return '[source:{} | {} | {} | {} | 校验 {}]'.format(
        p['basis_source'],p['rules_version'],p['source_locator'],p['source_url'],p['verified_at'])


def verified_profile(p, root=None):
    """Bind quoted text, version, provenance and the exact reviewed condition graph."""
    errors, _ = source_evidence(p['basis_source'],root,locator=p['source_locator'],
        edition=p['rules_version'],url=p['source_url'],quote=p['source_quote'],max_age=FRESHNESS_DAYS)
    review=p.get('review',{})
    if not isinstance(review,dict): review={}
    if not isinstance(review,dict) or not review.get('by') or review.get('profile_sha256')!=profile_fingerprint(p):
        errors.append('profile 条件图无有效人工复核指纹')
    try:
        when=date.fromisoformat(str(review.get('date')))
        if when>date.today() or (date.today()-when).days>FRESHNESS_DAYS: errors.append('profile 复核日期无效或过期')
    except (ValueError,TypeError): errors.append('profile 复核日期无效')
    for i,outcome in enumerate(p['outcomes']):
        basis=outcome.get('basis')
        if not isinstance(basis,dict) or not all(isinstance(basis.get(k),str) and basis[k].strip() for k in ('locator','quote')):
            errors.append('outcomes.%s 缺少条件对应的条文定位与引文'%i);continue
        issues, _ = source_evidence(p['basis_source'],root,locator=basis['locator'],edition=p['rules_version'],url=p['source_url'],quote=basis['quote'],max_age=FRESHNESS_DAYS)
        errors.extend(issues)
    return not errors, '; '.join(dict.fromkeys(errors)) if errors else None


def assess(d):
    if not isinstance(d,dict): raise ValueError('输入须为 JSON 对象')
    profile,error=load_profile(d)
    if error:return {'decision':'NO_PROFILE','action':error,'submission_ready':False}
    errs=profile_errors(profile)
    if errs:return {'decision':'PROFILE_INVALID','errors':errs,'submission_ready':False}
    missing=[x for x in ('institution','rules_version') if not d.get(x)]
    if missing:return {'decision':'NEEDS_FACTS','missing':missing,'submission_ready':False}
    if str(d['institution']).casefold()!=profile['institution'].casefold():
        return {'decision':'PROFILE_MISMATCH','field':'institution','profile':profile['institution'],'submission_ready':False}
    if str(d['rules_version'])!=profile['rules_version']:
        return {'decision':'PROFILE_MISMATCH','field':'rules_version','profile':profile['rules_version'],'submission_ready':False}
    ok,reason=verified_profile(profile,d.get('workdir'))
    if not ok:
        return {'decision':'PROFILE_UNVERIFIED','reason':reason,'action':'按来源凭证核验正文、版本、每项条件及 profile 指纹；缓存位置服从 RULESUITE_DATA_DIR','submission_ready':False}
    required=profile['required']
    missing=[x for x in required if x not in d or d[x] is None or d[x]=='']
    if missing:return {'decision':'NEEDS_FACTS','missing':missing,'submission_ready':False}
    for key,kind in required.items():
        if kind=='boolean' and type(d[key]) is not bool:raise ValueError('判断项须为 JSON true/false；未知用 null')
        if kind=='decimal':
            if isinstance(d[key],(float,bool)):raise ValueError('金额须为十进制字符串或整数')
            amount=Decimal(str(d[key]))
            if not amount.is_finite() or amount<0:raise ValueError('金额无效')
        if kind=='text' and (not isinstance(d[key],str) or not d[key].strip()):raise ValueError('依据须为非空文本')
        if kind not in ('boolean','decimal','text'):raise ValueError('未知字段类型')
    confirmations=profile.get('confirmations',[])
    if not confirmations or any(d.get(x) is not True for x in confirmations):
        return {'decision':'NEEDS_REVIEW','action':'先核对规则适用、金额口径及配置所需确认项','submission_ready':False}
    result={'decision':'SCREENED','binding_determination':False,'profile_status':'VERIFIED',
            'rules_source':profile['basis_source'],'source_marker':source_marker(profile),
            'references':profile.get('references',[]),
            'limitations':'仅执行本 profile 已核验的条件筛查；不构成本案程序轨道、任命结果或法律结论。'}
    for outcome in profile['outcomes']:
        condition=evaluate(outcome['when'],d)
        if type(condition) is not bool:raise ValueError('程序条件须返回布尔值')
        if condition:
            values=dict(outcome.get('result',{}))
            if set(values)-{'track','action','appointment'}:raise ValueError('结果含不允许覆盖的字段')
            result.update(values)
            for name,expr in outcome.get('computed',{}).items():
                if name in result:raise ValueError('计算字段不得覆盖判定状态')
                result[name]=evaluate(expr,d)
            return result
    return {'decision':'NEEDS_REVIEW','action':'profile 条件未覆盖本案，人工核对，不默认为普通程序'}


def main():
    require_python(script_name=__file__)
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True);ap.add_argument('--fingerprint',action='store_true',help='只输出 profile 条件图指纹，须人工复核后再登记 review');a=ap.parse_args()
    try:
        data=json.loads(Path(a.input).read_text(encoding='utf-8'))
        if a.fingerprint:
            profile=data.get('profile',data) if isinstance(data,dict) else None
            if not isinstance(profile,dict): raise ValueError('profile 须为对象')
            print(json.dumps({'profile_sha256':profile_fingerprint(profile),'legal_verified':False}));return 0
        if isinstance(data,dict) and data.get('profile_file'):
            path=Path(data['profile_file'])
            if not path.is_absolute(): data['profile_file']=str(Path(a.input).resolve().parent/path)
        if isinstance(data,dict) and data.get('workdir'):
            path=Path(data['workdir'])
            if not path.is_absolute(): data['workdir']=str(Path(a.input).resolve().parent/path)
        result=assess(data);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['decision']=='SCREENED' else 2
    except (ValueError,TypeError,KeyError,OSError,InvalidOperation) as e:
        print(json.dumps({'decision':'INVALID_INPUT','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__': raise SystemExit(main())
