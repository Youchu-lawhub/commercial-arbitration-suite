---
name: 03-forum-rules
description: 机构规则与官方指引的实时调取与答疑：按仲裁启动日判定适用版本，取回官方文本并逐条核对，输出带来源标记的条文答案与本地缓存凭证。跨阶段被调用。
---

# 机构规则实时调取

本子技能是全套件唯一的"条文进货渠道"。其他子技能需要条号、期限、格式要件、费用档级时都走这里；未取得文本前不得落笔（铁律 1、2）。

## 一、入口闸门

材料要求以 `suite.yaml` 的本子技能条目为唯一依据。已在会话中明确的事实直接登记，不重复索取。
对实际案件，先核对本案配置，再把已读取的材料逐项登记到案件根 `case.json`（`rulesuite-case/1`）；台账 `case` 与配置一致，Markdown 清单仅由台账生成供人阅读。

```bash
python3 <suite>/scripts/route.py --gate 03-forum-rules --workdir <案件目录> --provided <案件目录>/case.json
```

未通过时，针对影响本轮结论的缺项提问；可先整理已知事实、检索路径与明确标为未完成的框架，不虚构事实，不交付未核验定稿。通用教学或规则导航问题不要求伪造案件配置。

本闸门另设三项任选其一的来源基础（`suite.yaml` 的 `gate_any_ids`）：`rules.clause_text`（条款原文）、`rules.official_url`（机构官网链接）、`rules.cached_text`（`data/official` 已缓存文本）。在 `case.json.facts` 中把实际具备的一项或多项登记为 `confirmed` + value/evidence 即满足；三项均未登记时返回一条 `gate_any` 缺项。`conflict` 阻断提交，`pending` 只允许受控草案；本任务不开放 `unknown`。`route.py --gate` 与 `intake.py checklist` 会逐项列出这些候选项，不得另建 Markdown 勾选代替台账。

## 二、调取动作

- 沿用当前配置、材料与已有矩阵，仅补本轮规则问题所需信息；通用问答不建虚构案件。紧急期限先提示风险与待核事项，再取文，不以检索阻断提醒。
- 向调用技能回传已核条文、版本适用理由、来源定位、时间依据与剩余缺口；案件存在矩阵时同步相关 A/程序事实及日历，不重建全案。
- **先取机制索引**：按机构键读 `assets/institutional-knowledge/` 对应册（`icc-lcia`／`siac-hkiac`／`chinese-institutions`／`global-others`／`apac-others`／`icsid-uncitral-others`），用来确认这家机构有无该机制、去哪一条找。该层只回答"有没有、去哪找"，其中的期限与金额是上一轮核验快照，一律不得直接抄进交付物；进入答案前必须按 1–4 步在本案适用版本全文中重新命中。

1. **定版本，不是取最新版**：
   ```bash
   python3 <suite>/scripts/fetch_official.py applicable --inst <机构> --commencement <YYYY-MM-DD>
   ```
   `--inst` 取注册表机构键（如 `icc`／`lcia`／`siac`／`hkiac`／`cietac`／`scia`／`aaa-icdr`），`--commencement` 取按规则认定的真实启动事件日期；尚未启动仅可用拟提交日筛选候选，标明预测，不将其登记为实际启动日。旧版约定加 `--agreed-edition`，同机构规则族用 `--ruleset`，两者用途不同。判读输出：`edition`／`effective`／`applies_to_note`／`citation_fields`／`citation_ready`／`confidence`。退出码 0 只表示候选筛选成功，须再核条款、过渡规则及官方全文；`citation_ready=false` 不许可未核条文进入提交态。退出码 2 的三种情形必须停手向机构秘书处或官网确证，禁止臆定或回填——`NO_DATED_EDITIONS` 表示没有任何条目登记生效日期、无法按日期判版；`NO_ELIGIBLE_EDITION` 表示启动日落在全部已登记版本窗口之外（历史案件早于最早版本，或唯一版本尚未生效）；`LOW_CONFIDENCE_MANUAL_CHECK` 表示命中版本可信度低，须人工核对官网文本后方可引用具体条号。`all_dated_editions` 用来回答"改版会不会影响本案"。
2. **探源与看缓存**：
   ```bash
   python3 <suite>/scripts/fetch_official.py check [--inst <机构> | --source-id <id>] [--timeout 20]
   ```
   逐行输出 `REACHABLE／UNREACHABLE／NEEDS_MANUAL + cached=True/False + source-id`，末尾 JSON 给 `needs_human` 汇总与刷新周期；有 `NEEDS_MANUAL` 时退出码为 2。这一命令同时把核验结果写进 `data/_provenance/<source-id>.json`，即来源凭证。`--inst` 批量重核一家机构，`--source-id` 只重核一条（改版或换链接后用这条，不必修跑全表）。慢站把 `--timeout` 提到 40–60，超时会误报 `UNREACHABLE`。
3. **取文本**：
   ```bash
   python3 <suite>/scripts/fetch_official.py fetch <source-id> [--to-md]
   ```
   成功输出 `saved <路径> (<字节>)`，PDF 与哈希、原始 URL 一并落到 `data/official/` 与凭证文件。`--to-md` 转 Markdown 后才能被 `lookup` 检索；返回 `NO_PARSE_BACKEND` 时按提示的三条降级路走（装解析后端／用户自行转换后放入 `data/official/<source-id>.md`／暂时用浏览器定位官网条文页，且引用仍需官方 PDF 复核）。
4. **在文本里定位条文**：
   ```bash
   python3 <suite>/scripts/fetch_official.py lookup <source-id> --pattern "<关键词或条号>" [--max 12]
   ```
   命中返回行号与该行文本。命中只是"定位"，必须在同一文本中读完该条完整表述与小节编号后才写条号。`NOT_CACHED` 或退出码 2 时先 `fetch`，或换英文原词重试（期限类问题用 `days`／`time limits`，立案类用 `Request`／`Notice of Arbitration`，费用类用 `advance on costs`／`filing fee`）。
5. **NEEDS_MANUAL 的处置（降级路径，不得绕过）**：站点拒绝自动抓取或不可达时，把 `fetch`／`check` 输出的官方下载入口逐条列给用户，请其人工下载 PDF 并存为 `data/official/<source-id>.pdf`，用 `import` 登记来源后逐条核对官方全文、适用版本与引用定位；`check`/`cached=True` 仅是连通/文件状态，不代表正文已核。人工取得并核验的官方全文同样可用，不以自动抓取成功为前提。输出里的 `mirror_if_emergency` 只能用于应急定位，引用前必须回校官方文本。正文或适用性未核时，对该来源的引用一律写成"待核验（官方文本或本案适用性尚未核实）"，**绝不以二手摘要、评述文章或旧版本文本替代**，也不给出具体条号、天数与金额。
6. **登记真实核验并维护台账**：
   在官方全文逐条核对完成后，按 `references/verification-contract.md` 用 verify 登记实际核验人、精确版本标签及各已核定位；只跑 check/fetch/lookup 不能获得提交态来源放行。新机构或本案法源可登记在案件本地 case-sources.json，不需要改公共来源表。

   ```bash
   python3 <suite>/scripts/fetch_official.py report
   ```
   生成 `data/_index.md` 状态索引，给出 `stale`（超过刷新周期，默认 90 天）、`never_checked`、`needs_manual_download` 三类待办；表末「备注」列写有该条为何需人工（站点反爬码、路径已更正、本机不可达）与最近一次维护日期，据此判断是换链接还是必须人工下载。`cached=True` 但已 `stale` 的来源，涉及费用表、简易程序门槛、修订生效日时必须重新 `check` + `fetch`，不能沿用旧缓存答题。新机构不在注册表内时，由用户或维护者向 `assets/sources-registry.json` 追加官方出处条目后重跑，不自行猜测 URL。
7. **组装答案（三段式，缺一不可）**：
   - 结论：一句话给出该问题在本案适用版本下的答案与不确定性；
   - 依据：条文要点 + 来源标记。从 `applicable` 取 `citation_fields`，在已核验正文中定位条号后运行 `fetch_official.py cite <id> --locator "<定位>"` 生成五段标记。`citation_fields.ready=false` 时只回答版本与缺口，不生成 `[source:]`，用 `[[待官方文本核对]]`；不得把 `citation_format` 当模板，也不得手工拼接标记。
     ```bash
     python3 <suite>/scripts/fetch_official.py cite <source-id> --locator "<Rule n>"
     python3 <suite>/scripts/fetch_official.py cite <source-id> --locator "<Rule n>" --workdir <案件目录>
     ```
     `cite` 要求核验凭证已覆盖该定位、版本与 `verified_edition` 一致，日期一律取 `verified_at`；输出 `CITATION_BLOCKED`（退出码 2）时按 `reasons` 补齐缺口，不得绕过。
   - 对置视角（铁律 7）：同一条文下**对方最可能的解读**与**仲裁庭关注点**各一段，并给出我方最不利情形下的应对；涉及期限的还要写起算点（送达日／收件日／次日）、届满顺延与营业日口径。
8. **沉淀**：答案写进案件目录的答案卡（模板 `assets/templates/03-条文答案卡.md`），缓存与凭证默认留在技能包 `data/official/` 与 `data/_provenance/`；只读安装或需要外部可写目录时，用 `RULESUITE_DATA_DIR` 指向外部缓存（缓存与凭证须同址迁移）。规则文本本身属公开官方文件，可缓存；**案件材料一律不得写入技能包或该缓存目录**（铁律 8）。把 `applies_to_note`、剩余缺口与下次需重核的来源回写到 `.arbitration-config.md` 与案件档案，避免同一问题重复进货。

## 三、产出

| 产出 | 位置 | 内容 |
|---|---|---|
| 条文答案（带来源标记） | 案件目录，模板 `assets/templates/03-条文答案卡.md` | 三段式：结论／条文依据与来源标记／对方解读与仲裁庭关注点 |
| data/official 缓存与凭证 | 技能包 `data/official/<source-id>.pdf(.md)`、`data/_provenance/<source-id>.json` | 官方文本、下载来源、字节与哈希、最近核验日期 |

对外交付时按 `render_docx.py --strip-sources` 移除标记，答案卡留在案件目录作为可回溯底稿。

## 四、常见错误

- 把"现行最新版"当"本案适用版"回答，忽略条款约定版本与启动日分界。
- 给了条号却没在该版本文本中命中；或小节、脚注、附则编号错位。
- 站点 `blocked` 就用评述文章或旧版 PDF 作答，且不标注待核验 → 同时违反铁律 1、2。
- 费用、简易程序金额门槛、临时机构费率一类"网站公布值"按缓存数字给死，未提示取值日与实时抓取要求。
- 期限只答天数，不答起算点、届满顺延、时区与节假日基准地，导致案件日历算错。
- 混淆机构规则与仲裁地法：`lex arbitri` 属 `statute` 层来源，须分开核对，涉及效力与撤销事由时转 `11-governing-law`。
- 只看 `cached=True` 不看 `stale`，用过期缓存答新规问题。
- 把答案或案件材料写进 `data/`；把机构名或案号放进缓存文件名。
- 一次并行回答多个机构的多条规则问题，版本与文本对不上号。

## 五、下游

`suite.yaml` 中 `next: []`：本子技能是被调用的支撑环节，答完回到发起它的子技能继续——`02-clause-diagnosis`（条款效力与机制）、`04-commencement`／`05-defence`（必载项、份数、答辩期）、`06-tribunal`（组庭与披露时限）、`07-measures-costs`（紧急机制与预缴）、`08-evidence`、`09-hearing`、`10-award-post`（更正解释窗口、执行要件）、`13-stage-qa`。机构核验问题与取文流程用 `references/forum-rules-matrix.md`，术语中英对照用 `references/glossary-en-zh.md`；清单不含机构答案，一切结论以本案适用版本的官方文本命中结果为准。
