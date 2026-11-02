---
name: 12-delivery
description: 交付引擎：把任何子技能的产出物变成可交付 Word 文书，并按铁律 5 为一份非中文文书强制配对《中文审阅说明》。触发词：转成 Word、排版、交付、docx、汇报、中文说明。任一文书对外发送、提交仲裁庭或交管理层前都必须经过本子技能。
---

# 交付：Word 文书（非中文文书另配中文审阅说明）

铁律 5 的执行者：**一份可交付文书 = `.docx` ＋（仅当文书非中文时）配套《中文审阅说明》.docx**。非中文文书缺配套说明即视为未完成，不许"先发文书、说明后补"；本身以中文提交给机构的文书不再另出中文说明，需要交付前逐段核对时出内部核对件并标 `pair: false`。排版规则以 `references/delivery-typography.md` 为唯一出处，本文件只写动作顺序与验收判据。

## 一、入口闸门

按 `suite.yaml` 核对待交付终稿、案件目录、署名与日期口径；已确认信息直接登记到案件根 `case.json`，不以 Markdown 勾选或口头确认代替。本地教学示例注明虚构，不伪造机构核验。

```bash
python3 <suite>/scripts/route.py --gate 12-delivery --workdir <案件目录> --provided <案件目录>/case.json
```


## 二、动作序列

- 先按本轮文书 frontmatter 的 `workflow`、`profile`、`matrix` 确定材料及矩阵依赖，以 `suite.yaml` 为准；04 无 profile，不补造。缺失/冲突的元数据退回上游修正，不靠漏传开关跳过依赖。
- `matrix: case` 读取当前 `案件档案/case-matrix.yaml` 并检查本轮锚点、阶段及对抗记录；独立 02/14 仅检查各自矩阵及适用阶段，不强建 case、不因无关矩阵阻断。
- `verify_suite.py --workdir` 指案件根，不是交付子目录。仅检查本轮交付件及其依赖，历史稿隔离，不混入校验；矩阵是否核对由文书 frontmatter 声明触发。
- 正式交付按 `references/verification-contract.md` 生成案件根 `delivery.json`，明确本轮每份文书、说明与附件；提交模式缺清单即 `VERIFY_INCOMPLETE` 且退出码 2，不放行。**用生成器而不是手写**：`python3 <suite>/scripts/delivery.py build --workdir <案件目录>` 自动列出主文书、配对说明、附件并计算各文件 sha256 与页数估计，视觉复核状态一律 pending；经办人在 Word 逐页复核后运行 `delivery.py attest --workdir <案件目录> --reviewer <姓名>`，状态才变 passed 并刷新哈希绑定，机器不得代签视觉通过。新旧稿无需移动，未列入清单的历史件不参与本轮校验。所有正式 DOCX 保留带正文及记稿哈希的渲染记录。
- 同一轮 verify 按每份文书的 `workflow/profile` 读取案件根 `case.json` 并调用材料闸门：缺台账、缺项、`pending`、`conflict`、无效 profile 或 redirect 以 `[GATE]` 阻断提交；`not_applicable` 有 reason 视为已核。草案模式允许带 `pending_id` 的 pending 与完整 follow-up 的 allow_unknown，但仍须有台账，缺项/冲突照样阻断。
- verify 的 `--mode` 只用 `draft` / `submission`；render 的 `--mode` 才用 `legal` / `memo` / `board`。受控草案登记 `pending.json`，渲染走 `--draft`，核验用 `--mode draft --pending <pending.json>`。审阅草案（review draft）是**可交付的审阅件**：渲染自动附"含 N 处待确认项，不可提交"状态声明与黄底高亮，供当事人逐项确认；可以交给用户，但不可提交仲裁机构、不得当作最终版。
- 案件矩阵、AT/PM 记录不进卷宗，内部件按实际用途 `pair: false`；`#! 锚点：` 行渲染删除，正常法律引注与对外证据引用保留。正式文书按铁律 5 的语言条件配对：非中文文书逐份配中文审阅说明，中文文书不另出。

1. **写 Markdown 记稿**。按 `references/delivery-typography.md` 的受限方言书写；排版键为 `title`、`case`、`mode`、`footer_left`、`keep_sources`、`toc`、`pair`，另保留核验依赖键 `workflow`、`profile`、`matrix`。`case` 只填稳定案件代号，机构案号写正文；不要把依赖元数据当排版项忽略：

   ```markdown
   ---
   title: Request for Arbitration
   case: <内部案件代号>
   workflow: 04-commencement
   matrix: case
   mode: legal
   footer_left: <文号>
   keep_sources: false
   toc: true
   ---
   ```

   文书标题用工作语言原样写进 `title`（英文文书写英文标题，中文文书写中文标题），文号靠 `footer_left` 落到页脚，不在正文里重复。

   正文标记与渲染效果：`#` 文书标题（居中不编号）；`##`／`###`／`####` 层级标题；**普通行＝自动编号段落**（Word 自动编号，插入段落会重排，手写序号会被改写为自动编号以避免双重编号）；`~ ` 取消编号；`- ` 项目符号；`> ` 缩进段；竖线表格（首行为表头）；`<pagebreak>` 分页；`[[待填写内容]]` 渲染为**黄色高亮占位**；`[source:…]` 渲染为灰色小字，且 **legal 模式自动剥离**，除非文件头写 `keep_sources: true`（内部审阅版留标记、对外版剥离即靠此开关，不必改正文）。memo 模式默认保留标记，要强行删除加 `--strip-sources`。

2. **渲染文书**：

   ```bash
   python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> \
     --mode legal --toc --strict --header "<案件名 | 文书名>" --footer "<文号>" \
     --manifest <draft.paras.json>
   ```

   `--header`／`--footer` 可省略，省略时分别取文件头 `case` 与 `footer_left`。退出码：**0** 成功；**2** 输入或依赖问题（文件不存在、不是合法 Markdown 记稿、zip 写入失败）；**3** `--strict` 下仍有未填占位（输出的 `placeholder_items` 就是待用户确认清单）。`--manifest` 导出的段落编号表是交叉引用的唯一依据。

3. **核对交叉引用**。文书里所有 "paragraph N"／"段落 N"／表格里引用编号处，必须落在 manifest `numbered_paragraphs` 的真实区间内；编号变动后**重渲染并重新核对**，不许凭上一次输出放行。

4. **非中文文书同出《中文审阅说明》**（本身用中文提交的文书跳过第 4—5 步，不产本件），五节固定且顺序不变，逐节都要有内容（`verify_suite.py` 按节名匹配）：本文件作用与程序依据（每处规则／指引引用带 `[source:…]`）／逐段填写要点／我方立场与可选表述／风险与待用户确认事项／给管理层的三句话汇报。骨架见 `assets/templates/12-中文审阅说明.md`。

5. **渲染说明**（仅第 4 步产出了说明件时），使用 memo 模式并同样开启 strict：

   ```bash
   python3 <suite>/scripts/render_docx.py --in <draft-中文审阅说明.md> \
     --out <draft-中文审阅说明.docx> --mode memo --strict
   ```

6. **按本轮状态自检**：提交与草案示例二选一；独立 02/14 按其声明检查专用矩阵及阶段，不强迫补 case-matrix。读取真实退出码和 JSON 的判定、`gate_issues` 与 checked_stage；只有 `VERIFIED`（退出 0、`submission_ready=true`）才是提交态，`DRAFT_OK` 表示审阅草案结构可交付（含已登记待确认项），不代表可提交，`VERIFY_INCOMPLETE` 不可提交。自动通过不代替法律/视觉验收。来源未取文、版本或核验范围不符时提交态阻断；受控草案按 pending 流程保留。**审阅草案完成时必须把 .docx 连同配套中文说明（非中文文书才有）与 pending 清单一并呈现给用户**，不得只给文本摘要或答复"草稿已写好"。

   ```bash
   python3 <suite>/scripts/verify_suite.py --workdir <案件目录> --mode submission
   python3 <suite>/scripts/verify_suite.py --workdir <案件目录> --mode draft --pending <pending.json>
   ```

   七类检查：PAIR（非中文 `.docx` 有配套中文说明且五节齐全；正文本身为中文的文书按语言豁免）、FILL（无残留 `[[占位符]]` 与黄底高亮）、CITE（所有交付件的来源标记均检查字段、ID 与 URL，说明中的规则引用带来源标记、正文条号有说明对应；条文内容及适用性另做人工复核）、XREF（交叉引用不超过实际编号段落数，依赖 `.paras.json`）、CONSIST（配对文书之间当事人名称、争议金额、关键日期、请求项数量一致）、GATE（按文书 `workflow/profile` 与案件根 `case.json` 互校材料闸门）、DOCX（必备部件齐全）。退出码 2 即回到对应上游子技能修补后重跑；`--pairs "A.docx:A-中文审阅说明.md"` 仅兼容旧结构检查；正式交付以 delivery.json 为准，两者不能并用，`--selftest` 用于新机器上验证两个脚本可用（铁律 2、5）。

7. **工作语言判定**：仲裁庭／条款约定的工作语言为英文 → 文书出英文并配中文《中文审阅说明》；纯中文程序（CIETAC、北仲、SCIA 中文案等）→ 文书直接出中文，**不再另出中文审阅说明**，需要交付前逐段核对时出内部核对件并标 `pair: false`；仅在用户或程序要求时追加译本。渲染器不识别 `lang` 元数据；需提交仲裁庭的非权威语言文本，附翻译并注明译者与是否为官方译文。

8. **降级路径**（`docx_render` 未绑定或本机无 python3）：仍按第 1 步出 `.md` 定稿，并给用户四步转 Word 说明——① 用 Word 打开该 `.md`（或粘进空白文档）；② 按 `references/delivery-typography.md` 的样式表套标题与正文样式，段落编号改用 Word 多级列表；③ 手工把 `[[…]]` 加黄色底纹、`[source:…]` 改灰色小字或删；④ 页眉填案件名、页脚填文号。降级期间第 6 步的 DOCX／XREF 检查无法执行，必须在回复中明示"未经结构自检"，并把这一步列为待办。

9. **保密与落盘边界**（铁律 8）：交付物只写用户指定的案件目录；文件名用内部代号 + 文号，**不得出现对方名称、争议标的金额或项目细节**（例：`A-24-003-RFA-v2.docx`，而非 `<对方公司全名>-<合同名>-索赔USD…….docx`）；带 `keep_sources: true` 的内部版与对外剥离版分文件名区隔，对外版后缀加 `-ext`；技能包目录与 `data/` 不写案件材料。

## 三、产出

**交付物（与 `suite.yaml` 的 outputs 一致，缺一即未完成）**：

| 文件 | 内容 | 判据 |
|---|---|---|
| `.docx`（文书） | 上游子技能定稿的排版版（legal 模式） | 退出码 0；无黄底占位；交叉引用在区间内 |
| `《中文审阅说明》.docx` | 五节固定结构（memo 模式） | 五节齐全且每节有实质内容 |

| 配套文件 | 内容 | 判据 |
|---|---|---|
| `<文书>.md`／`<文书>-中文审阅说明.md` | 记稿原件，改写与二次交付的基础 | 与 `.docx` 同名同目录 |
| `<文书>.paras.json` | 段落编号表，交叉引用与 XREF 检查的依据 | 与文书同批生成，改版后即重生成 |
| 自检报告 | `verify_suite.py` 输出（含修补项与重跑结果） | 全绿才可对外发送 |
| `-ext` 版 `.docx` | 对外交付版：`keep_sources` 关闭或加 `--strip-sources`，剥离来源标记与缓存路径 | 内部版与对外版分文件，不覆盖 |

## 四、常见错误

- 只出文书不出中文说明，或说明写成五节标题齐全但内容为空——PAIR 直接不过。
- 半成稿就渲染：`--strict` 退出码 3 被忽略，带黄底占位的文件发给了仲裁庭。
- 用 `--mode legal` 渲染中文说明（正文变成自动编号段落，说明无法逐段对照），或反过来用 memo 渲染对外文书。
- 改了记稿不重渲染、不重出 manifest，文书里的 "paragraph 12" 指向已漂移的段落。
- 对外版还留着 `[source:…]` 内部标记与缓存路径；或反过来内部审阅版把标记全剥光，后续无法追溯版本（铁律 2）。
- 手写段落序号又开自动编号，出现双重编号；跨页表格首行未设重复表头。
- 文件名写出对方全名与索赔金额（铁律 8）；把交付物写进技能包目录。
- 署名、签署地、日期、份数口径未确认就定稿，文书落款处与案件档案不一致。
- 未确认程序语言就机械生成双语版本，增加无必要的翻译与校对。

## 五、下游

交付后只登记已生成文件及验收状态；实际提交/送达取得凭证后才由 `13-stage-qa` 回写当前底账、程序地图与日历，不能把渲染完成当提交完成。修改回原上游更新矩阵及记稿，再重跑本序列。裁决救济交 10，执行文件包（正本、译本、认证）按 `14-cross-border-enforcement` 的目标法域要求处理，本技能不代办认证或实际递交。

## 六、视觉与语义复核

结构通过后，按 `references/verification-contract.md` 登记绑定文件哈希、页数和复核人的 visual_review；缺记录或文件改版时 submission_ready 为 false。必须实际打开渲染后的每一页（Word 或其 PDF/页面图像），逐页验收字体、中文可见性、表格分页、标题孤行、签署区及页码，并记录所看文件版本、页数、问题与复核人；只查 XML/退出码不算视觉验收。无法查看页面须明示未完成，不声称 Word 验收完成。`board` 只是排版模式，不能保证一页；一页纸要求须渲染后实测并调整。编号范围正确不代表引用内容正确，来源字段完整不代表法律结论正确；案件根仍为 `--workdir`，只核本轮交付件及声明依赖。

认证翻译、公证、附加证明书/领事认证由相应外部专业服务完成；本技能仅准备材料与核对状态，不用脚本生成冒充认证。申请件随附立案申请指引，执行件按 14 的目标法域清单交接。

本轮材料预填、跨阶段 gate_ids、显式 pending 草案、缓存导入、利息与程序轨道工具按 `references/practical-workflow.md` 执行；已登记待确认草案走 DRAFT_OK 交付审阅件，提交态仍须清除占位并通过 strict。该工作流取代“所有缺项一律禁止出草案”的旧说法。

起草、重写或润色按 `references/legal-writing-workflow.md` 分轮处理任务与论证、事实叙事、语言和版面，并回查法律含义；不得仅以表面流畅代替论证或改动事实与请求。

配对义务按铁律 5 的文书语言条件判定，本文件不复述规则；免配说明时，逐段要点、对置检查与待确认项写进矩阵 `adversarial_review`／`open_questions`，需要成文核对再出标 `pair: false` 的内部核对件。内部立案清单、办理指引或计算台账可在记稿 frontmatter 标 `pair: false`；渲染会登记，核验明确输出内部件豁免，仍检查来源、占位、结构和同步性。不得为对外文书使用该豁免。
