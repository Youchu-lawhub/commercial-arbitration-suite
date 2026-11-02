#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付前质检：把"配对、占位符、引用、跨文书一致、Word 结构"五类硬伤挡在交付之前。

铁律 2/3/5 的执行器。每轮交付前运行，未通过项必须回到对应子技能修补，不得口头解释后放行。

用法：
  python3 verify_suite.py --workdir <案件目录> --mode submission
  python3 verify_suite.py --workdir <案件目录> --mode draft --pending <pending.json>
  python3 verify_suite.py --workdir <案件目录> --pairs "RFA.docx:RFA-中文审阅说明.md"
  python3 verify_suite.py --selftest        # 用内置样例验证本脚本与 render_docx 可用

检查项：
  PAIR      非中文 .docx 文书须有配套《中文审阅说明》（.md/.docx 均可）且说明含五节固定结构；正文本身为中文的文书按语言豁免，不另出说明
  DELIVERY  仅提交模式：配套《中文审阅说明》不得只有 .md 记稿，须与文书一并交付 .docx，且须登记交付清单与视觉复核
  FILL      文书中不得残留 [[占位符]]（Word 内黄底高亮或记稿内 [[...]]）
  CITE      说明文件里的规则/指引引用必须带 [source:...] 标记；正文条号须在说明中对应说明；条文内容和适用性另作人工核对
  XREF      文书内 "paragraph N" 交叉引用不超过实际编号段落数（依赖 render_docx 的 .paras.json 清单）
  CONSIST   配对文书之间：当事人名称、争议金额、关键日期、请求项数量一致
  DIALECT   记稿占位符必须单层、行内闭合（嵌套或跨行会让高亮区间切错并漏出方括号）
  DOCX      .docx 结构完整（必备部件齐全；有 xmllint 时按 OOXML schema 校验；有 python-docx 时试读）
退出码：0 全部通过 / 2 存在必须修补的问题 / 3 目录或参数错误
"""
from __future__ import annotations

from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import hashlib
import posixpath
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from _markers import iter_markers, parse_source_marker, source_marker_issues as _source_marker_issues

CJK_NOTE_MARK = ("中文审阅说明", "审阅说明", "-note")
PLACEHOLDER_RE = re.compile(r"\[\[(.*?)\]\]", re.S)
PARA_REF_RE = re.compile(
    r"(?:paragraphs?|para\.?|段落)\s*"
    r"(\d[\d,]*|[IVXLCDM]+|[一二三四五六七八九十百千]+)"
    r"(?:\s|$|[,.\u3002])|"
    r"第\s*(\d+)\s*段", re.I)


def para_ref_findall(text: str) -> list:
    results = []
    for m in PARA_REF_RE.finditer(text):
        if m.group(2) and re.search(r'(?:裁决书|裁决)$', text[:m.start()]):
            continue
        val = m.group(1) or m.group(2)
        if val:
            results.append(val)
    return results
RULE_RE = re.compile(
    r"(?:Rule|rule)\s+\d+[°\s]?(?:\([a-z]\))?|"
    r"Art\.?\s*\d+|Article\s+\d+|"
    r"条文\s*\d+|第\s*\d+\s*条", re.I)
BODY_RULE_RE = re.compile(r"(?:Rule|rule|Art\.?|Article)\s+(\d+)", re.I)
DEADLINE_DAYS_RE = re.compile(r"(\d+)\s*(?:days?|日|天)", re.I)
# Calendar dates end in 日/号, so they would otherwise be read as deadline lengths.
CALENDAR_DATE_TEXT_RE = re.compile(r"\d{4}\s*年\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*[日号])?|\d{4}-\d{2}-\d{2}")
RELIEF_COUNT_RE = re.compile(r"(\d+)\s*(?:项|个)\s*(?:请求|救济|relief|remedy|prayer)", re.I)
RELIEF_ITEMS_RE = re.compile(r"(?:relief\s*sought|请求.*?项|prayer|仲裁请求)\s*[:：]?\s*(\d+)", re.I)
AMOUNT_RE = re.compile(r"((?:USD|EUR|GBP|RMB|CNY|HKD|SGD|JPY|S\$|HK\$|US\$|€|\$|￥)\s?[\d,]+(?:\.\d+)?(?:\s?(?:million|billion|m\b|bn\b))?)", re.I)
DATE_RE = re.compile(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b|"
                     r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s+\d{1,2}\s+\d{4}\b")
CAPTION_RE = re.compile(r"([A-Z][A-Za-z0-9&'.\- ]{2,60}?)\s+(?:v\.\s+|v\s+(?=[A-Z])|versus\s+)([A-Z][A-Za-z0-9&'.\- ]{2,60}?)(?=[,.\u3002\uff1a\)]|\s*$)", re.M)
PARTY_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?(Claimant|Respondent|Applicant|Respondent\s*Party|申请人|被申请人)\s*[:：]\s*(.+)$", re.M)
NOTE_SECTIONS = ["本文件作用与程序依据", "逐段填写要点", "我方立场与可选表述", "风险与待用户确认事项", "给管理层的三句话汇报"]
REQUIRED_PARTS = ["[Content_Types].xml", "_rels/.rels", "word/document.xml",
                  "word/_rels/document.xml.rels", "word/styles.xml", "word/numbering.xml",
                  "word/settings.xml"]
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

SUITE_ROOT = Path(__file__).resolve().parent.parent
# Schema discovery must follow the runtime environment: an explicit WML_XSD override or the
# canonical sibling docx skill under $HOME. No __file__-absolute root — it would survive an
# isolated HOME and defeat the honest xmllint+OOXML vs part-only downgrade label.
SCHEMA_ROOTS = [Path(p) for p in [os.environ.get("WML_XSD", ""),
                                  str(Path.home() / ".qoder" / "skills")] if p]
PLACEHOLDER_HOSTS = ("localhost", "127.0.0.1", "example.com", "example.org", "example.net")
_REGISTRY_IDS = None


def registry_ids() -> set:
    global _REGISTRY_IDS
    if _REGISTRY_IDS is not None:
        return _REGISTRY_IDS
    ids = set()

    def walk(node):
        if isinstance(node, dict):
            sid = node.get("id")
            if isinstance(sid, str) and sid.strip():
                ids.add(sid.strip())
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    try:
        for name in ("sources-registry.json", "research-sources.json"):
            walk(json.loads((SUITE_ROOT / "assets" / name).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        ids = set()
    _REGISTRY_IDS = ids
    return ids


def registry_urls():
    result = {}
    keys = ('download', 'download_en', 'pdf', 'pdf_zh', 'pdf_en', 'pdf_url',
            'landing', 'landing_en', 'url', 'canonical_url')
    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get('id'), str):
                result.setdefault(node['id'], set()).update(v for k,v in node.items() if k in keys and isinstance(v,str) and v.startswith(('http://','https://')))
            for v in node.values(): walk(v)
        elif isinstance(node,list):
            for v in node: walk(v)
    for name in ('sources-registry.json','research-sources.json'):
        walk(json.loads((SUITE_ROOT/'assets'/name).read_text(encoding='utf-8')))
    return result

def load_registry() -> dict:
    merged = {}
    for name in ('sources-registry.json', 'research-sources.json'):
        path = SUITE_ROOT / 'assets' / name
        if path.is_file():
            try:
                merged[name] = json.loads(path.read_text(encoding='utf-8'))
            except ValueError:
                continue
    return merged

def citation_url_issue(sid, url):
    from urllib.parse import urlsplit
    def key(u):
        p=urlsplit(u);return ((p.hostname or '').lower(), p.path.rstrip('/') or '/')
    urls=registry_urls(); target=key(url); own=urls.get(sid,set())
    if any(target==key(u) for u in own):return None
    def prefix(a,b):
        return a==b or a=='/' or b=='/' or a.startswith(b+'/') or b.startswith(a+'/')
    if any(target[0]==key(u)[0] and prefix(target[1],key(u)[1]) for u in own):return None
    owners=[i for i,us in urls.items() if i!=sid and any(target==key(u) for u in us)]
    if owners:
        return f'来源 id 与 URL 不匹配：{sid} 的登记 URL 为 {sorted(own)}，该 URL 属于另一 id {owners}'
    return f'WARN 来源 URL 未与 {sid} 登记地址匹配，须人工核对：{url}'

def source_marker_issues(marker: str, valid_ids: set) -> list:
    return _source_marker_issues(marker, valid_ids, citation_url_issue)



def docx_text(p: Path) -> str:
    try:
        with zipfile.ZipFile(p) as z:
            parts = [n for n in z.namelist()
                     if n == "word/document.xml" or re.fullmatch(r"word/(header|footer)\d*\.xml", n)]
            xml = "\n".join(z.read(n).decode("utf-8", "ignore") for n in parts)
    except Exception:
        return ""
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n", xml)
    import html
    text = html.unescape(re.sub(r"<[^>]+>", "", xml))
    text = re.sub(r"Page\s+PAGE\s+\d+\s+of\s+NUMPAGES\s+\d+", "", text)
    text = re.sub(r"\d+\s+/\s*\d+", "", text)
    return text


def docx_all_text_parts(p: Path) -> dict:
    try:
        with zipfile.ZipFile(p) as z:
            result = {}
            for n in z.namelist():
                if n == "word/document.xml" or re.fullmatch(r"word/(header|footer)\d*\.xml", n):
                    result[n] = z.read(n).decode("utf-8", "ignore")
            return result
    except Exception:
        return {}


_YELLOW_RE = re.compile(r'<w:highlight\s[^>]*w:val\s*=\s*"yellow"\s*/?>', re.I)


def docx_has_placeholder(p: Path) -> list:
    issues = []
    try:
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n == "word/document.xml" or re.fullmatch(r"word/(header|footer)\d*\.xml", n):
                    xml = z.read(n).decode("utf-8", "ignore")
                    if _YELLOW_RE.search(xml):
                        issues.append(n)
    except Exception:
        pass
    return issues


def md_has_placeholder(p: Path) -> list:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    found = []
    for m in PLACEHOLDER_RE.finditer(text):
        found.append(m.group(1)[:60])
    return found


def find_schema() -> Path | None:
    for root in SCHEMA_ROOTS:
        if root.is_file():
            return root
        for pat in ("*/openxml/schemas/*/wml.xsd", "*/assets/schemas/*/wml.xsd", "*/schemas/*/wml.xsd"):
            for h in sorted(root.glob(pat)):
                if h.exists():
                    return h
    return None


def check_docx_structure(p: Path, schema: Path | None) -> list:
    issues = []
    try:
        with zipfile.ZipFile(p) as z:
            names = set(z.namelist())
            bad = z.testzip()
            if bad:
                issues.append(f"{p.name}: ZIP 损坏于 {bad}")
            missing = [r for r in REQUIRED_PARTS if r not in names]
            if missing:
                issues.append(f"{p.name}: 缺少必需部件 {missing}")
            for n in names:
                if n.endswith(".xml") or n.endswith(".rels"):
                    try:
                        root = ET.fromstring(z.read(n))
                        if n == "word/document.xml":
                            root_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
                            if root_tag != "document":
                                issues.append(f"{p.name}: document.xml 根元素为 '{root_tag}' 而非 'document'")
                    except ET.ParseError as e:
                        issues.append(f"{p.name}: 部件 {n} XML 解析失败：{e}")
            rels_path = "word/_rels/document.xml.rels"
            if rels_path in names:
                try:
                    rels_xml = ET.fromstring(z.read(rels_path))
                    for rel in rels_xml.findall(f"{{{REL_NS}}}Relationship"):
                        target = rel.get("Target", "")
                        if target and rel.get("TargetMode") != "External":
                            resolved = posixpath.normpath(f"word/{target}") if not target.startswith("/") else target.lstrip("/")
                            if resolved not in names:
                                issues.append(f"{p.name}: 关系 Target '{target}' 在包中不存在")
                except ET.ParseError:
                    pass
    except zipfile.BadZipFile:
        return [f"{p.name}: 不是有效的 .docx（zip）文件"]
    if schema and subprocess_has("xmllint"):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(p) as z:
                for member in z.namelist():
                    target = (Path(td) / member).resolve()
                    try:
                        target.relative_to(Path(td).resolve())
                    except ValueError:
                        return [f"{p.name}: ZIP 部件路径越界"]
                z.extractall(td)
            xmls = [n for n in names if n.endswith(".xml") and n.startswith("word/")]
            for part in xmls:
                f = Path(td) / part
                if not f.exists():
                    continue
                r = subprocess.run(["xmllint", "--noout", "--schema", str(schema), str(f)],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    msg = (r.stderr or r.stdout).strip().splitlines()
                    issues.append(f"{p.name} 部件 {part} 不符合 OOXML schema：{msg[0] if msg else '见 xmllint 输出'}")
    if not issues:
        try:
            import docx
        except ImportError:
            return issues
        try:
            docx.Document(str(p))
        except Exception as e:  # noqa: BLE001
            issues.append(f"{p.name}: python-docx 无法打开：{type(e).__name__}: {e}")
    return issues


def subprocess_has(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None


def is_note(path: Path) -> bool:
    return any(m in path.name for m in CJK_NOTE_MARK)


def norm(s: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s.lower())


def declared_parties(workdir: Path, doc_text: str) -> list:
    names = []
    cfg = workdir / ".arbitration-config.md"
    if cfg.exists():
        for m in PARTY_LINE_RE.finditer(cfg.read_text(encoding="utf-8", errors="ignore")):
            v = m.group(2).strip().strip("[]").strip()
            if v and not v.startswith("__") and len(v) > 2 and v not in names:
                names.append(v)
    for m in CAPTION_RE.finditer(doc_text):
        for g in m.groups():
            g = g.strip().rstrip(".,")
            if len(g) > 2 and g not in names:
                names.append(g)
    for m in PARTY_LINE_RE.finditer(doc_text):
        v = m.group(2).strip().rstrip(".,;")
        if v and len(v) > 2 and v not in names:
            names.append(v)
    return names


def check_note_sections(text: str) -> list:
    missing = []
    lines = text.split('\n')
    header_line_indices = []
    for i, line in enumerate(lines):
        stripped = line.strip().lstrip('#').strip()
        stripped = re.sub(r'^(?:[一二三四五六七八九十]+[、.．]|[0-9]+[.、])\s*', '', stripped)
        aliases = {'管理层三句话汇报': '给管理层的三句话汇报', '管理层摘要': '给管理层的三句话汇报', '风险与待确认事项': '风险与待用户确认事项', '文件作用与程序依据': '本文件作用与程序依据'}
        stripped = aliases.get(stripped, stripped)
        for s in NOTE_SECTIONS:
            if stripped == s or stripped.startswith(s):
                header_line_indices.append((i, s))
                break
    found_sections = [s for _, s in header_line_indices]
    for s in NOTE_SECTIONS:
        if s not in found_sections:
            if s in text:
                missing.append(f"{s}（未作为独立标题出现）")
            else:
                missing.append(s)
    prev_end = 0
    expected_order = [s for s in NOTE_SECTIONS if s in found_sections]
    for idx, (line_idx, s) in enumerate(header_line_indices):
        if idx > 0 and line_idx < prev_end:
            missing.append(f"{s}（顺序错乱）")
        prev_end = line_idx + 1
        if idx + 1 < len(header_line_indices):
            next_line = header_line_indices[idx + 1][0]
        else:
            next_line = len(lines)
        content_lines = lines[line_idx + 1:next_line]
        content_text = '\n'.join(content_lines).strip()
        if not content_text:
            missing.append(f"{s}（标题下无实质内容）")
    found_order = [s for _, s in header_line_indices]
    if found_order != expected_order and not missing:
        missing.append("五节顺序与规定不符")
    return missing


def lint_dialect(files) -> list:
    out = []
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").split("\n")
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if s.startswith("#!") or s.startswith("---"):
                continue
            if line.count("[[") != line.count("]]"):
                out.append(f"[DIALECT] {p.name}:{i} 占位符方括号不配对或跨行，渲染会切错高亮：{s[:50]}")
                continue
            for m in re.finditer(r"\[\[(.*?)\]\]", line):
                if "[[" in m.group(1) or "]]" in m.group(1):
                    out.append(f"[DIALECT] {p.name}:{i} 占位符嵌套（[[…[[…]]…]]），须拆成两个单层占位：{m.group(0)[:50]}")
    return out


def gather(workdir: Path):
    docs = sorted(p for p in workdir.rglob("*.docx") if not p.name.startswith("~$") and not is_note(p))
    notes = sorted(p for p in workdir.rglob("*") if p.suffix in (".md", ".docx") and is_note(p) and not p.name.startswith("~$"))
    return docs, notes


def pair_of(doc: Path, notes: list, used: set) -> Path | None:
    # Exact stem and same directory: A must not accidentally pair with A-ext or A2.
    candidates = [n for n in notes if n not in used and n.parent == doc.parent
                  and n.stem in (doc.stem + "-中文审阅说明", doc.stem + "-审阅说明", doc.stem + "-note")]
    candidates.sort(key=lambda n: (n.suffix != ".docx", n.name))
    return candidates[0] if candidates else None


def flatten_text(text: str) -> str:
    """docx 抽取常把币种与数字拆到不同段落（SGD\\n1926000.00），金额/日期
    镜像比对前先折叠空白，消除跨行变体的假阳性。"""
    return re.sub(r"\s+", " ", text)


def normalize_amount(s: str) -> str:
    s = s.strip().upper().replace(",", "").replace(" ", "")
    return s


_ROMAN_MAP = [('M', 1000), ('D', 500), ('C', 100), ('L', 50), ('X', 10), ('V', 5), ('I', 1)]

_CN_DIGITS = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
              '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9}
_CN_UNITS = {'十': 10, '百': 100, '千': 1000, '拾': 10, '佰': 100, '仟': 1000}


def para_ref_to_int(s: str) -> int | None:
    s = s.strip()
    if re.fullmatch(r'\d[\d,]*', s):
        return int(s.replace(",", ""))
    if re.fullmatch(r'[IVXLCDM]+', s, re.I):
        s_upper = s.upper()
        result = 0
        for i, (numeral, value) in enumerate(_ROMAN_MAP):
            while s_upper.endswith(numeral) or (numeral in s_upper):
                idx = s_upper.find(numeral)
                if idx == -1:
                    break
                next_val = 0
                for n2, v2 in _ROMAN_MAP:
                    if idx + len(numeral) <= s_upper.find(n2, idx + len(numeral)) if n2 in s_upper[idx + len(numeral):] else False:
                        next_val = max(next_val, v2)
                break
        result = 0
        prev = 0
        for ch in reversed(s_upper):
            val = dict(_ROMAN_MAP).get(ch, 0)
            if val < prev:
                result -= val
            else:
                result += val
            prev = val
        return result if result > 0 else None
    if all(c in _CN_DIGITS or c in _CN_UNITS for c in s):
        result = 0
        current = 0
        for c in s:
            if c in _CN_DIGITS:
                current = _CN_DIGITS[c]
            elif c in _CN_UNITS:
                if current == 0:
                    current = 1
                result += current * _CN_UNITS[c]
                current = 0
        result += current
        return result if result > 0 else None
    return None


def normalize_date(value):
    from datetime import datetime
    for fmt in ('%Y-%m-%d', '%d %B %Y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value  # ambiguous numeric dates remain unresolved


def extract_amounts(text: str) -> list:
    text = flatten_text(text)
    # docx 抽取会把千分位逗号后的数字换行/加空格（1, 926,000.00）；先拼回再匹配
    text = re.sub(r"(?<=\d),\s+(?=\d)", ",", text)
    raw = AMOUNT_RE.findall(text)
    raw = [re.sub(r"^(S\$|HK\$|US\$|RMB)", lambda m: {"S$":"SGD", "HK$":"HKD", "US$":"USD", "RMB":"CNY"}[m.group().upper()], a, flags=re.I) for a in raw]
    return [normalize_amount(a) for a in raw]


def docx_count_numbered_paras(p: Path) -> int:
    try:
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        import re as _re
        paras = _re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, _re.DOTALL)
        count = sum(1 for p in paras if '<w:numId w:val="1"/>' in p)
        return count
    except Exception:
        return 0


def count_relief_items(text: str) -> int:
    cn_num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                  '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
                  '两': '2'}
    patterns = [
        re.compile(r"(?:relief|remedy|prayer|请求|仲裁请求|救济)\s*[:：]?\s*(\d+)", re.I),
        re.compile(r"(\d+)\s*(?:项|个)\s*(?:请求|救济|relief|remedy)", re.I),
        re.compile(r"(?:请求|救济)\s*(?:项|个)\s*共\s*([一二三四五六七八九十两\d])", re.I),
        re.compile(r"共\s*([一二三四五六七八九十两\d])\s*(?:项|个)", re.I),
    ]
    for p in patterns:
        m = p.search(text)
        if m:
            val = m.group(1)
            return int(cn_num_map.get(val, val))
    relief_heading = re.search(r'(?:relief\s*sought|prayer|仲裁请求)\s*\n', text, re.I)
    if relief_heading:
        after = text[relief_heading.end():]
        items = re.findall(r'^\d+[\.\)]\s+', after, re.M)
        if items:
            return len(items)
    return 0


def internal_document(path):
    try:
        from pending import source_path
        from render_docx import split_front_matter
        mp=path.with_suffix('.paras.json');manifest=json.loads(mp.read_text(encoding='utf-8'))
        if manifest.get('pair') is not False:return False
        source=source_path(mp,manifest)
        if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest.get('source_sha256') or hashlib.sha256(path.read_bytes()).hexdigest()!=manifest.get('docx_sha256'):return False
        meta,_=split_front_matter(source.read_text(encoding='utf-8'))
        return str(meta.get('pair','true')).lower()=='false'
    except (OSError,ValueError,KeyError):return False


CJK_SHARE = 0.5


def chinese_document(path):
    """铁律 5 解决的是"读不懂"：文书本身以中文撰写时无需再配中文审阅说明。"""
    text = docx_text(path) if path.suffix.lower() == '.docx' else path.read_text(encoding='utf-8', errors='replace')
    cjk = len(re.findall(r'[㐀-䶿一-鿿]', text))
    latin = len(re.findall(r'[A-Za-z]', text))
    return cjk >= 40 and cjk / (cjk + latin) >= CJK_SHARE

BOARD_SECTIONS = {
    'decision': ('决策事项', '需要决策什么', '决策请求', '本次决策', 'decision'),
    'options': ('可选方案', '方案比较', '选项', 'options'),
    'costs': ('成本与预算', '费用与预算', '预算', '成本', 'costs'),
    'risks': ('主要风险', '风险与未知', '风险', 'risks'),
    'recommendation': ('建议与下一步', '建议', 'recommendation'),
}
MATRIX_FILES = {'case': ('case_matrix', 'case-matrix.yaml'),
                'clause': ('clause_audit', 'clause-audit.yaml'),
                'enforcement': ('enforcement_matrix', 'enforcement-plan.yaml')}
ANCHOR_ID = re.compile(r'(?:F-\d+|CL-\d+|DF-\d+|E-[A-Z0-9]+-\d+|EV-\d+|R-\d+|A-\d+)')
DISPUTE_WORKFLOWS = {'04-commencement', '05-defence', '08-evidence', '09-hearing'}


def check_board_sections(text):
    headings = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.match(r'^\s*#{1,4}\s+', line):
            continue
        title = re.sub(r'^\s*#+\s*(?:[一二三四五六七八九十\d]+[、.．)）]\s*)?', '', line).strip().lower()
        key = next((key for key, aliases in BOARD_SECTIONS.items() if any(title == a or title.startswith(a + '（') or title.startswith(a + '：') for a in aliases)), None)
        headings.append((index, key))
    found = []
    errors = []
    for pos, (index, key) in enumerate(headings):
        if not key:
            continue
        found.append(key)
        end = headings[pos + 1][0] if pos + 1 < len(headings) else len(lines)
        if not any(s.strip() and not s.strip().startswith('#!') for s in lines[index + 1:end]):
            errors.append(key + ' 标题下无内容')
    for key in BOARD_SECTIONS:
        if found.count(key) != 1:
            errors.append(key + ' 须有且仅有一个独立标题')
    if len(found) == 5 and found != list(BOARD_SECTIONS):
        errors.append('五节顺序应为 decision/options/costs/risks/recommendation')
    return errors


def known_anchor_ids(data):
    ids = set()
    if isinstance(data, dict):
        if isinstance(data.get('id'), str) and ANCHOR_ID.fullmatch(data['id']):
            ids.add(data['id'])
        for key, value in data.items():
            if isinstance(key, str) and ANCHOR_ID.fullmatch(key):
                ids.add(key)
            ids.update(known_anchor_ids(value))
    elif isinstance(data, list):
        for value in data:
            ids.update(known_anchor_ids(value))
    return ids


def check_anchors(text, known, require=False, label=None, offset=0):
    """Anchors precede prose paragraphs; titles/tables/letters need no blanket anchors."""
    from _anchors import scan
    result = scan(text, require=require, known=known)
    errors = []
    where = (label + ' ') if label else ''
    text_of = {
        'syntax': '锚点语法无效；使用 #! 锚点：F-001 / E-CL01-01 / EV-001 / R-01 / A-01',
        'order': '锚点分组须按 F/CL/DF/E/EV/R/A 顺序',
        'not_attached': '锚点未挂接正文段落',
        'not_adjacent': '锚点须紧邻后续正文而非空行、标题或表格',
        'missing': '实质正文段落缺锚点',
        'dangling': '悬空锚点',
    }
    for line in sorted(result['issues']):
        for issue in result['issues'][line]:
            if issue['kind'] == 'unknown':
                errors.append(f'[ANCHOR] {where}line {line + offset} 引用矩阵中不存在的ID：' + ', '.join(issue['ids']))
            else:
                errors.append(f'[ANCHOR] {where}line {line + offset} ' + text_of[issue['kind']])
    return errors


def workflow_kind(meta, text='', filename=''):
    workflow = str(meta.get('workflow') or '')
    if not workflow and meta.get('profile'):
        from route import PROFILE_HINTS
        candidates = [sid for sid, profiles in PROFILE_HINTS.items() if meta['profile'] in profiles]
        if len(candidates) == 1:
            workflow = candidates[0]
        elif meta['profile'] in ('answer','counterclaim','jurisdiction','production','witness','expert','hearing','post-hearing','case'):
            workflow = 'case'
    if workflow.startswith('02') or workflow in ('clause', 'clause-audit'):
        return 'clause'
    if workflow.startswith('14') or workflow in ('enforcement', 'cross-border-enforcement'):
        return 'enforcement'
    if workflow in DISPUTE_WORKFLOWS or workflow.startswith(('04-', '05-', '08-', '09-')) or workflow in ('case', 'case-construction'):
        return 'case'
    hint = str(meta.get('title', '')) + '\n' + filename + '\n' + '\n'.join(text.splitlines()[:4]) + '\n' + '\n'.join(line for line in text.splitlines() if line.startswith('# '))
    if re.search(r'仲裁申请书|答辩状|证人陈述|庭后简报|request for arbitration|answer to request|statement of (?:claim|defence)|witness statement|post-hearing brief', hint, re.I):
        return 'case'
    return None


def matrix_specs(meta, kind):
    matrix = meta.get('matrix')
    if matrix is None:
        return {kind: MATRIX_FILES[kind][1]} if kind else {}
    if isinstance(matrix, str):
        if matrix in MATRIX_FILES:
            result = {matrix: MATRIX_FILES[matrix][1]}
        else:
            inferred = next((k for k, (_, name) in MATRIX_FILES.items() if Path(matrix).name == name), kind)
            if not inferred:
                raise ValueError('matrix 自定义路径须同时声明 workflow')
            result = {inferred: matrix}
    elif isinstance(matrix, dict) and all(k in MATRIX_FILES and isinstance(v, str) and v.strip() for k, v in matrix.items()):
        result = dict(matrix)
    else:
        raise ValueError('matrix 须为路径或 case/clause/enforcement 到路径的映射')
    if kind and kind not in result:
        result[kind] = MATRIX_FILES[kind][1]
    return result


def resolve_matrix(workdir, source, value):
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        options = [workdir / candidate, source.parent / candidate]
        if str(candidate) in {entry[1] for entry in MATRIX_FILES.values()}:
            options.append(workdir / '案件档案' / candidate)
        candidate = next((p for p in options if p.is_file()), options[0])
    if candidate.is_symlink():
        raise ValueError('矩阵不得是符号链接')
    candidate = candidate.resolve()
    candidate.relative_to(workdir.resolve())
    return candidate


OUTPUT_TYPE_ALIASES = (
    ('仲裁申请书', ('仲裁申请书', 'request for arbitration', 'request-for-arbitration', 'notice of arbitration')),
    ('立案材料包', ('立案材料包', '送达方案')),
    ('费用测算', ('费用预缴测算', '费用测算', '预缴', '利息计算', 'interest', 'advance on costs')),
    ('审阅说明', ('中文审阅说明', '审阅说明')),
    ('立案指引', ('立案申请指引', '立案指引', 'filing-guide', 'filing_guide')),
    ('条款诊断', ('条款诊断', '条款体检', 'clause')),
    ('答辩状', ('答辩', 'answer to request', 'answer-to-request', 'answer')),
    ('反请求', ('反请求', 'counterclaim')),
    ('管辖异议', ('管辖异议', 'jurisdiction')),
    ('仲裁员', ('仲裁员', '提名', '挑战', 'nomination', 'challenge', 'disclosure')),
    ('临时措施', ('临时措施', '紧急', 'interim', 'urgent')),
    ('费用担保', ('费用担保', 'security for costs', 'security-for-costs')),
    ('披露', ('披露', 'document production', 'document-production', 'redfern')),
    ('证人', ('证人', 'witness')),
    ('专家', ('专家', 'expert')),
    ('庭审', ('庭审', 'hearing')),
    ('庭后', ('庭后', 'post-hearing')),
    ('裁决后', ('裁决', 'award', '更正', '解释', 'correction', 'interpretation', '和解', 'consent')),
    ('执行', ('执行', 'enforcement', 'set-aside', '撤销')),
    ('外部律师', ('外部律师', 'external counsel', 'external-counsel')),
    ('研究简报', ('研究', 'research', '简报', 'brief', '答案卡')),
    ('程序函', ('程序函', 'procedural letter', 'procedural-letter')),
    ('案件档案', ('案件档案', '案件构建矩阵', 'case-matrix', '主体信息', '主体')),
)


def output_type(text):
    low = str(text).lower()
    for token, aliases in OUTPUT_TYPE_ALIASES:
        if any(a in low for a in aliases):
            return token
    return None


def declared_output_types():
    from intake import safe_yaml
    data = safe_yaml((SUITE_ROOT / 'suite.yaml').read_text(encoding='utf-8')) or {}
    result = {}
    for sid, spec in (data.get('subskills') or {}).items():
        rows = spec.get('outputs') or []
        typed = [(row, output_type(row)) for row in rows]
        result[sid] = [(row, tok) for row, tok in typed if tok]
    return result


def output_completeness(workdir, docs, artifacts):
    """suite.yaml 声明产出 vs 本轮交付件；产出可以是另一份文件内的小节，故按类型与正文双通道匹配。"""
    from render_docx import split_front_matter
    declared = declared_output_types()
    if not declared:
        return []
    names = [p.name for p in artifacts]
    present = {t for t in (output_type(n) for n in names) if t}
    corpus = ' '.join(names)
    for path in artifacts:
        if path.suffix.lower() != '.md':
            continue
        try:
            corpus += '\n' + path.read_text(encoding='utf-8', errors='replace')[:200000]
        except OSError:
            continue
    corpus = re.sub(r'\s+', '', corpus)
    issues = []
    reported = set()
    for doc in docs:
        source = doc.with_suffix('.md')
        meta = {}
        if source.is_file():
            try:
                meta, _ = split_front_matter(source.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                meta = {}
        workflow = str(meta.get('workflow') or '')
        for row, token in declared.get(workflow, []):
            if token in present or re.sub(r'\s+', '', str(row)) in corpus:
                continue
            if token == '审阅说明' and chinese_document(doc):
                continue
            if (workflow, row) in reported:
                continue
            reported.add((workflow, row))
            issues.append('[OUTPUTS] %s 声明产出「%s」（类型 %s）未在本轮交付清单出现；'
                          '若本轮确属不适用请在交付说明中写明，不要默示省略' % (workflow, row, token))
    return issues



def render_anchor_check(source, meta, text):
    from intake import safe_yaml
    kind = workflow_kind(meta, text, source.name)
    # Rendering is not the matrix submission gate, but strict anchors must resolve.
    if '锚点' not in text and kind != 'case':
        return []
    specs = matrix_specs(meta, kind)
    value = specs.get('case', 'case-matrix.yaml')
    roots = [source.parent] + list(source.parents)
    root = next((p for p in roots if (p / '.arbitration-config.md').is_file() or (p / value).is_file()
                 or (value in {entry[1] for entry in MATRIX_FILES.values()} and (p / '案件档案' / value).is_file())), source.parent)
    path = resolve_matrix(root, source, value)
    if not path.is_file():
        return ['[ANCHOR] 严格模式缺少可解析的 case-matrix.yaml']
    known = known_anchor_ids(safe_yaml(path.read_text(encoding='utf-8')))
    try:
        offset = len(source.read_text(encoding='utf-8').splitlines()) - len(text.splitlines())
    except (OSError, UnicodeError):
        offset = 0
    return check_anchors(text, known, require=kind == 'case' and str(meta.get('mode','legal')) == 'legal',
                         label=source.name, offset=max(0, offset))


def matrix_stage(kind, meta, mode):
    if kind == 'case':
        return 'draft' if mode == 'draft' else ('enforcement' if str(meta.get('matrix_stage','')) == 'enforcement' else 'submission')
    if kind == 'clause':
        return 'draft' if mode == 'draft' else 'report'
    if str(meta.get('mode')) == 'board' or meta.get('profile') == 'board':
        return 'board'
    if meta.get('profile') == 'forecast':
        return 'forecast'
    if mode == 'submission' and meta.get('matrix_stage') == 'filing':
        return 'filing'
    return 'plan'


def check_matrix_file(kind, path, stage, profile):
    import importlib
    if not path.is_file():
        return {'exit_code':2,'decision':'MISSING_MATRIX','errors':[{'code':'CASE' if kind == 'case' else 'MATRIX','path':path.name,'message':'交付物所需矩阵不存在'}],
                'warnings':[],'allowed_to_draft':False,'submission_ready':False,'checked_stage':stage}
    try:
        module = importlib.import_module(MATRIX_FILES[kind][0])
        result = module.check_file(path, stage=stage, profile=profile)
        if not isinstance(result, dict) or type(result.get('exit_code')) is not int or result['exit_code'] not in (0,2,3,4) or not isinstance(result.get('errors'),list):
            raise ValueError('check_file 接口返回格式不正确')
        return result
    except (ImportError, AttributeError, ValueError, TypeError, OSError):
        return {'exit_code':4,'decision':'MATRIX_API_ERROR','errors':[{'code':'MATRIX','path':path.name,'message':'矩阵检查模块缺失、输入无效或接口不兼容'}],
                'warnings':[],'allowed_to_draft':False,'submission_ready':False,'checked_stage':stage}


def check_case_delivery(workdir, docs, mode, pending_path=None):
    from intake import safe_yaml
    from render_docx import split_front_matter
    from pending import source_path
    errors, warnings, checks = [], [], []
    exit_code = 0
    for doc in docs:
        mp = doc.with_suffix('.paras.json')
        source = doc.with_suffix('.md')
        manifest = {}
        try:
            if mp.is_file():
                manifest = json.loads(mp.read_text(encoding='utf-8'))
                source = source_path(mp, manifest)
            elif doc.with_suffix('.docx.md').is_file():
                source = doc.with_suffix('.docx.md')
            raw = source.read_text(encoding='utf-8') if source.is_file() else ''
            meta, body = split_front_matter(raw)
            kind = workflow_kind(meta, body or docx_text(doc), doc.name)
            if str(meta.get('mode', manifest.get('mode',''))) == 'board':
                errors += [f'[BOARD] {doc.name} {e}' for e in check_board_sections(body)]
                warnings.append(f'[BOARD] {doc.name} 分页未验证；须实际转PDF并视觉复核，不自动截短')
            declared = bool(str(meta.get('workflow') or meta.get('profile')
                                or manifest.get('workflow') or manifest.get('profile') or '').strip())
            if not declared:
                warnings.append(f'[MATRIX] {doc.name} 未声明 workflow/profile；矩阵核验跳过，材料闸门将阻断')
                continue
            active = bool(kind or meta.get('workflow') or meta.get('profile') or meta.get('matrix') or manifest.get('workflow') or manifest.get('matrix') or '#! 锚点：' in body)
            if not active:
                continue
            if not raw or not mp.is_file():
                errors.append(f'[MATRIX] {doc.name} 新工作流须保留记稿与渲染manifest')
                exit_code = max(exit_code, 2)
                continue
            if any(manifest.get(k) != meta.get(k) for k in ('workflow','profile','matrix')):
                errors.append(f'[SYNC] {doc.name} workflow/profile/matrix 与渲染记录不一致')
            if not kind and not meta.get('matrix'):
                # Cross-stage correspondence does not acquire a case matrix merely by opting in.
                from route import load_suite
                workflow = meta.get('workflow')
                if workflow not in load_suite()['subskills']:
                    raise ValueError('workflow/profile 无法解析；请声明本次任务或矩阵')
                checks.append({'document':doc.name,'kind':'case','decision':'not_applicable'})
                continue
            specs = matrix_specs(meta, kind)
            if kind in ('clause','enforcement') and 'case' not in specs:
                checks.append({'document':doc.name,'kind':'case','decision':'not_applicable'})
            known = set()
            dated_records = {}
            for mkind, value in specs.items():
                path = resolve_matrix(workdir, source, value)
                stage = matrix_stage(mkind, meta, mode)
                profile = meta.get('profile') if mkind == kind or kind is None else None
                report = check_matrix_file(mkind, path, stage, profile)
                checks.append({'document':doc.name,'kind':mkind,'matrix':str(path),**report})
                code = report['exit_code']
                exit_code = max(exit_code, code)
                for e in report.get('errors',[]):
                    errors.append(f"[{'CASE' if mkind == 'case' else 'MATRIX'}] {doc.name} {e.get('code','')} {e.get('path','')}: {e.get('message','')}")
                warnings += [f'[MATRIX] {doc.name} {w}' for w in report.get('warnings',[])]
                if code and not report.get('errors'):
                    errors.append(f'[MATRIX] {doc.name} {report.get("decision", "BLOCKED")}')
                if path.is_file():
                    data = safe_yaml(path.read_text(encoding='utf-8'))
                    if not isinstance(data, dict):
                        raise ValueError('matrix 须为映射')
                    if meta.get('case') and data.get('case') and str(meta['case']) != str(data['case']):
                        errors.append(f'[CONSIST] {doc.name} 矩阵案件代号与交付物不一致')
                    if mkind == 'case':
                        known.update(known_anchor_ids(data))
                    # Only the primary matrix owns declared dates/targets; auxiliary matrices
                    # may have different ID families and must not produce false missing-ID errors.
                    if mkind == kind or kind is None:
                        errors += check_matrix_metadata(meta, data, doc.name)
                    for ref, date_value in matrix_dates(data).items():
                        if ref in dated_records and dated_records[ref] != date_value:
                            errors.append(f'[CONSIST] {doc.name} 已关联矩阵的日期字段 {ref} 不一致')
                        dated_records[ref] = date_value
                    if pending_path:
                        from pending import cross_check
                        cross = cross_check(pending_path, path, mode=mode, files=[source], profile=profile)
                        errors += [f'[PENDING] {doc.name} {e}' for e in cross['errors']]
                        warnings += [f'[PENDING] {doc.name} {w}' for w in cross['warnings']]
            if 'case' in specs or '#! 锚点：' in body:
                errors += check_anchors(body, known, require=kind == 'case' and str(meta.get('mode',manifest.get('mode','legal'))) == 'legal',
                                        label=doc.name, offset=len(raw.splitlines()) - len(body.splitlines()))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f'[MATRIX] {doc.name} 记稿、metadata或矩阵输入无效：{type(exc).__name__}')
            exit_code = max(exit_code, 4)
    if errors and not exit_code:
        exit_code = 2
    return {'errors':errors,'warnings':warnings,'checks':checks,'exit_code':exit_code}


GATE_ALIASES = {'clause': '02-clause-diagnosis', 'clause-audit': '02-clause-diagnosis',
                'enforcement': '14-cross-border-enforcement',
                'cross-border-enforcement': '14-cross-border-enforcement'}


def gate_subskill(suite, workflow, profile):
    subs = suite.get('subskills') or {}
    wf = str(workflow or '').strip()
    if wf in subs:
        return wf
    if wf in GATE_ALIASES:
        return GATE_ALIASES[wf]
    if re.fullmatch(r'\d{2}(?:-[A-Za-z0-9_-]+)?', wf):
        matches = [sid for sid in subs if sid.startswith(wf[:2] + '-')]
        if len(matches) == 1:
            return matches[0]
    if profile:
        matches = [sid for sid, meta in subs.items() if profile in (meta.get('profiles') or {})]
        if len(matches) == 1:
            return matches[0]
    return None


def document_front_matter(workdir, doc):
    from render_docx import split_front_matter
    from pending import source_path
    mp = doc.with_suffix('.paras.json')
    source = doc.with_suffix('.md')
    manifest = {}
    if mp.is_file():
        manifest = json.loads(mp.read_text(encoding='utf-8'))
        source = source_path(mp, manifest)
    elif doc.with_suffix('.docx.md').is_file():
        source = doc.with_suffix('.docx.md')
    if source.is_symlink():
        raise ValueError('渲染记稿不得为符号链接')
    source.resolve().relative_to(Path(workdir).resolve())
    raw = source.read_text(encoding='utf-8') if source.is_file() else ''
    meta, body = split_front_matter(raw)
    return meta, body, source, manifest


def check_material_gates(workdir, docs, mode):
    from intake import SchemaError, evaluate, load_case
    from route import config_status, load_suite
    errors, warnings, gate_issues, draft_issues, checks = [], [], [], [], []
    try:
        suite = load_suite()
    except (OSError, ValueError, TypeError, SchemaError) as exc:
        return {'errors': ['[GATE] suite.yaml 无法加载：' + type(exc).__name__], 'warnings': [],
                'gate_issues': [], 'draft_issues': [], 'checks': []}
    tasks = []
    config_cases = {}
    for doc in docs:
        try:
            meta, body, source, manifest = document_front_matter(workdir, doc)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            warnings.append(f'[GATE] {doc.name} 前端元数据无法解析：{type(exc).__name__}')
            continue
        workflow = str(meta.get('workflow') or manifest.get('workflow') or '').strip()
        profile = str(meta.get('profile') or manifest.get('profile') or '').strip() or None
        if not workflow and not profile:
            errors.append(f'[GATE] {doc.name} 未声明 workflow/profile，材料闸门无法核验')
            checks.append({'document': doc.name, 'workflow': '', 'profile': None,
                           'decision': 'UNRESOLVED', 'submission_ready': False, 'allowed_to_draft': False})
            continue
        sid = gate_subskill(suite, workflow, profile)
        if not sid:
            message = (f'[GATE] {doc.name} workflow/profile 无法映射到 suite.yaml 子技能'
                       f'（workflow={workflow or "-"}, profile={profile or "-"}），材料闸门无法核验')
            (gate_issues if mode == 'submission' else draft_issues).append(message)
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile,
                           'decision': 'UNRESOLVED', 'submission_ready': False, 'allowed_to_draft': False})
            continue
        spec = suite['subskills'][sid]
        profiles = spec.get('profiles') or {}
        if profiles and not profile:
            errors.append(f'[GATE] {doc.name} {sid} 须选择 profile：{", ".join(profiles)}')
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': None, 'subskill': sid,
                           'decision': 'PROFILE_REQUIRED', 'submission_ready': False, 'allowed_to_draft': False})
            continue
        if profiles and profile not in profiles:
            errors.append(f'[GATE] {doc.name} {sid} profile 无效：{profile}')
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                           'decision': 'PROFILE_INVALID', 'submission_ready': False, 'allowed_to_draft': False})
            continue
        if not profiles and profile:
            errors.append(f'[GATE] {doc.name} {sid} 不设 profile，不得虚构 {profile}')
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                           'decision': 'PROFILE_INVALID', 'submission_ready': False, 'allowed_to_draft': False})
            continue
        effective = dict(spec, **profiles.get(profile, {}))
        if effective.get('redirect'):
            target = str(effective['redirect']) + ('/' + str(effective['redirect_profile'])
                                                   if effective.get('redirect_profile') else '')
            message = f'[GATE] {doc.name} {sid}{"/" + profile if profile else ""} 须改用 {target} 并重跑材料闸门'
            (gate_issues if mode == 'submission' else draft_issues).append(message)
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                           'decision': 'REDIRECT_REQUIRED', 'redirect': target,
                           'submission_ready': False, 'allowed_to_draft': False})
            continue
        if sid != '00-cold-start':
            configured = config_status(workdir, effective.get('requires', []))
            if configured['decision'] != 'CONFIGURED':
                detail = configured.get('error') or configured.get('action') or configured['decision']
                if configured.get('unfilled'):
                    detail += '；未满足槽位：' + ', '.join(configured['unfilled'])
                errors.append(f'[GATE] {doc.name} .arbitration-config.md {detail}')
                checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                               'decision': 'CONFIG_REQUIRED', 'config_decision': configured['decision'],
                               'submission_ready': False, 'allowed_to_draft': False})
                continue
            config_cases[doc] = configured['case']
            if meta.get('case') and str(meta['case']).strip() != configured['case']:
                errors.append(f'[GATE] {doc.name} 案件代号与 .arbitration-config.md 不一致')
        if not effective.get('gate_ids') and not effective.get('gate_any_ids'):
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                           'decision': 'NO_GATE', 'submission_ready': True, 'allowed_to_draft': True})
            continue
        tasks.append((doc, workflow, profile, sid, effective, str(meta.get('case') or '').strip()))
    if not tasks:
        return {'errors': errors, 'warnings': warnings, 'gate_issues': gate_issues,
                'draft_issues': draft_issues, 'checks': checks}
    ledger = Path(workdir) / 'case.json'
    if not ledger.is_file() or ledger.is_symlink():
        reason = '缺少案件材料台账 case.json' if not ledger.is_file() else 'case.json 不得为符号链接'
        message = f'[GATE] {reason}；以下文书的材料闸门无法核验：' + ', '.join(t[0].name for t in tasks)
        (gate_issues if mode == 'submission' else draft_issues).append(message)
        for doc, workflow, profile, sid, _, _ in tasks:
            checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                           'decision': 'NO_LEDGER', 'submission_ready': False, 'allowed_to_draft': False})
        return {'errors': errors, 'warnings': warnings, 'gate_issues': gate_issues,
                'draft_issues': draft_issues, 'checks': checks}
    try:
        case = load_case(ledger)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append('[GATE] case.json 无效：' + str(exc))
        return {'errors': errors, 'warnings': warnings, 'gate_issues': gate_issues,
                'draft_issues': draft_issues, 'checks': checks}
    for doc, workflow, profile, sid, _, doc_case in tasks:
        if doc in config_cases and config_cases[doc] != case['case']:
            errors.append(f'[GATE] {doc.name} case.json 案件代号与 .arbitration-config.md 不一致')
        if doc_case and doc_case != case['case']:
            errors.append(f'[GATE] {doc.name} 案件代号与 case.json 不一致')
            continue
        try:
            result = evaluate(case, sid, profile, 'submission' if mode == 'submission' else 'draft')
        except (ValueError, TypeError, KeyError, SchemaError) as exc:
            errors.append(f'[GATE] {doc.name} 材料闸门评估失败：{exc}')
            continue
        ids = {name: [row.get('id') for row in result.get(name, [])]
               for name in ('missing', 'pending', 'conflict', 'not_applicable', 'unknown')}
        checks.append({'document': doc.name, 'workflow': workflow, 'profile': profile, 'subskill': sid,
                       'decision': result.get('decision'),
                       'submission_ready': bool(result.get('submission_ready')),
                       'allowed_to_draft': bool(result.get('allowed_to_draft')), **ids})
        failed = (not result.get('submission_ready')) if mode == 'submission' else (not result.get('allowed_to_draft'))
        if failed:
            blockers = ids['missing'] + ids['pending'] + ids['conflict']
            if mode == 'submission':
                blockers += ids['unknown']
            message = (f"[GATE] {doc.name} {sid}{'/' + profile if profile else ''} 材料闸门未达"
                       f"{'提交' if mode == 'submission' else '草案'}态：{result.get('decision')}")
            if blockers:
                message += '；未满足/未确认：' + ', '.join(str(x) for x in blockers)
            (gate_issues if mode == 'submission' else draft_issues).append(message)
        elif result.get('decision') == 'UNKNOWN_RECORDED':
            warnings.append(f"[GATE] {doc.name} 未知项已按 follow-up 登记：" + ', '.join(ids['unknown']))
    return {'errors': errors, 'warnings': warnings, 'gate_issues': gate_issues,
            'draft_issues': draft_issues, 'checks': checks}


def matrix_dates(data):
    dates = {}

    def walk(node, ident=None):
        if isinstance(node, dict):
            ident = node.get('id', ident)
            if isinstance(ident, str):
                for key, value in node.items():
                    if not isinstance(value, (dict, list)) and DATE_RE.fullmatch(str(value)):
                        dates[f'{ident}.{key}'] = normalize_date(str(value))
            for key, value in node.items():
                mapped_id = key if isinstance(key, str) and re.fullmatch(r'[A-Z]+-[A-Z0-9-]*\d', key) else None
                walk(value, mapped_id)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return dates


def check_matrix_metadata(meta, data, filename):
    """Compare declared field references, not unrelated dates anywhere in the directory."""
    errors = []
    records = {}
    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get('id'), str):
                records[node['id']] = node
            for key, value in node.items():
                if isinstance(key, str) and isinstance(value, dict):
                    records.setdefault(key, value)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(data)
    dates = meta.get('matrix_dates', {})
    if not isinstance(dates, dict):
        return [f'[CONSIST] {filename} matrix_dates 须为 ID.field 到日期的映射']
    for ref, value in dates.items():
        ident, _, field = str(ref).partition('.')
        actual = records.get(ident, {}).get(field)
        if actual is None or normalize_date(str(actual)) != normalize_date(str(value)):
            errors.append(f'[CONSIST] {filename} 日期字段 {ref} 与对应矩阵记录不一致')
    targets = meta.get('enforcement_targets', [])
    if not isinstance(targets, list) or any(t not in records for t in targets):
        errors.append(f'[CONSIST] {filename} enforcement_targets 含未知目标或格式错误')
    return errors


VERIFY_FIX_CMD = "fetch_official.py verify <source-id> --by <核验人> --scope <核验范围> --edition <精确版本标签> --locator <已核定位>"


def provenance_limitations(cited_ids, legal_status):
    """Split cited sources by provenance state so an empty on-demand cache is not read as a citation error."""
    states = {}
    for sid in cited_ids:
        states.setdefault(legal_status(sid)['legal_state'], []).append(sid)
    no_text = sorted(states.get('未取文本', []))
    unverified = sorted(states.get('已取文本未核验', []))
    verified = sorted(states.get('已核验', []))
    lines = []
    if no_text:
        lines.append(
            f"引用来源 {len(no_text)} 个尚未取文（按需缓存为空，属首次运行正常态，不是引用错误）：{', '.join(no_text)}；"
            f"补法：fetch_official.py fetch <source-id> --to-md 后运行 {VERIFY_FIX_CMD}")
    if unverified:
        lines.append(
            f"引用来源 {len(unverified)} 个已取文本但未登记哈希核验（须在官方文本逐条复核后补记）：{', '.join(unverified)}；补法：{VERIFY_FIX_CMD}")
    if verified and not no_text and not unverified:
        lines.append(f"引用来源 {len(verified)} 个均已完成取文与哈希核验（清单：{', '.join(verified)}）")
    return lines


def verify(workdir: Path, forced_pairs=None, mode="submission", pending_path=None, filing_guide=None, delivery_manifest=None) -> int:
    workdir = Path(workdir).resolve()
    schema = find_schema()
    selected_pairs = None
    artifacts = None
    selected_manifest = delivery_manifest or (workdir / 'delivery.json' if (workdir / 'delivery.json').is_file() else None)
    if selected_manifest:
        try:
            from _delivery import selection
            docs, notes, artifacts, selected_pairs = selection(workdir, selected_manifest)
            if forced_pairs: raise ValueError('交付清单与 --pairs 不可同时指定')
            selection_path=Path(selected_manifest)
            if not selection_path.is_absolute():selection_path=workdir/selection_path
            selected_data=json.loads(selection_path.read_text(encoding='utf-8'))
            if selected_data.get('filing_guide'):
                declared=(workdir/selected_data['filing_guide']).resolve()
                if filing_guide:
                    given = Path(filing_guide)
                    given = (workdir / given if not given.is_absolute() else given).resolve()
                    if given != declared: raise ValueError('立案指引参数与本轮清单不一致：--filing-guide 解析为 %s，清单声明为 %s' % (given, declared))
                filing_guide=str(declared)
        except (ValueError,TypeError,OSError,KeyError) as exc:
            print(json.dumps({'decision':'VERIFY_FAILED','submission_ready':False,'gate_issues':[],
                              'problems':['[DELIVERY] '+str(exc)]},ensure_ascii=False));return 2
    else:
        docs, notes = gather(workdir)
    gate_issues = []
    if mode == 'submission' and not selected_manifest:
        gate_issues.append('[DELIVERY] 提交模式须提供 delivery.json 或 --delivery-manifest')
    all_docx = sorted({p for p in (artifacts if artifacts is not None else docs + notes)
                       if p.suffix == '.docx'})
    auxiliary_docx = [p for p in all_docx if p not in docs and p not in notes]
    # rulesuite-delivery/1 attachments are authored auxiliary files, not original
    # exhibits. Do not fabricate a render source or a workflow for external evidence.
    originals = [p for p in auxiliary_docx if not any(
        p.with_suffix(suffix).is_file() for suffix in ('.md', '.docx.md', '.paras.json'))]
    task_docs = docs + [p for p in auxiliary_docx if p not in originals]
    matrix_report = check_case_delivery(workdir, task_docs, mode, pending_path=pending_path)
    material_report = check_material_gates(workdir, task_docs, mode)
    matrix_report['warnings'] += material_report['warnings']
    if mode == 'submission':
        gate_issues += material_report['gate_issues']
    # Only check deliverable drafts; do not block on intake/config/source archives.
    md_all = [p for d in docs for p in (d.with_suffix(".md"), d.with_suffix(".docx.md")) if p.is_file()]
    md_all += [n for n in notes if n.suffix == ".md" and any(n.stem.startswith(d.stem + "-") and n.parent == d.parent for d in docs)]
    citation_errors = []
    cited_ids = set()
    source_checks = []
    for artifact in (artifacts if artifacts is not None else sorted(workdir.rglob('*'))):
        if artifact.suffix.lower() not in ('.md', '.docx') or artifact.name.startswith('~$'):
            continue
        text = docx_text(artifact) if artifact.suffix == '.docx' else artifact.read_text(encoding='utf-8', errors='replace')
        for found in iter_markers(text):
            if found.kind == 'kb':
                citation_errors.append(f'[CITE] {artifact.relative_to(workdir)} 交付物不得使用 [kb:] 知识锚点，须按本案核验后改为 [source:]：{found.raw[:100]}')
                continue
            if found.example:
                continue
            fields, marker_issues = parse_source_marker(found.raw, registry_ids(), citation_url_issue)
            cited_ids.add(fields['source_id'])
            for issue in marker_issues:
                target = matrix_report['warnings'] if issue.startswith('WARN ') else citation_errors
                target.append(f'[CITE] {artifact.relative_to(workdir)} {issue}')
            # Registry warnings do not attest evidence. Check every parsed marker;
            # hard marker errors above independently continue to block delivery.
            if mode == 'submission' and fields:
                from _source_evidence import source_evidence
                try:
                    issues, _ = source_evidence(fields['source_id'], workdir, locator=fields['locator'],
                                                edition=fields['version'], url=fields['url'],
                                                checked_at=fields['checked_at'])
                    source_checks.append({'source_id': fields['source_id'], 'locator': fields['locator'], 'verified': not issues})
                    citation_errors += [f'[SOURCE] {artifact.relative_to(workdir)} {fields["source_id"]}: {x}' for x in issues]
                except (ValueError, TypeError, OSError, KeyError) as exc:
                    citation_errors.append(f'[SOURCE] {artifact.relative_to(workdir)} 来源记录无效：{exc}')
    draft_errors = list(material_report['errors'])
    draft_errors += [f'[DELIVERY] {p.name} 未提供自有记稿；attachments 仅接受自有辅助件，'
                     '外部证据原件须保留原始身份并通过 case.json 与证据索引核对，不得补造渲染来源'
                     for p in originals]
    if mode == 'draft':
        draft_errors += material_report['draft_issues']
    from render_docx import split_front_matter
    needs_guide=False
    for doc in docs:
        mp=doc.with_suffix('.paras.json')
        if mp.is_file():
            from pending import source_path
            source=source_path(mp,json.loads(mp.read_text(encoding='utf-8')))
            meta,body=split_front_matter(source.read_text(encoding='utf-8'))
            if str(meta.get('workflow','')).startswith('04-') or re.search(r'仲裁申请书|request for arbitration',str(meta.get('title',''))+' '+doc.name,re.I): needs_guide=True
    if needs_guide and not filing_guide:
        draft_errors.append('[GUIDE] 仲裁申请、重写或补正须在本轮清单 filing_guide 声明立案申请指引；草案亦须说明未核步骤')
    if filing_guide:
        try:
            guide = Path(filing_guide)
            if not guide.is_absolute():
                guide = (workdir / guide)
            guide = guide.resolve()
            if not guide.is_relative_to(workdir):
                raise ValueError(f'立案指引须位于案件目录内：{guide}（案件目录 {workdir}）；相对路径按 --workdir 解析')
            relative = guide.relative_to(workdir).as_posix()
            text = guide.read_text(encoding='utf-8')
            required = ['线上立案', '邮寄', '送达', '费用', '提交后', '核查日期']
            if guide.suffix != '.md' or any(x not in text for x in required) or not re.search(r'https://[^\s]+', text):
                raise ValueError('立案指引须为 Markdown，包含核查日期、官方链接、线上立案、邮寄、送达、费用与提交后跟进')
            if mode == 'draft':
                from pending import load, validate_text
                _, entries = load(pending_path)
                validate_text(text, str(guide), entries)
            elif PLACEHOLDER_RE.search(text):
                raise ValueError('提交态立案指引仍有占位')
        except (ValueError, OSError, TypeError) as e:
            draft_errors.append('[GUIDE] ' + str(e))
    if mode == 'draft':
        try:
            if not pending_path:
                raise ValueError('--mode draft 需要 --pending')
            from pending import validate_docx
            for artifact in docs + [n for n in notes if n.suffix=='.docx']:
                validate_docx(artifact, workdir, pending_path)
        except (ValueError, OSError, KeyError, zipfile.BadZipFile) as e:
            draft_errors.append('[PENDING] ' + str(e))
    pending_map = {}
    if mode == 'draft' and pending_path:
        try:
            from pending import load as _load_pending
            _, _pentries = _load_pending(pending_path)
            for _e in _pentries:
                if _e.get('status') == 'open':
                    for _f in _e.get('files', []):
                        pending_map.setdefault(str(Path(_f).resolve()), set()).add(_e['placeholder'])
        except (ValueError, OSError):
            pass  # 登记表加载失败已由 PENDING 块报出；此处按无登记处理
    draft_fill = []
    draft_pending_info = []
    if artifacts is not None:
        for artifact in artifacts:
            if artifact in docs or artifact in notes: continue
            if artifact.suffix == '.md':
                md_all.append(artifact)
            if mode == 'submission':
                ph = docx_has_placeholder(artifact) if artifact.suffix == '.docx' else md_has_placeholder(artifact)
                if ph: draft_errors.append('[FILL] 本轮附件 '+artifact.name+' 残留占位符')
    md_all = sorted(set(md_all))
    for md in md_all:
        if is_note(md):
            continue
        md_ph = PLACEHOLDER_RE.findall(md.read_text(encoding="utf-8", errors="ignore"))
        if not md_ph:
            continue
        if mode == 'draft' and pending_path:
            reg = pending_map.get(str(md.resolve()), set())
            stray = [t for t in md_ph if t not in reg]
            if stray:
                draft_fill.append(f"[FILL] {md.name} 记稿存在未登记占位符 {stray[:3]}：登记进 pending.json 或替换为案件事实")
            else:
                draft_pending_info.append(f"[FILL] {md.name} 含 {len(md_ph)} 处已登记待确认占位（审阅草案允许）")
        else:
            draft_fill.append(f"[FILL] {md.name} 记稿残留占位符 {md_ph[:3]}：需同步更新对应 .docx")
    if draft_fill:
        problems = lint_dialect(md_all) + draft_fill + citation_errors + draft_errors + matrix_report['errors']
        print(json.dumps({"decision": "VERIFY_FAILED", "workdir": str(workdir),
                          "documents": len(docs), "notes": len(notes),
                          "gate_issues": gate_issues,
                          "problems": problems,
                          "action": "先把记稿中的占位符替换为案件事实或登记 pending.json，再生成 .docx"},
                         ensure_ascii=False, indent=2))
        return 2
    if not docs and not notes:
        print(json.dumps({"decision": "EMPTY_WORKDIR", "workdir": str(workdir),
                          "action": "本轮没有可交付文件：先由子技能产出记稿并用 render_docx.py 生成 .docx"},
                         ensure_ascii=False, indent=2))
        return 3
    if not docs and notes:
        print(json.dumps({"decision": "NO_DOCX", "workdir": str(workdir),
                          "problems": ["[PAIR] 存在说明文件但无可交付 .docx 文书"],
                          "action": "先用 render_docx.py 生成 .docx"},
                         ensure_ascii=False, indent=2))
        return 3
    problems, passed = list(draft_errors) + citation_errors + matrix_report['errors'], list(draft_pending_info)
    pairs = []
    if selected_pairs is not None:
        pairs = selected_pairs
    elif forced_pairs:
        pairs = []
        for spec in forced_pairs:
            try:
                a, b = spec.split(":", 1)
                d, n = workdir / a, workdir / b
                if not a or not b or d.resolve() == n.resolve() or not d.is_file() or not n.is_file():
                    raise ValueError("文书与说明必须是两个已存在文件")
                d.resolve().relative_to(workdir.resolve()); n.resolve().relative_to(workdir.resolve())
                if d.suffix != ".docx" or is_note(d) or not is_note(n) or n.suffix not in (".md", ".docx"):
                    raise ValueError("配对须为主文书.docx:中文说明.md/.docx")
                pairs.append((d, n))
            except ValueError as e:
                print(json.dumps({"decision": "INVALID_PAIRS", "error": str(e)}, ensure_ascii=False))
                return 3
        if len({d for d, _ in pairs}) != len(pairs) or len({n for _, n in pairs}) != len(pairs):
            print(json.dumps({"decision": "INVALID_PAIRS", "error": "重复配对"}, ensure_ascii=False))
            return 3
    else:
        used_notes = set()
        for d in docs:
            n = None if internal_document(d) else pair_of(d, notes, used_notes)
            if n:
                used_notes.add(n)
            pairs.append((d, n))

    dl = lint_dialect(md_all)
    if dl:
        problems += dl
    else:
        passed.append(f"[DIALECT] {len(md_all)} 份记稿的占位符写法合规")

    for d, n in pairs:
        if internal_document(d):
            passed.append(f"[PAIR] {d.name} 按内部件豁免（pair:false）")
        elif n is None and chinese_document(d):
            passed.append(f"[PAIR] {d.name} 正文本身为中文，铁律 5 无需另配《中文审阅说明》（按文书语言豁免，非内部件豁免）")
        elif n is None:
            problems.append(f"[PAIR] {d.name} 缺少配套《中文审阅说明》（铁律 5）；说明件须与主文书同目录同前置名，"
                            f"命名为 {d.stem}-中文审阅说明.docx（或 .md）")
        else:
            passed.append(f"[PAIR] {d.name} ↔ {n.name}")
            if mode == 'submission' and n.suffix.lower() != ".docx":
                problems.append(
                    f"[NOTE] {n.name} 仅有 .md 记稿、缺少配套《中文审阅说明》.docx："
                    "12-delivery 要求文书与本说明均交付 .docx，请用 render_docx.py 生成说明 .docx")

    cache = {}
    for artifact in all_docx:
        problems += [f'[DOCX] {issue}' for issue in check_docx_structure(artifact, schema)]
        if mode != 'draft' and docx_has_placeholder(artifact):
            problems.append(f'[FILL] {artifact.name} DOCX 残留占位符')
        if artifact in originals:
            continue  # Invalid delivery role, not a request to manufacture provenance.
        # Every authored DOCX, including auxiliary files and notes, binds both hashes.
        mp = artifact.with_suffix('.paras.json')
        if mode == 'submission' and not mp.is_file():
            problems.append(f'[SYNC] {artifact.name} 缺少渲染记录')
        if mp.exists():
            try:
                from pending import source_path
                manifest = json.loads(mp.read_text(encoding='utf-8'))
                for field, candidate in (("docx_sha256", artifact), ("source_sha256", source_path(mp, manifest))):
                    expected = manifest.get(field)
                    if mode == 'submission' and not expected:
                        problems.append(f'[SYNC] {artifact.name} 渲染记录缺 {field}')
                    if expected and hashlib.sha256(candidate.read_bytes()).hexdigest() != expected:
                        problems.append(f'[SYNC] {artifact.name} 与记稿或渲染清单不一致，须重新渲染')
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                problems.append(f'[SYNC] {mp.name} 无法读取')
    for d, n in pairs:
        txt = docx_text(d)
        cache[d] = txt
        ph_parts = docx_has_placeholder(d)
        if ph_parts and mode != 'draft':
            problems.append(f"[FILL] {d.name} 在 {ph_parts} 残留黄色高亮占位符：交付前逐项替换")
        try:
            with zipfile.ZipFile(d) as z:
                for part_name in z.namelist():
                    if re.fullmatch(r"word/(header|footer)\d*\.xml", part_name):
                        hxml = z.read(part_name).decode("utf-8", "ignore")
                        import html as _html
                        htxt = _html.unescape(re.sub(r"<[^>]+>", "", hxml))
                        hph = PLACEHOLDER_RE.findall(htxt)
                        if hph:
                            problems.append(f"[FILL] {d.name} 页眉/页脚 {part_name} 含未填占位符 {hph[:3]}")
        except Exception:
            pass
        for i in check_docx_structure(d, schema):
            problems.append(f"[DOCX] {i}")
        mf = d.with_suffix(".paras.json")
        if not mf.exists():
            mf = d.parent / (d.stem + ".paras.json")
        para_refs = para_ref_findall(txt)
        if n is not None:
            ntxt_early = n.read_text(encoding="utf-8", errors="ignore") if n.suffix == ".md" else docx_text(n)
            para_refs += para_ref_findall(ntxt_early)
        if para_refs:
            if not mf.exists():
                problems.append(f"[XREF] {d.name} 含段落引用但缺少 manifest {mf.name}")
            else:
                try:
                    total = json.loads(mf.read_text(encoding="utf-8")).get("numbered_paragraphs", 0)
                except (json.JSONDecodeError, KeyError, AttributeError):
                    problems.append(f"[XREF] {d.name} manifest 解析失败")
                    total = 0
                if not isinstance(total, int) or isinstance(total, bool) or total < 0:
                    problems.append(f"[XREF] {d.name} manifest 的 numbered_paragraphs 不是非负整数：{total!r}")
                    total = 0
                actual = docx_count_numbered_paras(d) if d.suffix == ".docx" else 0
                if total > actual:
                    problems.append(f"[XREF] {d.name} manifest 报告 {total} 个编号段落，但文书实际仅 {actual} 个：清单虚高，不得据此放行")
                    total = actual
                if total > 0:
                    over = []
                    for m in para_refs:
                        ref_int = para_ref_to_int(m)
                        if ref_int is not None and ref_int > total:
                            over.append(ref_int)
                        elif ref_int is not None and ref_int <= 0:
                            over.append(ref_int)
                    if over:
                        problems.append(f"[XREF] {d.name} 引用了不存在的段落号 {sorted(set(over))}（实际编号段落 {total} 个）")
                    else:
                        passed.append(f"[XREF] {d.name} 交叉引用落在 1–{total} 区间内")
                elif total == 0:
                    problems.append(f"[XREF] {d.name} manifest 报告 0 个编号段落，但正文含段落引用")
        if n is not None:
            ntxt = n.read_text(encoding="utf-8", errors="ignore") if n.suffix == ".md" else docx_text(n)
            cache[n] = ntxt
            n_ph = md_has_placeholder(n) if n.suffix == ".md" else docx_has_placeholder(n)
            if n_ph:
                if mode == 'draft' and n.suffix == ".md" and pending_path:
                    tokens = PLACEHOLDER_RE.findall(n.read_text(encoding="utf-8", errors="ignore"))
                    reg = pending_map.get(str(n.resolve()), set())
                    stray = [t for t in tokens if t not in reg]
                    if stray:
                        problems.append(f"[FILL] {n.name} 说明存在未登记占位符：{stray[:5]}")
                    else:
                        passed.append(f"[FILL] {n.name} 含 {len(tokens)} 处已登记待确认占位（审阅草案允许）")
                elif mode == 'draft':
                    pass  # docx 说明的高亮占位已由 PENDING 块逐 run 校验兜底
                else:
                    problems.append(f"[FILL] {n.name} 说明中残留占位符：{n_ph[:5]}")
            miss = check_note_sections(ntxt)
            if miss:
                problems.append(f"[PAIR] {n.name} 五节结构不合格：{miss}")
            else:
                passed.append(f"[NOTE] {n.name} 五节完整")
            registry = registry_ids()
            valid_sources = []
            for found in iter_markers(ntxt):
                if found.kind == 'kb':
                    problems.append(f"[CITE] {n.name} 说明不得使用 [kb:] 知识锚点，须改为本案 [source:]：{found.raw[:100]}")
                    continue
                if found.example:
                    continue
                marker_issues = [issue for issue in source_marker_issues(found.raw, registry) if not issue.startswith('WARN ')]
                if marker_issues:
                    problems.append(f"[CITE] {n.name} 来源标记不合格（{'；'.join(marker_issues)}）：{found.raw[:100]}")
                else:
                    valid_sources.append(found)
            rule_mentions = list(RULE_RE.finditer(ntxt))
            if rule_mentions:
                uncovered = []
                for rm in rule_mentions:
                    rule_text = rm.group()
                    prefix = ntxt[max(0, rm.start() - 30):rm.start()]
                    if re.search(r'(?:\bContract\s+|合同\s*)$', prefix, re.I):
                        continue
                    rm_line = ntxt[:rm.start()].count('\n')
                    has_source = False
                    for vs in valid_sources:
                        if vs.line - 1 == rm_line:
                            has_source = True
                            break
                    if not has_source:
                        uncovered.append(rule_text)
                if uncovered:
                    problems.append(f"[CITE] {n.name} 以下条文引用缺少有效 [source:...] 标记（铁律 2）：{sorted(set(uncovered))[:5]}")
                else:
                    passed.append(f"[CITE] {n.name} 含 {len(valid_sources)} 处来源标记覆盖所有条文引用")
            body_rules = set(BODY_RULE_RE.findall(cache[d]))
            noted_rules = set(BODY_RULE_RE.findall(ntxt))
            if body_rules - noted_rules:
                problems.append(f"[CITE] {d.name} 正文条号未在说明中对应说明：{sorted(body_rules - noted_rules)}")
            dtxt, ntxtd = cache[d], cache[n]
            declared = declared_parties(workdir, dtxt)
            for party in declared:
                p_norm = norm(party)
                if p_norm and len(p_norm) > 2 and p_norm not in norm(ntxtd):
                    problems.append(f"[CONSIST] 当事方 '{party}' 出现在文书 {d.name} 中，但未出现在 {n.name}")
            if declared:
                passed.append(f"[CONSIST] {d.name} ↔ {n.name} 当事方名称一致：{declared}")
            doc_amounts = extract_amounts(flatten_text(dtxt))
            note_amounts = extract_amounts(flatten_text(ntxtd))
            for da in doc_amounts:
                if da not in note_amounts:
                    problems.append(f"[CONSIST] 金额 {da} 只见于文书 {d.name}、未见于说明 {n.name}")
            for na in note_amounts:
                if na not in doc_amounts:
                    na_curr = re.match(r'^[A-Z€$￥]+', na)
                    na_num = re.search(r'[\d.]+', na)
                    conflict = False
                    for da in doc_amounts:
                        da_curr = re.match(r'^[A-Z€$￥]+', da)
                        da_num = re.search(r'[\d.]+', da)
                        if na_curr and da_curr and na_num and da_num:
                            if na_curr.group() != da_curr.group() and na_num.group() == da_num.group():
                                conflict = True
                    if conflict:
                        problems.append(f"[CONSIST] 说明 {n.name} 含矛盾金额 {na}（文书中为不同币种同数值）")
            dds = {normalize_date(x) for x in DATE_RE.findall(flatten_text(dtxt))}
            note_dates = {normalize_date(x) for x in DATE_RE.findall(flatten_text(ntxtd))}
            for dd in dds:
                if dd not in note_dates:
                    problems.append(f"[CONSIST] 关键日期 '{dd}' 见于文书但未同步到说明")
            doc_days = set(DEADLINE_DAYS_RE.findall(CALENDAR_DATE_TEXT_RE.sub(' ', flatten_text(dtxt))))
            note_days = set(DEADLINE_DAYS_RE.findall(CALENDAR_DATE_TEXT_RE.sub(' ', flatten_text(ntxtd))))
            if doc_days and note_days and doc_days != note_days:
                problems.append(f"[CONSIST] 期限天数不一致：文书 {sorted(doc_days)} 天 vs 说明 {sorted(note_days)} 天")
            doc_relief_count = count_relief_items(flatten_text(dtxt))
            note_relief_count = count_relief_items(flatten_text(ntxtd))
            if doc_relief_count and note_relief_count and doc_relief_count != note_relief_count:
                problems.append(f"[CONSIST] 请求项数量不一致：文书 {doc_relief_count} 项 vs 说明 {note_relief_count} 项")
    if mode == 'submission':
        for artifact in docs:
            mp = artifact.with_suffix('.paras.json')
            if mp.exists() and json.loads(mp.read_text()).get('delivery_state') == 'draft':
                problems.append('[DRAFT] 草案须确认事实后按提交态重新渲染')
    from _visual import font_environment, visual_receipt
    font_status=font_environment()
    visual_ok=False
    visual_issues=['未声明本轮交付清单，无法绑定视觉复核版本']
    if selected_manifest:
        path=Path(selected_manifest)
        if not path.is_absolute():path=workdir/path
        visual_ok,visual_issues=visual_receipt(json.loads(path.read_text(encoding='utf-8')),docs+[n for n in notes if n.suffix=='.docx'],workdir)
    matrix_incomplete = [c for c in matrix_report['checks'] if not c.get('submission_ready', True)]
    if mode == 'submission':
        gate_issues += ['[VISUAL] ' + x for x in visual_issues]
        gate_issues += [f"[MATRIX] {c.get('document','')} {c.get('kind','')} 未达提交态：{c.get('decision','')}"
                        for c in matrix_incomplete]
    else:
        matrix_report['warnings'] += ['[VISUAL] '+x for x in visual_issues]
    if font_status['cjk']!='available':matrix_report['warnings'].append('[FONT] '+font_status['message'])
    matrix_report['warnings'] += output_completeness(
        workdir, docs, artifacts if artifacts is not None
        else list(workdir.rglob('*.md')) + list(workdir.rglob('*.docx')))
    extra_limitations = []
    if mode == 'submission':
        from fetch_official import legal_status
        from _source_evidence import load_local
        local_ids=set(load_local(workdir))
        extra_limitations.extend(provenance_limitations(cited_ids-local_ids, legal_status))
    submission_ready = (mode == 'submission' and not problems and not gate_issues and visual_ok
                        and all(r.get('submission_ready', True) for r in matrix_report['checks']))
    if problems:
        decision = 'VERIFY_FAILED'
    elif mode == 'draft':
        decision = 'DRAFT_OK'
    elif submission_ready:
        decision = 'VERIFIED'
    else:
        decision = 'VERIFY_INCOMPLETE'
    if problems:
        action = '逐项修补后再交付'
    elif mode == 'draft':
        action = '审阅草案可交付：将 docx 与说明连同 pending 清单交用户逐项确认，标注不可提交；确认事实后按 --mode submission 重跑'
    elif submission_ready:
        action = '自动校验与已登记视觉复核通过；仍需法律及授权复核后交付'
    else:
        missing = []
        if not selected_manifest: missing.append('交付清单')
        if visual_issues: missing.append('视觉复核')
        if matrix_incomplete: missing.append('矩阵提交态')
        if material_report['gate_issues']: missing.append('材料台账闸门')
        action = '不可提交：尚未满足' + '、'.join(missing or ['提交条件']) + '；补齐后按 --mode submission 重跑'
    exit_code = 0 if ((mode == 'draft' and not problems) or submission_ready) else 2
    # Different documents may legitimately concern different dates, parties and currencies.
    # Cross-document legal consistency requires a field-level human review, not set equality.
    print(json.dumps({
        "decision": decision,
        "submission_ready": submission_ready,
        "allowed_to_draft": not problems,
        "checked_stage": mode,
        "workdir": str(workdir),
        "documents": len(docs), "notes": len(notes),
        "schema_validation": "xmllint+OOXML" if (schema and subprocess_has("xmllint")) else "仅部件完整性检查（未装 xmllint 或 schema）",
        "checks_passed": passed,
        "matrix_checks": matrix_report['checks'],
        "material_gate_checks": material_report['checks'],
        "source_checks": source_checks,
        "visual_review_completed": visual_ok,
        "font_environment": font_status,
        "delivery_manifest": str(selected_manifest) if selected_manifest else None,
        "gate_issues": gate_issues,
        "warnings": matrix_report['warnings'],
        "problems": problems,
        "action": action,
        "limitations": ["来源标记校验不证明来源真实、条文内容正确或适用于本案", "段落引用只检查编号范围", "未验证视觉分页、证据真实性或法律结论", "法系适配、机构中立性和对抗审查属于记录闸门，不以正则匹配证明法律判断正确"] + extra_limitations,
    }, ensure_ascii=False, indent=2))
    return exit_code


def selftest() -> int:
    import tempfile
    print("--- xref external award reference check ---")
    refs = para_ref_findall("内部段落 2。裁决书第42段及裁决第43段。")
    if refs != ["2"]:
        print(json.dumps({'decision': 'SELFTEST_FAIL',
                          'problems': ['外部裁决段落被误作本文件交叉引用：%r' % refs],
                          'action': 'XREF 只核对本文件段落，保留内部引用并排除明示的裁决书／裁决段落'},
                         ensure_ascii=False, indent=2))
        return 2
    print('OK    XREF     外部裁决段落不计入本文件交叉引用')
    suite = Path(__file__).resolve().parent.parent
    td = Path(tempfile.mkdtemp(prefix="arb-selftest-"))
    legal = td / "Sample-Request.md"
    legal.write_text(
        "---\ntitle: PROCEDURAL LETTER\ncase: SELFTEST\nworkflow: 13-stage-qa\nmode: legal\n---\n"
        "# PROCEDURAL LETTER\n## I. THE PARTIES\n1. The Claimant is A Ltd.\n"
        "2. The Respondent is B GmbH, as described in paragraph 1 above.\n",
        encoding="utf-8")
    (td / "case.json").write_text(json.dumps({'schema': 'rulesuite-case/1', 'case': 'SELFTEST', 'facts': {
        'procedure.current_order': {'status': 'confirmed', 'value': 'Synthetic procedural order dated 2026-01-10',
                                    'evidence': 'synthetic selftest fixture'},
        'task.question': {'status': 'confirmed', 'value': 'Synthetic procedural question',
                          'evidence': 'synthetic selftest fixture'}}}, ensure_ascii=False), encoding="utf-8")
    (td / ".arbitration-config.md").write_text(
        'case: SELFTEST\n~ 工作目录：' + str(td) + '\n'
        '- slot(official_rules_fetch): degraded (selftest)\n'
        '- slot(law_retrieval): degraded (selftest)\n'
        '- slot(docx_render): bound (local)\n'
        '- slot(local_corpus): skipped\n'
        '- slot(party_data): user-materials-only\n',
        encoding="utf-8")
    note = td / "Sample-Request-中文审阅说明.md"
    note.write_text(
        "---\ntitle: 中文审阅说明\ncase: SELFTEST\nmode: memo\n---\n"
        "# 中文审阅说明\n## 本文件作用与程序依据\n本案 A Ltd v. B GmbH，本合成示例只测试程序函格式，不作法律断言。\n"
        "## 逐段填写要点\nA Ltd 的全称以营业执照为准；B GmbH 的名称以合同抬头为准。\n## 我方立场与可选表述\nA Ltd 主张 USD 1,000,000。\n"
        "## 风险与待用户确认事项\n日期 2026-01-15 需确认。\n## 给管理层的三句话汇报\n已完成草稿。\n",
        encoding="utf-8")
    pending = td / "pending.json"
    pending.write_text(json.dumps({'schema': 'rulesuite-pending/1', 'case': 'SELFTEST', 'items': []}),
                       encoding="utf-8")
    jobs = [(legal, td / "Sample-Request.docx", []),
            (note, td / "Sample-Request-中文审阅说明.docx", ["--mode", "memo"])]
    for source, out, extra in jobs:
        print("--- render ---")
        r = subprocess.run([sys.executable, str(suite / "scripts/render_docx.py"),
                            "--in", str(source), "--out", str(out),
                            "--manifest", str(out.with_suffix(".paras.json")),
                            "--draft", "--pending", str(pending), *extra],
                           capture_output=True, text=True)
        print(r.stdout or r.stderr)
        if r.returncode != 0:
            return 2
    print("--- pairing language check ---")
    en, zh = chinese_document(td / "Sample-Request.docx"), chinese_document(td / "Sample-Request-中文审阅说明.docx")
    if en or not zh:
        print(json.dumps({'decision': 'SELFTEST_FAIL',
                          'problems': ['铁律 5 语言判定异常：英文样例应不免配（实测 %s），中文样例应免配（实测 %s）；'
                                       '免配豁免只适用于正文以中文为主的文书' % (en, zh)],
                          'action': '修 chinese_document 的 CJK 占比判定，不得放宽为全部免配或一律不免'},
                         ensure_ascii=False, indent=2))
        return 2
    print('OK    PAIR     英文样例不免配、中文样例按语言免配')
    print("--- verify (draft) ---")
    return verify(td, mode="draft", pending_path=pending)


def main() -> int:
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--workdir")
    ap.add_argument("--mode", choices=["draft", "submission"], default="submission")
    ap.add_argument("--pending")
    ap.add_argument("--delivery-manifest", help="本轮交付清单 JSON（默认案件根 delivery.json）")
    ap.add_argument("--filing-guide", help="申请材料必须随附的立案申请指引 Markdown")
    ap.add_argument("--pairs", action="append", help="强制配对 spec：docx:说明文件（相对 workdir）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--templates", action="store_true", help="只体检技能包 assets/templates 的占位符方言")
    a = ap.parse_args()
    if a.templates:
        suite = Path(__file__).resolve().parent.parent
        tpls = sorted((suite / "assets" / "templates").glob("*.md"))
        bad = lint_dialect(tpls)
        print(json.dumps({"decision": "TPL_FAIL" if bad else "TPL_OK",
                          "scanned": len(tpls), "problems": bad,
                          "action": "把嵌套/跨行占位符拆成单层，或改写为 #! 指引行" if bad else "模板方言合规"},
                         ensure_ascii=False, indent=2))
        return 2 if bad else 0
    if a.selftest:
        return selftest()
    if not a.workdir:
        ap.error("需要 --workdir 或 --selftest")
    wd = Path(a.workdir).expanduser()
    if not wd.is_dir():
        print(json.dumps({"decision": "NO_WORKDIR", "path": str(wd)}, ensure_ascii=False))
        return 3
    try:
        return verify(wd, a.pairs, mode=a.mode, pending_path=a.pending, filing_guide=a.filing_guide, delivery_manifest=a.delivery_manifest)
    except (OSError,ValueError,TypeError,KeyError,zipfile.BadZipFile,ET.ParseError) as exc:
        print(json.dumps({'decision':'VERIFY_FAILED','submission_ready':False,'gate_issues':[],'problems':['[INPUT] '+str(exc)]},ensure_ascii=False));return 2


if __name__ == "__main__":
    sys.exit(main())
