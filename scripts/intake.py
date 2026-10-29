#!/usr/bin/env python3
"""Evidence-backed case facts shared by all stages; no semantic guessing in gates."""
from __future__ import annotations
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
import yaml
ROOT=Path(__file__).resolve().parents[1]


class SchemaError(ValueError):
    """Unsupported or malformed structured input (CLI exit 4)."""


def safe_yaml(text):
    class UniqueLoader(yaml.SafeLoader):
        pass
    def mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                if key in result:
                    raise SchemaError('YAML 重复键')
                result[key] = loader.construct_object(value_node, deep=deep)
            except TypeError as exc:
                raise SchemaError('YAML 键须为标量') from exc
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        return yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise SchemaError('YAML 结构无效') from exc


def validate_gate_spec(spec, label='profile'):
    if not isinstance(spec, dict):
        raise SchemaError(label + ' 须为映射')
    labels, ids = spec.get('gate'), spec.get('gate_ids')
    if (not isinstance(labels, list) or not isinstance(ids, list)
            or len(labels) != len(ids)
            or not all(isinstance(x, str) and x.strip() for x in labels)
            or not all(isinstance(x, str) and re.fullmatch(r'[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+', x) for x in ids)
            or len(ids) != len(set(ids)) or len(labels) != len(set(labels))):
        raise SchemaError(label + ' gate/gate_ids 须等长、非空字符串且各自唯一')
    alt_labels, alt_ids = spec.get('gate_any'), spec.get('gate_any_ids')
    if (alt_labels is None) != (alt_ids is None):
        raise SchemaError(label + ' gate_any 与 gate_any_ids 须同时提供')
    if alt_labels is not None:
        if (not isinstance(alt_labels, list) or not isinstance(alt_ids, list)
                or len(alt_labels) != len(alt_ids)
                or not all(isinstance(x, str) and x.strip() for x in alt_labels)
                or not all(isinstance(x, str) and re.fullmatch(r'[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+', x) for x in alt_ids)
                or len(alt_ids) != len(set(alt_ids)) or len(alt_labels) != len(set(alt_labels))
                or set(ids) & set(alt_ids)):
            raise SchemaError(label + ' gate_any/gate_any_ids 须等长、非空字符串、各自唯一且不得与 gate_ids 重复')
    allowed_ids = set(ids) | set(alt_ids or [])
    unknown = spec.get('allow_unknown', [])
    if not isinstance(unknown, list) or not all(isinstance(x, str) and x in allowed_ids for x in unknown):
        raise SchemaError(label + ' allow_unknown 必须引用本任务 gate_ids/gate_any_ids')


def validate_suite(data):
    if not isinstance(data, dict) or type(data.get('schema', 1)) is not int or data.get('schema', 1) not in (1, 2):
        raise SchemaError('suite schema 不支持')
    subs = data.get('subskills')
    if not isinstance(subs, dict) or not subs:
        raise SchemaError('subskills 须为非空映射')
    for sid, meta in subs.items():
        validate_gate_spec(meta, str(sid))
        profiles = meta.get('profiles', {})
        if not isinstance(profiles, dict):
            raise SchemaError(str(sid) + ' profiles 须为映射')
        for profile, spec in profiles.items():
            validate_gate_spec(spec, str(sid) + '/' + str(profile))
            if not spec['gate']:
                raise SchemaError('profile gate 不可为空')
    return data


def task_spec(sid, profile=None):
    suite = validate_suite(safe_yaml((ROOT/'suite.yaml').read_text(encoding='utf-8')))
    if sid not in suite['subskills']:
        raise ValueError('未知子技能')
    meta = suite['subskills'][sid]
    if meta.get('profiles'):
        if profile not in meta['profiles']:
            raise SchemaError('请选择有效 profile: ' + ', '.join(meta['profiles']))
        meta = dict(meta, **meta['profiles'][profile])
    elif profile:
        raise SchemaError('该子技能没有 profile')
    return meta


def extract(path: Path) -> str:
    if path.is_symlink():
        raise ValueError('不自动读取符号链接；请显式提供原文件')
    suffix=path.suffix.lower()
    if suffix in ('.md','.txt','.json','.yaml','.yml','.csv'):
        return path.read_text(encoding='utf-8-sig')
    if suffix=='.docx':
        with zipfile.ZipFile(path) as z:
            if z.getinfo('word/document.xml').file_size>20_000_000:raise ValueError('DOCX正文过大')
            root=ET.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        return '\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p',ns))
    if suffix=='.pdf':
        try:
            from pypdf import PdfReader
            return '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)
        except ImportError:
            try:
                import fitz
                with fitz.open(path) as doc:return '\n'.join(p.get_text() for p in doc)
            except ImportError as e:raise ValueError('PDF需 pypdf 或 pymupdf；扫描件需OCR/宿主解析') from e
    raise ValueError('未支持格式；使用宿主解析/OCR后提供UTF-8文本')


def load_case(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema')!='rulesuite-case/1' or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',str(data.get('case',''))):
        raise SchemaError('需要 schema=rulesuite-case/1 与脱敏 case 代号')
    if not isinstance(data.get('facts'),dict):raise SchemaError('facts须为字段ID到记录的映射')
    for key,record in data['facts'].items():
        if not isinstance(record,dict) or record.get('status') not in ('confirmed','pending','conflict','not_applicable','unknown'):
            raise SchemaError(f'{key}: status须为confirmed/pending/conflict/not_applicable/unknown')
        if record['status']=='confirmed' and (record.get('value') is None or record.get('value')=='' or not record.get('evidence') or str(record.get('value')).strip().lower() in ('unknown','不知道','未知','未定')):
            raise ValueError(f'{key}: confirmed须有已知value和evidence；未知须登记unknown')
        if record['status']=='unknown' and not unknown_action(record):
            raise ValueError(f'{key}: unknown须有明确回答的evidence、后续action、owner与有效due日期')
        if record['status']=='not_applicable' and not record.get('reason'):raise ValueError(f'{key}: 不适用需写reason')
        if record['status']=='pending' and (not record.get('pending_id') or not record.get('question')):
            raise ValueError(f'{key}: pending须含pending_id与question')
    return data


def requirements(sid,profile=None):
    meta = task_spec(sid, profile)
    return list(zip(meta['gate_ids'], meta['gate'])), list(zip(meta.get('gate_any_ids', []), meta.get('gate_any', [])))


def unknown_action(record):
    from datetime import date
    action = record.get('follow_up', record)
    if not isinstance(action, dict) or not record.get('evidence') or not all(action.get(k) for k in ('action', 'owner', 'due')):
        return False
    try:
        date.fromisoformat(str(action['due']))
    except (ValueError, TypeError):
        return False
    return True


def _confirmed(fact):
    return (fact.get('status')=='confirmed' and fact.get('evidence')
            and fact.get('value') not in (None,'')
            and str(fact.get('value')).strip().lower() not in ('unknown','不知道','未知','未定'))


def evaluate(data,sid,profile=None,mode='submission'):
    meta = task_spec(sid, profile)
    if meta.get('redirect'):
        return {'decision':'REDIRECT_REQUIRED','subskill':sid,'profile':profile,
                'redirect':meta['redirect'],'redirect_profile':meta.get('redirect_profile'),
                'allowed_to_draft':False,'submission_ready':False}
    req,alternatives=requirements(sid,profile)
    missing=[];pending=[];reused=[];unknown=[];not_applicable=[];conflict=[]
    for key,label in req:
        fact=data['facts'].get(key,{})
        status=fact.get('status')
        if _confirmed(fact):
            reused.append({'id':key,'label':label,'evidence':fact['evidence']})
        elif status=='unknown' and key in meta.get('allow_unknown',[]) and unknown_action(fact):
            unknown.append({'id':key,'label':label,'status':'unknown','follow_up':fact.get('follow_up',fact)})
        elif status=='not_applicable' and fact.get('reason'):
            not_applicable.append({'id':key,'label':label,'reason':fact['reason']})
        elif status=='pending' and fact.get('pending_id') and fact.get('question'):
            pending.append({'id':key,'label':label,'pending_id':fact['pending_id'],'question':fact['question']})
        elif status=='conflict':
            conflict.append({'id':key,'label':label})
        else:
            missing.append({'id':key,'label':label,'status':status or 'absent'})
    gate_any=[]
    if alternatives:
        states=[]
        for key,label in alternatives:
            fact=data['facts'].get(key,{});status=fact.get('status')
            if _confirmed(fact):
                kind,row='confirmed',{'id':key,'label':label,'evidence':fact['evidence']}
            elif status=='conflict':
                kind,row='conflict',{'id':key,'label':label}
            elif status=='pending' and fact.get('pending_id') and fact.get('question'):
                kind,row='pending',{'id':key,'label':label,'pending_id':fact['pending_id'],'question':fact['question']}
            elif status=='unknown' and key in meta.get('allow_unknown',[]) and unknown_action(fact):
                kind,row='unknown',{'id':key,'label':label,'status':'unknown','follow_up':fact.get('follow_up',fact)}
            else:
                kind,row='absent',{'id':key,'label':label,'status':status or 'absent'}
            states.append((kind,row));gate_any.append({'id':key,'label':label,'status':kind})
        if not any(kind=='confirmed' for kind,_ in states):
            for kind,target in (('conflict',conflict),('pending',pending),('unknown',unknown)):
                rows=[row for k,row in states if k==kind]
                if rows:
                    target.extend(rows);break
            else:
                missing.append({'id':'gate_any','label':'任一项即可：'+' / '.join(label for _,label in alternatives),
                                'status':'absent','options':[row for kind,row in states if kind!='confirmed']})
    draft_ok=mode=='draft' and not missing and not conflict and all(x.get('pending_id') for x in pending)
    information_ok=not missing and not pending and not conflict
    ready=information_ok and not unknown
    return {'decision':'READY' if ready else ('UNKNOWN_RECORDED' if information_ok else ('DRAFT_READY' if draft_ok else 'MATERIALS_REQUIRED')),
            'case':data['case'],'subskill':sid,'profile':profile,'mode':mode,'reused':reused,
            'missing':missing,'pending':pending,'conflict':conflict,'not_applicable':not_applicable,'unknown':unknown,
            'gate_any':gate_any,
            'allowed_to_draft':information_ok or draft_ok,
            'submission_ready':ready and mode=='submission',
            'limitation':'材料闸门只复用记录；不适用项按 reason 记为已核；未知项不是已确认事实，法律与矩阵核验另行完成'}


def main():
    require_python(script_name=__file__)
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('bootstrap');p.add_argument('--facts',required=True);p.add_argument('--workdir',required=True)
    p=sub.add_parser('checklist');p.add_argument('--gate',required=True);p.add_argument('--profile');p.add_argument('--facts')
    p=sub.add_parser('extract');p.add_argument('--input',required=True);p.add_argument('--out',required=True)
    a=ap.parse_args()
    try:
        if a.cmd=='extract':
            source=Path(a.input).resolve();out=Path(a.out).resolve()
            if out==source:raise ValueError('不得覆盖原始材料')
            files=sorted(p for p in source.rglob('*') if p.is_file() and not p.is_symlink()) if source.is_dir() else [source]
            rows=[]
            for p in files:
                if p.resolve()==out:continue
                try:
                    text=extract(p);rows.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'text':text,'status':'parsed' if text.strip() else 'needs_ocr'})
                except Exception as e:rows.append({'file':str(p),'status':'needs_parser','reason':str(e)})
            out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'schema':'rulesuite-extract/1','documents':rows},ensure_ascii=False,indent=2),encoding='utf-8')
            result={'decision':'EXTRACTED','file':str(out),'parsed':sum(x['status']=='parsed' for x in rows),'unparsed':[x['file'] for x in rows if x['status']!='parsed']}
        elif a.cmd=='checklist':
            req,alt=requirements(a.gate,a.profile);data=load_case(a.facts) if a.facts else {'case':'CASE-ID','facts':{}}
            def mark(key):return data['facts'].get(key,{}).get('status')
            lines=['- ['+('x' if mark(key)=='confirmed' else ' ')+'] '+label for key,label in req]
            if alt:
                lines.append('以下任一项（gate_any_ids）：')
                lines.extend('- ['+('x' if mark(key)=='confirmed' else ' ')+'] '+label+'（'+key+'）' for key,label in alt)
            result={'case':data['case'],
                    'requirements':[{'id':key,'label':label,'record':data['facts'].get(key,{'status':'absent'})} for key,label in req],
                    'gate_any':[{'id':key,'label':label,'record':data['facts'].get(key,{'status':'absent'})} for key,label in alt],
                    'markdown':'case: '+data['case']+'\n'+'\n'.join(lines)}
        else:
            data=load_case(a.facts);wd=Path(a.workdir).expanduser().resolve()
            if wd==ROOT or ROOT in wd.parents:raise ValueError('案件目录不能位于技能目录')
            wd.mkdir(parents=True,exist_ok=True);target=wd/'case.json';cfg=wd/'.arbitration-config.md'
            if target.exists() and target.resolve()!=Path(a.facts).resolve():raise ValueError('已有case.json；请显式编辑现有文件，防止覆盖')
            if cfg.exists():raise ValueError('已有配置；请更新未决项，不重复bootstrap')
            target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            cfg.write_text('case: '+data['case']+'\n~ 工作目录：'+str(wd)+'\n'
                '- slot(official_rules_fetch): degraded (await content import/review)\n'
                '- slot(law_retrieval): skipped\n- slot(docx_render): bound (local standard-library renderer)\n'
                '- slot(local_corpus): skipped\n- slot(company_research): degraded (official registries; jurisdiction pending)\n- slot(party_data): user-materials-only\n',encoding='utf-8')
            result={'decision':'BOOTSTRAPPED','case':data['case'],'case_file':str(target),'config':str(cfg),
                    'pending':[k for k,v in data['facts'].items() if v['status']!='confirmed'],
                    'note':'只登记可观测环境与有来源的事实；没有宣称访谈完成、联网权限或规则已核验'}
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except SchemaError as e:
        print(json.dumps({'decision':'SCHEMA_INVALID','error':str(e)},ensure_ascii=False));return 4
    except (OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps({'decision':'INPUT_ERROR','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':sys.exit(main())
