"""Explicit current-delivery selection; every checker receives the same file set."""
from __future__ import annotations
import json
from pathlib import Path
from _source_evidence import within


def selection(root, manifest):
    root=Path(root).resolve();manifest=Path(manifest)
    if not manifest.is_absolute(): manifest=root/manifest
    manifest.resolve().relative_to(root)
    if manifest.is_symlink(): raise ValueError('交付清单不接受符号链接')
    d=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(d,dict) or d.get('schema')!='rulesuite-delivery/1' or not isinstance(d.get('documents'),list) or not d['documents']:
        raise ValueError('交付清单须为 rulesuite-delivery/1 并列出 documents')
    docs=[];notes=[];artifacts=[];pairs=[];seen=set()
    for row in d['documents']:
        if not isinstance(row,dict) or not isinstance(row.get('document'),str): raise ValueError('每项须含 document 相对路径')
        doc=within(root,row['document'])
        if doc.suffix!='.docx' or '中文审阅说明' in doc.stem: raise ValueError('document 须为主文书 DOCX')
        if doc in seen: raise ValueError('交付清单含重复主文书')
        seen.add(doc);docs.append(doc)
        if row.get('review_note') is not None:
            note=within(root,row['review_note'])
            if note.suffix not in ('.docx','.md') or note in seen: raise ValueError('说明文件无效或被重复配对')
            seen.add(note);notes.append(note);pairs.append((doc,note))
        else:pairs.append((doc,None))
    attachments=d.get('attachments',[])
    if not isinstance(attachments,list): raise ValueError('attachments 须为路径数组')
    if d.get('filing_guide') is not None:
        if not isinstance(d['filing_guide'],str):raise ValueError('filing_guide 须为目录内 Markdown 相对路径')
        attachments=list(attachments)+[d['filing_guide']]
    for item in attachments:
        if not isinstance(item,str): raise ValueError('附件须为相对路径')
        path=within(root,item)
        if path.suffix not in ('.md','.docx'): raise ValueError('仅选择 Markdown/DOCX 附件，其他文件由材料清单核对')
        artifacts.append(path)
    for path in docs+notes+artifacts[:]:
        artifacts.append(path)
        for suffix in ('.md','.docx.md'):
            source=path.with_suffix(suffix)
            if source.is_file():
                source.resolve().relative_to(root)
                if source.is_symlink(): raise ValueError('记稿不接受符号链接')
                artifacts.append(source)
        mp=path.with_suffix('.paras.json')
        if path.suffix=='.docx' and mp.exists():
            from pending import source_path
            source=source_path(mp,json.loads(mp.read_text(encoding='utf-8')))
            source.resolve().relative_to(root)
            if source.is_symlink(): raise ValueError('渲染记稿不接受符号链接')
            artifacts.append(source)
    return docs,notes,sorted(set(artifacts)),pairs
