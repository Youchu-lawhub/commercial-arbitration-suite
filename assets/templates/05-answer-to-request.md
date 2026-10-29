---
title: Answer to the Request for Arbitration
case: "[[case code]]"
workflow: 05-defence
profile: answer
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
toc: false
---
#! ===== 使用说明：以下所有 #! 行只给起草人看，渲染时整行丢弃，绝不进入 Word =====
#! 归属子技能 05-defence（被申请人开局），对应 suite.yaml 05 号 outputs 中的 "Answer to Request for Arbitration"。三种开局策略里本模板用于"实体详析答复"与"极简答复且明示不构成接受管辖"两式
#! （后者删去 V 节实体涵摄、把 VI 节压成条件性表态即可）；"延期申请保期限"式另用 13-procedural-letter.md。
#! 仅核 suite.yaml 的 answer profile：对方仲裁申请书全文与随附材料清单、机构收件日与规则规定的答辩期限、我方对程序事实的确认（送达、条款、主体）、对请求事项的回应与反请求/抵销是否提出；运行 route.py --gate 05-defence --profile answer --workdir <案件目录> --provided <案件目录>/case.json。缺项可按 pending/Q 出不可提交草案，不并入 counterclaim/jurisdiction 材料要求。
#! 读取当前 case-matrix.yaml，实质段按 05 写 F/E/EV/R/A 的 #! 锚点：追溯行，不用 [[F]]；纯否认可无本方 CL/R，不虚构己方举证事实。提交前留对抗审查，自审标 self_review。
#! 先取文本再落笔：applicable --inst <机构> --commencement <案件启动日> 定适用版本；fetch <rules-source-id> --to-md；lookup <rules-source-id> --pattern "Answer|counterclaim|time limit|number of arbitrators"。
#! 期限依适用规则、机构指令与实际触发事件核算；快递、邮件、内部收文凭证分别登记，不机械取最晚日；次日起算、节假日顺延、多方分别/共同起算及电子送达时区，
#! 全部从该版本规则文本现查后再填本模板的条号与期限占位（铁律 1、2）；届满日连同依据条号与来源标记写入时限日历，内部截稿提前量不少于期限的三分之一。
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --toc --strict --manifest <x.paras.json>；退出码 3＝仍有占位未填，本轮不交付。英文定稿必须同出《中文审阅说明》，
#! 并按 manifest 段落号用 paragraph n 引用（XREF 核验）；当事方名称、金额与关键日期的跨文件一致性由 CONSIST 核验。
#! 写法纪律：本答复是表态文书不是终审书状，火力留给实体书状与程序令后的披露阶段；纯否认可指明对方未证明的具体命题/要件，不要求虚构己方版本、积极抗辩或反请求；不适用的事实、金额及利息段删除。每一争点在中文审阅说明里配一行"对方最可能的反驳＋仲裁庭关注点"（铁律 7）。
#! 全篇失权风险：本答复是管辖与可受理性异议、组庭表态、仲裁地与语言与规则版本立场的唯一早期窗口，逾期即按失权处理；VI 节的最低必载项（仲裁员人数与提名表态、主席产生方式意见、规则版本表态）
#! 即使同时申请延期也必须在原期限内给出——机构可在我方沉默时径行按对方主张推进组庭，提名机会与三人庭结构事后不可复原；管辖异议不在此刻提出可能被认定为默示接受；
#! 合并句里作出的事实承认（合同签署＋收到货物＋欠款数额）不可撤回，须拆成单独行分别定态。
# Answer to the Request for Arbitration
~ [[date of submission; format 31 January 2026 or ISO, used consistently throughout]]; submitted pursuant to [[Rule/期限/费用以适用规则版本官方文本核对]] of the Rules, by and on behalf of the Respondent.
## THE PARTIES
#! 主体信息只从用户材料与机构来函取得，逐行 ~ 取消编号，四拍固定：法定全称→法律形式与注册地→送达地址与邮箱→代理人；名称须与申请书及案件档案逐字一致。
#! 多个被申请人时逐个列明并各自保留独立立场，共同答辩口径不一致会被对方利用；涉及国家或国有企业主体时区分各自主体地位与豁免主张，逐人写明保留。
~ [[Respondent full statutory name]],
~ a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]];
~ for all notices and communications in this arbitration: [[address for notices]], telephone [[number]], e-mail [[e-mail]], for the attention of [[name and title]];
~ represented by [[law firm name]], [[firm address]], telephone [[number]], e-mail [[e-mail]], for the attention of [[lead counsel name and title]].
~ Respondent,
~ versus
~ [[Claimant full statutory name]],
~ a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]]; represented by [[law firm and counsel details as stated in the Request]].
~ Claimant.
## I. INTRODUCTION
#! 下面前两句是承重句：缺第一句＝沉默回避可能被认定为接受；缺第二句＝后续补充答辩、追加异议与提出反请求被指为程序突袭。
#! 承认/否认粒度：以申请书段落号为行，每行只取 admitted / denied / no admission made 三种状态之一；禁止"全部否认"式偷懒，也禁止把可分割事实并成一句承认。
1. The Respondent submits this Answer pursuant to [[Rule/期限/费用以适用规则版本官方文本核对]] of the Rules, within the time limit running from its actual receipt on [[date]] of the institution's notification of the Request, as evidenced by [[courier receipt / e-mail timestamp / internal registration record, with its reference number]].
2. Except where expressly admitted below, the Respondent denies each and every allegation contained in the Request, including any allegation which it has not yet been able to verify, and admits nothing by its silence.
3. The Respondent reserves the right to supplement, amend or further particularize this Answer, its objections, its evidence and its arguments, including further objections to jurisdiction and admissibility.
4. This Answer is accompanied by the exhibits R-1 to R-[[n]] listed at its end and, where material, by extracts of the legal authorities cited, which are provided for the assistance of the tribunal and not as a matter of obligation; "the Request" means [[document and date]], "the Contract" means [[instrument and date]] and "the Rules" means [[rules and version, the Respondent's position being stated in section VI]].
## II. THE SALIENT FACTS
#! 己方版本时间线：只在与申请书冲突处展开，不复述对方叙述；一段一事实、不引法条。谈判与签署过程的事实要挂函件或会议纪要，无据写入会被指无据。
#! 逐条对应表把内部工作底稿的三态结论对外呈现，单元格内不写长段落；每一行的状态只取一个值，可分割事实拆行处理，一处过度承认后续无法撤回。
5. The Respondent sets out below the material facts so far as they differ from the account given in the Request.
6. The Respondent's position on each material allegation in the Request is as follows, stated at the granularity of the shortest severable assertion; a position recorded as "no admission made" is not a denial of such facts as may be proved.
| Request paragraph | Respondent's position | Basis |
|---|---|---|
| paragraph [[n]] | admitted | [[admitted as stated in the Contract, see exhibit R-1]] |
| paragraph [[n]] | denied | [[one sentence of reason, anchored to an exhibit number]] |
| paragraph [[n]] | no admission made | [[the Respondent has no knowledge of the matter and requires the Claimant to prove it]] |
7. On [[date]] the Respondent [[own version of the event, one fact per paragraph, each anchored to an exhibit listed at the end of this Answer]].
## III. JURISDICTION AND ADMISSIBILITY
#! 逐层递进，每层各自给证据锚点；任何异议此刻提出并明示不构成对管辖的接受。机构此阶段仅作表见（prima facie）判断，最终由仲裁庭裁，因此每一层都要"提出＋保留"。
#! 只写结论不写分层与锚点、或只在内部记录而未书面提交，都等于放弃；异议将在任务书与实体书状阶段重复提出。涉境外法对协议效力与可仲裁性的结论一律转 11-governing-law 分层标注置信度并注明需外部律师意见。
### A. Existence of the Arbitration Agreement
8. The Respondent denies that an arbitration agreement within the meaning of [[Rule/期限/费用以适用规则版本官方文本核对]] was ever concluded between the Claimant and the Respondent, because [[no signature by a person authorized to bind it]] / [[the instrument relied upon never entered into force]] / [[the alleged clause appears only in a document never agreed]], as appears from [[exhibit reference]].
### B. Validity
9. The Respondent contends that any arbitration agreement relied upon is invalid, because [[a form requirement was not met]] / [[the clause is void for uncertainty as to the institution or the seat]] / [[the signatory lacked capacity]], its validity being assessed under [[law of the arbitration agreement]]; [[法域依据须由 11-governing-law 出具并标置信度]].
### C. Enforceability and Arbitrability
10. The Respondent contends that the subject matter of the claims is not capable of settlement by arbitration in [[jurisdiction or jurisdictions to be identified]]; [[法域依据须由 11-governing-law 出具并标置信度]], and that the claims are to that extent inadmissible, being reserved to [[the exclusive jurisdiction of the State courts or of a statutory regime]].
### D. Scope: Whether the Clause Covers This Dispute
11. The Respondent contends that the arbitration agreement, properly construed, does not extend to the claims advanced, because [[the claims arise under a different instrument containing no arbitration clause]] / [[the clause covers disputes arising out of performance only]] / [[the parties named in the clause differ from the parties to the claims]]. Where several instruments are invoked, their correspondence with the clause is as follows.
| Contract or instrument | Arbitration clause | Party said to be bound | Position on coverage |
|---|---|---|---|
| [[instrument name and number]] | [[clause reference or "none"]] | [[party as named in the instrument]] | [[position taken, with the objection stated]] |
### E. Whether the Respondent Is Bound
12. The Respondent denies that it is a party to or otherwise bound by the arbitration agreement, because [[it did not sign the instrument]] / [[it is a distinct legal entity within the group and no act of assumption, succession or guarantee extends the clause to it]] / [[the alleged joinder by conduct is unsupported by the documents]], the burden of establishing that it is bound resting on the Claimant.
### F. Conditions Precedent and Time Limits
13. The Respondent contends that the claims are premature or inadmissible because the steps the clause requires before arbitration were not taken or not completed, namely [[amicable consultation or negotiation period]] / [[mediation]] / [[escalation to senior management]] / [[expert determination]], and because of [[any contractual or statutory time bar alleged to apply]]; [[法域依据须由 11-governing-law 出具并标置信度]]. The relevant rule provisions and periods are [[Rule/期限/费用以适用规则版本官方文本核对]].
### G. Express Objection and Reservation
14. The objections in this section are raised expressly and are not waived by the Respondent's participation in these proceedings, by its comments on the constitution of the tribunal or by the submission of this Answer; they will be repeated, and may be amplified, before the tribunal, in the terms of reference and in the Respondent's subsequent pleadings.
## IV. APPLICABLE LAW AND THE TRIBUNAL'S POWERS
#! 合同准据法与仲裁协议准据法分开写；条款若允许依公平善良原则（ex aequo et bono / amiable compositeur）裁断，先说明其含义、是否须先确定准据法以及我方是否同意。
15. The Respondent submits that the Contract is governed by [[law designated or contended, with the connecting factor stated]] and that the arbitration agreement is governed by [[law]]; [[法域依据须由 11-governing-law 出具并标置信度]]. It [[consents / does not consent]] to the tribunal deciding as amiable compositeur or ex aequo et bono and, in either case, submits that the applicable rules of law must first be established.
## V. APPLICATION OF THE LAW TO THE FACTS
#! 初步涵摄，点到为止：按法律要件逐段排列（无违约／因果中断／免责或限责条款适用／时效／金额不成立），每段先点出条款或依据再作涵摄，不在此阶段完成举证。
#! 责任抗辩与金额抗辩并行：每争点写成"即使认定责任成立，上限亦仅为 X"的双向防守；两处口径必须一致，同一事件不得出现两个日期或两种算法。
16. Without prejudice to its objections to jurisdiction and admissibility, the Respondent submits in outline that the claims fail for the following reasons.
17. In the first place, [[no breach is attributable to the Respondent, the obligation relied upon requiring proof of an event which the Claimant has not established]].
18. In the second place, [[causation is interrupted, by reason of the intervening event to be set out with its date and exhibit]].
19. In the third place, [[an exemption or limitation clause applies, under the Article of the Contract whose wording will be quoted verbatim in the Respondent's subsequent pleading]].
20. In any event, even if liability were established, the Respondent's exposure would be limited to [[currency]] [[amount]], computed on the basis stated in section VI below.
## VI. THE RESPONDENT'S COMMENTS ON THE REQUEST
#! 最低必载项不可因延期省略：人数与提名表态、主席产生方式意见、规则版本表态必须在原期限内给出，否则提名权与三人庭结构失权。
#! 若主张不存在有效仲裁协议或我方非条款约束方，本节全部表述改用条件句（in the event that / without prejudice and without any admission），杜绝任何无条件承认管辖的措辞。
#! 仲裁地、语言与准据法立场各给可操作理由（文件语言、证人语言、执行地、中立性），情绪化偏好无效；对对方金额量化的异议既影响费用档级也是担保费用的计算基数，须逐项具体提出，不得一笔带过。
21. As to the number of arbitrators, the Respondent agrees with the number proposed in the Request, namely [[number]], or proposes a different number, namely [[number]], having regard to the amount in dispute and the complexity of the case.
22. As to nomination, the Respondent nominates as arbitrator [[full name]], [[nationality]], resident of [[place]], telephone [[number]], e-mail [[e-mail]], whose curriculum vitae is filed at [[exhibit reference]], the nominee having confirmed in writing his or her willingness to serve, in accordance with [[Rule/期限/费用以适用规则版本官方文本核对]].
23. As to the presiding arbitrator, the Respondent proposes the mechanism provided by [[the clause or the applicable Rule/期限/费用以适用规则版本官方文本核对]] and invites the institution to have regard to the objective criteria of [[proficiency in the language of the arbitration, experience of the relevant industry and of the governing law, availability]], stating no preference as to any individual.
24. As to the place of arbitration, the Respondent [[supports the seat proposed in the Request]] or contends that the seat should be [[city and jurisdiction]], for reasons of [[the availability of enforcement, neutrality and court support for interim relief]]; [[法域依据须由 11-governing-law 出具并标置信度]].
25. As to the language of the arbitration, the Respondent contends that the language should be [[language]], being [[the language of the Contract, of the documentary record and of the witnesses]].
26. As to the applicable rules, the Respondent accepts that the proceedings are governed by [[rules and version per the fetch_official applicable output]] or contends that [[version]] applies, and is amenable to the Rules in their [[version]].
27. As to the amounts stated in the Request, the Respondent objects that [[the claim is not quantified]] / [[the computation duplicates certain items]] / [[amounts already paid have not been deducted]] / [[the exchange rate and the period applied are incorrect]] / [[alternative claims should be counted on the principal claim only]], and reserves its position on the advance on costs and on any application for security for costs under [[Rule/期限/费用以适用规则版本官方文本核对]].
28. The Respondent further reserves the right to request document production, to seek interim measures and, if appropriate, to oppose or apply for security for costs, and to ask for a procedural timetable reflecting [[the steps referred to above]].
## VII. RESERVATIONS AND RELIEF SOUGHT
#! 主文按实际立场选用层次句式：In the first place / In the alternative / Subsidiarily / In any event；币种、金额及利息仅用于金钱请求，利息须有依据并写明利率或算法与起止点。非金钱请求写清具体裁判内容，履行方式与期限仅在适用时填写。
#! 第 32 段按当事人实际指示仅保留一项：不提出反请求／同时提出／依法保留以后提出。同提时用 05-counterclaim.md 并以 paragraph n 交叉引用而不复述；保留不等于承诺提出，也不豁免适用规则、期限及所需许可。纯否认可仅请求驳回对方请求，不强造本方 CL/R、积极事实或反请求；删除不适用的异议与救济。
29. The Respondent respectfully requests that the tribunal: in the first place, decide that it lacks jurisdiction over, or that the claims are inadmissible to the extent of, the objections stated in section III; in the alternative, dismiss the Claimant's claims in their entirety;
30. order that the Claimant bear the costs of this arbitration in full, being the institution's administrative charges, the arbitrators' fees and expenses and the Respondent's legal and other costs [[if interest is sought on those monetary costs: with interest under the verified applicable basis at the stated rate or calculation method from the stated start date to the stated end date or actual payment]]; and
31. in any event, grant such further or other relief as the tribunal considers appropriate, the Respondent expressly reserving each of the rights and objections stated in this Answer.
32. The Respondent [[does not bring a counterclaim]] / [[files a counterclaim together with this Answer, as set out at paragraph n of the accompanying Counterclaim]] / [[reserves the right to seek to bring a counterclaim later, subject to the applicable Rules, time limits and any required permission, without committing to bring one]].
## RESERVATIONS, SERVICE AND SIGNATURE
#! 送达与份数：依适用版本判定由机构转送还是由本方直接向对方送达并交副本；提交前再核份数、递交渠道与是否须附送达说明，不合该版本要求即被要求补正而浪费期限。
33. The Respondent serves a copy of this Answer on the Claimant by [[channel and address]] on [[date]], retaining proof of despatch, and files it with the institution in [[number of copies and format required under Rule/期限/费用以适用规则版本官方文本核对]].
#! 签名块四项齐备：授权签字人姓名、职务、签署地、签署日期。PoA 权能与形式要求（公证、认证、译本）属当地法判断，转 11-governing-law，本技能只提示触发。未在期限内按机构要求的份数与方式提交，在部分规则下不影响程序继续，等于自弃抗辩机会。
~ Dated: [[date]]
~ Place of signature: [[city, jurisdiction]]
~ For and on behalf of [[Respondent full statutory name]]
~ [[signature]]
~ [[name and title of the authorized signatory]], duly authorized
<pagebreak>
## LIST OF EXHIBITS
#! 附件按 R- 连续编号并与正文逐段引用对照；本阶段不放证人陈述与专家报告。机构来函与收件凭证是期限起算的锚点，务必列入。
| Exhibit | Document | Date | Referred to at |
|---|---|---|---|
| R-1 | [[Request for Arbitration as notified by the institution, with its paragraph references]] | [[date]] | paragraph [[n]] |
| R-2 | [[Institution's notification and evidence of the actual date of receipt]] | [[date]] | paragraph [[n]] |
| R-3 | [[Instrument containing the alleged arbitration clause]] | [[date]] | paragraph [[n]] |
| R-4 | [[Correspondence on the negotiation and execution of the Contract]] | [[date]] | paragraph [[n]] |
| R-5 | [[Records of performance and of amounts already paid]] | [[date]] | paragraph [[n]] |
| R-6 | [[Schedule of the Respondent's computation of the amounts in dispute]] | [[date]] | paragraph [[n]] |
| R-7 | [[Curriculum vitae and written consent of the nominee]] | [[date]] | paragraph [[n]] |
| R-8 | [[Power of attorney evidencing the signatory's authority]] | [[date]] | paragraph [[n]] |
