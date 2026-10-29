---
title: Expert Evidence Pack — Terms of Engagement, Agreed Terms of Reference, Joint Conference and Report Structure
case: "[[案件代号]]"
workflow: 08-evidence
profile: expert
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
---

# Expert Evidence Pack (Master Template)

#! 适用 08-evidence / expert；仅按 suite.yaml 本 profile 核专业争点与是否需要专家、双方专家机制，涉密/特权文件处理口径，专家拟委托事项与资质信息。运行 route.py --gate 08-evidence --profile expert --workdir <案件目录> --provided <案件目录>/case.json；缺项可按 pending/Q 出不可提交草案，不并入披露/证人闸门。
#! 先读当前 case-matrix.yaml；实质段按 08 写 F/E/EV/R/A 的 #! 锚点：追溯行，不用 [[F]]；逐项区分事实、数据、假设与专业意见，非金钱事项不强加利息。提交前对抗审查，自审标 self_review；拆件保留适用元数据。
#! 先取官方文本：专家人数、报告交换与会议日期、可采性与询问方式的规则依据、费用分摊一律不手写。
#! python3 <suite>/scripts/fetch_official.py applicable --inst [[机构代号]] --commencement [[仲裁启动日]]
#! python3 <suite>/scripts/fetch_official.py fetch [[规则 source_id]] --to-md ；python3 <suite>/scripts/fetch_official.py lookup [[规则或软法 source_id]] --pattern "expert"
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json>
#! 用法：A 委托要点给对方与仲裁庭看（或写入程序令）；B 问题清单双方联合商定；C 会议议程与联合报告在专家报告交换后使用；D 是每份专家报告的固定章节。复制进案件目录后按用途拆成独立草稿。
#! 范围纪律：只允许量子、技术、外国法三类专家争点，其余事实问题由事实证人承担；范围写宽会引发对等指定、拖长程序表并推高费用。
#! 外国法：争点一旦落在外国法的存在与内容，即触发 11-governing-law，按来源分层给出置信度或标注"需外部律师意见"（铁律 6），本包内不作任何外国法实体结论；[[法域依据须由 11-governing-law 出具并标置信度]]。
#! 假设事实（assumptions）必须与本方书状段落号一致：专家的假设与书状主张不符，等于让仲裁庭以假设代替证据，报告整体失效。
#! 计算模型可核性：每一输入项须注明出处（书状段落号／卷宗页码／文件附件号）并给出可复算的取值路径；无法回溯的输入项在盘问中即被剔除，其结果连带失分。
#! 越界风险：专家不是 Advocatus Dei。报告只做其专业范围内的判断，不得代当事人论证法律责任、不得评价对方诚信、不得写"仲裁庭应当如何裁决"；越界部分会被要求删除，并拖累其余意见的可信度。
#! 独立性先于专业度：委托前完成利益冲突核查并在委托函中写入对仲裁庭的首要义务、独立性声明、费用计时方式与不予结果挂钩的承诺；不得推荐具体专家人选，人选由用户与其外部顾问确定。
## PART A — TERMS OF ENGAGEMENT AND INSTRUCTIONS TO THE EXPERT

### A.1 Scope of the Engagement
- Field of expertise and the specific issue: [[先选 quantum／technical／foreign law 三者之一，再用一句话界定争点，并写明不含哪些事项]].
- Matters the expert is asked NOT to address: [[法律责任的认定／对方诚信的评价／裁决主文的建议]].
- Documents supplied, each with its reference: [[书状名称与段落号、证据编号、数据源导出件]]; the list shall be finalised before the report is drafted so that no new material is added after the exchange of reports.
- Facts to be assumed, each anchored to a submission paragraph: [[逐条写"假设内容 + 见何份书状第几段"，与书状主张逐字一致]].
- Deliverables and dates: [[初稿／口头说明／会议出席／联合报告／庭审作证]] on the dates fixed in Procedural Order No. [[__]].
### A.2 Independence, Overriding Duty and Fees
The expert's overriding duty is to assist the Tribunal within the expert's field of knowledge, and that duty prevails over the obligations arising from the instrument of appointment. The expert shall state in the report that he or she is and remains independent of the parties and of their counsel, and shall disclose, in the report, any circumstance liable to affect that assessment.
- Remuneration: hourly or daily rates per timekeeper, with a running record of time and task category, payable [[由何方、按何节奏]], and expressly not contingent on the outcome of the case.
- Travel and inspection: any site visit or inspection shall be notified to the other party in advance, and the other party shall be entitled to attend; reports of visits shall be produced to the Tribunal and not used as undisclosed material.
- Instructions log: a written record of all instructions and of all materials supplied shall be kept and, if the Tribunal so directs, exchanged, since the drafting process will be examined at the hearing.
- No advocacy: the expert shall not be a person who will also be claimed as a factual witness, and shall not be billed both as a fact witness and as an expert.
### A.3 Pre-Appointment and Pre-Filing Checks
- Conflict check completed against the candidate's current and recent engagements, and the result recorded in the file: [[核查日期、核查依据与结论]].
- Remuneration not contingent on the outcome; rate basis and cap agreed in writing: [[计费方式与上限，以机构或事务所官方费率文本核对]].
- Scope tested against the pleadings: every matter assigned must correspond to a pleaded issue, and every pleaded issue assigned to an expert must not be one that a factual witness can cover.
- Assumptions tested sentence by sentence against [[书状名称]] paragraph [[__]]; any mismatch corrected in the instructions before the report is drafted.
- Data tested for auditability: each input in the model has a source reference and a stated method of derivation, failing which the input is removed from the model.
- Foreign-law content of the issue identified: if the question concerns the existence or content of a foreign law, the instruction is issued only after [[法域依据须由 11-governing-law 出具并标置信度]]; no substantive conclusion on foreign law is written in this pack.
- Candidate selection is made by the client and its external advisers; this template does not nominate or recommend any expert.
## PART B — AGREED TERMS OF REFERENCE AND QUESTION LIST

#! 双方使用同一组问题、同一份职权范围，问题由双方共同拟定并请仲裁庭确认；一方单方拟定的问题清单会在庭上被指为引导。第 5 列在联合报告完成后填写，写明该问的结论是 agreed 还是 unagreed，并指向联合报告的对应段。
| Issue No. | Question to be put to both experts | Claimant's expert and position | Respondent's expert and position | Outcome in the joint report |
|---|---|---|---|---|
| [[1]] | [[单句、可回答、限定专业范围的问题；不含预设答案与评价语]] | [[专家姓名占位与职务；其报告结论段落号与该结论一句话]] | [[专家姓名占位与职务；其报告结论段落号与该结论一句话]] | [[agreed 或 unagreed；联合报告对应段落号；分歧幅度与量化区间]] |
## PART C — EXPERT JOINT CONFERENCE AND JOINT REPORT

### C.1 Conference Agenda
- Opening by the chair of the conference; confirmation that the experts' overriding duty is to the Tribunal and that the conference is not an exercise in settling a common position in advance.
- Discussion of each question in Part B in turn, recorded as agreed or non-agreed, with the reason for each disagreement.
- Identification of the issues the experts ask the Tribunal to clarify, and the direction of any further data or inspection required.
- Signature of the joint report by both experts, with the date and place, and an agreed list of the matters that remain in dispute for oral examination.
### C.2 Joint Report
#! 联合报告只列共识与分歧，不得在庭前统一口径；分歧点须写明分歧的量化幅度与各自推理要点，方便仲裁庭直接抄用。会议记录与报告交换的日期须与程序令一致。
| Item | Question (Part B reference) | Agreed between the experts | Non-agreed: position of each expert and reason |
|---|---|---|---|
| [[1]] | [[问题编号与简述]] | [[双方共同接受的事实、方法或计算公式，一句话；并注明其记录出处]] | [[分别写专家甲与专家乙的立场与依据，再给出分歧幅度与量化区间]] |
### C.3 Mode of Oral Examination
#! 择一写入庭审程序令，判据：争点方法性强、双方专家在同一数据基础上分歧、仲裁庭需要即时对照时用并列询问（hot-tub）；分歧在于事实经过、需要完整陈述其工作与假设、或需口译控制节奏时按传统顺序分别询问。并列询问须预先约定主持人、提问顺序、每人回答时限与仲裁庭插问优先。
- Option 1, examination in the traditional order: [[主询问时限、盘问时限、再盘问限于盘问新出现事项、仲裁庭提问时限，均以小时计，以程序令官方文本核对]].
- Option 2, concurrent examination (hot-tub): [[由主席主持，双方就同一问题轮流提问，专家之间可互相回应，仲裁庭可随时插问；限时与记录方式同上]].
## PART D — STRUCTURE OF THE EXPERT REPORT

### D.1 Instructions
The expert states who appointed him or her, on what issue, the documents supplied, the facts assumed and the questions put, and identifies any instruction received after the report was started.
### D.2 Opinion
The expert's conclusions are set out in summary form at the beginning of the report, one numbered paragraph per conclusion, each cross-referring to the reasoning in section D.4, so that the Tribunal can lift the conclusion into the award without reconstruction.
### D.3 Data and Assumptions
Each input is listed with its source reference — [[书状 paragraph __ / 卷宗页码 / Exh. C-__ / 专家自行取得的数据及其取得方法]] — together with the reason the input is relied on, the range of alternative values considered and the sensitivity of the result to each of them.
#! 下表同时是交付前自检与庭上应对盘问的核对工具：凡无法回溯到卷宗或书状段落的输入项，要么删除，要么在报告中明确标为纯假设，不得让它进入最终数字——被剔除的输入项会连带其计算结果一起失分。
| Input no. | Input item | Value adopted | Source reference | Alternative values considered | Effect on the result |
|---|---|---|---|---|---|
| [[1]] | [[逐项列出：设备寿命／折价率／价格递增率／贴现率等]] | [[__]] | [[书状段落号、卷宗页码或数据取得方法]] | [[区间与取值理由]] | [[对结论金额的量化影响]] |
### D.4 Reasoning
The methodology is stated first, including the recognised standards or authorities applied and the version of each, then the calculation or analysis is worked through step by step so that a reader can reproduce it; the alternative method and why it was not preferred are addressed in the same section.
### D.5 Limitations
The expert states what he or she has not been asked to do, what is outside the field of expertise, the data that could not be obtained and the effect of that gap, and any matter on which the expert's view would change if a different assumption were found by the Tribunal to be correct.
### D.6 Declaration
I state that I have understood my duty to assist the Tribunal and that this duty overrides my obligation to the party instructing me; that I am independent of the parties and of their counsel; that this report contains my genuine professional opinion; that where my opinion is not fully expressed I have explained why; and that I will attend the hearing and submit to examination if directed to do so.
~ Signed: [[专家签名占位]] — [[专家姓名占位]], [[专业资格与所属机构]]
~ Date: [[date]] Place: [[地点]]
~ Attachments: [[简历、资格证明、独立性声明、计算底稿的表格式导出]]
