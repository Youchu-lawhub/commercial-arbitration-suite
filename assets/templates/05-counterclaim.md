---
title: Counterclaim
case: "[[case code]]"
workflow: 05-defence
profile: counterclaim
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
toc: false
---
#! ===== 使用说明：以下所有 #! 行只给起草人看，渲染时整行丢弃，绝不进入 Word =====
#! 归属子技能 05-defence，对应 suite.yaml 05 号 outputs 中的 "Counterclaim（如有）"；与 05-answer-to-request.md 同提时，本文件是答复之后的第二份文书（也可并作一份，按适用版本允许的写法现查）。
#! 仅在用户选择提出反请求且存在依据时使用；纯否认无需本模板。按适用规则、程序令与实际阶段核期限和新增请求许可，不默认存在任务书；确有以后提出意图才如实保留，保留文字不延长期限或替代许可。
#! 仅核 suite.yaml 的 counterclaim profile 全部材料要求，运行 route.py --gate 05-defence --profile counterclaim --workdir <案件目录> --provided <案件目录>/case.json；缺项可按 pending/Q 出不可提交草案，未核关键依据不得进入提交态。
#! 读取当前 case-matrix.yaml，以 CL 标识反请求；实质段按 05 写 F/E/EV/R/A 的 #! 锚点：追溯行，不用 [[F]]。非金钱请求不强加金额、币种或利息，删除不适用计算栏；提交前留对抗审查，自审标 self_review。
#! 先取文本再落笔：applicable --inst <机构> --commencement <案件启动日> 定适用版本；fetch <rules-source-id> --to-md；lookup <rules-source-id> --pattern "counterclaim|advance on costs|set-off"；
#! 反请求的期限、份数、递交渠道、是否须同时向对方送达、是否须随附预缴款及其计算方式（含是否与主请求合并计算争议金额）一律现查后替换占位（铁律 1、2）；未取得文本前不得落任何条号、天数与费率。
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --toc --strict --manifest <x.paras.json>；退出码 3＝仍有占位未填，本轮不交付。
#! 与答复同时交付时，每份正式文书各配同名《中文审阅说明》，不以一份说明替代两份配对；按各自 manifest 的段落号用 paragraph n 引用（XREF 核验），当事方、同一事件日期与金额口径须一致（CONSIST 核验）。
#! 自足性铁律：本反请求假设答复部分不被阅读也能独立支撑管辖、责任与所求救济；保留管辖依据、必要条款引述和事实主线。金钱请求附计算，非金钱请求写清对象、行为、范围、条件与适用期限。
#! 未量化金钱请求、缺少必要事实或依据，可能引发补正、费用核定或期限风险，具体后果须核适用规则。共用事实可用 paragraph [[n]] 交叉引用，但必要事实仍在本文件写明并与答复保持一致。
#! 不同合同或主体不当然排除反请求；逐项核仲裁协议范围、当事人约束及多合同程序依据。送达主体、渠道、时点与证明按本案规则及程序指示落实。
#! 新争点涉及文件披露或专家证据时，同步提出时间安排；迟延申请的许可标准及后果现查，不预断必然获准或被拒。
# Counterclaim
~ [[date of submission; format 31 January 2026 or ISO, used consistently throughout]]; submitted together with the Answer pursuant to [[Rule/期限/费用以适用规则版本官方文本核对]] of the Rules.
## THE PARTIES IN THEIR COUNTERCLAIM CAPACITY
#! 逐行 ~ 取消编号；本节要把双重身份写清，避免后续书状把"Respondent"与"Claimant"指代混乱；名称与答复及案件档案逐字一致。
~ [[Respondent full statutory name]], a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]], for all notices: [[address]], telephone [[number]], e-mail [[e-mail]], represented by [[law firm and counsel details]],
~ the Respondent in the arbitration and the Counterclaimant,
~ versus
~ [[Claimant full statutory name]], a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]], represented by [[law firm and counsel details as stated in the Request]],
~ the Claimant in the arbitration and the Respondent to the Counterclaim.
## OPENING AND STATUS OF THIS COUNTERCLAIM
#! 自足性声明是本节的骨头：说明本反请求依同一仲裁条款提出、独立成立，并说明与答复的关系（合并或并行），使仲裁庭无须回读答复即可理解请求。
1. The Counterclaimant submits this Counterclaim pursuant to [[Rule/期限/费用以适用规则版本官方文本核对]] of the Rules, together with its Answer of [[date]], and pleads it as an independent claim arising out of the same instrument and the same course of dealing as the claims in the Request.
2. This Counterclaim is complete in itself for the purposes of jurisdiction, liability and quantum; where facts are common to the Answer, the Counterclaimant refers to and relies upon the paragraphs there identified rather than restating them, and where it does state a fact here, that statement is intended to be consistent with, and not an alternative to, the statement made in the Answer.
## A. FACTS
#! 两段分工：与答复共用的事实只用 paragraph [[n]] 引用（不复述，避免同一事件两处不同日期或口径）；反请求特有的事实必须在本文书里写全，四拍顺序（合同—履行—违约—损害）与答复一致。
### A1. Facts Common with the Answer
3. The Counterclaimant repeats and relies upon paragraph [[n]] of its Answer (formation and terms of the Contract) and paragraph [[n]] of its Answer (the course of performance), and adopts each admission and denial recorded in the table at paragraph [[n]] of its Answer.
4. So far as those paragraphs are relied upon for the purposes of this Counterclaim, the following facts are stated in the Counterclaimant's own words: [[the single fact necessary to support the counterclaim which is not already pleaded in the Answer, with its date and exhibit reference]].
### A2. Facts Specific to the Counterclaim
5. On [[date]] the Claimant [[act or omission relied upon as the basis of the Counterclaim, one fact per paragraph, each anchored to an exhibit listed at the end of this Counterclaim]].
6. The Counterclaimant performed its corresponding obligations, in particular [[each step taken, with date and documentary reference]].
7. By reason of the matters set out in paragraphs [[n]] to [[n]] above the Counterclaimant suffered [[the loss or additional cost incurred, with its date range and the document evidencing it]].
## B. LIABILITY
#! 责任段只讲构成要件与因果关系，不论金额；每项请求各自给出合同条款依据与法律或原则依据，条款原文用 > 缩进段逐字引述并标附件号。
#! 与主请求的关系要交代：哪些事实同时构成对主请求的抗辩（双向防守），哪些是独立请求；抵销（set-off）作为替代立场提出时用 "in the alternative and by way of set-off"。
8. The Counterclaimant claims that the Claimant is liable to it in respect of the matters set out in section A, on the ground that [[the obligation breached, identified by the Article of the Contract and the conduct relied upon]].
9. The relevant provision of the Contract provides as follows, its wording being material to the constituent elements of the claim:
> "[[verbatim text of the provision relied upon, transcribed exactly from the Contract as filed with exhibits]]"
10. The breach caused the loss complained of, because [[the causal link stated as a matter of fact, with the intervening events identified and addressed]].
11. In the alternative, and in any event, the Counterclaimant claims set-off against the Claimant's claims in the amount of [[currency]] [[amount]], computed as set out in section C below.
12. The law governing this head of liability is [[law designated in the Contract or contended, with the connecting factor stated]]; [[法域依据须由 11-governing-law 出具并标置信度]].
## C. QUANTUM
#! 金额段不论责任；每一分项一行，给计算式、期间、币种与凭证号，利息写满四要素（基数、利率或口径、起算日、单利或复利直至实际支付日）。
#! 争议金额口径按适用规则现查：反请求与主请求是否合并计算、选择性请求按主请求计、抵销是否影响基数、汇率取值日、连带责任不重复计；口径同时决定费用档级与是否触发或脱离简易程序。
13. The Counterclaimant's claims are quantified as follows, each item being supported by the document identified in the last column of the table set out below.
| Item | Amount claimed | Currency | Computation (base x rate x period) | Period | Evidence |
|---|---|---|---|---|---|
| [[head of loss 1]] | [[amount]] | [[currency]] | [[formula with each input stated]] | [[from date]] to [[to date]] | [[exhibit reference]] |
| [[head of loss 2]] | [[amount]] | [[currency]] | [[formula with each input stated]] | [[from date]] to [[to date]] | [[exhibit reference]] |
| [[additional costs incurred]] | [[amount]] | [[currency]] | [[schedule of costs with unit rates]] | [[from date]] to [[to date]] | [[exhibit reference]] |
| Total | [[sum of the items above]] | [[currency]] | [[computation stated, duplicates and sums already paid deducted]] | [[period]] | [[schedule exhibit]] |
14. Interest is claimed on each item above at [[rate or basis]] from [[date]] to the date of actual payment, on a [[simple / compound]] basis, the basis of the rate being [[the contractual provision relied upon or the basis to be determined]].
15. The exchange rate applied is [[rate]] as at [[date]], being the date [[the rules or the practice of the institution indicates for conversion]].
16. The amount in dispute for the purposes of the advance on costs is stated by the Counterclaimant as [[currency]] [[amount]] on the footing that [[the counterclaim is assessed on its own amount / is aggregated with the claim / is left out of the aggregation under the applicable provision]], the point being governed by [[Rule/期限/费用以适用规则版本官方文本核对]].
## D. RELIEF SOUGHT
#! 主文逐条独立成段，与 R 救济记录一致；金钱请求写金额、币种及有依据的利息并与 C 节对账；非金钱请求写对象、行为、范围、条件及适用期限。按实际主备位关系选用下列示例，非金钱请求可为首位，删除不适用的付款、抵销、利息与金额段。
17. The Counterclaimant respectfully requests that the tribunal: in the first place, order the Claimant to pay it [[currency]] [[amount]], together with interest at [[rate or basis]] from [[date]] to the date of actual payment;
18. in the alternative, and to the extent that the tribunal does not make the order sought in the preceding paragraph, give effect to the Counterclaimant's claim by way of set-off against the Claimant's claims in the amount of [[currency]] [[amount]];
19. subsidiarily, order [[the non-monetary relief sought, stated in operable terms: performance of a specified obligation, delivery of documents, release of a security, a declaration as to the parties' rights]], within [[period]];
20. in any event, order that the Claimant bear the costs of this Counterclaim, including the institution's administrative charges, the arbitrators' fees and expenses and the Counterclaimant's legal and other costs, with interest at [[rate or basis]] from [[date]] to actual payment; and
21. grant such further or other relief as the tribunal considers appropriate, the Counterclaimant reserving the right to supplement, amend or particularize this Counterclaim and to increase the amounts claimed.
## CHECKLIST ONE: WHETHER THE COUNTERCLAIM FALLS WITHIN THE SAME ARBITRATION CLAUSE
#! 本节与下节是提交前内部核对表：定稿对外版整节删除（或原样转入《中文审阅说明》第四节）；删除后其余段落编号由 Word 自动重排，不影响 paragraph n 的引用逻辑。
#! 仲裁协议范围或当事人约束等关键项未核时，不进入提交态；先补材料并评估原期限内可行行动。后续提出须核本案新增请求条件与所需许可，不默认存在任务书或必然获准。
| Item to be verified | Basis of the counterclaim | Arbitration clause for the principal claim | Result |
|---|---|---|---|
| Whether the counterclaim arises under the same instrument as the principal claim | [[instrument name and number]] | [[clause reference]] | [[verified / not verified]] |
| Whether the wording of the clause extends to the type of dispute claimed | [[type of dispute relied upon]] | [[quoted words of the clause]] | [[verified / not verified]] |
| Whether the parties to the counterclaim are both bound by that clause | [[party said to be bound]] | [[signatory identified in the instrument]] | [[verified / not verified]] |
| Where several instruments are invoked, whether a common or incorporated clause supports them | [[other instruments relied upon]] | [[common clause, or none]] | [[verified / not verified]] |
| Whether any special governing law or condition precedent applies to the counterclaim | [[special regime or condition precedent]] | [[applicable law to be determined]] | [[法域依据须由 11-governing-law 出具并标置信度]] |
| Whether the facts pleaded here match the facts pleaded in the Answer | [[event and date as pleaded in the Answer]] | [[event and date as pleaded here]] | [[consistent / to be aligned]] |
## CHECKLIST TWO: ADVANCE ON COSTS AND MODE OF FILING
#! 反请求的预缴与提交方式必须现查规则文本与机构费用表后填实，未附预缴或份数不合要求，可能被视作未提出而错过同提窗口。
| Item to be verified | Content | Source | Status |
|---|---|---|---|
| Whether a separate advance on costs accompanies the counterclaim | [[Rule/期限/费用以适用规则版本官方文本核对]] | [[fee schedule, date of retrieval]] | [[to be verified]] |
| Amount of the advance and the basis of its computation | [[以官方费用表核对]] | [[fee schedule, date of retrieval]] | [[to be verified]] |
| Time limit for payment and the date of receipt required | [[Rule/期限/费用以适用规则版本官方文本核对]] | [[institution's payment notice]] | [[to be verified]] |
| Filing channel and file format | [[online portal, e-mail or paper; searchable PDF and bundling requirements]] | [[institution's filing page, date of retrieval]] | [[to be verified]] |
| Number of copies, per party, per arbitrator and for the institution | [[computed from the applicable version]] | [[Rule/期限/费用以适用规则版本官方文本核对]] | [[to be verified]] |
| Whether service on the other party is required together with proof of service | [[self-service or transmission by the institution]] | [[Rule/期限/费用以适用规则版本官方文本核对]] | [[to be verified]] |
| Filing of the proof of service | [[courier reference, e-mail timestamp with time zone, acknowledgment]] | internal records | [[to be verified]] |
| Whether the need for document production and expert evidence is announced in time for the timetable | [[heads of disclosure and expert fields]] | coordination with 08-evidence | [[to be verified]] |
~ Dated: [[date]]
~ Place of signature: [[city, jurisdiction]]
~ For and on behalf of [[Respondent full statutory name]]
~ [[signature]]
~ [[name and title of the authorized signatory]], duly authorized
## LIST OF EXHIBITS
#! 附件按 R- 连续编号并与正文逐段引用对照；与答复共用的附件沿用原编号并注明"also filed with the Answer"，不重复列。本阶段不放证人陈述与专家报告。
| Exhibit | Document | Date | Referred to at |
|---|---|---|---|
| R-9 | [[Instrument or purchase order underlying the Counterclaim]] | [[date]] | paragraph [[n]] |
| R-10 | [[Correspondence on the breach relied upon in section A]] | [[date]] | paragraph [[n]] |
| R-11 | [[Records of the additional costs incurred, with unit rates]] | [[date]] | paragraph [[n]] |
| R-12 | [[Computation schedule supporting section C]] | [[date]] | paragraph [[n]] |
| R-13 | [[Evidence of service of this Counterclaim on the Claimant]] | [[date]] | paragraph [[n]] |
