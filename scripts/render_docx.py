#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把套件的文书记稿（.md）渲染为可直接交付的 Word 文书：零第三方依赖，直接生成 OOXML。

设计取舍：
- 不依赖 python-docx / node / 联网安装，企业内网与受限环境也能出 Word。
- 段落编号用 Word 自动编号（插入段落自动重排），同时输出 manifest 以便交叉引用核验。
- 中文《审阅说明》用 memo 模式（无编号段落、CJK 字体与缩进），英文文书用 legal 模式。

用法：
  python3 render_docx.py --in draft.md --out draft.docx
  python3 render_docx.py --in draft.md --out draft.docx --mode memo --manifest draft.paras.json
  python3 render_docx.py --in draft.md --out draft.docx --strip-sources --strict
输入格式（受限的 Markdown 方言）：
  --- 文件头 key: value（title/case/mode/footer_left/keep_sources/toc）---
  # 文书标题（居中，不编号）
  ## I. 一级标题   ### A. 二级标题   #### 三级标题
  普通行 = 编号段落（legal 模式）；行首 `~ ` = 不编号段落；行首 `- ` = 项目符号
  > 引用块 / 缩进段
  | 表头 | 表头 | 管道表格（首行为表头）
  [[待填写内容]] = 占位符（黄色底纹，--strict 时报错）
  [source:...] = 来源标记（--strip-sources 时删除，否则灰色小字）
  #! 行首 = 模板填写指引，只给起草人看，绝不渲染进 Word
  <pagebreak> = 分页
退出码：0 成功 / 2 输入或依赖问题 / 3 --strict 下存在未填占位符
"""
from __future__ import annotations

from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import os
import argparse
import hashlib
import tempfile
import datetime as dt
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XMLNS = f'xmlns:w="{W}" xmlns:r="{R}"'

# 版式常量（twips；1cm=567twips；A4=11906x16838）
PAGES = {"A4": (11906, 16838), "Letter": (12240, 15840)}
MARGINS = {"top": 1417, "bottom": 1417, "left": 1701, "right": 1417, "header": 851, "footer": 851}

FONTS = {
    # ascii/hAnsi 用西文衬线，eastAsia 分别给正文与标题
    "legal": {"latin": "Times New Roman", "cjk_body": "宋体", "cjk_head": "黑体", "size": 24},
    "memo": {"latin": "Times New Roman", "cjk_body": "宋体", "cjk_head": "黑体", "size": 22},
    "board": {"latin": "Times New Roman", "cjk_body": "宋体", "cjk_head": "黑体", "size": 22},
}

SRC_RE = re.compile(r"\[source:[^\]]*\]")
PLACEHOLDER_RE = re.compile(r"\[\[(.*?)\]\]", re.S)
TOKEN_RE = re.compile(r"(\[source:[^\]]*\]|\[\[.*?\]\])", re.S)
UNCLOSED_PH_RE = re.compile(r"\[\[(?![\s\S]*?\]\])")
_XML_ILLEGAL_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f]"
)


def _xml_escape(text: str) -> str:
    return escape(_XML_ILLEGAL_RE.sub("", text))


class RenderError(Exception):
    pass


# ───────────────────────────── 文件头 ─────────────────────────────
def split_front_matter(text: str):
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            from intake import safe_yaml
            meta = safe_yaml(text[3:end]) or {}
            if not isinstance(meta, dict) or not all(isinstance(k, str) for k in meta):
                raise ValueError('frontmatter 须为映射')
            meta = {k.lower(): v for k, v in meta.items()}
            for key in ('title','case','mode','footer_left'):
                if key in meta and meta[key] is not None:
                    meta[key] = str(meta[key])
            return meta, text[end + 4:]
    return meta, text


# ───────────────────────────── 运行文本 ─────────────────────────────
def runs_from_inline(s: str, mode: str, strip_sources: bool):
    """把一行内联文本切成 run 列表：[source:...]→灰色小字，[[...]]→黄底占位符，**粗体**、*斜体*。"""
    out = []
    for piece in TOKEN_RE.split(s):
        if not piece:
            continue
        if piece.startswith("[source:"):
            if not strip_sources:
                out.append(_run_factory(text=piece, src=True))
            continue
        if piece.startswith("[["):
            inner = piece[2:-2].replace("\n", " ").strip()
            out.append(_run_factory(text="[" + inner + "]", ph=True))
            continue
        for tok in re.split(r"(\*\*[^*]+\*\*|__[^_]+__|\*[^*\n]+\*|_[^_\n]+_)", piece):
            if not tok:
                continue
            if (tok.startswith("**") and tok.endswith("**") and len(tok) > 4) or \
               (tok.startswith("__") and tok.endswith("__") and len(tok) > 4):
                out.append(_run_factory(text=tok[2:-2], b=True))
            elif (tok.startswith("*") and tok.endswith("*") and len(tok) > 2) or \
                 (tok.startswith("_") and tok.endswith("_") and len(tok) > 2):
                out.append(_run_factory(text=tok[1:-1], i=True))
            else:
                out.append(_run_factory(text=tok))
    merged = []
    for r_ in out:
        if merged and merged[-1]["simple"] == r_["simple"] and "t" in merged[-1] and "t" in r_:
            merged[-1]["t"] += r_["t"]
        else:
            merged.append(r_)
    return merged


def _run_factory(text=None, b=False, i=False, u=False, sz=None, color=None,
                 src=False, ph=False, latin=None, cjk=None):
    d = {"b": b, "i": i, "u": u, "src": src, "ph": ph, "sz": sz, "color": color,
         "latin": latin, "cjk": cjk}
    if text is not None:
        d["t"] = text
    d["simple"] = (b, i, u, src, ph, sz, color, latin, cjk)
    return d


def rPr(run, mode):
    f = FONTS[mode]
    latin = run.get("latin") or f["latin"]
    cjk_raw = run.get("cjk")
    cjk_b = cjk_raw or f["cjk_body"]
    rfonts_parts = [f'w:ascii="{escape(latin)}"', f'w:hAnsi="{escape(latin)}"',
                    f'w:cs="{escape(latin)}"']
    if cjk_raw != "NONE":
        rfonts_parts.insert(2, f'w:eastAsia="{escape(cjk_b)}"')
    rfonts = "<w:rFonts " + " ".join(rfonts_parts) + "/>"
    parts = [rfonts]
    if run["b"]:
        parts.append("<w:b/><w:bCs/>")
    if run["i"] or run["src"]:
        parts.append("<w:i/><w:iCs/>")
    if run["u"]:
        parts.append('<w:u w:val="single"/>')
    if run["src"]:
        parts.append('<w:color w:val="7F7F7F"/>')
    if run["color"]:
        parts.append(f'<w:color w:val="{run["color"]}"/>')
    if run["sz"]:
        parts.append(f'<w:sz w:val="{run["sz"]}"/><w:szCs w:val="{run["sz"]}"/>')
    elif run["src"]:
        parts.append('<w:sz w:val="18"/><w:szCs w:val="18"/>')
    if run["ph"]:
        parts.append('<w:highlight w:val="yellow"/>')
    return "<w:rPr>" + "".join(parts) + "</w:rPr>"


def render_runs(runs):
    out = []
    for run in runs:
        t = run.get("t", "")
        if not t:
            continue
        out.append(f'<w:r>{rPr(run, out_mode[0])}<w:t xml:space="preserve">{_xml_escape(t)}</w:t></w:r>')
    return "".join(out)


out_mode = ["legal"]  # 由 render_document 设定，供 rPr 取字号


def fld(instr, mode, sz=None, runs_text=None):
    f = FONTS[mode]
    rpr = f'<w:rPr><w:rFonts w:ascii="{f["latin"]}" w:hAnsi="{f["latin"]}" w:eastAsia="{f["cjk_body"]}"/>'
    if sz:
        rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    rpr += "</w:rPr>"
    inner = runs_text or f'<w:r>{rpr}<w:t>1</w:t></w:r>'
    return (f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{rpr}<w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r>'
            f'{inner}'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>')


# ───────────────────────────── 段落 ─────────────────────────────
def para(runs, style=None, numbered=False, bullet=False, jc=None, ind_left=None,
         hanging=None, keep_next=False, space_before=None, space_after=None,
         line=None, outline=None, p_bdr_bottom=False, page_break_before=False):
    p = []
    if style:
        p.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next:
        p.append("<w:keepNext/>")
    if page_break_before:
        p.append("<w:pageBreakBefore/>")
    p.append("<w:widowControl/>")
    if numbered:
        p.append('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')
    if bullet:
        p.append('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>')
    if p_bdr_bottom:
        p.append('<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="808080"/></w:pBdr>')
    if space_before is not None or space_after is not None or line is not None:
        sp = '<w:spacing'
        if space_before is not None:
            sp += f' w:before="{space_before}"'
        if space_after is not None:
            sp += f' w:after="{space_after}"'
        if line is not None:
            sp += f' w:line="{line}" w:lineRule="auto"'
        p.append(sp + "/>")
    if ind_left is not None or hanging is not None:
        ind = "<w:ind"
        if ind_left is not None:
            ind += f' w:left="{ind_left}"'
        if hanging is not None:
            ind += f' w:hanging="{hanging}"'
        p.append(ind + "/>")
    if jc:
        p.append(f'<w:jc w:val="{jc}"/>')
    if outline is not None:
        p.append(f'<w:outlineLvl w:val="{outline}"/>')
    ppr = "<w:pPr>" + "".join(p) + "</w:pPr>" if p else ""
    return "<w:p>" + ppr + render_runs(runs) + "</w:p>"


def hrule():
    return para([], jc="left", space_after=120, p_bdr_bottom=True)


def table(rows, mode):
    """rows: list of list of run-lists；首行为表头。"""
    if not rows:
        return para([_run_factory(text="")], space_after=0, line=240)
    f = FONTS[mode]
    avail = PAGES["A4"][0] - MARGINS["left"] - MARGINS["right"]
    ncol = max(len(r) for r in rows)
    # 依据内容长度分配列宽，避免均分导致表头换行难看
    weights = []
    for c in range(ncol):
        maxlen = max((len(x.get("t", "")) for r in rows for x in (r[c] if c < len(r) else [])), default=0)
        weights.append(max(maxlen, 6))
    tot = sum(weights) or 1
    widths = [int(avail * w / tot) for w in weights]
    widths[-1] = avail - sum(widths[:-1])
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    xml = ['<w:tbl><w:tblPr>'
           '<w:tblW w:w="0" w:type="auto"/>'
           '<w:tblBorders>'
           '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
           '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
           '</w:tblBorders><w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
           '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
           f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    for ri, row in enumerate(rows):
        trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if ri == 0 else "<w:trPr><w:cantSplit/></w:trPr>"
        cells = []
        for ci in range(ncol):
            runs = row[ci] if ci < len(row) else []
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="EFEFEF"/>' if ri == 0 else ""
            runs2 = [_run_factory(b=True, latin=f["latin"], cjk=f["cjk_head"]) if ri == 0 and not runs else None]
            body = [r_ for r_ in runs2 if r_] + runs
            if ri == 0 and runs:
                body = [dict(r_, b=True) for r_ in runs]
            ptxt = para(body or [_run_factory(text="")], jc="left", space_before=0, space_after=0, line=276)
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{shd}'
                         f'<w:vAlign w:val="center"/></w:tcPr>{ptxt}</w:tc>')
        xml.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    xml.append("</w:tbl>")
    xml.append(para([_run_factory(text="")], space_after=0, line=240))
    return "".join(xml)


# ───────────────────────────── 解析记稿 ─────────────────────────────
def parse_and_build(text: str, mode: str, strip_sources: bool):
    """返回 (body_xml, manifest, placeholders, toc_headings)"""
    global out_mode
    out_mode[0] = mode
    body, manifest, placeholders = [], [], []
    heads = []          # (level, text)
    n = 0               # 编号段落计数
    cur_path = []
    body_mode = mode

    def flush_par(lines, numbered, bullet):
        nonlocal n
        txt = " ".join(lines).strip()
        if not txt:
            return
        runs = runs_from_inline(txt, mode, strip_sources)
        if numbered:
            n += 1
            manifest.append({"no": n, "path": " > ".join(cur_path), "text": re.sub(r"\*\*|\[\[|\]\]", "", txt)[:90]})
        body.append(para(runs, numbered=numbered, bullet=bullet,
                         jc="both" if mode == "legal" else "left",
                         space_after=120, line=360))

    lines = text.splitlines()
    # 预扫描：收集全文占位符（含多行占位），不遗漏标题/表格/引文中的占位
    _cleaned_lines = []
    for _raw_line in lines:
        if _raw_line.strip().startswith("#!"):
            continue
        _cleaned_lines.append(_raw_line)
    _full_text = "\n".join(_cleaned_lines)
    seen_ph = set()
    for _m in PLACEHOLDER_RE.finditer(_full_text):
        _ph = _m.group(1)[:80]
        if _ph not in seen_ph:
            seen_ph.add(_ph)
            placeholders.append(_ph)
    for _m in UNCLOSED_PH_RE.finditer(_full_text):
        _tail = _full_text[_m.start():_m.start()+80].split("\n")[0]
        if _tail not in seen_ph:
            seen_ph.add(_tail)
            placeholders.append(_tail)
    i = 0
    pending, pending_kind = [], None
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        s = line.strip()
        if not s:
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
            pending, pending_kind = [], None
            i += 1
            continue
        if s.lower() == "<pagebreak>":
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            body.append(para([_run_factory(text="")], page_break_before=True))
            i += 1
            continue
        # 表格块
        if s.startswith("|"):
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            trows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                # 单元格里允许 \| 转义（来源标记常用），先保护再按未转义的 | 分列
                raw = lines[i].strip().strip("|").replace("\\|", "\x00")
                cells = [c.strip().replace("\x00", "|") for c in re.sub(r"\[source:[^\]]*\]", lambda m: m.group().replace("|", "\x00"), raw).split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                    trows.append(cells)
                i += 1
            rows = [[runs_from_inline(c, mode, strip_sources) for c in row] for row in trows]
            body.append(table(rows, mode))
            continue
        # 模板填写指引行：只给起草人看，绝不进入交付文件
        if s.startswith("#!"):
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            i += 1
            continue
        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            lvl, htxt = len(m.group(1)), m.group(2).strip()
            if lvl == 1:
                base = runs_from_inline(htxt, mode, strip_sources)
                title_runs = [dict(r_, b=True, sz=28, cjk="NONE") for r_ in base]
                body.append(para(title_runs, jc="center", keep_next=True,
                                 space_before=0, space_after=240, line=360))
                cur_path = [htxt]
            else:
                style = {2: "Heading1", 3: "Heading2", 4: "Heading3"}[lvl]
                heads.append((lvl - 1, re.sub(r"\*\*", "", htxt)))
                cur_path = cur_path[:lvl - 2] + [re.sub(r"\*\*", "", htxt)]
                runs = runs_from_inline(htxt, mode, strip_sources)
                f = FONTS[mode]
                body.append(para([dict(r_, b=True, cjk=f["cjk_head"]) for r_ in runs], style=style, keep_next=True,
                                 space_before=240 if lvl == 2 else 160, space_after=100, line=360))
            i += 1
            continue
        # 引用块 → 缩进不编号
        if s.startswith(">"):
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            txt = s[1:].strip()
            runs = runs_from_inline(txt, mode, strip_sources)
            body.append(para(runs, ind_left=720, hanging=0, jc="left", space_before=60,
                             space_after=120, line=300))
            i += 1
            continue
        # 分隔线
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            body.append(hrule())
            i += 1
            continue
        # 编号段落：显式 "12. " 或 legal 模式默认编号
        mnum = re.match(r"^\d+[.]?\s+(.*)$", s)
        if s.startswith("~ "):
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            flush_par([s[2:].strip()], False, False)
            i += 1
            continue
        if s.startswith("- ") or s.startswith("* "):
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
                pending, pending_kind = [], None
            flush_par([s[2:].strip()], False, True)
            i += 1
            continue
        if mnum:
            if mode in ("memo", "board"):
                # 内部件沿用作者手写的序号，不转自动编号
                if pending and pending_kind:
                    flush_par(pending, pending_kind == "num", pending_kind == "bul")
                    pending, pending_kind = [], None
                flush_par([s], False, False)
                i += 1
                continue
            # 作者手写的编号：改为 Word 自动编号，避免双重编号
            if pending and pending_kind:
                flush_par(pending, pending_kind == "num", pending_kind == "bul")
            pending, pending_kind = [mnum.group(1)], "num"
            i += 1
            continue
        # 普通段落
        if pending and pending_kind == "num":
            pending.append(s)
            i += 1
            continue
        if pending and pending_kind == "bul":
            pending.append(s)
            i += 1
            continue
        pending, pending_kind = [s], ("num" if body_mode == "legal" else "raw")
        if pending_kind == "raw":
            flush_par(pending, False, False)
            pending, pending_kind = [], None
        i += 1
    if pending and pending_kind:
        flush_par(pending, pending_kind == "num", pending_kind == "bul")
    return "".join(body), manifest, placeholders, heads, n


# ───────────────────────────── 部件生成 ─────────────────────────────
def styles_xml(mode: str):
    f = FONTS[mode]
    cjk_h = f["cjk_head"]
    sz = f["size"]
    line = 360
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {XMLNS}>
<w:docDefaults>
<w:rPrDefault><w:rPr><w:rFonts w:ascii="{f["latin"]}" w:hAnsi="{f["latin"]}" w:eastAsia="{f["cjk_body"]}" w:cs="{f["latin"]}"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/><w:kern w:val="2"/><w:lang w:val="en-GB" w:eastAsia="zh-CN" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:widowControl/><w:spacing w:before="0" w:after="120" w:line="{line}" w:lineRule="auto"/><w:jc w:val="{"both" if mode == "legal" else "left"}"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/><w:jc w:val="left"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:rFonts w:ascii="{f["latin"]}" w:hAnsi="{f["latin"]}" w:eastAsia="{cjk_h}"/><w:b/><w:bCs/><w:sz w:val="{sz + 2}"/><w:szCs w:val="{sz + 2}"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:rFonts w:ascii="{f["latin"]}" w:hAnsi="{f["latin"]}" w:eastAsia="{cjk_h}"/><w:b/><w:bCs/><w:i/><w:iCs/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr><w:rFonts w:ascii="{f["latin"]}" w:hAnsi="{f["latin"]}" w:eastAsia="{cjk_h}"/><w:b/><w:bCs/></w:rPr></w:style>
<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="1155CC"/><w:u w:val="single"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Header"><w:name w:val="header"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="0" w:right="0"/><w:jc w:val="center"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="footer"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
</w:styles>'''


def numbering_xml(mode: str):
    f = FONTS[mode]
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering {XMLNS}>
<w:abstractNum w:abstractNumId="0">
<w:multiLevelType w:val="singleLevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
<w:rPr><w:rFonts w:ascii="{f["latin"]}" w:hAnsi="{f["latin"]}" w:eastAsia="{f["cjk_body"]}"/><w:b w:val="0"/></w:rPr></w:lvl>
</w:abstractNum>
<w:abstractNum w:abstractNumId="1">
<w:multiLevelType w:val="singleLevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#183;"/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="1080" w:hanging="360"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr></w:lvl>
</w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>'''


def header_xml(left: str, right: str, strip_sources: bool = False):
    if strip_sources:
        left = SRC_RE.sub("", left)
        right = SRC_RE.sub("", right)
    p1 = para([_run_factory(text=left)] if left else [_run_factory(text="")], style="Header",
              p_bdr_bottom=True, space_after=0, line=240)
    p2 = para([_run_factory(text=right)] if right else [_run_factory(text="")], style="Header",
              jc="center", space_before=40, space_after=0, line=240)
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {XMLNS}>{p1}{p2}</w:hdr>'


def footer_xml(left: str, strip_sources: bool = False):
    if strip_sources:
        left = SRC_RE.sub("", left)
    runs = [_run_factory(text=left + "    "), _run_factory(text="Page ")] if left else [_run_factory(text="Page ")]
    p = para(runs, style="Footer", jc="center", space_after=0, line=240)
    # 用字段拼接：Page X of Y
    inner = fld("PAGE", "memo", sz=18)
    inner2 = fld("NUMPAGES", "memo", sz=18)
    p = (f'<w:p><w:pPr><w:pStyle w:val="Footer"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
         f'<w:jc w:val="center"/></w:pPr>'
         + (f'<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t xml:space="preserve">{_xml_escape(left)}    </w:t></w:r>' if left else "")
         + '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t xml:space="preserve">Page </w:t></w:r>'
         + inner
         + '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t xml:space="preserve"> of </w:t></w:r>'
         + inner2 + "</w:p>")
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {XMLNS}>{p}</w:ftr>'


def document_xml(body: str, has_header: bool, has_footer: bool):
    refs = ""
    rid = 4
    if has_header:
        refs += f'<w:headerReference w:type="default" r:id="rId{rid}"/>'
        rid += 1
    if has_footer:
        refs += f'<w:footerReference w:type="default" r:id="rId{rid}"/>'
    w, h = PAGES["A4"]
    sect = ('<w:sectPr>' + refs +
            f'<w:pgSz w:w="{w}" w:h="{h}"/>'
            f'<w:pgMar w:top="{MARGINS["top"]}" w:right="{MARGINS["right"]}" w:bottom="{MARGINS["bottom"]}" '
            f'w:left="{MARGINS["left"]}" w:header="{MARGINS["header"]}" w:footer="{MARGINS["footer"]}" w:gutter="0"/>'
            '<w:cols w:space="708"/><w:docGrid w:linePitch="360"/></w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document {XMLNS}><w:body>{body}{sect}</w:body></w:document>')


def rels_xml(has_header, has_footer):
    items = [
        ("rId1", f"{R}/styles", "styles.xml"),
        ("rId2", f"{R}/numbering", "numbering.xml"),
        ("rId3", f"{R}/settings", "settings.xml"),
    ]
    n = 4
    if has_header:
        items.append((f"rId{n}", f"{R}/header", "header1.xml"))
        n += 1
    if has_footer:
        items.append((f"rId{n}", f"{R}/footer", "footer1.xml"))
    xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i, t, tg in items:
        xml.append(f'<Relationship Id="{i}" Type="{t}" Target="{tg}"/>')
    xml.append("</Relationships>")
    return "".join(xml)


def content_types_xml(has_header, has_footer):
    ov = ["/word/document.xml|application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
          "/word/styles.xml|application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
          "/word/numbering.xml|application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
          "/word/settings.xml|application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"]
    if has_header:
        ov.append("/word/header1.xml|application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml")
    if has_footer:
        ov.append("/word/footer1.xml|application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml")
    ov.append("/docProps/core.xml|application/vnd.openxmlformats-package.core-properties+xml")
    ov.append("/docProps/app.xml|application/vnd.openxmlformats-officedocument.extended-properties+xml")
    x = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
         '<Default Extension="xml" ContentType="application/xml"/>']
    for o in ov:
        p, c = o.split("|")
        x.append(f'<Override PartName="{p}" ContentType="{c}"/>')
    x.append("</Types>")
    return "".join(x)


def toc_block(mode: str):
    f = FONTS[mode]
    title = "TABLE OF CONTENTS" if mode == "legal" else "目 录"
    return (para([_run_factory(text=title, b=True, latin=f["latin"], cjk=f["cjk_head"])],
                 jc="center", keep_next=True, space_before=120, space_after=200, line=360)
            + '<w:p><w:pPr><w:spacing w:after="240" w:line="360" w:lineRule="auto"/></w:pPr>'
            + fld('TOC \\o "1-3" \\h \\z \\u', mode) + "</w:p>"
            + para([_run_factory(text="", sz=18)], page_break_before=True))


def settings_xml():
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:settings {XMLNS}>'
            f'<w:defaultTabStop w:val="720"/>'
            f'<w:characterSpacingControl w:val="compressPunctuation"/>'
            f'<w:updateFields w:val="true"/>'
            f'<w:compat>'
            f'<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
            f'</w:compat>'
            f'</w:settings>')


def core_xml(title: str, creator: str):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(title)}</dc:title><dc:creator>{escape(creator)}</dc:creator>'
            f'<cp:lastModifiedBy>{escape(creator)}</cp:lastModifiedBy>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')


def app_xml():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            '<Application>commercial-arbitration-suite/render_docx</Application><DocSecurity>0</DocSecurity>'
            '<ScaleCrop>false</ScaleCrop></Properties>')


def root_rels():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            "</Relationships>")


# ───────────────────────────── 主流程 ─────────────────────────────
def render(inp: Path, outp: Path, mode=None, strip_sources=False, manifest_path=None,
           strict=False, toc=None, header_text=None, footer_text=None, creator="", draft=False, pending_path=None):
    if not inp.exists():
        raise RenderError(f"输入文件不存在: {inp}")
    try:
        text = inp.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise RenderError(f"输入文件含非法UTF-8: {e}")
    if inp.resolve() == outp.resolve():
        raise RenderError("输入和输出路径不能相同")
    if outp.suffix.lower() != ".docx":
        raise RenderError("输出扩展名必须为 .docx")
    manifest_path = Path(manifest_path) if manifest_path else outp.with_suffix(".paras.json")
    if manifest_path.resolve() in (inp.resolve(), outp.resolve()):
        raise RenderError("manifest 不能覆盖输入或 DOCX")
    meta, body_text = split_front_matter(text)
    if draft:
        from pending import load, validate_text, BANNER
        if strict or not pending_path:
            raise RenderError('--draft 需要 --pending，不能同时 --strict')
        data, entries = load(pending_path)
        if str(meta.get('case', '')) != data['case']:
            raise RenderError('记稿 frontmatter case 须与 pending 案件代号一致')
        relative = str(inp.resolve())
        validate_text(text, relative, entries)
        if header_text and '[[' in header_text or footer_text and '[[' in footer_text:
            raise RenderError('草案页眉页脚占位须写入记稿，不用 CLI 覆盖')
    elif pending_path:
        raise RenderError('--pending 仅与 --draft 一起使用')
    mode = mode or meta.get("mode") or "legal"
    if mode not in FONTS:
        raise RenderError(f"未知 mode={mode}，可选 legal|memo|board")
    if mode == 'board':
        from verify_suite import check_board_sections
        issues = check_board_sections(body_text)
        if issues:
            raise RenderError('董事会简报五节结构不完整：' + '；'.join(issues))
    if strict and ('锚点' in body_text or meta.get('workflow') or meta.get('matrix')):
        from verify_suite import render_anchor_check
        issues = render_anchor_check(inp, dict(meta, mode=mode), body_text)
        if issues:
            raise RenderError('；'.join(issues))
    if mode == "legal" and str(meta.get("keep_sources", "")).lower() not in ("true", "1", "yes"):
        strip_sources = True
    want_toc = (toc if toc is not None else str(meta.get("toc", "")).lower() in ("true", "1", "yes"))

    body, manifest, placeholders, heads, n = parse_and_build(body_text, mode, strip_sources)
    if draft:
        body = para([_run_factory(BANNER, b=True)], style="Normal") + body
    if want_toc:
        body = toc_block(mode) + body

    title = meta.get("title") or (heads[0][1] if heads else outp.stem)
    case = meta.get("case") or ""
    h_left = header_text if header_text is not None else case
    h_right = ""
    f_left = footer_text if footer_text is not None else meta.get("footer_left", "")
    has_header = bool(h_left) or bool(h_right)
    has_footer = bool(f_left) or True
    for _hf_text in (h_left, h_right, f_left):
        if not _hf_text:
            continue
        for _m in PLACEHOLDER_RE.finditer(_hf_text):
            _ph = _m.group(1)[:80]
            if _ph not in set(placeholders):
                placeholders.append(_ph)
        for _m in UNCLOSED_PH_RE.finditer(_hf_text):
            _tail = _hf_text[_m.start():_m.start()+80]
            if _tail not in set(placeholders):
                placeholders.append(_tail)

    parts = {
        "[Content_Types].xml": content_types_xml(has_header, has_footer),
        "_rels/.rels": root_rels(),
        "word/document.xml": document_xml(body, has_header, has_footer),
        "word/_rels/document.xml.rels": rels_xml(has_header, has_footer),
        "word/styles.xml": styles_xml(mode),
        "word/numbering.xml": numbering_xml(mode),
        "word/settings.xml": settings_xml(),
        "docProps/core.xml": core_xml(title, creator or "commercial-arbitration-suite"),
        "docProps/app.xml": app_xml(),
    }
    if has_header:
        parts["word/header1.xml"] = header_xml(h_left, h_right, strip_sources)
    if has_footer:
        parts["word/footer1.xml"] = footer_xml(f_left or (case if mode == "legal" else ""), strip_sources)

    if strict and placeholders:
        summary = {"decision": "STRICT_FAIL", "docx": str(outp), "mode": mode,
                   "paragraphs": n, "placeholders": len(placeholders),
                   "sources_kept": not strip_sources,
                   "source_markers_in_source_file": len(SRC_RE.findall(body_text))}
        summary["placeholder_items"] = placeholders[:20]
        summary["action"] = "存在未填占位符，--strict 模式下不写出文件；逐项替换后重新渲染"
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 3

    outp.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=outp.parent, suffix=".tmp")
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in parts.items():
                z.writestr(name, data)
        os.replace(tmp, outp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    if manifest_path:
        Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
        Path(manifest_path).write_text(json.dumps(
            {"source": os.path.relpath(inp.resolve(), manifest_path.resolve().parent), "docx": os.path.relpath(outp.resolve(), manifest_path.resolve().parent), "source_sha256": hashlib.sha256(inp.read_bytes()).hexdigest(),
             "docx_sha256": hashlib.sha256(outp.read_bytes()).hexdigest(), "pair": str(meta.get("pair", "true")).lower() != "false", "mode": mode, "numbered_paragraphs": n,
             "headings": [{"level": l, "text": t} for l, t in heads],
             "paragraphs": manifest, "placeholders": placeholders,
             "case": case, "delivery_state": "draft" if draft else "submission",
             "workflow": meta.get('workflow'), "profile": meta.get('profile'), "matrix": meta.get('matrix'),
             "pagination_verified": False,
             "pending_sha256": hashlib.sha256(Path(pending_path).read_bytes()).hexdigest() if draft else None},
            ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"decision": "RENDERED", "docx": str(outp), "mode": mode,
               "paragraphs": n, "placeholders": len(placeholders),
               "sources_kept": not strip_sources,
               "source_markers_in_source_file": len(SRC_RE.findall(body_text)),
               "bytes": outp.stat().st_size}
    if mode == 'board':
        summary['pagination_verified'] = False
        summary['limitation'] = '仅验证五节结构；未保证一页。须实际转PDF并视觉检查分页；不会裁掉超长内容。'
    if placeholders:
        summary["placeholder_items"] = placeholders[:20]
        summary["action"] = "交付前逐项补充并核验占位；用户同意不能替代法律或来源核验，重新渲染后运行交付检查"
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="outp", required=True)
    ap.add_argument("--mode", choices=["legal", "memo", "board"])
    ap.add_argument("--strip-sources", action="store_true", help="删除 [source:...] 标记（对外交付版建议开启）")
    ap.add_argument("--manifest", help="输出段落编号清单 JSON，供交叉引用核验")
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--pending", help="待确认登记 JSON")
    ap.add_argument("--strict", action="store_true", help="存在未填占位符时以退出码 3 失败")
    ap.add_argument("--header", dest="header_text")
    ap.add_argument("--footer", dest="footer_text")
    ap.add_argument("--creator", default="")
    a = ap.parse_args()
    try:
        return render(Path(a.inp), Path(a.outp), a.mode, a.strip_sources, a.manifest,
                      a.strict, True if a.toc else None, a.header_text, a.footer_text, a.creator, a.draft, a.pending)
    except (RenderError, OSError, ValueError, zipfile.BadZipFile) as e:
        print(json.dumps({"decision": "ERROR", "detail": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
