---
title: Objection to Jurisdiction and Admissibility
case: "[[case code]]"
workflow: 05-defence
profile: jurisdiction
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
toc: false
---
#! ===== 使用说明：以下所有 #! 行只给起草人看，渲染时整行丢弃，绝不进入 Word =====
#! 归属子技能 05-defence，对应 suite.yaml 05 号 outputs 中的 "管辖权/可受理性异议（保留权利写法）"；依适用版本可并入 05-answer-to-request.md 第三节，也可作为单独函件先行提出，两种路径先现查。
#! 仅核 suite.yaml 的 jurisdiction profile：对方仲裁申请书全文与随附材料清单、机构收件日与规则规定的答辩期限、我方对程序事实的确认（送达、条款、主体）、管辖权异议依据与提出时间；运行 route.py --gate 05-defence --profile jurisdiction --workdir <案件目录> --provided <案件目录>/case.json。缺项可按 pending/Q 出不可提交草案，不要求反请求材料。
#! 读取当前 case-matrix.yaml，实质段按 05 写 F/E/EV/R/A 的 #! 锚点：追溯行，不用 [[F]]，不强造本方 CL/R 或金额利息；提交前留对抗审查，自审标 self_review。
#! 先取文本再落笔：applicable --inst <机构> --commencement <案件启动日> 定适用版本；fetch <rules-source-id> --to-md；
#! lookup <rules-source-id> --pattern "jurisdiction|plea|admissibility|prima facie|preliminary question"；期限、递交方式、副本份数与机构此阶段的审查标准（多仅表见判断）全部现查（铁律 1、2）。
#! 未取得官方文本前，本文书所有条号、期限与份数一律保留 [[Rule/期限/费用以适用规则版本官方文本核对]] 占位；每个条号在替换后逐处挂来源标记（legal 模式默认剥离标记，底稿保留）。
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --toc --strict --manifest <x.paras.json>；退出码 3＝仍有占位未填，本轮不交付。
#! 英文定稿必须同出《中文审阅说明》（铁律 5），并在其中按本文书 manifest 段落号用 paragraph n 引用；每项异议还要在说明里各写一行"对方最可能的反驳＋仲裁庭关注点"（铁律 7）。
#! 失权后果须逐项核验：按异议性质、适用法、规则与程序令查提出期限、方式、审查主体及沉默或参与程序的后果，不预设此刻是所有异议的统一截止点；
#! 核机构当前审查权限（是否仅为 prima facie）、仲裁庭权限及法院审查路径；有依据的异议逐项"提出＋保留"，表明参与程序不意在接受管辖，但保留措辞不替代期限遵守或所需许可，
#! 后续在适用的任务书或书状阶段重申；补充或新增是否获准须另核，不把内部记录当提交，也不把表述或锚点缺陷自动等同放弃。
#! 写法纪律：对有争议的管辖前提使用条件性或保留措辞（without prejudice / in the event that / assuming arguendo），事实陈述须真实；不以单一句型断定同意或放弃；
#! 协议效力、可仲裁性、前置程序与时效转 11-governing-law 按合同法／仲裁协议法／仲裁地法分层研究；后两项依具体审理体系分类为管辖、可受理性或实体问题，查救济与审查路径，未闭合项列待核或外部律师问题；
#! 各项证据锚点必须指向具体附件号与文件内页；缺锚点须补证或标待核，是否依法提出仍依适用法、规则与程序事实判断。
# Objection to Jurisdiction and Admissibility
~ [[date of submission; format 31 January 2026 or ISO, used consistently throughout]]; submitted pursuant to [[Rule/期限/费用以适用规则版本官方文本核对]] of the Rules, without prejudice and solely in order to contest jurisdiction and admissibility.
## THE PARTIES
#! 逐行 ~ 取消编号；本节只列主体身份，不作任何接受管辖的表示；名称与答复及案件档案逐字一致，多个被申请人时逐个列明并各自保留独立异议。
~ [[Respondent full statutory name]], a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]], for all notices: [[address]], telephone [[number]], e-mail [[e-mail]], represented by [[law firm and counsel details]],
~ the Respondent,
~ versus
~ [[Claimant full statutory name]], a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]], represented by [[law firm and counsel details as stated in the Request]],
~ the Claimant.
## I. CONDITIONAL OPENING
#! 本节三句保留条件性开头：先界定实际异议、再按当前审查阶段请求处理、最后表明不意在接受管辖；如 F/G 经研究属实体问题，核准能否在本函备位提出，否则转实体答辩并调整开头及救济，不能一面提出一面声明绝不涉及实体。
1. Without prejudice to, and without any waiver of, the Respondent's objections to jurisdiction and admissibility as specified below, the Respondent files this Objection for their determination, together with [[any alternative defence on the merits identified below and permitted to be raised at this stage, or a reservation for the appropriate pleading]].
2. In the event that the arbitration proceeds under [[the applicable institutional review mechanism and Rule/期限/费用以适用规则版本官方文本核对]], the Respondent requests that the arbitral tribunal determine the objections set out below within its powers at the relevant stage.
3. Nothing in this Objection, and no participation by the Respondent in these proceedings, including any comment on the constitution of the tribunal, on the place of arbitration or on the language of the arbitration, is intended as an acceptance of jurisdiction, a waiver of any objection, or an admission of any allegation in the Request; the legal effect of such participation remains subject to the applicable law and Rules.
## II. THE OBJECTIONS, TAKEN ITEM BY ITEM
#! 下面七项按层展开（存在→生效→可执行→范围→主体约束→前置条件→时效），只保留有事实和法律依据的项；每项先提出、再列四栏表（事实／证据／规则依据（占位条号）／对方最可能的反驳）。
#! 有依据的备位层写明 "in the alternative"，逐项提出并保留；A/B/E 先核仲裁协议准据法、可分性及协议自身的合意、权限、形式或生效缺陷，不将主合同瑕疵自动传导；F/G 先研究分类、期限及救济，机构与仲裁庭的权限分别核验。
### A. That No Arbitration Agreement Exists
4. The Respondent objects that no arbitration agreement was ever concluded between it and the Claimant, and, in the alternative, that any such agreement was never perfected, because [[the instrument bearing the clause was never signed by an authorized person]] / [[the alleged agreement appears only in a document to which the Respondent is not a party]].
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the signing event or absence of it, with its date]] | [[exhibit number and page; original signature pages]] | [[clause reference; Rule/期限/费用以适用规则版本官方文本核对]] | [[authority, apparent signatory or course of dealing]] |
### B. That the Arbitration Agreement Has Not Entered into Force
5. The Respondent objects that, assuming arguendo that an arbitration agreement was concluded, it did not enter into force because [[an unfulfilled condition or approval requirement applicable to the arbitration agreement itself, with the clause wording, dates and verified legal basis]]. The Respondent relies on [[the agreement-specific defect and its effect after assessing separability under the law governing the arbitration agreement]], not merely on the main contract's invalidity, non-entry into force or termination.
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the condition affecting the arbitration agreement itself and the facts of non-fulfilment, with dates]] | [[exhibit number and page; clause and relevant approval records]] | [[arbitration agreement governing law; separability and agreement-specific condition; 法域依据须由 11-governing-law 出具并标置信度]]; [[Rule/期限/费用以适用规则版本官方文本核对]] | [[the arbitration clause is autonomous; the condition affects only the main contract or has been fulfilled or waived]] |
### C. That the Arbitration Agreement Is Incapable of Being Performed, or the Claims Are Not Arbitrable
6. The Respondent objects that, in the event that the tribunal were to find that an arbitration agreement exists and is in force, it is incapable of being performed, alternatively that the claims are not arbitral in character, because [[the clause refers to a body or institution that cannot be identified or no longer exists]] / [[the relief sought is reserved to the courts or a statutory regime]].
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the defect in the clause or the nature of the relief sought]] | [[exhibit number; correspondence on the attempted constitution of the tribunal]] | [[Rule/期限/费用以适用规则版本官方文本核对]]; arbitrability under [[law; 法域依据须由 11-governing-law 出具并标置信度]] | [[the clause is capable of a reasonable construction; severable claims]] |
### D. That the Arbitration Agreement Does Not Cover These Claims
7. The Respondent objects that the arbitration agreement, on its true construction, does not extend to the claims advanced in the Request, because [[the claims arise under a different instrument containing no arbitration clause]] / [[the clause is limited to disputes arising out of performance]] / [[the claims concern third parties not named in the clause]].
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the instrument under which each claim arises, and the parties to it]] | [[exhibit number per instrument; multi-contract correspondence table]] | [[quoted words of the clause; Rule/期限/费用以适用规则版本官方文本核对]] | [[incorporation by reference; a single economic unit; implied extension]] |
### E. That the Respondent Is Not a Party to or Bound by the Arbitration Agreement
8. The Respondent objects that it is not a party to, and is not otherwise bound by, the arbitration agreement, because [[it did not sign the instrument]] / [[it is a separate legal entity within the group and no act of assumption, succession or guarantee extends the clause to it]] / [[no consent to be joined can be inferred]].
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the signatory's identity and the absence of any mandate binding this entity]] | [[exhibit number; corporate records and signing authority documents]] | [[clause reference; Rule/期限/费用以适用规则版本官方文本核对 on parties and joinder]]; [[法域依据须由 11-governing-law 出具并标置信度]] | [[group of companies doctrine; agency; estoppel; participation in performance]] |
### F. That the Conditions Precedent to Arbitration Were Not Satisfied
#! 先核条款是否设强制前置条件及其适用法、履行、放弃和补正；记录具体体系将争点归为管辖／可受理性／实体的依据，按结论选相应请求，未定性不得预填不可受理。
9. The Respondent relies on the non-completion of [[the required consultation, mediation, escalation or notification step, its wording and relevant dates]]. Under [[the verified applicable law and authorities]], this is a matter of [[jurisdiction, admissibility or the merits; select the supported classification and explain why]], for which the Respondent seeks [[the corresponding relief identified in section IV, including any available stay or opportunity to cure]].
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the required step, attempts at compliance and relevant dates]] | [[exhibit number and page; notices and proof of despatch]] | [[clause reference; applicable law and authorities on classification, waiver and cure; 法域依据须由 11-governing-law 出具并标置信度]]; [[Rule/期限/费用以适用规则版本官方文本核对]] | [[the step is not mandatory, was waived or performed, can be cured, or entails a different classification or remedy]] |
### G. That the Claims Are Time-Barred
#! 逐请求核期限性质、起算、届满、中断／暂停／延展及时间适用；分类与准据法选择本身也须研究，不将时效一律归为可受理性，实体抗辩按许可阶段提出或转相应书状。
10. The Respondent relies, in the alternative, on limitation or prescription under [[the verified applicable regime and authorities]], classified in the relevant system as a matter of [[jurisdiction, admissibility or the merits; select and explain]]. For [[each affected claim]], the period began on [[verified triggering event and date]] and expired on [[verified date and calculation, accounting for interruption, suspension, extension and exceptions]], with the consequence of [[the supported legal effect and corresponding relief in section IV]].
| Fact relied upon | Evidence | Rule or clause basis | Likely contention of the Claimant |
|---|---|---|---|
| [[the triggering event and dates for each claim, including facts affecting the period]] | [[exhibit number and page; notices, acknowledgment and suspension materials]] | [[applicable limitation regime, time-applicable version and classification authorities; 法域依据须由 11-governing-law 出具并标置信度]]; [[Rule/期限/费用以适用规则版本官方文本核对]] | [[interruption, suspension, extension, a later accrual date, an exception or a different classification and consequence]] |
## III. RESERVATION OF RIGHTS AND NON-ACCEPTANCE OF JURISDICTION
#! 本节两句保留：表明不意在接受管辖，并说明后续主张受适用期限和许可约束；声明不保证免于失权，不替代及时、有效地提出异议。
11. This Objection is submitted without prejudice to and expressly reserving the Respondent's rights, and is not intended as acceptance of jurisdiction or of any disputed position concerning the applicable rules, the place or the language of arbitration, subject to the applicable law and Rules.
12. The Respondent reserves, to the extent permitted by the applicable law, Rules and procedural orders, the right to repeat, amplify or add to the objections in subsequent pleadings or any applicable terms of reference, including objections arising from newly known facts, subject to the relevant time limits and any required permission.
## IV. RELIEF SOUGHT IN RESPECT OF THIS OBJECTION
#! 两套时序表述按已核规则与争点选主备位：先行处理或随实体裁决处理；每项救济必须与 II 节已研究的分类及受影响请求对应，不将所有问题都写成无管辖或一律驳回。
#! 按分类核权限、提出和审查期限、裁决后救济：管辖问题可请求无管辖决定；可受理性问题研究暂缓、补正或不予受理；实体问题研究对应抗辩及驳回范围。费用、预缴款及并行法院路径依适用规则和法律转 11-governing-law 与 10-award-post 核验。
13. The Respondent respectfully requests preliminary determination of [[the identified objections suitable for separate determination]] under [[Rule/期限/费用以适用规则版本官方文本核对]], and [[relief supported by the verified classification: a finding of no jurisdiction over specified claims; a stay or opportunity to cure, or dismissal as inadmissible where available; or determination of an identified defence on the merits if appropriate at this stage]].
14. In the alternative, the Respondent requests determination of [[the remaining objections or defences]] in the award, with [[the legally supported consequence for each affected claim, consistent with its classification and without treating a merits defence as a jurisdictional objection]], and [[the corresponding costs and advance-on-costs treatment under the applicable Rules]].
15. Subsidiarily, if determination is deferred or an objection is rejected at this stage, the Respondent requests [[directions preserving the opportunity to address unresolved objections or defences, any available stay or cure, responsive pleading deadlines and costs arrangements]], subject to [[the verified requirements for further review or challenge]].
## SERVICE, COPIES AND SIGNATURE
#! 送达与份数：依适用版本判定由机构转送还是由本方直接向对方送达并附送达说明；异议函未在期限内按要求的份数与方式提交，可能被视作未提出。
16. The Respondent serves a copy of this Objection on the Claimant by [[channel and address]] on [[date]], retaining proof of despatch, and files it with the institution in [[number of copies and format required under Rule/期限/费用以适用规则版本官方文本核对]].
#! 方言陷阱：~ 行不会结束上一段的待处理段落，故本段与下方签名块之间必须保留一行 #! 指引（或空行），否则本段会被推到签名块之后成段，位置与编号都会错。
~ Dated: [[date]]
~ Place of signature: [[city, jurisdiction]]
~ For and on behalf of [[Respondent full statutory name]]
~ [[signature]]
~ [[name and title of the authorized signatory]], duly authorized
~ Evidence relied upon: exhibits R-1 to R-[[n]], listed in the schedule of evidence filed with this Objection and in the Answer.
