#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""境外法与判例检索通道的可用性体检、按法域选路、官方文本取回与时效报告。

数据源：assets/research-sources.json（外部通道登记表；核验证据写入 data/_provenance/research-<id>.json）
与 fetch_official.py 的分工：本脚本只管"境外法与判例从哪查、能不能查、怎么取回"，
                        机构规则文本与版本适用判定仍走 fetch_official.py。

用法：
  python3 research_sources.py doctor                       # 本机运行时与可安装性
  python3 research_sources.py check [--id <通道id>] [--timeout 15]   # 重核通道（版本漂移＋端点存活）
  python3 research_sources.py plan --jurisdiction DE [--layer lex_arbitri] [--limit 4]
  python3 research_sources.py get --id courtlistener-rest --param query="arbitration award" --out <案件目录>
  python3 research_sources.py report
退出码：0 正常，含"全部通道不可用→降级并披露『未取得一手文本，需外部律师意见』"；
       2 只在继续会写错东西时出现：输入非法、登记表本身坏了、法域代码无法识别。
原则：通道抓不通不是停止工作的理由，而是必须向用户披露检索边界的理由——但绝不据此编造条文号或判例名。
"""
from __future__ import annotations

from _safe_http import public_urlopen, validate_public_url, UnsafeURL
from _pymin import require_python
if __name__ == '__main__':
    require_python(script_name=__file__)

import argparse
import collections
import hashlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path

SUITE = Path(__file__).resolve().parent.parent
REG = SUITE / "assets" / "research-sources.json"
WEB_PATHS = SUITE / "assets" / "official-web-paths.json"
PROV = Path(os.environ.get("RULESUITE_DATA_DIR", str(Path.home() / ".local" / "share" / "you-chu-rulesuite" / "data"))).expanduser().resolve() / "_provenance"
UA = os.environ.get("RULESUITE_USER_AGENT", "RulesuiteBot/2.0 (rulesuite research)")

SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
MAX_ID_LEN = 128
# 参数值只允许安全字符：这些值会被拼进 URL 并落盘，必须挡住路径穿越与控制字符
SAFE_PARAM_RE = re.compile(r"^[\w \.\-+,:/§()（）「」’'\"&%]{1,200}$", re.UNICODE)

NO_TEXT_DISCLOSURE = "未取得一手文本，需外部律师意见"
STALE_DISCLOSURE = "未核验最新检索通道可用性"
UNREGISTERED_DISCLOSURE = ("本套件未登记该法域的检索通道：条文须经联网取官方原文后才能引注，"
                           "未取得原文前不下实体结论，并转外部律师")
# 无登记通道时的降级取文阶梯：按证据力从高到低，逐级说明可否作为引注来源。
# 登记表没有通道不等于无法工作——能取到官方原文就照常引注，取不到则按本阶梯降级并披露。
RETRIEVAL_LADDER = [
    {"tier": 1, "method": "联网取官方原文",
     "how": "先用联网检索定位该国官方立法／判例库（议会、司法部、官方公报、最高法院），"
            "再在该官方站点上取回条文全文；必要时用浏览器工具处理反爬页面",
     "citable": True,
     "trap": "实测常见陷阱：搜索该国仲裁法全文时，排名靠前的多是律所、文库或 NGO 转载的法律 PDF，"
             "形式上就是完整条文，极易被误当作官方原文。判定标准只看托管域名是否为该国官方机构"
             "（议会／司法部／官方公报／法院），不看文件内容像不像正文；"
             "转载件一律降为 tier 2，只能用来定位条号",
     "requires": "记录官方 URL、法律全称与编号、所引条号、版本或生效日期；译本只作辅助，以官方语言原文为准；"
                 "域名是否官方不得自判，须用 research_sources.py judge --url <候选URL> --jurisdiction <法域> 核实；"
                 "判定不是 OFFICIAL／SUPRANATIONAL_OFFICIAL（且适用于本案法域）者一律按 tier 2 处理"},
    {"tier": 2, "method": "联网检索权威二次文献",
     "how": "国际仲裁机构国别报告、UNCITRAL／ICCA 国别资料、大型律所该国仲裁法指南；"
            "非官方域名托管的法律全文 PDF 也属本级",
     "citable": False,
     "requires": "只用于定位条号与判断争点方向，必须回到 tier 1 取官方原文后才能写入文书；"
                 "不得以二次文献的条号转述充当引注"},
    {"tier": 3, "method": "模型内置知识",
     "how": "仅用于搭建程序框架、争点清单与须向外部律师提问的问题单",
     "citable": False,
     "requires": "禁止凭记忆写具体条号、条文内容、期限天数或金额门槛；"
                 "凡具体规则一律标注未核验并分配待核事项编号，转外部律师确认"},
]

# 可直接绑定 law_retrieval 的状态（实测免密可用）
BOUND_OK = {"VERIFIED_KEYLESS", "VERIFIED_REMOTE_MCP"}
# 需要额外条件（Key／运行时／先建库）才能用
CONDITIONAL = {"AUTH_REQUIRED", "PACKAGE_OK_LOCAL_BLOCKED", "BUILD_REQUIRED", "LIVE_CLIENT", "PARTIAL"}
# 只用于定位文件、本身不承载可引注正文的状态：get 不得把其响应当作已取回一手文本
LOCATOR_STATES = {"SECONDARY_ONLY", "BLOCKED"}
STATE_RANK = {"VERIFIED_KEYLESS": 0, "VERIFIED_REMOTE_MCP": 1, "LIVE_CLIENT": 2, "BUILD_REQUIRED": 3,
              "PACKAGE_OK_LOCAL_BLOCKED": 4, "PARTIAL": 5, "AUTH_REQUIRED": 6, "SECONDARY_ONLY": 7,
              "BLOCKED": 8, "DEAD": 9}
RELEVANCE_RANK = {"high": 0, "medium": 1, "low": 2}
LAYERS = {"lex_arbitri", "governing_law", "case_law", "enforcement", "citation_check",
          "compliance_crosscut", "procedure_secondary"}
RUNTIMES = ["python3", "node", "npx", "uvx", "uv", "pipx", "docker"]
# 通道 install.requires 里可能出现的运行时；缺其一则该通道在本机不可跑
RUNTIME_TOOLS = {"node", "npx", "uvx", "uv", "pipx", "docker"}


def available_runtimes() -> set:
    return {rt for rt in RUNTIME_TOOLS if shutil.which(rt)}


def unmet_requires(src: dict, ready: set) -> list:
    """该通道需要但本机缺失的运行时；`node>=18` 这类写法只比对运行时名。"""
    req = (src.get("install") or {}).get("requires") or []
    out = []
    for r in req:
        name = str(r).split(">=")[0].split(">")[0].strip()
        if name in RUNTIME_TOOLS and name not in ready:
            out.append(str(r))
    return out


def load() -> dict:
    return json.loads(REG.read_text(encoding="utf-8")) or {}


def die(msg: str, **extra) -> int:
    out = {"decision": "INVALID_INPUT", "verified": False, "reason": msg, "must_disclose_to_user": False}
    out.update(extra)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2


# 响应体是否真是可读正文。200 状态不等于取到条文：反爬壳、SPA 载入页与无文本层扫描 PDF
# 都会以正常响应返回，若不分级就会被当成已取回的一手文本，绕过"未取得原文须披露"的降级纪律。
SHELL_MARKERS = re.compile(
    rb"(checkclientconfig|javascript is (?:disabled|required|not enabled)"
    rb"|loading required resource|just a moment|please wait.{0,80}loading"
    rb"|access denied|akses ditolak|enable javascript|are you a robot"
    rb"|captcha|please enable cookies|verify you are human|cf-challenge)", re.I)
MIN_VISIBLE = 400          # 去标签后的最少正文字符数，低于此视为壳页
MIN_PDF_FONTS = 1          # 无 /Font 而有 /Image 的 PDF 是影印扫描本


def grade_body(body: bytes, ctype: str) -> tuple:
    """返回 (verdict, note)。verdict 为 'ok' / 'shell' / 'empty' / 'scan' / 'bad'。"""
    if not body or not body.strip():
        return "empty", "空响应"
    ct = (ctype or "").lower()
    if "application/pdf" in ct:
        if not body.startswith(b"%PDF-"):
            return "bad", "content-type 声明为 PDF 但响应体不是 PDF"
        fonts = len(re.findall(rb"/Font\b", body))
        images = len(re.findall(rb"/Subtype\s*/Image", body))
        if fonts < MIN_PDF_FONTS and images >= 1:
            return "scan", (f"PDF 含 {images} 张图像但无 /Font 资源，即整本扫描影印本、无文本层，"
                            "须经 OCR 取得文本后才能核对条文；不得当作已取得可读正文")
        return "ok", f"PDF 有文本层（/Font {fonts} 处）"
    if "html" in ct or "xml" in ct or "json" in ct or ct.startswith("text/"):
        if SHELL_MARKERS.search(body[:40000]):
            return "shell", "响应为反爬／JS 载入壳页，不含正文"
        text = re.sub(rb"<[^>]+>", b" ", body)
        text = re.sub(rb"\s+", b" ", text).strip()
        n = len(text.decode("utf-8", "ignore"))
        if n < MIN_VISIBLE:
            return "shell", f"去标签后可见正文仅 {n} 字符（低于 {MIN_VISIBLE}），疑为壳页或跳转页"
        return "ok", f"可见正文 {n} 字符"
    return "ok", "非网页响应，未作正文长度判定"


def safe_id(sid: str) -> bool:
    if not isinstance(sid, str) or not (0 < len(sid) <= MAX_ID_LEN) or not SAFE_ID_RE.match(sid):
        return False
    return not any(c in sid for c in "\x00\n\r\t\\")


def validate_date(s):
    try:
        return datetime.fromisoformat(s).date()
    except (ValueError, TypeError):
        return None


def sources_of(reg: dict) -> list:
    return list(reg.get("sources") or [])


def index_sources(reg: dict) -> dict:
    return {str(s.get("id")): s for s in sources_of(reg) if s.get("id")}


def read_prov(sid: str) -> dict:
    if not safe_id(sid):
        return {}
    p = PROV / f"research-{sid}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def write_prov(sid: str, data: dict) -> Path:
    PROV.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["_checked_at"] = date.today().isoformat()
    p = PROV / f"research-{sid}.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    return p


def http(url: str, timeout: int = 15, download: bool = False, payload: bytes | None = None,
         headers: dict | None = None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    if payload is not None:
        h["Content-Type"] = "application/json"
        h["Accept"] = "application/json, text/event-stream"
    req = urllib.request.Request(url, data=payload, headers=h, method="POST" if payload else "GET")
    try:
        with public_urlopen(req, timeout=timeout) as r:
            body = r.read(32 * 1024 * 1024 + 1) if download else r.read(4 * 1024 * 1024 + 1)
            if len(body) > (32 if download else 4) * 1024 * 1024:
                raise ValueError("响应超过大小限额")
            head = {k.lower(): v for k, v in r.headers.items()}
            return {"url": url, "status": r.status, "final_url": r.geturl(),
                    "content_type": head.get("content-type"), "last_modified": head.get("last-modified"),
                    "etag": head.get("etag"), "bytes": len(body), "head": head,
                    "sha256": hashlib.sha256(body).hexdigest() if download else None,
                    "_body": body}
    except urllib.error.HTTPError as e:
        snippet = b""
        try:
            snippet = e.read()[:400]
        except Exception:
            pass
        return {"url": url, "status": e.code, "error": f"HTTPError {e.code}", "detail": snippet.decode("utf-8", "ignore")[:220]}
    except Exception as e:
        return {"url": url, "status": 0, "error": f"{type(e).__name__}: {e}"}


def sse_or_json(raw: bytes) -> dict | None:
    text = raw.decode("utf-8", "ignore")
    if text.lstrip().startswith("{"):
        try:
            return json.loads(text)
        except Exception:
            return None
    last = None
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                last = json.loads(line[5:].strip())
            except Exception:
                pass
    return last


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """MCP 握手不自动跟随重定向：3xx 的目标要经过安全检查后才能重试。
    实测有端点把 POST 从 https 重定向到 http，自动跟随会把案情检索词写成明文传输。"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _mcp_post(url: str, payload: dict, timeout: int, extra: dict | None = None, _depth: int = 0):
    """向 streamable HTTP 端点发一次 JSON-RPC，返回 (解析对象, 响应头, HTTP 状态码)。
    每跳复用公共 HTTPS 校验；手动重定向只允许同源，避免泄漏案情、凭据与会话。"""
    try:
        validate_public_url(url)
        body = json.dumps(payload).encode()
        h = {"User-Agent": UA, "Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"}
        h.update(extra or {})
        req = urllib.request.Request(url, data=body, headers=h, method="POST")
        opener = urllib.request.build_opener(_NoRedirect)
        with opener.open(req, timeout=timeout) as r:
            raw = r.read(4 * 1024 * 1024 + 1)
            return sse_or_json(raw), {k.lower(): v for k, v in r.headers.items()}, r.status
    except urllib.error.HTTPError as e:
        try:
            loc = (e.headers.get("Location") if e.headers else None) or ""
            if e.code in (301, 302, 303, 307, 308) and loc:
                target = urllib.parse.urljoin(url, loc)
                if urllib.parse.urlsplit(target).scheme.lower() != "https":
                    return {"_insecure_redirect": target}, {}, e.code
                validate_public_url(target)
                before, after = urllib.parse.urlsplit(url), urllib.parse.urlsplit(target)
                if ((before.scheme, before.hostname, before.port or 443)
                        != (after.scheme, after.hostname, after.port or 443)):
                    raise UnsafeURL("Cross-origin MCP redirect blocked")
                if _depth >= 2:
                    return {"_redirect_loop": target}, {}, e.code
                return _mcp_post(target, payload, timeout, extra, _depth + 1)
            return {"_http_error": e.code}, {}, e.code
        except ValueError as err:
            return {"_error": f"{type(err).__name__}: {err}"}, {}, 0
        finally:
            e.close()
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}, {}, 0


def mcp_handshake(url: str, timeout: int) -> dict:
    """只读握手：initialize → notifications/initialized → tools/list。
    不发 tools/call，因此通过只代表工具面可枚举，不代表其正文级检索可用。"""
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "arbitration-suite-doctor", "version": "1"}}}
    obj, head, http_status = _mcp_post(url, init, timeout)
    out = {"status": http_status, "error": None, "detail": None}
    if isinstance(obj, dict) and obj.get("_http_error"):
        out["status"] = obj["_http_error"]
    elif isinstance(obj, dict) and obj.get("_insecure_redirect"):
        out["status"] = "INSECURE_REDIRECT"
        out["error"] = f"该端点把 MCP 请求重定向到明文：{obj['_insecure_redirect'][:80]}"
        out["initialized"] = False
        out["tools_status"] = "REFUSED_INSECURE_REDIRECT"
        return out
    elif isinstance(obj, dict) and obj.get("_error"):
        out["error"] = obj["_error"]
    session = head.get("mcp-session-id") or head.get("mcpsessionid")
    if isinstance(obj, dict):
        res = obj.get("result") or {}
        out["server_info"] = res.get("serverInfo")
        out["capabilities"] = sorted((res.get("capabilities") or {}).keys())
        if isinstance(obj.get("error"), dict):
            out["rpc_error"] = obj["error"]
    out["initialized"] = bool(isinstance(obj, dict) and obj.get("id") == 1
                              and isinstance(obj.get("result"), dict)
                              and obj["result"].get("protocolVersion") and not obj.get("error"))
    # 会话头：streamable HTTP 服务器多在 initialize 响应里给出 mcp-session-id，后续请求须带上
    if not out["initialized"] or not url:
        out["tools_status"] = "NOT_ATTEMPTED"
        return out
    hdr = {"Mcp-Session-Id": session} if session else {}
    proto = (obj.get("result") or {}).get("protocolVersion")
    if proto:
        hdr["Mcp-Protocol-Version"] = proto
    _n, _nh, _ns = _mcp_post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout, hdr)
    tl, _th, _ts = _mcp_post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, timeout, hdr)
    if isinstance(tl, dict) and tl.get("_http_error"):
        out["tools_status"] = f"HTTP_{tl['_http_error']}"
    elif isinstance(tl, dict) and tl.get("_error"):
        out["tools_status"] = tl["_error"][:60]
    elif isinstance(tl, dict) and isinstance(tl.get("result"), dict) and isinstance(tl["result"].get("tools"), list):
        names = [str(t.get("name")) for t in tl["result"]["tools"] if isinstance(t, dict)]
        out["tools_status"] = "LISTED"
        out["tool_count"] = len(names)
        out["tools"] = names[:80]
    else:
        out["tools_status"] = "NO_TOOLS_IN_RESPONSE"
    return out


def registry_lookup(kind: str, pkg: str, timeout: int) -> dict:
    if kind == "mcp-npm":
        name = urllib.parse.quote(pkg, safe="@")
        r = http(f"https://registry.npmjs.org/{name}", timeout=timeout)
        body = r.get("_body")
        if r.get("status") == 200 and body:
            try:
                j = json.loads(body.decode("utf-8", "ignore"))
                latest = (j.get("dist-tags") or {}).get("latest")
                return {"status": 200, "latest": latest, "license": (j.get("license") or {}).get("type")
                        if isinstance(j.get("license"), dict) else j.get("license"),
                        "engines": (j.get("versions", {}).get(latest or "", {}) or {}).get("engines")}
            except Exception:
                return {"status": 200, "latest": None, "note": "解析失败"}
        return {"status": r.get("status"), "error": r.get("error") or "无版本信息"}
    if kind == "mcp-pypi":
        r = http(f"https://pypi.org/pypi/{urllib.parse.quote(pkg)}/json", timeout=timeout)
        body = r.get("_body")
        if r.get("status") == 200 and body:
            try:
                j = json.loads(body.decode("utf-8", "ignore"))
                return {"status": 200, "latest": (j.get("info") or {}).get("version"),
                        "license": (j.get("info") or {}).get("license"),
                        "requires_python": (j.get("info") or {}).get("requires_python")}
            except Exception:
                return {"status": 200, "latest": None, "note": "解析失败"}
        return {"status": r.get("status"), "error": r.get("error") or "无版本信息"}
    return {"status": 0, "error": "unknown kind"}


def probe_url_for(src: dict) -> dict:
    """给 api/site 通道构造一个只读探活 URL。含必填参数而无默认值时退回站点根路径（仅测存活）。"""
    ep = src.get("endpoint") or {}
    tpl = ep.get("url_template")
    if not tpl:
        return {"skip": True, "reason": "通道无 endpoint.url_template"}
    params = ep.get("params") or {}
    vals = {}
    needs = []
    for k, v in params.items():
        if v in ("required", "optional"):
            needs.append(k)
        else:
            vals[k] = str(v)
    if needs:
        p = urllib.parse.urlsplit(tpl)
        return {"url": f"{p.scheme}://{p.netloc}/", "liveness_only": True, "missing_params": needs}
    url = tpl
    for k, v in vals.items():
        url = url.replace("{" + k + "}", urllib.parse.quote(v, safe="/:-"))
    return {"url": url}


def cmd_doctor(a, reg) -> int:
    found = {}
    for rt in RUNTIMES:
        p = shutil.which(rt)
        ver = None
        if p:
            try:
                r = subprocess.run([rt, "--version"], capture_output=True, text=True, timeout=8)
                ver = (r.stdout or r.stderr).strip().splitlines()[0][:60] if (r.stdout or r.stderr) else None
            except Exception as e:
                ver = f"版本探测失败 {type(e).__name__}"
        found[rt] = {"path": p, "version": ver}
    missing = [rt for rt in RUNTIMES if not found[rt]["path"]]
    ready = available_runtimes()
    blocked = []
    for s in sources_of(reg):
        unmet = unmet_requires(s, ready)
        if unmet:
            blocked.append({"id": s.get("id"), "unmet": unmet})
    out = {"decision": "DOCTOR", "verified": True, "runtimes": found,
           "missing_runtimes": missing, "channels_unrunnable": blocked,
           "python": sys.version.split()[0],
           "action": "缺 node/npx 时 npm 系 MCP 一律不可绑；改用 api/site 免密通道（research_sources.py plan），"
                     "或安装 Node ≥18。缺 pipx/uvx 时 PyPI 系通道同理。",
           "note": "运行时缺失属环境事实，不因此臆定任何条文号。"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_check(a, reg) -> int:
    idx = index_sources(reg)
    if a.id:
        if not safe_id(a.id) or a.id not in idx:
            return die(f"未知通道 id：{a.id}", action="先跑 report 取得通道清单")
        targets = [idx[a.id]]
    else:
        targets = sources_of(reg)
    rows, drift = [], []
    for s in targets:
        sid, kind = str(s.get("id")), str(s.get("kind"))
        res = {"id": sid, "kind": kind, "registered_state": s.get("state"), "registered_checked": s.get("checked")}
        if kind in ("mcp-npm", "mcp-pypi"):
            pkg = s.get("pkg")
            if pkg and "<" not in pkg:
                r = registry_lookup(kind, pkg, a.timeout)
                res["registry"] = r
                if r.get("latest") and s.get("version_known") and r["latest"] != s["version_known"]:
                    res["drift"] = f"{s['version_known']} → {r['latest']}"
                    drift.append(res["id"])
            else:
                res["skip"] = "包名为模板形式（<country>），逐个国别请显式 --id 或改写登记表"
        elif kind == "mcp-git":
            r = http(str(s.get("repo")), timeout=a.timeout)
            body = (r.get("_body") or b"").decode("utf-8", "ignore")
            res["probe"] = {"url": s.get("repo"), "status": r.get("status"), "error": r.get("error"),
                            "archived": "This repository has been archived" in body}
            if res["probe"]["archived"]:
                res["note"] = "仓库已归档：不再维护，绑定前确认上游 API 未变更"
        elif kind == "mcp-remote":
            h = mcp_handshake(str(s.get("url")), a.timeout)
            res["handshake"] = h
            # 工具面漂移：登记时能列出的工具现在列不出，说明服务改名、缩容或换成了别的东西
            known = [str(x) for x in (s.get("capabilities") or [])]
            live = [str(x) for x in (h.get("tools") or [])]
            if known and h.get("tools_status") == "LISTED":
                gone = [t for t in known if t not in live]
                if gone:
                    res["tool_drift"] = {"removed": gone[:12], "live_count": len(live)}
                    drift.append(f"{res['id']}: tools/list 中已无 {', '.join(gone[:5])}")
                if not live:
                    res["tool_drift"] = {"removed": known[:12], "live_count": 0}
        elif kind in ("api", "site"):
            pr = probe_url_for(s)
            if pr.get("skip"):
                res["skip"] = pr["reason"]
            else:
                r = http(pr["url"], timeout=a.timeout)
                res["probe"] = {"url": pr["url"], "status": r.get("status"), "bytes": r.get("bytes"),
                                "content_type": r.get("content_type"), "error": r.get("error"),
                                "liveness_only": pr.get("liveness_only", False),
                                "missing_params": pr.get("missing_params")}
                # 只探活到站点根／缺必填参数时不判正文：首页本来就只是定位入口
                body_b = r.get("_body") or b""
                if not pr.get("liveness_only") and r.get("status") == 200:
                    gv, gn = grade_body(body_b, str(r.get("content_type") or ""))
                    res["probe"]["content_grade"] = gv
                    res["probe"]["content_note"] = gn
        else:
            res["skip"] = f"kind={kind} 无自动核验方式，按登记表与 caveat 处理"
        # 结论：只有实测成功才把 state 保持为可用；否则记 DEGRADED_SINCE 并保留原证据
        st = res.get("handshake", {}).get("status") if kind == "mcp-remote" else res.get("probe", {}).get("status")
        reg_ok = res.get("registry", {}).get("status") == 200 if kind in ("mcp-npm", "mcp-pypi") else None
        grade = res.get("probe", {}).get("content_grade")
        hs_status = res.get("handshake", {}).get("status")
        # 405／400／406 只说明本次探测的请求形态不被接受（可能要求 SSE、不同路径或额外头），
        # 不等于通道坏了：把它记成 UNREACHABLE 会让 plan 把可用通道降级，形成假阴性
        if kind == "mcp-remote" and hs_status in (400, 405, 406):
            res["verdict"] = "TRANSPORT_MISMATCH"
            res["note"] = (f"initialize 返回 {hs_status}：本探测的 JSON-RPC 请求形态不被该端点接受，"
                           "不等于通道不可用。须在客户端里确认传输方式（SSE／不同路径或请求头）后重测，"
                           "不得据此把通道判为失效")
        elif kind == "mcp-remote" and hs_status in (401, 403) and s.get("state") == "VERIFIED_REMOTE_MCP":
            res["verdict"] = "AUTH_OR_FORBIDDEN"
            res["note"] = f"实测无凭据 initialize 返回 {hs_status}：原记免密已验证不成立，须按 auth 字段配好凭据后重验"
        elif grade and grade != "ok":
            res["verdict"] = "NO_TEXT"
            res["note"] = res["probe"].get("content_note")
        elif (st == 200 and (kind != "mcp-remote" or res.get("handshake", {}).get("initialized"))) or (reg_ok is True and res.get("registry", {}).get("latest")):
            res["verdict"] = "ALIVE"
        elif st in (401, 403) or "Authentication required" in json.dumps(res, ensure_ascii=False):
            res["verdict"] = "AUTH_OR_FORBIDDEN"
        elif st == 404:
            res["verdict"] = "GONE"
        elif res.get("skip"):
            res["verdict"] = "NOT_AUTO_CHECKABLE"
        else:
            res["verdict"] = "UNREACHABLE"
        if kind == "mcp-remote" and res["verdict"] == "ALIVE":
            cnt = res.get("handshake", {}).get("tool_count")
            res["note"] = ("握手与 tools/list 通过（枚举 %s 个工具）：仍未发 tools/call，"
                           "正文级检索是否可用须按 acceptance 在客户端验收" % (cnt if cnt else "若干"))
        write_prov(sid, res)
        rows.append({"id": sid, "kind": kind, "registered_state": s.get("state"),
                     "verdict": res["verdict"], "drift": res.get("drift"), "note": res.get("note")})
    n_bad = sum(1 for r in rows if r["verdict"] in ("GONE", "UNREACHABLE", "AUTH_OR_FORBIDDEN", "NO_TEXT"))
    out = {"decision": "CHECKED", "verified": False,
           "liveness_ok": n_bad == 0, "count": len(rows),
           "unavailable": n_bad, "version_drift": drift, "rows": rows,
           "provenance_dir": str(PROV),
           "disclosure": None if n_bad == 0 else STALE_DISCLOSURE,
           "must_disclose_to_user": n_bad > 0,
           "action": "探活完成；包存在、主页可达或 initialize 成功均不等于正文检索通过。须在宿主中执行 acceptance 后绑定" if n_bad == 0
                     else f"{n_bad} 条通道本次实测不可用：按 plan 输出改走免密通道或浏览器／人工路径，"
                          f"并在《中文审阅说明》风险节写出『{STALE_DISCLOSURE}』与具体通道名。"
                          f"登记表 evidence 是历史事实，不据本次失败改写。"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def known_jur(reg: dict) -> set:
    j = set()
    for s in sources_of(reg):
        j |= {str(x).upper() for x in (s.get("jurisdictions") or [])}
    for b in reg.get("blocked_paths") or []:
        j |= {str(x).upper() for x in (b.get("jurisdictions") or [])}
    return j


def independence_report(pool: list) -> dict:
    """按 provider 与 upstream 双维度评估交叉核验强度。

    provider 不同 ⇒ 满足"两条提供方不同的通道交叉一致"（同一提供方的两个工具只算一条来源）；
    upstream 相同 ⇒ 两家渲染的是同一份权威文本，可各自独立抓取与解析，
                   但无法发现该文本本身的问题，故交叉核验较弱。
    """
    subs = sorted({str(s["subdivision"]) for s in pool if s.get("subdivision")})
    if subs:
        # 联邦与州省层承载的是不同法律文本，不能互作交叉核验：分层各算，取最弱一层
        layers = {d: [s for s in pool if s.get("subdivision") == d] for d in subs}
        national = [s for s in pool if not s.get("subdivision")]
        if national:
            layers["national"] = national
        per = {k: _independence_flat(v) for k, v in layers.items()}
        order = ["NO_CHANNEL", "SINGLE_PROVIDER", "SAME_UPSTREAM_ONLY", "PROVIDERS_OK_UPSTREAM_OVERLAP", "INDEPENDENT"]
        worst = dict(min(per.values(), key=lambda r: order.index(r["verdict"])))
        worst["by_subdivision"] = {k: v["verdict"] for k, v in per.items()}
        worst["note"] = "联邦与州省层文本不同，按仲裁地所在层看 by_subdivision；最弱层：" + worst["note"]
        return worst
    return _independence_flat(pool)


def _independence_flat(pool: list) -> dict:
    by_provider, by_upstream = {}, {}
    for s in pool:
        by_provider.setdefault(str(s.get("provider") or s.get("id")), []).append(str(s.get("id")))
        by_upstream.setdefault(str(s.get("upstream") or "unknown"), []).append(str(s.get("id")))
    shared = {u: ids for u, ids in by_upstream.items() if len(ids) > 1}
    providers = len(by_provider)
    if providers == 0:
        verdict = "NO_CHANNEL"
    elif providers == 1:
        verdict = "SINGLE_PROVIDER"
    elif providers >= 2 and len(by_upstream) == 1:
        verdict = "SAME_UPSTREAM_ONLY"
    elif shared:
        verdict = "PROVIDERS_OK_UPSTREAM_OVERLAP"
    else:
        verdict = "INDEPENDENT"
    actions = {
        "NO_CHANNEL": "无可绑定通道：走人工取文路径，law_retrieval 记 degraded，不下实体结论。",
        "SINGLE_PROVIDER": "仅一家提供方，不满足两条独立来源：再绑一家 provider 不同的通道，或把该命题降至 medium 并转外部律师。",
        "SAME_UPSTREAM_ONLY": ("候选通道虽来自不同提供方，但读取的是同一份权威文本：可发现各自的抓取与解析错误，"
                               "不能发现该文本本身的问题。争议命题应再绑一条 upstream 不同的通道，或降至 medium。"),
        "PROVIDERS_OK_UPSTREAM_OVERLAP": ("已有两家以上不同提供方，但部分通道共用同一 upstream；"
                                          "对重要或有争议的命题，指明本次比对用的是哪两条 upstream。"),
        "INDEPENDENT": "提供方与权威源均不同，满足交叉核验；仍须逐命题核对版本、效力与支持程度。",
    }
    return {"providers": providers, "upstreams": len(by_upstream),
            "distinct_providers": sorted(by_provider), "distinct_upstreams": sorted(by_upstream),
            "same_upstream_groups": shared, "verdict": verdict, "note": actions[verdict]}


def effective_state(state: str, probe_verdict) -> str:
    """把登记状态与本次实测结论合成"这台机器上现在能不能取文"。
    实测已失效／被拦／无正文的通道不得在任何出口里被当作可绑定。
    缺运行时是另一件事，由调用方按候选过滤处理，不在此改写状态。"""
    v = probe_verdict
    if v == "GONE":
        return "DEAD"
    if state in BOUND_OK:
        if v == "UNREACHABLE":
            return "BLOCKED"
        if v == "AUTH_OR_FORBIDDEN":
            return "AUTH_REQUIRED"
        if v == "NO_TEXT":
            return "SECONDARY_ONLY"
    return state


ONBOARD_KEYS = {"type", "url", "command", "args"}


def install_route(src, text=False):
    """标明这份接入 JSON 该走 mcp_onboard 还是客户端原生界面。
    不写这一层的话，plan 会把带 headers／env 的接入 JSON 直接交给用户，
    用户拿去 prepare 只会得到一句不解释原因的拒绝。"""
    mj = (src.get("install") or {}).get("mcp_json")
    if not isinstance(mj, dict):
        return "n/a" if not text else "无接入 JSON：该通道不经配置文件接入，按 documentation 与 acceptance 处理"
    extra = set(mj) - ONBOARD_KEYS
    if not extra:
        return "onboard" if not text else (
            "可直接用 mcp_onboard.py prepare/apply 写入（不含任何密钥字段）")
    if any(k in mj for k in ("legifrance", "judilibre")) and all(isinstance(v, dict) for v in mj.values()):
        return "native_ui_multi" if not text else (
            "该条目一次给出多个服务，须按客户端原生界面逐个登记；mcp_onboard 只处理单个服务")
    return "native_ui" if not text else (
        f"接入 JSON 含 {'/'.join(sorted(extra))} 字段（密钥或认证材料）：mcp_onboard 拒绝写凭证，"
        f"须在客户端原生配置界面填入，认证要求见该通道 auth 字段")


def official_web_paths(jurisdiction: str) -> dict:
    """Offline, constant-time navigation lookup. Never represents retrieved law."""
    jur = str(jurisdiction).strip().upper()
    if not re.fullmatch(r"[A-Z]{2,6}", jur):
        raise ValueError("invalid jurisdiction code")
    data = json.loads(WEB_PATHS.read_text(encoding="utf-8"))
    if data.get("schema") != "official-web-paths/1":
        raise ValueError("invalid web-paths schema")
    return {"jurisdiction": jur, "status": "NAVIGATION_ONLY_NOT_VERIFIED",
            "official_candidates": data.get("jurisdictions", {}).get(jur, []),
            "global_navigation": data.get("navigation_fallbacks", []),
            "next_step": "Use agent browser/search to open primary issuer; fetch exact applicable text and verify effective date, version and scope. Do not scrape directories or cite navigation cards as law. If unavailable, mark unresolved and seek local counsel."}


def browser_action_plan(jurisdiction: str, candidates: list) -> dict:
    """Declarative plan consumed by host Agent; NO direct browser automation or scraping."""
    allowed = [x for x in candidates if x.get("url", "").startswith("https://")]
    return {
        "execution": "HOST_AGENT_BROWSER_OR_WEB_SEARCH_ONLY",
        "enabled_if": "Host grants web access and target website permits automation",
        "steps": [
            "Search official publisher for exact law name and version within selected jurisdiction",
            "Retrieve publisher-hosted text and identify effective/amendment dates",
            "Check subnational jurisdiction, translation status, and source provenance",
            "Record exact URL and pinpoint provision in case-local evidence registry"
        ],
        "initial_targets": [x["url"] for x in allowed[:3]],
        "limits": {"initial_official_targets": 3, "browser_if_simple_fetch_fails": True,
                   "no_bulk_crawling": True, "respect_access_controls": True},
        "never": "Never scrape MOFCOM directory, bypass CAPTCHA/login, treat a directory as law, or fabricate citations",
        "evidence": "Official navigation candidate is NOT a verified statute or case"
    }


def cmd_web(a, reg) -> int:
    result = official_web_paths(a.jurisdiction)
    result["browser_action_plan"] = browser_action_plan(result["jurisdiction"], result["official_candidates"])
    print(json.dumps({"decision": "WEB_FALLBACK", **result}, ensure_ascii=False, indent=2))
    return 0


def cmd_plan(a, reg) -> int:
    if getattr(a, 'config', None):
        from research_profile import select
        if not a.capability:
            return die('--config 需要 --capability；法律层次 layer 与检索能力不同')
        print(json.dumps(select(a.config, a.jurisdiction, a.capability, a.task),ensure_ascii=False,indent=2))
        return 0
    jur = str(a.jurisdiction).strip().upper()
    if not re.match(r"^[A-Z]{2,6}$", jur):
        return die(f"法域代码须为 2–6 位大写字母（如 DE/NL/UK/SG/INTL）：{a.jurisdiction}")
    if jur not in known_jur(reg) and jur != "INTL":
        out = {"decision": "PLAN", "jurisdiction": jur, "layer": a.layer,
               "gate": "UNREGISTERED_JURISDICTION",
               "bound_total": 0, "conditional_total": 0, "candidates": [],
               "verified": False, "acceptance_required": True,
               "known_jurisdictions": sorted(known_jur(reg)),
               "retrieval_ladder": RETRIEVAL_LADDER,
               "tier1_official_hosts": tier1_hosts(reg, jur),
               "web_fallback": official_web_paths(jur),
               "global_blocked_or_notes": [{"id": b.get("id"), "title": b.get("title"),
                                            "action": b.get("action"), "browser_url": b.get("browser_url"),
                                            "disclose": b.get("disclose")}
                                           for b in (reg.get("blocked_paths") or [])
                                           if "INTL" in {str(x).upper() for x in (b.get("jurisdictions") or [])}],
               "must_disclose_to_user": True,
               "disclosure": UNREGISTERED_DISCLOSURE,
               "drafting_rule": "登记表没有该法域通道，不等于不能办这件事：按 retrieval_ladder 自上而下取文，"
                                "取到官方原文即可照常引注；停在 tier 2／3 时，该处只写检索路径与待核验表述。"
                                "不得凭记忆补写条号或条文，也不得把二次文献转述当作引注来源。",
               "action": (f"本套件未登记 {jur} 的检索通道。按 retrieval_ladder tier 1 先联网定位该国官方立法／判例库"
                          f"并取回条文原文；取得原文后在《中文审阅说明》写明官方 URL、法律编号与版本日期，"
                          f"law_retrieval 记 degraded (web-official)。"
                          f"确实取不到官方原文时降至 tier 3，只给程序框架与问题单，"
                          f"具体规则分配唯一 Q 编号并转外部律师。")}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    layer = a.layer
    if layer and layer not in LAYERS:
        return die(f"layer 须取 {sorted(LAYERS)}")
    if a.limit < 1:
        return die("--limit 须为正整数（0 或负值会把候选清空并误报闸门）")
    prov_ok = {}
    for s in sources_of(reg):
        p = read_prov(str(s.get("id")))
        if p.get("verdict"):
            prov_ok[str(s.get("id"))] = p["verdict"]
    ready = available_runtimes()
    cands_specific, cands_contextual = [], []
    for s in sources_of(reg):
        js = {str(x).upper() for x in (s.get("jurisdictions") or [])}
        hit_jur = jur in js
        if not (hit_jur or "INTL" in js):
            continue
        if layer and layer not in (s.get("layers") or []):
            continue
        state = str(s.get("state"))
        v = prov_ok.get(str(s.get("id")))
        eff = effective_state(state, v)
        unmet = unmet_requires(s, ready)
        c = {"src": s, "state": state, "effective": eff, "probe_verdict": v, "unmet_runtime": unmet,
             "rank": (0 if hit_jur else 1, STATE_RANK.get(eff, 7), RELEVANCE_RANK.get(str(s.get("relevance")), 3))}
        (cands_specific if hit_jur else cands_contextual).append(c)
    cands_specific.sort(key=lambda c: c["rank"])
    cands_contextual.sort(key=lambda c: c["rank"])
    # 只有"本案法域专属"的免密通道才能满足闸门；通用国际页只作背景与交叉线索
    bound_all = [c for c in cands_specific if c["effective"] in BOUND_OK]
    # Historical registrations and transport probes are candidates, never current full-text acceptance.
    bound_all = [c for c in bound_all if not c["unmet_runtime"]]
    usable = bound_all[: a.limit]
    cond_all = [c for c in cands_specific if c["effective"] in CONDITIONAL]

    def setup_gap(c) -> list:
        """这台机器要把它跑起来还差什么：缺运行时／缺 Key／实测仅部分可用。"""
        ins = c["src"].get("install") or {}
        gaps = []
        if c["unmet_runtime"]:
            gaps.append("runtime:" + ",".join(str(x) for x in c["unmet_runtime"]))
        if ins.get("env_required"):
            gaps.append("key:" + ",".join(str(x) for x in ins["env_required"]))
        if c["effective"] == "AUTH_REQUIRED":
            gaps.append("key:见 auth 字段")
        if c["effective"] == "PARTIAL":
            gaps.append("partial:实测仅部分工具／路径可用")
        return gaps

    for c in cond_all:
        c["setup_gap"] = setup_gap(c)
    installable = [c for c in cond_all if not c["setup_gap"]]
    cond = (installable + [c for c in cond_all if c["setup_gap"]])[: a.limit]
    ctx = cands_contextual[:3]
    blocked, global_blocked = [], []
    for b in reg.get("blocked_paths") or []:
        bs = {str(x).upper() for x in (b.get("jurisdictions") or [])}
        if layer and layer not in (b.get("layers") or []):
            continue
        if jur in bs:
            blocked.append(b)
        elif "INTL" in bs:
            global_blocked.append(b)

    def card(c, tier):
        s = c["src"]
        ins = s.get("install") or {}
        return {"tier": tier, "id": s.get("id"), "title": s.get("title"), "kind": s.get("kind"),
                "provider": s.get("provider"), "upstream": s.get("upstream"), "role": s.get("role"),
                "state": c["state"], "effective": c["effective"], "probe_verdict": c.get("probe_verdict"),
                "subdivision": s.get("subdivision"),
                "auth": s.get("auth"), "layers": s.get("layers"), "relevance": s.get("relevance"),
                "corpus": (s.get("corpus") or {}).get("stats") or (s.get("corpus") or {}).get("mode"),
                "install": ins.get("mcp_json") or {"command": ins.get("command"), "args": ins.get("args")},
                "install_route": install_route(s),
                "install_route_note": install_route(s, True),
                "requires_runtime": ins.get("requires") or [], "unmet_runtime": c["unmet_runtime"],
                "setup_gap": c.get("setup_gap") or [],
                "env_required": ins.get("env_required") or [],
                "acceptance": s.get("acceptance"), "caveat": s.get("caveat"), "fallback": s.get("fallback"),
                "endpoint": (s.get("endpoint") or {}).get("url_template"),
                "checked": s.get("checked"), "capabilities": s.get("capabilities", []),
                "coverage_mode": s.get("coverage_mode"), "adapter": s.get("adapter")}
    locators = [c for c in cands_specific if c["effective"] in LOCATOR_STATES]
    cards = ([card(c, "immediate") for c in usable] + [card(c, "conditional") for c in cond]
             + [card(c, "contextual-only") for c in ctx] + [card(c, "locator") for c in locators[: a.limit]])
    indep = independence_report([c["src"] for c in bound_all])
    if len(bound_all) >= 2:
        gate, disclosure = "BOUND_OK", None if indep["verdict"] == "INDEPENDENT" else indep["note"]
    elif len(bound_all) == 1:
        gate, disclosure = "SINGLE_SOURCE", reg.get("disclosure", {}).get("single_source") or STALE_DISCLOSURE
    elif cond_all:
        gate, disclosure = "RUNTIME_OR_KEY_GAP", (reg.get("disclosure", {}).get("degraded")
                                                  or NO_TEXT_DISCLOSURE)
    else:
        gate, disclosure = "NO_BOUND_CHANNEL", NO_TEXT_DISCLOSURE
    def brief(b):
        return {"id": b.get("id"), "title": b.get("title"), "action": b.get("action"),
                "browser_url": b.get("browser_url"), "disclose": b.get("disclose")}
    if gate == "BOUND_OK":
        ids = "+".join(str(c["src"].get("id")) for c in bound_all[:2])
        action = (f"登记表列出 {indep['providers']} 家提供方 / {indep['upstreams']} 个权威源的 {jur} 候选通道"
                  f"（尚未完成本机正文验收）：逐条跑 acceptance 后写入 law_retrieval，"
                  f"并在 .arbitration-config.md 记 bound ({ids} @ {date.today().isoformat()})；"
                  f"独立性判定 {indep['verdict']} —— {indep['note']}")
    elif gate == "SINGLE_SOURCE":
        action = (f"仅登记一条 {jur} 专属免密候选（{bound_all[0]['src'].get('id')}），仍须验收正文与适用版本；"
                  "披露检索覆盖及交叉核验限制。单一权威全文不等于低质量，多条转载也不等于独立支持；"
                  "复杂解释、效力或适用疑问转外部律师意见")
    elif gate == "RUNTIME_OR_KEY_GAP":
        ready_ids = ", ".join(str(c["src"].get("id")) for c in installable)
        gap_ids = ", ".join(f"{c['src'].get('id')}（{'; '.join(c['setup_gap'])}）"
                            for c in [x for x in cond_all if x["setup_gap"]][:4])
        action = (f"无免密可用通道。本机运行时齐备、现在就能装的：{ready_ids or '（无）'}；"
                  f"还差条件的：{gap_ids or '（无）'}。"
                  "先补条件并跑 acceptance 再决定是否 bound；补不了 → law_retrieval 记 degraded (official-urls only)，"
                  "同时走 blocked_or_manual_paths 取官方文本")
    else:
        action = ("登记表未给出可用自动检索候选：先走 blocked_or_manual_paths 的浏览器／人工取文路径；"
                  "该法域没有登记人工路径时，按 retrieval_ladder tier 1 联网定位官方立法／判例库并取回原文。"
                  "law_retrieval 记 degraded (official-urls only)，取得并核验可靠正文前不下境外法实体结论；"
                  "文书中该处按受控草案分配唯一 Q 编号并登记待核事项。人工取得的正文仍须核查来源、版本与具体命题")
    out = {"decision": "PLAN", "jurisdiction": jur, "layer": layer, "gate": "CANDIDATES_REQUIRE_ACCEPTANCE" if gate in ("BOUND_OK", "SINGLE_SOURCE") else gate,
           "bound_total": len(bound_all), "conditional_total": len(cond_all),
           "independence": indep,
           "scope_note": scope_note(cands_specific),
           "verified": False, "acceptance_required": True, "candidates": cards,
           "contextual_note": "跨法域候选须先发现目标法域覆盖并验收全文；INTL 登记不是全法域覆盖证明，也不自动通过闸门。",
           "locator_note": "tier=locator 的卡片是官方检索门户／首页：用来定位文件，本身不是一手文本，"
                           "不参与闸门计数，也不得以其“可达”充作已取得条文。",
           "blocked_or_manual_paths": [brief(b) for b in blocked],
           "global_blocked_or_notes": [brief(b) for b in global_blocked],
           "retrieval_ladder": RETRIEVAL_LADDER if gate in ("NO_BOUND_CHANNEL", "RUNTIME_OR_KEY_GAP") else None,
           "tier1_official_hosts": tier1_hosts(reg, jur),
           "web_fallback": official_web_paths(jur),
           "must_disclose_to_user": gate != "BOUND_OK",
           "disclosure": disclosure,
           "drafting_rule": "逐命题评价来源权威、现行效力、时间适用及支持程度，重要或有争议的问题尽量独立复核；"
                            "未取得可靠正文时，只给检索路径与待核验表述。人工取得并核验的官方全文也可作为依据，"
                            "不能仅因未配置自动通道否定其可用性；仍有解释或适用疑问时转外部律师。",
           "action": action}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _write_evidence_pair(out_dir: Path, fp: Path, body: bytes, pp: Path, provenance: bytes):
    """Preflight both names, then exclusively create a pair in one pinned directory."""
    files = ((fp, body), (pp, provenance))
    if fp == pp or any(path.parent != out_dir for path, _ in files):
        raise ValueError("证据文件必须直接位于指定输出目录")
    out_dir.mkdir(parents=True, exist_ok=True)
    directory = os.open(out_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    created = {}
    try:
        # lstat semantics also reject dangling symlinks, directories and old evidence.
        for path, _ in files:
            try:
                os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise FileExistsError(f"输出已存在，拒绝覆盖或跟随符号链接：{path.name}")
        with ExitStack() as stack:
            streams = []
            for path, data in files:
                fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
                info = os.fstat(fd)
                created[path.name] = (info.st_dev, info.st_ino)
                stream = stack.enter_context(os.fdopen(fd, "wb"))
                streams.append((stream, data))
            # Both names are reserved before writing; provenance is written last.
            for stream, data in streams:
                stream.write(data)
                stream.flush()
    except BaseException:
        # Remove only this attempt's files, not pre-existing or concurrently replaced names.
        for name, identity in reversed(list(created.items())):
            try:
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
                if (info.st_dev, info.st_ino) == identity:
                    os.unlink(name, dir_fd=directory)
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(directory)


def cmd_get(a, reg) -> int:
    src = index_sources(reg).get(str(a.id))
    if src is None:
        return die(f"未知通道 id：{a.id}")
    ep = src.get("endpoint") or {}
    tpl = ep.get("url_template")
    if not tpl:
        return die(f"通道 {a.id} 无 endpoint.url_template，不适用 get", action="该通道请经 MCP 客户端调用，或走人工路径")
    if str(src.get("state")) in LOCATOR_STATES:
        out = {"decision": "LOCATOR_ONLY_CHANNEL", "verified": False, "channel": src["id"], "url": tpl,
               "must_disclose_to_user": True, "disclosure": NO_TEXT_DISCLOSURE,
               "action": f"通道 {src['id']} 登记为仅定位（state={src.get('state')}）：它是官方检索门户，"
                         "首页正文多但没有任何条文，取回也不能充当一手文本。先在该站内定位本案所引法令／判决的具体条目，"
                         "记下其详情页或文件 URL，再用承载该 URL 的通道取文，或按人工取文流程处理并另记来源与核验日期。"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    allow_host = ep.get("allow_host")
    params = {}
    for kv in a.param or []:
        if "=" not in kv:
            return die(f"--param 须为 k=v 形式：{kv}")
        k, v = kv.split("=", 1)
        v = v.strip()
        if not re.match(r"^[A-Za-z0-9_\-.]{1,40}$", k):
            return die(f"参数名非法：{k}")
        if not SAFE_PARAM_RE.match(v):
            return die(f"参数值含不允许的字符（防注入与路径穿越）：{k}", action="改用官方站点检索页或浏览器取文")
        params[k] = v
    declared = set((ep.get("params") or {}).keys())
    url = tpl
    for k in sorted(declared):
        if "{" + k + "}" in url:
            if k not in params:
                if (ep["params"]).get(k) == "required":
                    return die(f"缺少必填参数 {k}", required=sorted(declared))
                if ep["params"][k] == "optional":
                    url = url.replace("/{" + k + "}", "").replace("{" + k + "}", "")
                    continue
                params[k] = str(ep["params"][k])
            url = url.replace("{" + k + "}", urllib.parse.quote(params[k], safe="/:-"))
    for k, v in params.items():
        if k not in declared:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v})
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or (allow_host and p.netloc != allow_host):
        return die("渲染后的主机不在该通道的白名单内", url=url, allow_host=allow_host)
    out_dir = Path(a.out).resolve() if a.out else None
    if out_dir is None:
        return die("必须用 --out 指定案件工作目录", action="按铁律 8，取回的文本只进用户指定工作目录")
    try:
        out_dir.relative_to(SUITE)
        return die("拒绝写入技能包目录：--out 不得位于套件内", out=str(out_dir))
    except ValueError:
        pass
    r = http(url, timeout=a.timeout, download=True)
    if r.get("status") != 200 or not isinstance(r.get("_body"), bytes):
        out = {"decision": "FETCH_FAILED", "verified": False, "url": url, "status": r.get("status"),
               "error": r.get("error") or r.get("detail"), "must_disclose_to_user": True,
               "disclosure": NO_TEXT_DISCLOSURE,
               "action": "本机取不到正文（常见为反爬 202／403／SPA 壳）：改用浏览器打开同一 URL 另存，"
                         "或走 plan 给出的其他通道；文书中该处条文号写占位，不得凭记忆补写。"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    body = r["_body"]
    ct = (r.get("content_type") or "").lower()
    verdict, note = grade_body(body, ct)
    if verdict in ("empty", "shell", "bad"):
        out = {"decision": "FETCH_FAILED", "verified": False, "content_grade": verdict,
               "url": url, "bytes": len(body), "content_type": r.get("content_type"),
               "error": note, "must_disclose_to_user": True,
               "disclosure": NO_TEXT_DISCLOSURE,
               "action": "本机取到响应但其中没有正文（反爬壳、SPA 载入页、跳转页或空响应）："
                         "改用浏览器打开同一 URL 另存后人工取文，或走 plan 给出的其他通道。"
                         "文书中该处条文号写占位并分配唯一 Q 编号，不得凭记忆补写，也不得把本次下载当作一手文本。"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    ext = {"application/pdf": ".pdf", "text/html": ".html", "application/xml": ".xml",
           "application/json": ".json"}.get((r.get("content_type") or "").split(";")[0].strip(), ".txt")
    slug = re.sub(r"[^A-Za-z0-9_.-]", "-", "|".join(f"{k}{v}" for k, v in params.items()))[:60] or "page"
    fp = out_dir / f"{src['id']}-{slug}{ext}"
    scanned = verdict == "scan"
    prov = {"channel": src["id"], "title": src.get("title"), "url": url, "final_url": r.get("final_url"),
            "retrieved_at": datetime.now().isoformat(timespec="seconds"),
            "bytes": len(body), "sha256": r["sha256"], "content_type": r.get("content_type"),
            "content_grade": verdict, "content_note": note,
            "layer": src.get("layers"), "corpus_mode": (src.get("corpus") or {}).get("mode"),
            "tier": "下载响应，来源层级与正文内容须人工核对",
            "citable": not scanned,
            "caveat": src.get("caveat")}
    pp = fp.with_suffix(ext + ".provenance.json")
    try:
        _write_evidence_pair(out_dir, fp, body, pp, json.dumps(prov, ensure_ascii=False, indent=2).encode("utf-8"))
    except (OSError, ValueError) as e:
        return die(f"拒绝写入证据：{e}", action="未生成成功凭证；请保留已有证据并选择新的 --out 输出目录")
    if scanned:
        out = {"decision": "FETCHED_SCAN_OCR_REQUIRED", "verified": False, "content_grade": verdict,
               "file": str(fp), "provenance": str(pp), "bytes": len(body),
               "content_type": r.get("content_type"), "must_disclose_to_user": True,
               "disclosure": NO_TEXT_DISCLOSURE + "（本件为官方扫描影印 PDF，尚无文本层，尚未读到任何条文）",
               "action": "官方扫描件已存进案件目录但其中无可检索文本：先 OCR 取文，再逐条核对条号与版本；"
                         "在 OCR 文本被核对之前，该处一律按未取得一手文本处理——条号写占位、分配唯一 Q 编号，"
                         "不得给出实体结论。本条不附 citation_stub，因为尚无任何条文被读过。"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    out = {"decision": "FETCHED", "verified": False, "content_review_required": True, "file": str(fp), "provenance": str(pp),
           "bytes": len(body), "content_type": r.get("content_type"), "content_grade": verdict, "content_note": note,
           "citation_stub": f"[source:{src['id']} | {prov['retrieved_at'][:10]} | [[条号待核]] | {url} | 校验 {date.today().isoformat()}]",
           "action": "取回文本仍需按 references/foreign-law-research.md 的来源分层定级；"
                     "非官方镜像与聚合层不得作引注来源，须回官方原文逐字核对。"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0



def _host_key(h):
    """Normalize a hostname/authority, never interpreting userinfo as a host."""
    h = str(h or "").strip()
    if not h or any(ord(c) <= 32 for c in h):
        return ""
    try:
        return ipaddress.ip_address(h).compressed
    except ValueError:
        pass
    try:
        parsed = urllib.parse.urlsplit("//" + h)
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            return ""
        # Accessing .port rejects malformed/out-of-range ports without splitting IPv6.
        parsed.port
    except ValueError:
        return ""
    h = parsed.hostname.lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def _match_host(host, table):
    """按注册域后缀匹配：en.gesetze-im-internet.de 命中 www.gesetze-im-internet.de。"""
    hk = _host_key(host)
    best = None
    for e in table:
        base = _host_key(e.get("host"))
        if not base:
            continue
        if hk == base or hk.endswith("." + base):
            if best is None or len(base) > len(_host_key(best.get("host"))):
                best = e
    return best


def hosts_of_jur(reg, jur):
    out = []
    for e in reg.get("official_hosts") or []:
        js = {str(x).upper() for x in (e.get("jurisdictions") or [])}
        if not jur or jur in js or "INTL" in js or e.get("authority") == "supranational":
            out.append(e)
    return out


def scope_note(cands):
    """通道只在某个州省／自由区生效时必须在输出里点明。
    只给"该法域有可用通道"会让仲裁地与通道作用域错配（温哥华的案子用安大略法，或迪拜大陆用 ADGM 规则）。"""
    subs = sorted({str(c["src"].get("subdivision")) for c in cands if c["src"].get("subdivision")})
    if not subs:
        return None
    return ("以下标注了 subdivision 的通道只在其州省／自由区范围内生效：" + "、".join(subs) +
            "。须按本案仲裁地或资产所在地匹配后才算可用；作用域不符的通道不得计入交叉核验，"
            "也不得据以认定该国已有可用条文来源。")


def tier1_hosts(reg, jur):
    """本套件已证实为该法域官方、且能判定 tier 1 资格的域名。
    台账不穷举：未列出的域名一律先按 tier 2 处理，用 judge 核实后再补录。"""
    out = []
    for e in reg.get("official_hosts") or []:
        js = {str(x).upper() for x in (e.get("jurisdictions") or [])}
        if jur and jur not in js and "INTL" not in js:
            continue
        out.append({"host": e.get("host"), "authority": e.get("authority"),
                    "status": e.get("status"), "official_for": sorted(js),
                    "note": e.get("note")})
    return out


def cmd_judge(a, reg) -> int:
    """判定一个 URL 的托管域名是否为本套件已证实的官方来源。
    存在理由：retrieval_ladder tier 1 是唯一允许直接引注的降级档位，而其判据是"托管域名是否官方"；
    没有可核对的台账时这一判据只能靠模型自觉，最容易在不自知的情况下把转载件当官方原文。"""
    url = str(a.url or "").strip()
    if not re.match(r"^https?://", url, re.I):
        return die("judge --url 须为完整 http(s) URL", action="只给域名也要带 scheme，避免误判")
    try:
        parsed = urllib.parse.urlsplit(url)
        if (any(ord(c) <= 32 for c in url) or not parsed.hostname
                or parsed.username is not None or parsed.password is not None):
            return die("judge URL 必须包含主机且不得含 userinfo／空白字符", tier1_allowed=False)
        parsed.port
        host = parsed.hostname
    except ValueError:
        return die("judge URL 主机或端口非法", tier1_allowed=False)
    jur = str(a.jurisdiction).strip().upper() if a.jurisdiction else None
    if jur and not re.match(r"^[A-Z]{2,6}$", jur):
        return die("法域代码须为 2–6 位大写字母")
    no = _match_host(host, reg.get("non_official_hosts") or [])
    if no:
        out = {"decision": "NOT_OFFICIAL", "host": host, "jurisdiction": jur, "tier1_allowed": False,
               "authority": "non_official", "why": no.get("why"), "evidence": no.get("evidence"),
               "must_disclose_to_user": True,
               "action": "该域名已被本套件证实为非官方发布方：只可用来定位条号与争点（tier 2），"
                         "不得作为一手文本引注。需要 tier 1 时改从同法域官方域名取同一法律，或转外部律师。"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return 0
    e = _match_host(host, reg.get("official_hosts") or [])
    if not e:
        out = {"decision": "UNVERIFIED_HOST", "host": host, "jurisdiction": jur, "tier1_allowed": False,
               "must_disclose_to_user": True,
               "action": "本套件的官方域名台账未收录该域名，因此不能认定它是 tier 1 官方原文。"
                         "默认按 tier 2 处理：可定位条号，不得直接引注。要升 tier 1 须实证其一："
                         "(a) 该域名在目标法域政府站点上有明确的“官方法律发布机关”身份说明；"
                         "(b) 该国官方立法／公报站点的链接指向它；确认后写入 official_hosts 并记 evidence。"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return 0
    js = {str(x).upper() for x in (e.get("jurisdictions") or [])}
    supra = e.get("authority") == "supranational"
    if jur and supra and jur not in js and "INTL" not in js:
        out = {"decision": "SUPRANATIONAL_NOT_APPLICABLE", "host": host, "jurisdiction": jur,
               "official_for": sorted(js), "authority": e.get("authority"), "tier1_allowed": False,
               "must_disclose_to_user": True,
               "action": f"该文本是 {'/'.join(sorted(js))} 的官方（超国家）法源，而本案法域 {jur} 不在其适用范围内："
                         "引它不等于核验了 {0} 的现行法，不得充当本案法域的一手文本。"
                         "只有当本案争点本身就落在这部超国家文书的适用范围内（如该统法文件对成员国的仲裁地法、"
                         "或当事人选定的公约／示范法）时才能作 tier 1。".format(jur)}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return 0
    if jur and not supra and jur not in js and "INTL" not in js:
        out = {"decision": "OFFICIAL_OTHER_JURISDICTION", "host": host, "jurisdiction": jur,
               "official_for": sorted(js), "authority": e.get("authority"), "tier1_allowed": False,
               "must_disclose_to_user": True,
               "action": f"该域名是官方站点，但承载的是 {'/'.join(sorted(js))} 的文本，不是 {jur} 的一手法源。"
                         "只可作背景与交叉线索（如同引示范法不等于核验了本案法域条文），不得充当本案法域原文。"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return 0
    ok_text = e.get("status") == "verified_text"
    out = {"decision": "SUPRANATIONAL_OFFICIAL" if supra else "OFFICIAL",
           "host": host, "jurisdiction": jur, "authority": e.get("authority"),
           "status": e.get("status"), "official_for": sorted(js), "via": e.get("via"),
           "tier1_allowed": True,
           "note": e.get("note"),
           "must_disclose_to_user": not ok_text,
           "action": ("该域名已由本套件实测取回过真实法律文本：从同一主机取到本案所引条文并记录 URL、"
                      "法律编号与版本日期后即可按 tier 1 引注；条号与版本仍须逐条核对。"
                      + ("但本条属跨法域文书：只有当待证命题本身就是这部文书的内容时才算一手依据，"
                         "引它不等于核验了本案法域的国内法。" if (supra or "INTL" in js) else "") if ok_text else
                      "该域名是该法域的官方发布方，但本套件尚未从它取回过正文：以浏览器取回条文并核对版本后按 tier 1 引注，"
                      "取回前不得声称已取得一手文本。" + (f" 注意适用范围：{e.get('note')}" if e.get("note") else ""))}
    print(json.dumps(out, ensure_ascii=False, indent=2)); return 0


def cmd_report(a, reg) -> int:
    cadence = int(reg.get("refresh_cadence_days") or 90)
    rows, stale = [], []
    for s in sources_of(reg):
        # 与 install_suite 同口径：未连接账户的通道以 documentation_checked 计时，
        # 否则该条会永久挂在 stale 上，把真正的过期信号稀释掉
        c = validate_date(str(s.get("checked") or "")) or validate_date(str(s.get("documentation_checked") or ""))
        days = (date.today() - c).days if c else None
        r = {"id": s.get("id"), "kind": s.get("kind"), "state": s.get("state"),
             "relevance": s.get("relevance"), "auth": s.get("auth"),
             "jurisdictions": s.get("jurisdictions"), "checked": s.get("checked"),
             "age_days": days, "provenance_verdict": read_prov(str(s.get("id"))).get("verdict")}
        if days is None or days > cadence:
            stale.append(s.get("id"))
            r["stale"] = True
        rows.append(r)
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    # 覆盖面汇总：各层在各法域究竟有没有可绑定正文通道。文档不再手抄法域名单，
    # 名单一律由这里产出，避免"文档说的和 plan 算的不一样"这类过期
    prov_now = {str(x.get("id")): read_prov(str(x.get("id"))).get("verdict") for x in sources_of(reg)}
    jur_layer = collections.defaultdict(lambda: collections.defaultdict(set))
    for s_ in sources_of(reg):
        eff = effective_state(str(s_.get("state")), prov_now.get(str(s_.get("id"))))
        bucket = ("text" if eff in BOUND_OK else
                  "gated" if eff in CONDITIONAL else
                  "locator" if eff in LOCATOR_STATES else "none")
        for j in s_.get("jurisdictions") or []:
            for L in s_.get("layers") or []:
                jur_layer[L][str(j).upper()].add(bucket)
    for b in reg.get("blocked_paths") or []:
        for j in b.get("jurisdictions") or []:
            for L in b.get("layers") or []:
                jur_layer[str(L)][str(j).upper()].add("manual")
    coverage = {}
    for L, per_j in jur_layer.items():
        c = {"jurisdictions_with_channel_or_path": len(per_j)}
        for want, key in (("text", "text"), ("gated", "gated"), ("manual", "manual"), ("locator", "locator")):
            c[key] = sorted(j for j, bset in per_j.items() if want in bset)
        coverage[L] = c
    out = {"decision": "REPORT", "verified": False, "registry_fresh": not stale, "generated_of_registry": reg.get("generated"),
           "cadence_days": cadence, "sources": len(rows), "by_state": counts,
           "blocked_paths": len(reg.get("blocked_paths") or []), "dead_claims": len(reg.get("dead_claims") or []),
           "coverage": coverage,
           "discovery_channels": len(reg.get("discovery") or []),
           "stale_ids": stale, "rows": rows,
           "must_disclose_to_user": bool(stale),
           "disclosure": STALE_DISCLOSURE if stale else None,
           "action": "stale 通道须重跑 check 才能继续作为 law_retrieval 绑定依据；"
                     f"DEAD 与 dead_claims 所列名称已被证伪，不得再写入任何客户端配置。"
                     f"本次报告生成于 {date.today().isoformat()}。"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    require_python(script_name=__file__)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("doctor")
    p = sub.add_parser("check")
    p.add_argument("--id")
    p.add_argument("--timeout", type=int, default=15)
    p = sub.add_parser("plan")
    p.add_argument("--jurisdiction", required=True)
    p.add_argument("--config")
    p.add_argument("--capability", choices=["coverage","legislation","case_law","full_text","citation_check","treatment"])
    p.add_argument("--task")
    p.add_argument("--layer")
    p.add_argument("--limit", type=int, default=4)
    p = sub.add_parser("web", help="无MCP时按法域给出官方法律网站导航（不自动抓取、不证明条文已核）")
    p.add_argument("--jurisdiction", required=True)
    p = sub.add_parser("get")
    p.add_argument("--id", required=True)
    p.add_argument("--param", action="append", default=[])
    p.add_argument("--out")
    p.add_argument("--timeout", type=int, default=25)
    p = sub.add_parser("judge", help="判定 URL 的托管域名是否为本套件已证实的官方来源（tier 1 资格）")
    p.add_argument("--url", required=True)
    p.add_argument("--jurisdiction")
    p.set_defaults(func=cmd_judge)

    p = sub.add_parser("mcp-route", help="按本案能力、近期验收记录分级 MCP（只读、离线）")
    p.add_argument("--jurisdiction", required=True)
    p.add_argument("--capability", required=True, choices=["coverage","legislation","case_law","full_text","citation_check","treatment"])
    p.add_argument("--observations", help="用户案件目录内的观测记录 JSON；无记录不声称可用")
    p.add_argument("--max-age-hours", type=int, default=24)
    p = sub.add_parser("report")
    a = ap.parse_args()
    if not REG.exists():
        return die(f"缺少登记表 {REG}")
    try:
        reg = load()
    except Exception as e:
        return die(f"登记表 JSON 已损坏：{type(e).__name__}: {e}")
    if str(reg.get("schema")) != "research-sources/1":
        return die("登记表 schema 不符", found=reg.get("schema"), expected="research-sources/1")
    if not sources_of(reg):
        return die("登记表 sources 为空")
    try:
        if a.cmd == "mcp-route":
            from mcp_quality import evaluate
            if not 1 <= a.max_age_hours <= 168:
                return die("--max-age-hours must be between 1 and 168")
            observations = {}
            if a.observations:
                case_file = Path(a.observations).expanduser().resolve()
                if case_file.is_relative_to(SUITE):
                    return die("案件级 MCP 观测记录不得保存在技能包内")
                observations = json.loads(case_file.read_text(encoding="utf-8"))
            out = evaluate(reg, observations, a.jurisdiction.strip().upper(), a.capability, a.max_age_hours)
            out["web_fallback"] = official_web_paths(a.jurisdiction)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        return {"doctor": cmd_doctor, "check": cmd_check, "plan": cmd_plan, "get": cmd_get,
                "judge": cmd_judge, "report": cmd_report, "web": cmd_web}[a.cmd](a, reg)
    except (OSError, ValueError, TypeError) as e:
        return die(f"执行失败：{type(e).__name__}: {e}")


if __name__ == "__main__":
    sys.exit(main())
