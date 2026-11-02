---
title: Request for Interim Measures of Protection
case: [[案件代号]] | [[机构名]] Case No. [[案号]]
workflow: 07-measures-costs
profile: interim
mode: legal
footer_left: [[Draft v1]] — [[日期]]
keep_sources: false
toc: true
---

# REQUEST FOR INTERIM MEASURES OF PROTECTION

#! 本文件是骨架模板，复制到案件目录 deliverables/ 后逐段填写；所有 #! 行渲染时整行丢弃，永不进入 Word。文末两节（异议版骨架、建议裁定主文）分别供被申请人抗辩与申请方预写命令使用，交付时删除不需要的节。
#! 适用子技能：07-measures-costs 第 1—6 项动作。产出名对应 07 的 outputs 之"临时措施申请/异议"与"紧急仲裁员申请"。
#! 按本轮 interim 检查：python3 <suite>/scripts/route.py --gate 07-measures-costs --profile interim --workdir <案件目录> --provided <案件目录>/case.json。核实紧迫性、措施对象与依据、法院协助可行性；证据或行为保全不强制无关资产或费用明细。缺项先整理与研究，不虚构材料，不提交未核验申请。
#! 先取官方文本（顺序执行）：python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <仲裁启动日> ；python3 <suite>/scripts/fetch_official.py check --inst <机构id> ；python3 <suite>/scripts/fetch_official.py fetch <规则版source_id> --to-md ；python3 <suite>/scripts/fetch_official.py lookup <规则版source_id> --pattern "emergency|interim|conservatory|provisional|security|deposit" --max 12 。禁止凭记忆写机构是否设有紧急仲裁员、其天数与费用条件。
#! 渲染与核验：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json> ；再跑 python3 <suite>/scripts/verify_suite.py --workdir <交付目录> --mode submission；非中文文书另配中文审阅说明（本身用中文提交的文书不配）。
#! 核心纪律一（损害）：不可弥补损害要件的关键是"金钱不足以弥补"，不是"我方会受损"。可赔性与赔付路径未被排除，就是对方最有力的反驳；跨境场景中最站得住的表述是兑付后追索不能与资质、许可的不可逆丧失。
#! 核心纪律二（对象边界）：措施只能指向对方可控的行为。银行、登记机关、买方、承运人不是程序当事人，仲裁庭对非当事人通常无直接管辖权，请求命令第三人会把整份申请的可信度拉低。见索即付保函独立兑付，仲裁庭命令通常约束不到银行，止付须走法院路径（见 VI 节）。
#! 核心纪律三（基线）：凡请求"维持现状"必须定义 baseline，否则对方会主张现状已对其有利。以申请日或合同应然状态为准，二选一并全文统一。
#! 核心纪律四（范围）：请求过宽等于全案被驳。给出最小干预版本、可验证标准与明确期限；以临时措施实现实体结果（先行付款、继续全部合同义务）会被以"等同终局救济"驳回。

## Cover

~ To: [[机构名]]／[[仲裁庭组成与主席姓名或"the Arbitral Tribunal"]]
~ Claimant: [[申请人全称，取自用户材料]]
~ Respondent: [[被申请人全称，取自用户材料]]
~ Case No.: [[案号]] | Seat: [[仲裁地]] | Language: [[程序语言]]
~ [[日期]]
~ **REQUEST FOR INTERIM MEASURES OF PROTECTION — URGENT**
~ Requested decision by: [[期望裁定时限，以适用规则与仲裁庭指示核对]]；grounds of urgency: [[紧迫性事实的一句话概括]]

## I. Introduction

This Request is submitted pursuant to [[Rule/临时或保全措施权力条号以适用规则版本官方文本核对]]。It asks the Tribunal to restrain [[对方简称]] from [[具体行为]] until [[期限或裁决作出]]，and does not seek any final determination of the parties' rights.

#! 首段一句话把"谁在何时前不得做什么"说清；同时明示本申请不预断实体。

## II. Nature of Relief Requested

The relief sought is expressed in imperative, verifiable and time-bound terms, and is directed only at conduct within the Respondent's control:

1. The Respondent shall refrain from issuing, confirming, extending or instructing any call on [[保函或信用证编号，写明文本与兑付条件，附件号]] and shall not take any step producing the same effect through any person acting on its behalf.
1. The Respondent shall maintain the Claimant's access to the Site at [[现场地址]] and shall restore access badges and gate permissions to the state recorded at [[基线定义：申请日或合同应然状态，附照片与记录，附件号]] by [[日期与时刻]]。
1. The Respondent shall not transfer, encumber, deliver or dispose of [[标的描述与识别码]] pending the determination of this Request.
1. The Respondent shall confirm in writing, within [[期限以适用规则条号官方文本核对]]，compliance with each item above.

#! 第 1 项只约束对方自身及其代理人的行为，不命令银行止付；如确需阻止兑付本身，法院路径与仲裁路径的先后顺序写入 VI 节，并由 11-governing-law 出具法域口径与置信度。

## III. The Need for Provisional Relief

### A. Prima facie jurisdiction and admissibility

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[条款有效存续、范围涵盖本争议、当事人与程序适格]] | [[合同正本与条款编号、机构受理函]] | [[条款不涵盖本请求或已失效]] | [[表面审查即可，不需穷尽管辖争点]] |
### B. Prima facie case on the merits

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[权利表面成立：终止条件未成就、己方履约完成度]] | [[续期与终止通知及回复、验收与进度记录、付款凭证]] | [[合同已有效终止或条件已成就]] | [[是否变相预断实体]] |
### C. Urgency

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[正在发生或即将发生、无法等待正常程序、窗口关闭日]] | [[对方行为的时间戳证据：通知、指令、公告、索赔函、门禁与系统变更记录；我方知悉日至申请日的间隔]] | [[迟延申请本身否定紧迫性]] | [[是否有明确日期与不可逆节点]] |
### D. Irreparable harm

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[金钱不足以弥补的具体机制，而非损失金额本身]] | [[保函与信用证兑付条件及到期日、资质与许可清单及失效后果、客户与订单流失函件、无法恢复原状的现场证据、兑付后追索不能的架构事实]] | [[损害属纯经济损失且可量化可赔]] | [[主张是否有文件支撑还是推测]] |
### E. Balance of interests

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[对对方负担小于对己方保护，最小干预版本]] | [[双方履约成本测算、己方对等承诺（继续付款、允许监督、报告义务）]] | [[措施对第三方与经营造成不成比例影响]] | [[是否可用监管账户等中立化方案替代]] |
### F. Non-aggravation of the dispute

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[措施不扩大争议，己方不采取对应行动]] | [[第三方依赖清单、己方停止其他保全动作的书面承诺]] | [[批准将引发对等升级]] | [[己方是否已同时向法院或他处申请]] |
### G. Not prejudging the merits and provisional character

| What must be shown | Evidential anchor in the client's materials | Likely objection | Tribunal's concern |
|---|---|---|---|
| [[救济为临时性、期限届满或情势变化即可调整]] | [[请求项与实体请求项的对照表]] | [[措施等同终局救济]] | [[是否先行实现实体利益]] |
## IV. Interim Relief Requested

Where conduct is within the Respondent's exclusive control, the Claimant seeks the positive restoration of a defined state rather than a general prohibition, so that compliance can be verified against a documented baseline.

The Claimant further requests an order that the Respondent provide a written statement, signed by an authorised officer, that after reasonable search no [[指定文件、指令、通知或其他标的的类别与期间]] exists or, if it exists, that it be produced in the form described in [[附件号]]。

The Claimant offers [[对等承诺或反担保方案，写明主体、金额、形式与期限]] and does not seek an undertaking in damages that the rules do not permit, having regard to [[Rule/担保与损害赔偿条号以适用规则版本官方文本核对]]。

## V. Procedure and Pre-Constitution Relief

The Claimant requests a response within [[期望答辩期以适用规则与仲裁庭指示核对]]，to be determined on [[书面审理或听证，二选一]] and served by [[送达方式]]。

The Tribunal [[已组成／尚未组成]]。Where relief is required before constitution, the applicable emergency or pre-constitution mechanism is invoked only to the extent that [[适用条件以官方文本核对]] is satisfied, including whether the clause excludes the mechanism, whether the arbitration agreement predates its introduction, and whether the case is administered at all; the deposit or fee condition and the lapse period of any decision, together with the requirement to pursue the main case before expiry, are likewise to be verified at [[适用条件以官方文本核对]]。

#! 三项失权要点必须写进时限日历：申请费或押金未缴可否被径行驳回、决定作出后的失效期、失效前必须推进主案的衔接。

## VI. Parallel Court Relief and Reservation of Rights

The Claimant [[已／未]] approach the courts of [[法域]] and does not seek any order inconsistent with this Request. Coordination between the arbitral and judicial routes — including whether local law requires an application to the Tribunal first, whether an arbitral measure is enforceable locally, and whether the assets lie in a different jurisdiction requiring separate local preservation — is governed by [[法域依据须由 11-governing-law 出具并标置信度]]。

All rights are reserved, including the right to re-apply on changed circumstances and to seek costs of this application in the final award on costs.

<pagebreak>

## Appendix 1 — Objection Skeleton (for the Respondent)

#! 抗辩要拆要件，不要重复"我没违约"；只辩实体等于替对方完成论证。最强两项通常是无紧迫性与损害可用金钱弥补。

1. Jurisdiction and admissibility of the application: [[条款是否排除措施权力、是否须先用尽协商、决定是否预断实体]]，per [[Rule/条号以适用规则版本官方文本核对]]。
1. No prima facie case: [[权利基础不成立的具体条款与事实]]。
1. No urgency: the Applicant knew of the conduct on [[知悉日，证据附件号]] and filed on [[申请日]]，and during that interval took no protective step, namely [[清单]]。
1. Harm compensable in money or speculative: [[可赔付性与量化路径]]；[[推测性损害的具体表现]]。
1. The measure would prejudge the merits or amount to final relief: [[批准即实现实体利益的具体对应]]。
1. Balance of inconvenience and third-party impact: [[对己方与第三方的负担测算]]。
1. The Respondent's own definition of the status quo: [[基线定义与其证据]]，which the Applicant's Request does not reflect.
1. In the alternative: [[范围缩至最小、期限缩短、要求申请人提供担保或损害赔偿承诺、快速实体复核、明示不预断实体与费用]]。
1. Costs of this application reserved to the final award.

#! 反向工具：要求申请人书面声明"经合理检索后不存在"某类文件或行为，可固定其事实面，供后续实体与费用阶段引用。

## Appendix 2 — Draft Operative Wording

#! 申请方替仲裁庭写好命令主文，能显著缩短裁定路径；中立化方案（提存或监管账户）常是最易获批的版本。落地要件必须具体到户名、银行、币种、金额、存入期限、支取条件、利息与账户费用，并给出银行拒绝开户时的替代，否则命令无法执行。

1. The Respondent shall, by [[日期]]，deposit [[币种与金额]] into an account held in the name of [[开户主体与账户名称]] at [[银行与分支机构]]，under the conditions set out in [[附件号]]。
1. No withdrawal shall be made except on the joint written instruction of the parties or on further order of the Tribunal.
1. Interest and account charges shall accrue to [[归属]] and shall be reported to the Tribunal on a [[报告频率与格式]] basis.
1. If the account cannot be opened on the terms above, the Respondent shall instead [[替代方案：保函、法院提存或其他可验证安排]] within [[期限以适用规则条号官方文本核对]]。
1. Non-compliance shall be treated as procedural non-cooperation and may be taken into account in the allocation of costs and in the assessment of the parties' case.
1. This order is provisional, does not prejudge the merits, and may be varied on a showing of changed circumstances; costs are reserved to the final award.

~ [[己方代理律所全称]] — [[签署人姓名与职务]]
~ List of Exhibits: [[附件清单]]
