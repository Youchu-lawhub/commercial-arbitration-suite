---
title: Post-Hearing Pack — Post-Hearing Brief, Submission on Costs, Objections to Costs, Termination and Award by Consent
case: "[[案件代号]]"
workflow: 09-hearing
profile: post-hearing
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
---

# Post-Hearing Pack (Master Template)

#! 适用 09-hearing / post-hearing；仅按 suite.yaml 本 profile 核双方争点清单与证据清单终版、庭审笔录或记录与庭后简报指令、期限。运行 route.py --gate 09-hearing --profile post-hearing --workdir <案件目录> --provided <案件目录>/case.json；不倒逼补庭前时间分配表，缺项可按 pending/Q 出不可提交草案。PART D 转 10 的 settlement 流程，独立成文时改为对应 workflow/profile 并核其实际依赖。
#! 先读当前 case-matrix.yaml；实质段按 09 写 F/E/EV/R/A 的 #! 锚点：追溯行，不用 [[F]]，保留庭审记录页行；新证言/回款先回写底账，纯否认不强造 CL/R，非金钱事项不强加利息。提交前对抗审查，自审标 self_review。
#! 先取官方文本：庭后简报与费用陈述的期限、页数、格式与是否需可检索电子版，全部以庭审程序令与规则原文为准。
#! python3 <suite>/scripts/fetch_official.py applicable --inst [[机构代号]] --commencement [[仲裁启动日]]
#! python3 <suite>/scripts/fetch_official.py fetch [[规则 source_id]] --to-md ；python3 <suite>/scripts/fetch_official.py lookup [[规则 source_id]] --pattern "costs"
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json>
#! 期限自证：庭后阶段的每一个日期都自己算给自己看——笔录定稿日、更正期届满日、简报截止日、费用陈述与对方评论的截止日，逐项写明起算点与依据；期限一旦写明即进入裁决的费用与程序行为评价，逾期视为放弃。
#! 逐条对应编号：庭后简报的节标题逐字复制仲裁庭问题原文，问什么答什么、顺序一致，子问 (i)(ii)(iii) 用小标题逐一作答；费用陈述与费用异议都按项目号逐句对应，不作整体"过高"或"不合理"的评论。
#! 引用格式：一切主张挂庭审记录页码，关键问答逐字引用并加脚注标页码，不写转述、不改写原话；页数是硬约束，细节进附表与脚注。
#! 补交文件与法律的门槛：庭后简报只处理庭上已出现或仲裁庭提出的问题；需要补交新法律材料或新文件，必须先申请许可并说明为何庭前无法取得，未经许可的补交会被排除并引发重开庭风险。
#! 金额一致性：每一笔主张金额必须能回溯到账单明细与凭证，且与主文请求、己方书状中的数字口径不冲突；只有总额无凭证的清单会被按"无法判断合理性"整体打折。
## PART A — POST-HEARING BRIEF IN ANSWER TO THE TRIBUNAL'S QUESTIONS

### A.1 Introduction and Decisions Requested

This brief is submitted in answer to the questions put by the Tribunal on [[date]] and in accordance with Procedural Order No. [[__]], which fixes a limit of [[以适用规则版本/程序令官方文本核对]] pages. We ask the Tribunal to decide: [[请裁事项，逐条编号，与结案陈词一致]].
### A.2 Question-by-Question Answers
#! 每节先写 Executive Summary（两三句结论，让仲裁庭只读三句即可抄用），再写 Discussion；无仲裁庭问题清单时，自行归纳争点并请仲裁庭确认，不套用己方书状目录。数字争点按输入项逐一处理：对方取值—理由—正确取值—影响金额。
| No. | Question of the Tribunal (verbatim) | Our answer, with sub-questions (i)(ii)(iii) in the order asked | Authorities relied on | Record references |
|---|---|---|---|---|
| [[1]] | [[逐字复制仲裁庭问题原文]] | [[两三句结论，再逐子问展开；对模型类问题按输入项列出对方取值、对方理由、正确取值与影响金额]] | [[条文／判例／专家报告段落，注明适用版本，外国法部分引 11-governing-law 出具的意见并标置信度]] | [[庭审记录 page __ 的关键问答逐字引用；证人陈述 paragraph __；Exh. C-__；书状 paragraph __]] |
### A.3 Conclusion and Relief

Our conclusions follow the numbering of the questions above, and the relief sought remains [[请求主文，逐条与开场陈述及书状一致，含币种、起算点与期限]]. Cost consequences are dealt with in PART B and rest on [[对方的程序行为，而非仅结果]].
## PART B — SUBMISSION ON COSTS

### B.1 Itemised Statement
#! 表先于叙述：先给出可与裁决费用部分一一对抄的汇总表，再论证合理性与依据。计费期间切分为仲裁前／仲裁中／庭审期／裁决后四段，仲裁前工作须单独说明与本案的关联。每位出庭人员的姓名与角色（律师／客户代表／专家／证人）逐一标注，纯旁席不写入。金额折算为裁决币种并注明汇率时点与利息起算。
| Category | Counsel / provider | Timekeepers and role | Period | Hours | Rate | Amount | Evidence |
|---|---|---|---|---|---|---|---|
| [[机构费]] | [[机构]] | [[不适用]] | [[仲裁前／仲裁中／庭审期／裁决后]] | [[不适用]] | [[以适用规则版本/程序令官方文本核对]] | [[币种 + 金额]] | [[机构收费通知、缴款凭证与发票编号]] |
| [[仲裁员费用分摊]] | [[机构核定的预付款]] | [[不适用]] | [[__]] | [[不适用]] | [[同上]] | [[币种 + 金额]] | [[预付款通知与缴款凭证；注意机构已核定部分不在仲裁庭权限内，不要写成请求扣减对象]] |
| [[外部律师费]] | [[律所名称占位]] | [[计费人级别与姓名占位及其角色]] | [[__]] | [[__]] | [[以适用规则版本/程序令官方文本核对]] | [[币种 + 金额]] | [[委托代理合同、账单明细、发票、付款流水编号]] |
| [[专家与鉴定人费用]] | [[专家姓名占位与其机构]] | [[专家／助理]] | [[__]] | [[__]] | [[同上]] | [[币种 + 金额]] | [[聘用函、报告、发票]] |
| [[差旅]] | [[__]] | [[出庭人员姓名与角色]] | [[__]] | [[不适用]] | [[不适用]] | [[币种 + 金额]] | [[行程单、住宿与市内交通票据、签证费、内部差旅标准]] |
| [[速录与传译]] | [[服务商名称占位]] | [[不适用]] | [[庭审期]] | [[__]] | [[同上]] | [[币种 + 金额]] | [[服务合同、报价单与发票；本项可赔性论证见 B.2]] |
| [[场地]] | [[庭审中心]] | [[不适用]] | [[庭审期]] | [[不适用]] | [[不适用]] | [[币种 + 金额]] | [[租金收据]] |
| [[合计]] | [[__]] | [[__]] | [[__]] | [[__]] | [[__]] | [[币种 + 合计金额]] | [[各明细行凭证的汇总索引表]] |
### B.2 Reasonableness, Proportionality and Comparators

The amounts claimed are proportionate to the sum in dispute of [[币种 + 金额]], to the [[__]] issues the Tribunal had to decide and to the conduct of the proceedings by [[何方及其程序行为]]. Our total hours of [[__]], average rate of [[以适用规则版本/程序令官方文本核对]] and attendance of [[__]] persons at the hearing are stated so that the Tribunal can compare.
- In-house legal time and the salary time of employee witnesses are claimed only to the extent that [[证明这些工作替代了外部采购，或说明为何不予主张]]; the travel costs of employee witnesses are listed separately, as they are not salary time.
- Expert fees are claimed as necessary because [[争点的专业性与仲裁庭无法自行判断之处]], and the amount is materially lower than the comparable item in the other party's statement, namely [[对照数字与出处]].
- Transcript and interpretation costs are claimed as costs actually incurred for the hearing; the allocation agreed on the last day of the hearing was [[__]], and the Tribunal's direction on this is recorded at [[庭审记录 page __]].
- No person is claimed both as a factual witness and at expert rates, and no timekeeper is included who had no visible role in the proceedings.
### B.3 Interest and Currency

Amounts are expressed in [[裁决币种]] and converted from [[源币种]] at [[汇率与时点来源]]. We request interest on the costs awarded at [[利率依据，以适用规则版本/程序令官方文本核对]] from the date of the award until payment in full.
## PART C — OBJECTIONS TO THE OTHER PARTY'S SUBMISSION ON COSTS

#! 限于费用问题，不重开实体；泛称"不合理"而无项目号与数据者，仲裁庭无从采纳。必要性优先于单价：单价合理也可能与本案无关而不获偿。角色错配（证人／专家／旁席／客户代表混用）是最高频突破口，逐一指出。对方节选引用规则或法条时，完整引述原文再反驳。已撤回请求的费用后果区分"撤回时机"与"撤回事实"，尽早撤回者不应受罚。勿指向机构已核定的费用（超出仲裁庭权限），并在指定期间内提交。
| Item | Objection ground | Our comparable data | Suggested reduction | Record support |
|---|---|---|---|---|
| [[对方费用表第 __ 项]] | [[不合理／不成比例／未必要／重复计费／与争点无关／角色错配（名为专家实为事实证人、旁席计入出庭人数）／内法务费用伪装为律师费／计费期间远早于仲裁开始]] | [[己方同类工作总小时 __、平均费率 __、出庭人数 __]] | [[建议扣减金额或比例，并写明计算过程]] | [[庭审记录 page __；程序令第 __ 段；对方账单第 __ 页]] |
## PART D — CLOSING THE PROCEEDINGS: TERMINATION ORDER AND AWARD BY CONSENT

#! 先定关闭形式：终止令是命令不是裁决，不能依纽约公约执行；和解含将来付款义务（分期、担保、回购、退税申请等）时必须做成合意裁决，只签和解协议在跨境执行上等于落空。庭方指出裁决在他地难以执行，正是请求合意裁决的核心理由。
#! 恢复程序条件与费用处理必须同时写：不和解即恢复程序的自动时间表、预付款余额分配、机构管理费与仲裁员费用、增值税与税号、各自律师费的承担方式；费用谈不拢时请求"记载撤回并保留仲裁庭裁费用"，不因费用争执放弃关闭。
### D.1 Joint Request and the Terms to Be Recorded
- Status of the case at the date of request: [[已完成的程序步骤、争点、已缴预付款与机构核定费用]].
- Settlement obligations in command form, each with a date, an amount, a currency and an account: [[谁于何日前付多少至何账户；担保与信用证安排；发票与税务处理]].
- Consequences of non-performance attached to each obligation: [[加速到期、担保执行、利息、余额直接成为裁决金额]].
- Waiver drafted as a closed definition: [[以时间、主体、合同与请求类型圈定弃权范围，并明确 with prejudice 与反请求一并处理]].
### D.2 Form, Signature and Enforceability
#! 区分三层签署主体：双方或各自律师（附授权）、仲裁庭、机构结算部分；担保人未参与程序的须有其签署同意，否则庭方可能拒绝记载。避免"进一步协商"式条款与第三方义务，预判庭方对合法性与公共政策的筛查。合意裁决可省略实体理由，但费用与执行条款必须完整可执行。
| Point to be settled | Termination order | Award by consent | Our instruction |
|---|---|---|---|
| [[能否跨境执行付款义务]] | [[否：命令不可依公约执行]] | [[是]] | [[含将来付款义务时一律选此项，并逐项列出被执行方资产所在地与是否为公约适用地]] |
| [[费用与预付款结算]] | [[机构核定并分配余额]] | [[记入裁决主文]] | [[限额、超支归属、增值税与税号逐项写明]] |
| [[不和解时恢复程序]] | [[不适用]] | [[附条件记载自动时间表]] | [[谁在何日前提交什么、另一方何时回应、另定开庭日一并写入记录]] |
### D.3 Operative Provisions
We request that the Tribunal record the terms at paragraph [[__]] in the form of an award pursuant to [[以适用规则版本/程序令官方文本核对]], note the withdrawal of the claims and the counterclaims with prejudice, and allocate the costs of the arbitration as set out in paragraph [[__]].
~ [[申请人代理人签名占位]] — for the Claimant, under authority dated [[date]]
~ [[被申请人代理人签名占位]] — for the Respondent, under authority dated [[date]]
~ [[主席]] — Presiding Arbitrator, on behalf of the Tribunal, at [[地点]] on [[date]]
