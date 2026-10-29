"""Two marker grammars, one parser.

Delivery citations (case documents, review notes, case-local source cards):

    [source:<id> | <version> | <locator> | <https URL> | 校验 YYYY-MM-DD]

Knowledge anchors (only ``assets/institutional-knowledge/**``):

    [kb:<id> | <title> | <locator>]

A knowledge anchor is a compile-time pointer into the registry, not a case-level
citation: it carries no date and no URL, and it must never be copied into a
deliverable.  A delivery citation carries the five fields the verifier checks
against the source ledger and must never appear in the bundled knowledge files.
Only ``https://`` is accepted; a plain ``http://`` URL is a hard error, never a
silent downgrade.

In Markdown table cells a literal ``|`` terminates the cell, so markers there
write every separator as ``\\|``.  ``split_fields`` treats ``\\|`` as a
separator, not as content; a field that genuinely needs a vertical bar should
use ``/`` or ``、`` instead.  The same applies to formatting: pass
``table_cell=True`` to emit ``\\|`` separators.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

PLACEHOLDER_HOSTS = ("localhost", "127.0.0.1", "example.com", "example.org", "example.net")
SOURCE_NAMES = ("source", "kb")
MARKER_RE = re.compile(r"\[(source|kb):([^\]\r\n]*)\]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\r\n]*`")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CHECKED_RE = re.compile(r"^校验\s*(\d{4}-\d{2}-\d{2})$")
LOCATOR_RE = re.compile(
    r"(?:Art\.?|Article|Rule|Section|§|Schedule|Annex|Appendix|Chapter|Part|"
    r"Introduction|Preamble|序言|引言|附录|第\s*[0-9一二三四五六七八九十百千]+\s*条|"
    r"\b[RREL]-\d)", re.I)
EXAMPLE_MARKS = ("...", "…", "YYYY", "<")


@dataclass(frozen=True)
class Marker:
    kind: str
    raw: str
    line: int
    example: bool = False


def _clean(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip()


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", _clean(value)).casefold()


def split_fields(inner: str) -> list:
    """Split a marker body; ``\\|`` is a separator (table-cell form), never content."""
    return [part.strip() for part in inner.replace("\\|", "|").split("|")]


def registry_titles(registry: dict) -> dict:
    """Map every registered source id to its title (first title wins)."""
    titles = {}

    def walk(node):
        if isinstance(node, dict):
            sid = node.get("id")
            title = node.get("title")
            if isinstance(sid, str) and isinstance(title, str) and sid not in titles:
                titles[sid] = title
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    if isinstance(registry, dict):
        if all(isinstance(v, str) for v in registry.values()) and "institutions" not in registry:
            return dict(registry)
        walk(registry)
    return titles


def _url_issues(parts: list) -> list:
    issues = []
    for part in parts:
        if not part.lower().startswith(("http://", "https://")):
            continue
        host = (urlsplit(part).hostname or "").lower()
        if not host:
            issues.append(f"来源 URL 无法解析：{part}")
        elif host in PLACEHOLDER_HOSTS or host.endswith((".invalid", ".example", ".test")) or "invalid" in host.split("."):
            issues.append(f"来源 URL 非官方可核验地址：{part}")
    return issues


def _source_url_issues(sid: str, parts: list, valid_ids: set, url_check) -> list:
    issues = []
    if not sid or sid not in valid_ids or url_check is None:
        return issues
    for part in parts:
        if part.startswith("https://"):
            issue = url_check(sid, part)
            if issue:
                issues.append(issue)
    return issues


def parse_source_marker(marker: str, valid_ids: set, url_check=None) -> tuple:
    match = MARKER_RE.fullmatch(marker.strip())
    if not match or match.group(1) != "source":
        return None, ["不是 source 标记"]
    parts = split_fields(match.group(2))
    sid = parts[0].strip("`*_ ") if parts else ""
    issues = []
    if not sid:
        issues.append("source 标记缺 id")
    elif valid_ids and sid not in valid_ids:
        import difflib
        near = difflib.get_close_matches(sid, sorted(valid_ids), n=3)
        issues.append(f"WARN 来源 ID `{sid}` 不在登记表；建议 {near}，也可使用本案真实国内外法来源，须另行核验来源记录")
    if any(part.lower().startswith("http://") for part in parts):
        issues.append("来源 URL 须为 https://，不得使用 http://")
    if len(parts) > 3 and parts[3].strip().lower() in ("同上", "same", "idem"):
        issues.append("来源 URL 段不得写同上，须重复完整 URL")
    issues.extend(_url_issues(parts))
    issues.extend(_source_url_issues(sid, parts, valid_ids, url_check))
    if len(parts) != 5 or any(not part for part in parts):
        issues.append("须按顺序含非空 id、版本、定位、URL、校验日期五项")
    if len(parts) == 5 and (
            not parts[3].startswith("https://")
            or not CHECKED_RE.fullmatch(parts[4])):
        issues.append("URL 或校验日期字段位置无效")
    if not any(part.lower().startswith(("https://", "http://")) for part in parts):
        issues.append("缺来源 URL")
    dated = CHECKED_RE.fullmatch(parts[4]) if len(parts) == 5 else None
    if len(parts) == 5:
        try:
            if not dated or date.fromisoformat(dated.group(1)) > date.today():
                issues.append("校验日期缺失或在未来")
        except ValueError:
            issues.append("校验日期无效")
    if len(parts) == 5 and all(parts):
        version, locator = parts[1], parts[2]
        if DATE_RE.fullmatch(version) or re.fullmatch(r"生效\s*\d{4}-\d{2}-\d{2}", version):
            issues.append("版本段不得只写日期或生效日，须写精确版本标签")
        if not LOCATOR_RE.search(locator) or locator.startswith(("http://", "https://")):
            issues.append("定位段须为条号/条款/章节等可定位引用，不得写生效日、版本标题或首页 URL")
    fields = {
        "source_id": sid,
        "version": parts[1] if len(parts) > 1 else "",
        "locator": parts[2] if len(parts) > 2 else "",
        "url": parts[3] if len(parts) > 3 else "",
        "checked_at": dated.group(1) if dated else "",
        "raw": marker.strip(),
    }
    return fields, issues


def parse_kb_marker(marker: str, registry: dict) -> tuple:
    match = MARKER_RE.fullmatch(marker.strip())
    if not match or match.group(1) != "kb":
        return None, ["不是 kb 标记"]
    parts = split_fields(match.group(2))
    titles = registry_titles(registry)
    sid = parts[0].strip("`*_ ")
    issues = []
    if len(parts) != 3 or any(not part for part in parts):
        issues.append("须按顺序含非空 id、版本、定位三项")
    if not sid:
        issues.append("知识锚点缺 id")
    elif titles and sid not in titles:
        issues.append(f"知识锚点来源 ID 不在登记表：{sid}")
    elif titles:
        version = parts[1] if len(parts) > 1 else ""
        if normalize_title(version) != normalize_title(titles[sid]):
            issues.append(f"知识锚点版本与登记表 title 不一致：{version!r} != {titles[sid]!r}")
    locator = parts[2] if len(parts) > 2 else ""
    if locator:
        if locator.startswith(("http://", "https://")):
            issues.append("知识锚点定位不得为 URL")
        if locator in ("...", "…", "[[", "待核验") or locator.startswith("[["):
            issues.append("知识锚点定位不得为占位符")
        if len(locator) > 80:
            issues.append("知识锚点定位超过 80 字符")
    fields = {
        "source_id": sid,
        "version": parts[1] if len(parts) > 1 else "",
        "locator": locator,
        "raw": marker.strip(),
    }
    return fields, issues


def _without_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def iter_markers(text: str) -> list:
    """Yield markers in prose, skipping fenced blocks and inline code.

    Example markers (containing ``...``, ``YYYY`` or ``<...>``) are returned with
    ``example=True`` so callers can skip them instead of treating syntax
    snippets in the documentation as live anchors.
    """
    markers = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in MARKER_RE.finditer(_without_inline_code(line)):
            inner = match.group(2)
            example = any(mark in inner for mark in EXAMPLE_MARKS)
            markers.append(Marker(kind=match.group(1), raw=match.group(0), line=number, example=example))
    return markers


def _checked_field(value) -> str:
    value = str(value).strip()
    if value.startswith("校验"):
        value = value[2:].strip()
    if not DATE_RE.fullmatch(value):
        raise ValueError(f"核对日期须为 YYYY-MM-DD：{value!r}")
    date.fromisoformat(value)
    return value


def _field(value, name: str) -> str:
    value = str(value).strip()
    if not value:
        raise ValueError(f"{name} 不得为空")
    if "|" in value or "\\|" in value:
        raise ValueError(f"{name} 不得含竖线，请改用 / 或 、：{value!r}")
    return value


def format_source_marker(source_id, version, locator, url, checked_at, table_cell: bool = False) -> str:
    fields = [
        _field(source_id, "来源 id"),
        _field(version, "版本"),
        _field(locator, "定位"),
        _field(url, "URL"),
        "校验 " + _checked_field(checked_at),
    ]
    if not fields[3].startswith("https://"):
        raise ValueError("URL 须为 https:// 地址")
    sep = " \\| " if table_cell else " | "
    return "[source:" + sep.join(fields) + "]"


def format_kb_marker(source_id, version, locator, table_cell: bool = False) -> str:
    fields = [_field(source_id, "来源 id"), _field(version, "版本"), _field(locator, "定位")]
    sep = " \\| " if table_cell else " | "
    return "[kb:" + sep.join(fields) + "]"


def source_marker_issues(marker: str, valid_ids: set, url_check=None) -> list:
    _, issues = parse_source_marker(marker, valid_ids, url_check)
    return issues


def format_citation(fields: dict, table_cell: bool = False) -> str:
    return format_source_marker(fields["source_id"], fields["version"], fields["locator"],
                                fields["url"], fields["checked_at"], table_cell=table_cell)
