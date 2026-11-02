#!/usr/bin/env python3
"""Explicit simple-interest segments and principal reconciliation; no legal rate assumptions."""
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from pathlib import Path


def number(x):
    if isinstance(x, (float,bool)):
        raise ValueError('金额与利率请用十进制字符串，禁止 float/bool')
    d=Decimal(x)
    if not d.is_finite(): raise ValueError('数值必须有限')
    return d


def calculate(data):
    if data.get('schema')!='rulesuite-interest/1' or not data.get('currency'):
        raise ValueError('schema/currency 缺失' + ('' if data.get('schema') else '（缺 schema=rulesuite-interest/1）')
                         + ('' if data.get('currency') else '（缺 currency）'))
    missing=[k for k in ('method','interval','basis') if not data.get(k)]
    if missing:
        raise ValueError('缺少字段：' + '、'.join(missing)
                         + '；合法取值 method=simple（明确单利），interval=start-inclusive-end-exclusive（含起日不含止日），'
                           'basis=ACT/365F｜ACT/360｜ACT/ACT-year')
    if data.get('method')!='simple':
        raise ValueError(f"method 仅支持 simple（明确单利），现在是「{data.get('method')}」；复利或其他口径须另行计算")
    if data.get('interval')!='start-inclusive-end-exclusive':
        raise ValueError(f"interval 仅支持 start-inclusive-end-exclusive（含起日不含止日），现在是「{data.get('interval')}」")
    basis=data.get('basis')
    if basis not in ('ACT/365F','ACT/360','ACT/ACT-year'):
        raise ValueError(f"basis 仅 ACT/365F、ACT/360、ACT/ACT-year，现在是「{basis}」")
    rows=[];total=Decimal(0);ends={}
    for row in data['segments']:
        start=date.fromisoformat(row['start']);end=date.fromisoformat(row['end']);principal=number(row['principal']);rate=number(row['annual_rate'])
        ident=row['claim_id']
        if not ident or end<=start or principal<0 or rate<0: raise ValueError('日期、基数或利率无效')
        if ident in ends and start!=ends[ident]: raise ValueError('同请求分段须连续且按日期排序，不得重叠或漏段')
        if not row.get('basis_evidence'): raise ValueError('每段须记录利率/本金口径的依据或明确待确认说明')
        ends[ident]=end;fraction=Decimal(0);cursor=start
        while cursor<end:
            stop=min(end,date(cursor.year+1,1,1)) if basis=='ACT/ACT-year' else end
            denominator=(date(cursor.year+1,1,1)-date(cursor.year,1,1)).days if basis=='ACT/ACT-year' else (365 if basis=='ACT/365F' else 360)
            fraction+=Decimal((stop-cursor).days)/Decimal(denominator);cursor=stop
        interest=principal*rate*fraction;total+=interest
        rows.append(dict(row, days=(end-start).days,unrounded_interest=str(interest),interest=str(interest.quantize(Decimal('.01'),rounding=ROUND_HALF_UP))))
    if not rows: raise ValueError('segments 不得为空')
    rec=data.get('reconciliation',{})
    gross=number(rec['face_principal']);adjustments=rec.get('adjustments',[])
    for a in adjustments:
        if not a.get('reason') or not a.get('evidence'): raise ValueError('调节项须有原因与凭证')
    net=gross+sum((number(a['amount']) for a in adjustments),Decimal(0))
    claimed=number(rec['claimed_principal'])
    return {'decision':'CALCULATED','legal_verified':False,'currency':data['currency'],'basis':basis,'interval':data['interval'],
            'rounding':'sum unrounded segments, then HALF_UP to 0.01; displayed row sums can differ',
            'segments':rows,'total_interest':str(total.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)),
            'reconciliation':{'computed_net':str(net),'claimed_principal':str(claimed),'difference':str(net-claimed),'balanced':net==claimed},
            'limitations':['付款如何冲抵本金/利息、利率及起止日合法性须另核；付款或调息按生效日拆段','不同币种与不同口径分别运行；不自动换汇、不自动推定复利']}


def allocate(data):
    if data.get('allocation_scope')!='invoice_or_running_account':
        raise ValueError('--allocation 仅适用于票据／往来账型金钱债权；须显式提供 allocation_scope=invoice_or_running_account，其他案由改用普通 segments 按付款证书、提款、期间或估值基准日分段')
    policy=data.get('allocation_policy')
    if policy not in ('oldest_first','designated'):
        raise ValueError('须显式提供 allocation_policy: oldest_first 或 designated')
    if data.get('payment_application')!='principal_only':
        raise ValueError('须显式确认 payment_application=principal_only；本金/利息优先顺序的法律效果另核')
    end=date.fromisoformat(data['as_of']);rate=number(data['annual_rate'])
    if rate<0:raise ValueError('利率不得为负')
    invoices={};balances={};cursors={};segments=[];allocations=[];unallocated=Decimal(0)
    def decimal_string(value):
        if not isinstance(value,str):raise ValueError('allocation 金额与利率须用十进制字符串')
        return number(value)
    decimal_string(data['annual_rate'])
    for inv in data['invoices']:
        ident=inv['invoice_id'];amount=decimal_string(inv['amount']);due=date.fromisoformat(inv['due_date'])
        if not ident or ident in invoices or amount<=0:raise ValueError('发票 ID 须唯一且金额为正')
        invoices[ident]=inv;balances[ident]=amount;cursors[ident]=due
    if not invoices:raise ValueError('invoices 不得为空')
    def accrue(ident,stop):
        start=cursors[ident]
        if stop>start:
            if balances[ident]>0:
                segments.append({'claim_id':ident,'invoice_id':ident,'start':start.isoformat(),'end':stop.isoformat(),
                                 'principal':str(balances[ident]),'annual_rate':data['annual_rate'],'basis_evidence':data.get('basis_evidence','')})
            cursors[ident]=stop
    payments=sorted(enumerate(data.get('payments',[])),key=lambda x:(date.fromisoformat(x[1]['date']),x[0]))
    for index,payment in payments:
        when=date.fromisoformat(payment['date']);amount=decimal_string(payment['amount'])
        if amount<=0 or when>end:raise ValueError('付款金额须为正且付款日不得晚于 as_of')
        selected=payment.get('invoice_id')
        if selected and selected not in invoices:raise ValueError('指定发票不存在')
        if policy=='designated' and not selected:raise ValueError('designated 模式每笔付款须指定 invoice_id')
        order=[selected] if selected else sorted(invoices,key=lambda k:(invoices[k]['due_date'],k))
        remaining=amount
        for ident in order:
            applied=min(remaining,balances[ident])
            if not applied:continue
            accrue(ident,when);balances[ident]-=applied;remaining-=applied
            allocations.append({'payment_index':index+1,'date':when.isoformat(),'invoice_id':ident,'allocated_principal':str(applied)})
            if remaining==0:break
        unallocated+=remaining
    for ident in invoices:accrue(ident,end)
    total_face=sum((number(x['amount']) for x in invoices.values()),Decimal(0));unpaid=sum(balances.values(),Decimal(0))
    # Reuse the audited day-count and rounding implementation for every interval.
    base=dict(data,segments=segments,reconciliation={'face_principal':str(total_face),'adjustments':[{'amount':str(unpaid-total_face),'reason':'explicit payment allocation','evidence':data.get('basis_evidence','')}],'claimed_principal':str(unpaid)})
    if not data.get('basis_evidence'):raise ValueError('须提供 basis_evidence 或明确待确认说明')
    if not segments:
        # Validate the same schema and basis even where nothing accrues.
        probe=dict(base,segments=[{'claim_id':'validation','start':'2000-01-01','end':'2000-01-02','principal':'0','annual_rate':data['annual_rate'],'basis_evidence':data['basis_evidence']}])
        result=calculate(probe);result['segments']=[]
    else:result=calculate(base)
    result.update(allocation_policy=policy,payment_application='principal_only',as_of=end.isoformat(),
                  invoices=[{'invoice_id':ident,'amount':invoices[ident]['amount'],'due_date':invoices[ident]['due_date'],'unpaid_principal':str(balances[ident])} for ident in invoices],
                  allocations=allocations,total_unpaid_principal=str(unpaid),unallocated_payment=str(unallocated))
    result['limitations']=['仅按显式口径将付款冲抵本金；超额付款单列，不抵利息、不跨指定发票',
        '仅适用于票据／往来账型金钱债权；工程、合资、许可、投资条约等应按付款证书、单笔本金、期间或估值基准日分段，不套用逐票口径',
        '利率合法性、单利或复利约定、换汇、付款冲抵顺序及提前付款的法律效果须另核；本结果不作法律认定']
    return result

def main():
    require_python(script_name=__file__)
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True);ap.add_argument('--allocation',action='store_true');a=ap.parse_args()
    try:
        result=(allocate if a.allocation else calculate)(json.loads(Path(a.input).read_text()));print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except KeyError as e:
        print(json.dumps({'decision':'INVALID_INPUT',
              'error':f'输入缺少必填字段 {e.args[0]}',
              'action':'按 references/practical-workflow.md 的利息计算输入结构补齐该字段，不要在脚本里改字段名凑过校验'},
             ensure_ascii=False));return 2
    except (ValueError,TypeError,OSError,InvalidOperation) as e:
        print(json.dumps({'decision':'INVALID_INPUT','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__': raise SystemExit(main())
