---
name: 01-case-file
description: 接案建档与程序坐标校准：把用户给散的合同、条款、函件、时间线整理成案件档案，产出程序地图与时限日历。用户说"不知道现在到哪一步/还有什么期限"时的入口。
---

# 接案建档

## 一、入口闸门

材料要求以 `suite.yaml` 的本子技能条目为唯一依据。已在会话中明确的事实直接登记，不重复索取。
对实际案件，先核对本案配置，再把已读材料逐项登记到案件根唯一的 `case.json`（`rulesuite-case/1`，`case` 与配置一致）：`confirmed` 须有 `value` 与 `evidence`，缺项用 `pending`+`pending_id/question` 或 `not_applicable`+`reason` 如实登记，必要时用 `unknown`+完整 follow-up。Markdown 清单只由 `intake.py checklist` 生成供人阅读，不是材料台账。

```bash
python3 <suite>/scripts/intake.py checklist --gate 01-case-file --facts <案件目录>/case.json
python3 <suite>/scripts/route.py --gate 01-case-file --workdir <案件目录> --provided <案件目录>/case.json
```

未通过时，针对影响本轮结论的缺项提问；可先整理已知事实、检索路径与明确标为未完成的框架，不虚构事实，不交付未核验定稿。通用教学或规则导航问题不要求伪造案件配置。

## 二、建档动作

### 案件构建接线（先底账，后视图）

- 读取 `references/case-construction.md`；争议构建使用 `案件档案/case-matrix.yaml`（`schema: 2`）作为单一事实源，已有矩阵先读当前版本，不另建平行底账。
- 从已读材料抽取原子 F 与 EV，保留文档及页/段定位、争议状态和不利事实；按具体请求 CL/抗辩 DF 连接 E、证据或缺口、R 与 A，不套欠款树。纯否认可无 CL/R，非金钱救济不强制金额、币种或利息。
- 主体、合同与资产线索关系图由材料和矩阵生成，不要求用户先交图；档案、时间线、程序地图、日历都是引用/生成视图。
- 新材料先更新底账版本与变更理由，再刷新视图；冲突并列来源并登记 `open_questions`，不悄悄覆盖。执行目标 T 主表仅在 `enforcement-plan.yaml`，case 仅引用。
- 独立 `02-clause-diagnosis` / `14-cross-border-enforcement` 分别使用其矩阵，不以补建 case 矩阵或补齐全案为前置条件。
- 首次用 `case_matrix.py init --case <代号> --out <案件目录>/案件档案/case-matrix.yaml` 建骨架；填写后用 `check --in <矩阵路径> --stage draft` 检查，不把初始化当作事实确认。
- 下游 04/05/08/09 读取当前矩阵及缺口、核验记录、对抗审查；实质段用 F/E/EV/R/A 的 `#! 锚点：` 追溯行，按本轮阶段检查。

1. **材料清点**：逐个文件登记（文件名、类别、日期、对方当事人是否持有、原件持有方）。类别固定为：合同与附件／仲裁条款／往来函件／履行证据／财务凭证／机构文书（通知、受理、程序令）／裁决与法院文书／其他。
2. **主体表**：只从材料取证。每个主体记录法定名称、注册地、注册号、送达地址、邮箱、与我方关系。用户口头给的名称也记，但标 `来源：用户口述，待书面核验`。本套件不代为认定工商信息。
3. **时间线**：把事实与程序事件分列。程序事件必须写"触发起算的文件 + 收件日 + 依据规则条文 + 届满日"，其中条文来自 `fetch_official.py` 缓存文本，不得凭记忆（铁律 1）。
4. **争议结构图**：合同链条（谁与谁签了什么、几份合同、是否有担保/从合同）、请求基础、可能的反请求与追加当事人。
5. **程序坐标**：确定当前处于 P0–P7 哪一阶段（阶段定义见套件路由层），并列出本阶段与下一阶段的必经动作与可选动作。
6. **时限日历**：产出 `时限日历.csv`，列固定为：事项／起算依据（含来源标记）／起算日／届满日／负责人／需提前准备的材料／风险。所有无法确定的日期写成 `UNKNOWN`，不编造。
7. **反向核对**：仅把影响当前任务的冲突、未核与变化回给用户，最多三个关键问题；已确认信息沿用，不要求整份档案重签。保期限动作先行，缺项按受控草案与提交闸门分别处理。

## 三、产出

| 文件 | 内容 |
|---|---|
| `案件档案/case-matrix.yaml` | schema 2 单一事实与决策底账，仅本轮争议构建需要时维护，不对外提交 |
| `案件档案/00-case-file.md` | 从底账生成主体、时间线、争议结构及程序坐标视图；材料台账保留为案件根 `case.json`，供 route 与 verify 互校 |
| `案件档案/procedural-map.json` | 机器可读：阶段、已完成动作、待办、期限 |
| `案件档案/时限日历.csv` | 见上 |
| `案件档案/00-case-file-中文审阅说明.md` | 五节固定结构，供内部汇报 |

材料台账使用稳定字段 ID（由 `intake.py checklist` 取得，多个阶段共用同一 ID）：
```json
{"schema":"rulesuite-case/1","case":"DEMO","facts":{
 "contract.arbitration_clause":{"status":"confirmed","value":"SIAC, seat Singapore","evidence":["contract.pdf p12 clause18"]},
 "authority.status":{"status":"pending","pending_id":"Q1","question":"签署人姓名与授权范围？"}
}}
```

- `confirmed` 须有 `value` 与 `evidence`；`pending` 须有 `pending_id` 与 `question`；`not_applicable` 须写 `reason`（视为已核）。
- `unknown` 仅在 `suite.yaml` 的 `allow_unknown` 允许时有效，并须有明确回答的 evidence、`follow_up.action/owner/due`；它允许受控草案，不使提交态就绪。
- 提交态 `verify_suite` 对每份文书的 `workflow/profile` 调用同一闸门；缺 `case.json`、缺项、`pending`、`conflict`、无效 profile 或 redirect 均以 `[GATE]` 阻断并退出 2。
- Markdown 勾选只是人读视图，不得作为台账或用来绕过闸门。

## 四、常见错误

- 把用户口述当成已核实事实，起草文书时直接写死 → 违反铁律 3。
- 期限起算用了"发出日"而非规则规定的"送达/收件日"，或忽略规则中的期间延长（电子送达次日到达、节假日届满顺延）。条文必须现查。
- 只记自己的时间线，不记对方可能的时限，导致无法预判对方动作。
- 多份合同时只找主合同条款，漏掉从合同/订单/附件里不一致的争议解决条款——这是后续管辖权争议的雷点，移交 `02-clause-diagnosis`。
- 把影响本轮决定的冲突或未核材料当成已确认，或反过来要求用户重填已确认的全案问卷。

## 五、下游

`02-clause-diagnosis`（条款有问题）／`03-forum-rules`（规则细节待查）／`04-commencement`（我方启动）／`05-defence`（对方已启动）。
