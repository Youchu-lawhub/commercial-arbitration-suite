#!/usr/bin/env python3
"""Local MCP setup: inspect, prepare, apply and guarded rollback. Never executes servers."""
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import tempfile
from urllib.parse import urlsplit

FORMATS={'cursor':'mcpServers','claude-code':'mcpServers','vscode-local':'servers'}

def digest(b):return hashlib.sha256(b).hexdigest()

def safe_path(p, allowed_root=None):
    original = Path(p).expanduser()
    if '..' in original.parts:
        raise ValueError(f'路径逃逸：不接受 .. 路径 {original}')
    original = original.absolute()
    root = Path(allowed_root).expanduser().resolve() if allowed_root else original.parent.resolve()
    resolved = original.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        if any(x.is_symlink() for x in [original, *original.parents]):
            raise ValueError(f'符号链接指向允许根之外：{original} 与 {resolved}')
        raise ValueError(f'路径超出允许根 {root}：{original} 与 {resolved}')
    return resolved

def private_write(path,data):
    """原子写入。目标已存在时沿用其原本权限：mkstemp 的临时文件是 0600，
    直接 replace 会把用户原有的 0644 配置静默改成 0600，客户端可能因此读不到。"""
    path=safe_path(path);path.parent.mkdir(parents=True,exist_ok=True)
    mode=path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data)
        os.chmod(tmp,mode)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def read_config(path):
    if not path.exists():return None,{}
    raw=path.read_bytes()
    try:d=json.loads(raw)
    except ValueError:raise ValueError('不是标准 JSON；JSONC/TOML 请用客户端原生配置界面，原文件未改动')
    if not isinstance(d,dict):raise ValueError('配置顶层必须为对象')
    return raw,d

def entry_for(client,spec):
    if client not in FORMATS:raise ValueError('此客户端须用原生界面/CLI，不自动改配置')
    extra=set(spec)-{'type','url','command','args'}
    if extra:
        raise ValueError(f"不接受字段 {'/'.join(sorted(extra))}：本助手不写入密钥与认证材料。"
                         f"请在客户端原生配置界面填入这些字段（登记表该通道的 auth 字段写明需要什么），"
                         f"或去掉它们后只写入连接部分。目标文件未被改动")
    if spec.get('type')=='http':
        u=urlsplit(spec.get('url',''))
        if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('远端须为不含凭证、查询串或片段的 HTTPS 端点')
        if set(spec)-{'type','url'}:raise ValueError('http 不接受 command/args')
        return {'url':spec['url']} if client=='cursor' else {'type':'http','url':spec['url']}
    if spec.get('type')=='stdio':
        if set(spec)-{'type','command','args'} or not isinstance(spec.get('command'),str) or not spec['command'].strip():raise ValueError('stdio 需要 command/args')
        args=spec.get('args',[])
        if not isinstance(args,list) or not all(isinstance(a,str) for a in args):raise ValueError('args 必须为字符串数组')
        if any(re.search(r'(?i)(bearer |api[_-]?key|token=|password|secret)',a) for a in [spec['command'],*args]):raise ValueError('命令不得嵌入凭证')
        e={'command':spec['command'],'args':args}
        if client=='vscode-local':e['type']='stdio'
        return e
    raise ValueError('只接受已核对的 http/stdio；不自动猜测协议或安装包')

def prepare(client,target,name,spec,plan,replace=False,allowed_root=None):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',name):raise ValueError('服务别名无效')
    target=safe_path(target,allowed_root);plan=safe_path(plan)
    if target==plan:raise ValueError('plan 不能覆盖目标配置')
    entry=entry_for(client,spec);raw,d=read_config(target);key=FORMATS[client]
    servers=d.get(key,{})
    if not isinstance(servers,dict):raise ValueError('现有服务节点不是对象')
    exists=name in servers
    if exists and servers[name]!=entry and not replace:raise ValueError('别名冲突；使用新别名，或明确 --replace 后审阅计划')
    record={'schema':'rulesuite-mcp-plan/1','client':client,'target':str(target),'name':name,'entry':entry,
            'before_sha256':digest(raw) if raw is not None else None,'replace':replace,
            'allowed_root':str(Path(allowed_root).resolve() if allowed_root else target.parent),
            'action':'unchanged' if exists and servers[name]==entry else ('replace' if exists else 'add')}
    if plan.exists():raise ValueError('plan 已存在，请用新文件名')
    private_write(plan,json.dumps(record,ensure_ascii=False,indent=2).encode())
    return {'decision':'PREPARED','plan':str(plan),'target':str(target),'action':record['action'],'server':name,
            'next':'审阅新增服务规格，确认客户端/范围及安装授权后 apply；写配置不等于连接成功'}

def apply(plan,journal):
    p=json.loads(Path(plan).read_text());target=safe_path(p['target'],p.get('allowed_root'));journal=safe_path(journal)
    if p.get('schema')!='rulesuite-mcp-plan/1' or journal in (target,safe_path(plan)) or journal.exists():raise ValueError('plan/journal 无效或路径冲突')
    # Validate normalized entry again; Cursor HTTP entries omit type.
    e=dict(p['entry']);e.setdefault('type','http' if 'url' in e else 'stdio');entry=entry_for(p['client'],e)
    raw,d=read_config(target)
    if (digest(raw) if raw is not None else None)!=p['before_sha256']:raise ValueError('配置已变化，重新 prepare，不覆盖并发修改')
    key=FORMATS[p['client']];servers=d.setdefault(key,{})
    if not isinstance(servers,dict):raise ValueError('服务节点无效')
    if p['name'] in servers and servers[p['name']]!=entry and not p['replace']:raise ValueError('未经授权替换同名服务')
    if servers.get(p['name'])==entry:return {'decision':'UNCHANGED','connection_verified':False}
    servers[p['name']]=entry;new=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
    backup=None
    if raw is not None:
        fd,b=tempfile.mkstemp(prefix=target.name+'.backup-',dir=target.parent);os.close(fd);backup=Path(b);private_write(backup,raw)
    receipt={'schema':'rulesuite-mcp-receipt/1','target':str(target),'allowed_root':p.get('allowed_root',str(target.parent)),'backup':str(backup) if backup else None,'before_sha256':p['before_sha256'],'after_sha256':digest(new)}
    # Persist rollback receipt before target mutation; a failed write can be inspected safely.
    private_write(journal,json.dumps(receipt,indent=2).encode());private_write(target,new)
    return {'decision':'CONFIG_WRITTEN','receipt':str(journal),'connection_verified':False,'next':'在客户端启用/重载，完成认证，再做工具发现和目标法域能力验收'}

def rollback(journal):
    j=json.loads(Path(journal).read_text());target=safe_path(j['target'],j.get('allowed_root'))
    if j.get('schema')!='rulesuite-mcp-receipt/1':raise ValueError('回滚记录无效')
    if not target.exists() or digest(target.read_bytes())!=j['after_sha256']:raise ValueError('目标已有后续变更，不自动回滚；人工合并删除本次条目')
    if j['backup']:
        raw=safe_path(j['backup'],j.get('allowed_root')).read_bytes()
        if digest(raw)!=j['before_sha256']:raise ValueError('备份哈希不符')
        private_write(target,raw)
    else:target.unlink()
    return {'decision':'ROLLED_BACK','target':str(target)}

def inspect(target=None):
    tools=['python3','node','npx','uv','uvx','pipx','docker','claude','codex','code','cursor']
    result={'decision':'ENVIRONMENT','os':platform.system(),
            'executables':{x:bool(shutil.which(x)) for x in tools},
            'writable_clients':{'cursor':'mcpServers','claude-code':'mcpServers','vscode-local':'servers'},
            'clients_needing_native_ui':['Claude Desktop','Windsurf','Cline','ChatGPT','Codex','企业托管配置','任何 JSONC/TOML 文件'],
            'client_confirmed':False}
    if target:
        p=safe_path(target);_,d=read_config(p)
        result['target']=str(p);result['server_names']={k:list(d[k]) for k in ['mcpServers','servers'] if isinstance(d.get(k),dict)}
    result['next']='运行时存在不等于客户端或权限已确认；只读用户指定配置，不扫描凭证。'
    return result

def main():
    require_python(script_name=__file__)
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('inspect');p.add_argument('--target')
    p=sub.add_parser('prepare');p.add_argument('--client',choices=sorted(FORMATS),required=True);p.add_argument('--target',required=True);p.add_argument('--name',required=True);p.add_argument('--spec',required=True);p.add_argument('--plan',required=True);p.add_argument('--replace',action='store_true');p.add_argument('--allowed-root',help='宿主允许写入的配置目录')
    p=sub.add_parser('apply');p.add_argument('--plan',required=True);p.add_argument('--receipt',required=True)
    p=sub.add_parser('rollback');p.add_argument('--receipt',required=True)
    a=ap.parse_args()
    try:
        if a.cmd=='inspect':out=inspect(a.target)
        elif a.cmd=='prepare':out=prepare(a.client,a.target,a.name,json.loads(Path(a.spec).read_text()),a.plan,a.replace,a.allowed_root)
        elif a.cmd=='apply':out=apply(a.plan,a.receipt)
        else:out=rollback(a.receipt)
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps({'decision':'SETUP_BLOCKED','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
