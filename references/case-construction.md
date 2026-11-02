# 案件构建：从材料到可检验的请求与抗辩

## 1. 先办当前任务

中国企业法务只需说明一句当前任务。先读材料、既有档案、旧结论及其核验日期，自行选择子技能和当前 profile；每轮最多询问三个会改变当前决定的问题。材料解析失败不等于材料不存在。先识别最近不可回避的期限；可并行准备延期、最低合规答复或紧急措施，申请未获准前不假定原期限暂停。

未知登记 `open_questions`，标明问题、类型、影响、负责人和期限，不以默认值补成事实。普通规则问答不创建案件；独立条款审计和执行预判也不以虚构 case-matrix 为前提。执行预判不要求已有裁决。接案时的主体、合同、资产关系图由系统从材料生成，不反过来作为准许接案的条件。

复杂度用 `light`、`standard`、`complex`，写理由：事实与材料规模、争点数量、多方多合同、多法域、语言、专家、紧急期限、监管、破产、国家实体等特殊风险。金额只是预算或已核规则门槛的输入，不能单独决定复杂度。

## 2. 单一事实源与主键

`案件档案/case-matrix.yaml` 使用 `schema: 2`。事实只在 `facts` 中维护；人读档案、时间线、书状、程序地图及日历都是引用/生成视图。收到新证据先更新底账，再更新视图，记录版本和变更理由；冲突事实并列保留来源，不悄悄覆盖。

| 主键 | 含义与边界 |
|---|---|
| F-001 | 原子事实，主体、时间和行为可分别核查 |
| CL-01 | 请求或反请求；反请求仍使用 CL 主键并标明性质 |
| DF-01 | 否认、积极抗辩、管辖/可受理性或金额抗辩 |
| E-CL01-01 / E-DF01-01 | 具体请求/抗辩的法律要件，不以交易标签代替研究 |
| EV-001 | 证据内部 ID；`exhibit_no: C-1` 是对外附件号，另行映射 |
| R-01 | 救济项；非金钱救济不强制金额、币种或利息 |
| A-01 | 支持具体法律命题的权威及核验记录 |
| T-01 | 执行目标，主表只在 `enforcement-plan.yaml`，case 仅引用 |
| OQ-01 | 案件层开放问题，不等同文书中的 Q 占位 |
| AT-01 / PM-01 | 对抗攻击线 / 预演失败条目 |

对外被申请人附件号 R-1、法律资料号 CL-1 与内部 R-01、CL-01 是不同命名空间。一个文件可在不同程序有不同附件号，但不重复创建内部证据或事实。旧数据迁移须保留旧号映射、来源和变更记录，不把旧 chronology 再留作并行底账。

### 核心记录

- `case`、`version`、`complexity`、`posture`、`stage`；`forum` 记机构、仲裁地、语言；`governing_law` 分合同与仲裁协议，并引用仲裁地/执行地研究。未知用 `unknown`，不猜。
- `theory`：一句话理论、`tribunal_questions`、`must_prove`、`opponent_best_case`、`predictions`、`falsifiers`。理论是待检验解释，不是裁判结果。
- `claims` / `defences`：性质、对象、法律基础、对应要件及实际请求救济。纯答辩可无 CL/R；单纯否认无需虚构己方举证要件，指向对方命题/要件和未满足之处即可。
- `elements`：`statement`、`burden`、`standard`、`facts`、证据或 `gap`、`witnesses`、`strength`（strong/partial/missing）、`opponent_attack`、`response`、`fallback`。先从本案适用法取得要件，再归摄；付款请求树不是通用树。
- `facts`：日期或期间、`actor`、`act`、`source.document_id`、`source.locator`（页/段/时间戳）、`status`（undisputed/disputed/unverified）、关联要件、`adverse`、`background`。文件存在不等于内容真实或双方无争议；用户口述也标来源。
- `evidence`：原件/副本与持有人、完整性、取得方式、语言、页段、密级/特权、对方持有情况、对外附件映射、证明范围和限制。实体证据关联 E；送达、授权、期限、组庭等证据可写明确程序用途，不强造实体 E。
- `relief`：请求对象、行为/给付、范围、期限、权限与执行障碍。金钱项另列本金、计算、币种、利息条件、费用及已付抵减；选择性/连带请求不得重复累计。
- `authorities`：引注、法院/发布机关、日期、版本、原文和定位、具体命题、有效期间、效力状态、后续处理、事实相似度、拘束力/权重、支持强度、使用方式、来源及核验日。详细方法见 `legal-family-reasoning.md`、`foreign-law-research.md`。
- `enforcement`：预判文件引用与 T 引用；不复制目标主表。保全、送达、授权、组庭、救济措辞的风险传给 14；没有资产线索登记调查缺口，不臆造资产。

## 3. 从材料覆盖到论证

1. 材料清点：已读、待解析、缺页、重复、冲突分别登记；合同附件、版本、主体和授权不可遗漏。
2. 抽取原子 F 与 EV，生成主体/合同关系、时间线和资产线索视图。不利事实显式标记，背景事实与要件事实分开。
3. 按具体争点分别研究合同法、仲裁协议法、仲裁地法、执行地法；用交易/争议模式仅提示遗漏。
4. CL/DF → 法律基础 → E → F → EV/缺口 → 对方最强攻击 → 回应/备位 → R → 执行障碍。举证责任和证明标准逐项核实，不把所有反驳都当积极抗辩。
5. 一句话理论须解释关键事实并经得起不利材料检验。写出什么新增事实会支持预测、什么会推翻理论，以及调整或放弃条件。
6. 缺口有动作、负责人、期限和替代证据路径；不把证人预计答案登记成已发生事实。

## 4. 对抗审查与预演失败

起草前、庭前、提交前及重大新事实出现时复核。冷读六问：案件讲什么？争点是什么？最强点？最弱点？缺什么？什么能说服审查者？先以最强版本重建对方立场，再检查己方回应。

AT 记录被攻击的 CL/DF/E/F/EV/A/R、对方论证、最有力材料、回应与残余风险；纯否认可直接攻击并锚定 DF，无需虚构 E，但核心 must_prove 要件仍须逐项覆盖。PM 从不利结果倒推可能失败原因、预警信号、补救人和日期。light/standard/complex 的攻击线及预演条目参考数量分别为 2/3/5；不足时说明原因，不为凑数虚构事实、攻击或残余风险。由同一人完成须标 `self_review`，不得冒充独立审查。该闸门只证明审查有记录，不保证法律质量或胜诉。

## 5. 锚点与受控草案

内部锚点紧邻其支持的实际论证段；示意语法（只能保留本案真实存在的 ID）：

```text
#! 锚点：F-001 / E-CL01-01 / EV-001 / R-01 / A-01
对应的事实、归摄或救济论证段。
```

按 F/E/EV/R/A 分组，组内可用逗号列多个 ID；不相关组可省略。不要把示例 ID 灌进所有段，不用 `[[F]]` 冒充占位。标题、表格、签名、例行程序函豁免逐段锚点；关键事实和实质论证仍须可追溯。`#!` 行渲染删除，不替代对外证据引用和正式法律引注。

实质未知先登记 OQ；确需受控草案时，在 `pending.json` 登记 `[[Q1:待确认事项]]`，并在问题说明中关联 OQ、负责人及文书范围。Q 不代替 OQ，解决后回写事实源并重渲染。提交态不得残留占位或以“用户同意”绕过未核验关键依据。

矩阵 `documents` 只收记稿文件路径的字符串数组（不是对象），路径按矩阵文件所在目录解析（矩阵在 `案件档案/`，交付件在 `交付/` 时写 `../交付/<文书>.md`）；核验会逐份读取这些记稿并核锚点，因此实际请求的每个 `R-` 必须出现在其中某份文书的锚点行里，否则报 RELIEF_ANCHOR 或 DOCUMENT 不存在。

04/05/08/09 文书记稿加入 `workflow`（子技能名）、`matrix: case`、`profile`（当前任务）。`case` 只写稳定案件代号，机构案号放正文。内部矩阵、办理清单、决策件标 `pair: false` 和“仅内部，不得对外”；正式文书按铁律 5 的语言条件配对——非中文文书逐份配中文审阅说明，本身用中文提交的文书不另出（需逐段核对时出 `pair: false` 内部核对件）。

## 6. 工具顺序与闸门

```bash
python3 <suite>/scripts/case_matrix.py init --case <代号> --out <案件档案/case-matrix.yaml>
python3 <suite>/scripts/case_matrix.py check --in <案件档案/case-matrix.yaml> --stage draft
python3 <suite>/scripts/case_matrix.py render --in <案件档案/case-matrix.yaml> --out <案件档案/01-案件构建矩阵.md>
python3 <suite>/scripts/case_matrix.py summary --in <案件档案/case-matrix.yaml>
python3 <suite>/scripts/case_matrix.py anchors --in <案件档案/case-matrix.yaml> --draft <文书.md>
python3 <suite>/scripts/case_matrix.py check --in <案件档案/case-matrix.yaml> --stage submission
python3 <suite>/scripts/case_matrix.py scaffold --record element|fact|evidence|relief|authority|claim [--id <编号>]
python3 <suite>/scripts/case_matrix.py explain --code <判定码>
python3 <suite>/scripts/verify_suite.py --workdir <案件目录> --mode submission
```

`init` 仅建含 unknown 的骨架，不能自动完成法律推理；必须按材料完善。不会写某类记录时用 `scaffold` 取键名齐全的骨架再填值（unknown 字段须用 OQ 的 paths/targets 覆盖）；看不懂判定码（如 REVIEW_COVERAGE、ORPHAN_FACT）时用 `explain --code` 取含义与修法，不必读校验器源码。旧版迁移先查看 `case_matrix.py migrate --help`，另存输出、核映射后使用，不猜未支持参数。`check --stage enforcement` 用于案件链条的执行衔接，不替代执行矩阵检查：

```bash
python3 <suite>/scripts/clause_audit.py check --in <clause-audit.yaml> --stage report
python3 <suite>/scripts/enforcement_matrix.py check --in <enforcement-plan.yaml> --stage forecast
```

执行后续阶段按实际任务选择 `plan`、`filing`、`board`。无 case 的独立条款/执行件只跑对应矩阵和交付检查，不制造 case；`--workdir` 是案件目录，不是交付子目录。矩阵是否核对由文书 frontmatter 的 `workflow/profile/matrix` 声明触发。verify 模式是 draft/submission，render 模式才是 legal/memo/board。

读取真实退出码和 JSON 判定，包括缺项、未核验、允许草拟、可提交状态及 checked_stage；不能只凭退出 0 宣称法律合格。阻断按具体任务隔离：可继续整理、研究、受控草案和保期限动作，但未核验关键事实/权源不能变成可提交结论。接口不支持时明确报告并人工复核，不假称运行成功。
