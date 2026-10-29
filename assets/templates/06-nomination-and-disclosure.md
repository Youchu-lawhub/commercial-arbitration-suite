---
title: Nomination, Acceptance and Disclosure Correspondence Pack
case: [[案件代号]] | [[机构名]] Case No. [[案号]]
workflow: 06-tribunal
profile: disclosure
mode: legal
footer_left: [[Draft v1]] — [[日期]]
keep_sources: false
toc: true
---

# NOMINATION, ACCEPTANCE AND DISCLOSURE CORRESPONDENCE

#! 本文件是骨架模板，复制到案件目录 deliverables/ 后逐段填写；所有 #! 行只给起草人看，渲染时整行丢弃，永不进入 Word。
#! 适用子技能：06-tribunal 第 3 项（发提名/指定函）、第 4 项（收到披露函后的处理）、第 8 项（授权委托书权限核验）。Part A 提名函、Part B 候选人回应要点表、Part C 披露函代理人回应、Part D 权限骨架，四段共用本文件。本包默认按 disclosure profile 过闸；仅单用 Part A 提名函时改为 profile: nomination 并重跑闸门。
#! 闸门未过不得使用：python3 <suite>/scripts/route.py --gate 06-tribunal --profile disclosure --workdir <案件目录> --provided <案件目录>/case.json。三项 gate（条款约定的仲裁员人数与指定机制／双方已提名或已指定人选与日期／候选人背景与潜在利益冲突线索）任一缺项，本轮只出《补充材料与信息确认清单》视图。
#! 先取官方文本（顺序执行，未跑完不得落笔条号与期限）：python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <仲裁启动日> ；python3 <suite>/scripts/fetch_official.py check --inst <机构id> ；python3 <suite>/scripts/fetch_official.py fetch <规则版source_id> --to-md ；python3 <suite>/scripts/fetch_official.py lookup <规则版source_id> --pattern "number of arbitrators|appointment|president|confirmation|disclosure" --max 12 。软法分类另跑：python3 <suite>/scripts/fetch_official.py lookup iba-conflicts-2024 --pattern "List|waivable|non-exploitable" --max 12 。
#! 渲染与核验：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json> ；再跑 python3 <suite>/scripts/verify_suite.py --workdir <交付目录> --mode submission。--strict 下残留占位以退出码 3 拦下，本轮不交付。
#! 纪律一（提名函）：只写可验证的客观资质与可用性——语言能力、行业与技术背景、相关法域与程序经验、仲裁地／执行地的中立性、当前在办案件数、时间承诺、费用计算方式的接受度、与当事人及代理人的既往接触（列案号、年份、角色、方别）。禁止任何倾向性表述（如"理解我方立场""与我方理念一致""熟悉我方处境"）：这类文字一旦进入披露，就成为对方挑战与裁决撤销阶段攻击独立性的证据，也损害己方可信度。
#! 纪律二（软法定位、规则定论）：情形分类清单只作分类语言使用，结论必须落回本案适用规则的独立公正义务、"可正当怀疑"式客观标准、披露义务、异议与挑战期限、决定机关，条号现查后带来源标记；软法不具拘束力，不得作为准许或驳回的依据。
#! 纪律三（表态）：只有两种可写的表态——不提出异议并声明就此事实放弃异议，或提出异议并保留挑战权利（条号与事实逐一对应）。"希望仲裁庭予以考虑""请仲裁庭自行裁量"一类模糊句式等于放弃异议：可能被认定为未在规则期限内提出异议而失权。内部备忘不等于向机构或仲裁庭的书面表态。

## Part A — Letter of Nomination

#! 收件块逐行用 ~ 取消编号。秘书处、对方代理人、（如已组成）仲裁庭全覆盖；送达方式与份数按机构来函与规则口径写，不凭印象。

~ [[己方代理律所全称]]
~ [[地址]]，[[电话]]，[[邮箱]]
~ Counsel for the [[Claimant 或 Respondent]]
~ To: [[机构名]] Arbitration Secretariat, attention [[部门或收件人]]
~ Copy to: [[对方代理人全称]]，[[邮箱]]
~ [[日期，格式全文统一]]
~ **Re: Nomination of co-arbitrator — [[案件代号]] / Case No. [[案号]]（规则版本 [[适用规则版本]]）**

#! 正文段：首段写指定权来源与条号；次段写人数与主席产生机制的意见与规则补足依据；再次是候选人可核验信息与同意声明；末段留联系与收件日确认。缺一项必载项即可能被要求补正而吃掉期限。

We act for the [[Claimant 或 Respondent]] in the above-referenced arbitration and write pursuant to [[Rule/我方指定权条款条号以适用规则版本官方文本核对]] to nominate a co-arbitrator on behalf of our client.

The arbitration agreement provides for [[条款约定的仲裁员人数，按条款原文摘录]]. As to the mechanism for the presiding arbitrator: where the clause provides one, quote it; where it does not, state our client's position under [[Rule/主席或独任产生机制与任命机关条号以适用规则版本官方文本核对]] as [[补足结论]]，with the source marker attached. Our client's position on the applicable rules edition is [[表态]].

The candidate nominated is:

- Full name, including titles and spelling as in the passport or bar register: [[候选人全名]]
- Nationality: [[国籍]]
- Residential and postal address: [[住址与通讯地址]]
- Email address: [[邮箱]]
- Curriculum vitae, academic and professional career: [[附件号]]
- Current availability: [[在办案件数与时间表承诺，取候选人书面确认]]
- Acceptance of the fee basis: [[计时或从价、费率上限口径，取候选人书面确认]]
- Prior contact with the parties or counsel: [[案号、年份、角色、方别，逐项列明]]

The candidate has consented in writing to the appointment. The candidate's statement of acceptance, impartiality and independence, together with the disclosure statement, are enclosed as [[附件号]]，and that statement covers the positions of all affiliated entities identified in the curriculum vitae. The contact details set out above are provided so that the Secretariat and counsel may put questions directly to the candidate for the purpose of completing any disclosure.

Please treat this letter as our nomination under the rules referred to above and confirm the date on which it is deemed received, having regard to [[Rule/异议期与确认期的起算与送达条号以适用规则版本官方文本核对]]. Any request for further information on the nomination should be addressed to the undersigned.

~ Yours faithfully,
~ [[己方代理律所全称]]
~ [[签署人姓名与职务]]
~ Enclosures: [[附件清单]]

<pagebreak>

## Part B — Response Memorandum: Eight Questions to the Candidate

#! 本节用于己方对候选人（含我方提名者）发问与核验，也用于阅读对方披露时逐项比对。八问全部要落到具体事实与时间段，抽象的"无利益冲突"表态在挑战程序中几乎没有价值。
#! 我方提名仲裁员的披露同样要评估：过度"沉默使用"披露会在裁决撤销阶段反噬，故答复与承诺均书面留存。

| 序号 | 拟向候选人提出的问题 | 要确定的事实 | 答复含糊时的跟进 |
|---|---|---|---|
| 1 | Present and past relationships with each party and each counsel firm, in any capacity | 关系性质与相对方主体 | 要求列出实体全称 |
| 2 | Period of each relationship: start date, end date, still continuing | 时间轴 | 要求到月份并标注是否存续 |
| 3 | Whether any such relationship concerned the same subject matter as this dispute | 与本案标的的关联性 | 要求说明业务事项类型 |
| 4 | Direct or indirect economic interest in any party or in the outcome | 经济利益与持股 | 要求说明收费安排与结算主体 |
| 5 | Role within, and relationship to, parent, sister or affiliated entities | 关联方与办公室层面 | 要求指明具体办公室与隔离措施 |
| 6 | Prior involvement as arbitrator, expert or counsel in arbitrations involving the parties or counsel | 既有仲裁 involvement，列案号与方别 | 要求提供案件编号与年份 |
| 7 | Availability and time commitment for the expected timetable | 可用性 | 要求书面时间表承诺 |
| 8 | Undertaking to make continuing disclosure throughout the proceedings | 持续披露义务承诺 | 要求书面确认至裁决签署 |

#! 收到答复后建时间轴表：关系起始日、终止日、是否仍存续、是否同一业务领域、是否与本案标的相连、涉及哪一办公室或关联实体、收费安排。软法分类只用于给事实归类型，结论仍写规则标准。

## Part C — Counsel's Response to an Arbitrator's Disclosure Statement

~ To: [[机构名]] Secretariat and [[仲裁庭全体成员／首席仲裁员]]
~ Copy to: [[对方代理人全称]]
~ [[日期]]
~ **Re: Response to the disclosure statement dated [[披露函日期]] — Case No. [[案号]]**

We confirm receipt on [[收到日期与时刻，附送达凭证编号]] of the disclosure statement of [[仲裁员全名]] dated [[披露函日期]]. We note that the time limit for any objection runs from that receipt and is governed by [[Rule/异议与挑战期限条号以适用规则版本官方文本核对]].

#! 信息不足时先发问询再决定是否挑战，顺序有独立价值：问询本身要写成行使异议权所必需的步骤，否则事后被指异议迟延由己方造成。

The statement does not permit our client to assess the matters disclosed. Pursuant to [[Rule/要求补充披露或询问的条号以适用规则版本官方文本核对]] we request that the arbitrator provide the following further information: [[逐条具体问题：时间段、是否同一事项、是否仍存续、涉及的实体与办公室、收费安排]]. These questions are necessary for the exercise of our client's right of challenge, and we request a reply within [[答复期限，Rule/期限以适用规则版本官方文本核对]]，such period not to be counted against the time limit for our client to state its position.

#! 表态只能二选一，且必须书面发给机构／仲裁庭。以下两段是互斥选项，交付前删除其一，保留的段落必须逐条对应事实与条号。

**Option A.** Having reviewed the disclosure and the further information received on [[日期]]，our client does not object to the arbitrator's continued mandate and, for the purposes of [[Rule/放弃异议条号以适用规则版本官方文本核对]]，waives any objection based on the facts disclosed.

**Option B.** Our client objects to the continued mandate of [[仲裁员全名]] and reserves its right to challenge under [[Rule/挑战程序条号以适用规则版本官方文本核对]]，on the basis that the disclosed facts [[逐条对应：事实编号 — 标准要素]]。A separate challenge application will follow within the applicable time limit.

~ [[己方代理律所全称]] — [[签署人姓名与职务]]

<pagebreak>

## Part D — Power of Attorney: Enumerated Powers Skeleton

#! 以"要做的每一个程序动作"为轴逐项对照权限清单。缺一项就可能在提名或签署任务书时被要求补正而吃掉期限；写入又无内部授权（如和解）同样损害诚信评价。期限式授权必须留缓冲：到期日晚于裁决签署与费用结算的预计时点，或直接写覆盖至执行完毕。
#! 公证、附加证明书或领事认证、官方译本等跨境形式要求，以用户材料与机构实践为准提示；若某法域有强制要求，转 11-governing-law 出具口径并标置信度。本套件不代为认定主体信息。

~ **POWER OF ATTORNEY**
~ Grantor: [[公司全称]]，[[注册地与注册号]]，[[地址]]，represented by [[签署人姓名与职务]]
~ Grantee: [[律师或法律顾问姓名、执业身份、律所名称与地址]]
~ Matter: claims and counterclaims before the arbitral tribunal constituted under [[适用规则版本]] in case no. [[案号]] and all matters connected with it

The Grantor confers the following enumerated powers, to be checked item by item against the procedural steps actually planned:

- to conclude or participate in arbitration proceedings and to sign procedural submissions
- to nominate, propose or agree arbitrators and to comment on the number and the mechanism for the presiding arbitrator
- to sign terms of reference and procedural orders
- to bring, amend, respond to and withdraw claims and counterclaims
- to settle, to sign settlement documentation and to acknowledge receipt of settlement sums
- to accept service of documents and to receive monies against valid receipt
- to appoint experts and to present witnesses
- to apply for interim measures and security for costs, and to respond to such applications
- to attend hearings and to make oral submissions
- to sign award-related documents and to take enforcement steps

The power is valid until [[有效期或到期日，须晚于裁决签署与费用结算预计时点]]，or, where preferred, until completion of the proceedings including enforcement. Place, date, signature and seal: [[签署与印章信息]]。Case number and rules edition must match the institution's correspondence exactly.
