---
title: Witness Statement — [[证人姓名占位]]
case: "[[案件代号]]"
workflow: 08-evidence
profile: witness
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
---

# Witness Statement of [[证人姓名占位]]

#! 适用 08-evidence / witness；仅按 suite.yaml 本 profile 核拟作证证人名单、与案件关系、能证明什么，涉密/特权文件处理口径，证人亲历事实与支持文件。运行 route.py --gate 08-evidence --profile witness --workdir <案件目录> --provided <案件目录>/case.json；缺项可按 pending/Q 出不可提交草案，不并入披露/专家闸门。
#! 先读当前 case-matrix.yaml；事实段按 08 写真实 F/E/EV 的 #! 锚点：追溯行，R/A 仅在确需时关联，不用 [[F]]，不把证言改成法律论辩。证人记忆本身可登记来源，不因无文件而虚构附件；提交前对抗审查，自审标 self_review。
#! 先取官方文本，证人陈述的形式要求、交换方式与日期、逾期不出庭的后果、庭前证人准备是否允许，全部来自本条，不手写：
#! python3 <suite>/scripts/fetch_official.py applicable --inst [[机构代号]] --commencement [[仲裁启动日]]
#! python3 <suite>/scripts/fetch_official.py fetch [[规则 source_id]] --to-md ；python3 <suite>/scripts/fetch_official.py lookup [[规则或软法 source_id]] --pattern "witness"
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json>
#! 一份陈述只给一位证人。复制进案件目录后按证人改名，逐份渲染并配套《中文审阅说明》；manifest 的段落号是后续盘问提纲与结案陈词引用 "paragraph __" 的唯一依据。
#! 更新禁止：陈述一经签署不得补写新事实；情况变化须另出一版新陈述并在版本说明里写清改了哪段、为何改。开庭前夜改核心事实等于把弹劾材料送给对方。
#! 接触纪律：证人只由本方及其律师接触，不得与对方有任何接触，不得与其他证人讨论彼此证言；庭前能否由律师准备证人存在法域差异，须先与程序令逐条比对，程序令未写者列为"待向仲裁庭确认"，不得按己方习惯默认允许。
#! 一段一事实：每段只写一个事实，段内不写法律评价、不写"本案应如何裁决"、不写推测；技术评价与推断只能由鉴定人写入专家报告，事实证人不得出意见证言。
#! 来源区分：亲历写 I saw / I said / I wrote / I decided；转述必须写成 as I was told by [[姓名]] on [[date]]，不得伪装成亲历；评价语（we believe、clearly the respondent breached）一律删。
#! 独立支撑：每段自问"除了这份文件本人还能说出什么"。无凭证的回忆尽量少写；重要事实给六要素——时间、地点、在场人、载体、内容摘要、文件编号。
#! 真实的不利事实由证人坦然承认，优于庭上被揭穿；起草流程须真实留痕（证人自写初稿→交律师→证人提供文件→律师加证据编号与格式→语言润饰→证人逐页审阅签署回传），此流程日后必在庭上被问。
## I. The Witness and the Basis of This Statement

I, [[证人姓名占位]], state as follows. I am [[职务全称]] of [[当事人全称]], a position I have held since [[起始日]] to [[终止日 or present]]. My qualifications and prior appointments are set out in the curriculum vitae attached as [[Exh. C-__]].
My relationship with the [[当事人全称]] is [[雇佣关系／任职期间／股权或关联关系／有无其他利益]]. I [[have / have not]] received any payment, benefit or inducement in connection with giving this statement, and I confirm that I am aware of the existence and status of this arbitration.
Before preparing this statement I read the documents listed in paragraph [[__]] below and the following further materials: [[逐项列名与其附件号，包括本方书状、案卷节选与访谈笔记]]. I did not discuss my evidence with any other witness in these proceedings.
This statement is made in [[语言]] and is [[prepared by me / drafted by counsel from notes made by me, with the process described in paragraph __]]. Where I refer to something said or written by another person, I say so expressly and identify who told me and when.
## II. Facts Within My Own Knowledge

The matters in this section are based on what I saw, said, wrote or decided myself. Where a statement is based on what I was told by another person, I identify that person and the date on which I was told.
#! 锚点纪律：每段末尾必须挂该段所依据的证据编号，与证据清单一一对应；段落不编号、无锚点，庭上就无法定位，盘问提纲与结案陈词也无法引用 "paragraph __"。编号在同一提名方全部证人陈述中连续，不按证人重开；不得引用未提交或庭前被排除的文件。
- Exhibit anchors in this statement run as [[Exh. C-__]] and are consistent with the exhibit list filed on [[date]]; no document is referred to that is not in the bundle.
- I do not express any opinion on the meaning of the contract, on whether any party is in breach or on what the Tribunal should decide; those matters are for the Tribunal and, where professional opinion is required, for the expert evidence.
- Paragraph numbers run continuously through this statement and are not restarted at each section.
### A. [[主题小节标题，按事件而非按论点评定，例如 The signing of the ESA]]

On [[31 January 2026 or date, 全文统一格式]] I [[在场／出席]] at [[地点]] together with [[在场人逐名及其身份]]. [[本人亲历的事实，一段一事实，短句、过去时、主动语态、不用法律术语]]. [[Exh. C-__]].
I wrote to [[收件人姓名与职务]] on [[date]] in the following terms: "[[邮件或函件的关键原文摘录]]". [[Exh. C-__]].
I decided to [[本人作出的决定及其依据]] because [[当时所知事实，不写事后推断]]. [[Exh. C-__]].
### B. [[主题小节标题，例如 The first delivery delay]]

I refer to paragraph [[__]] of the [[对方书状名称／己方书状名称]], which states [[该段被引用的具体内容，中性复述]]. As to that matter, [[本人亲历的事实]]. [[Exh. C-__]].
As I was told by [[姓名与职务]] on [[date]], [[转述内容，明确标注为转述]]. I did not see this myself, and I set it out only because it explains what I did next, namely [[本人随后的亲历行为]]. [[Exh. C-__]].
### C. [[主题小节标题，例如 The meeting of 4 March]]

At the meeting held on [[date]] at [[地点]], attended by [[出席人]], [[谁说了什么，逐句归属到具体人，不得笼统归属为 we agreed]]. [[Exh. C-__]].
I keep the [[会议纪要／系统记录／即时通讯导出]] of that meeting, a copy of which I attach as [[Exh. C-__]]. The document was created by [[制表人]] in the ordinary course of [[系统或流程]].
### D. [[不利事实小节标题：主动写入，不留给对方在盘问中揭示]]

I must state, and do not shy away from, that [[对己方不利但本人亲历的事实]]. At the time I understood this to mean [[当时的理解]], and [[本人随后的处理]]. [[Exh. C-__]].
## III. Source and Support Register

#! 本表起草后不随陈述对外提交，但它是交付前的自检工具，也是 manifest 之外唯一的段落—证据对照表：逐段核一遍"该段有无文件锚点""来源是亲历还是转述""除本人外还有谁能证同一事实"。凡无锚点、多证人重叠且日期口径不一致的段落，先改陈述再签署；同一细节在多份陈述中日期不一致会被集中攻击。
| Paragraph no. | Matter deposed to | Source of my knowledge | Document referred to | Other witness covering the same matter |
|---|---|---|---|---|
| [[__]] | [[一段一句话概括该事实]] | [[亲历：我看见／我说／我写／我决定；或转述：写明由何人于何日告知]] | [[Exh. C-__；无文件时写 none — 并考虑删除该段]] | [[姓名或 none；若另有证人，日期与措辞口径已核对]] |
## IV. Statement of Truth

I confirm that I have read this statement and that the facts set out in it are true to the best of my knowledge and belief. Where I have recorded what another person told me, I have said who told me and when, and I have not presented that as something I saw myself. I understand that this statement will stand as the evidence in chief if I am called to give oral evidence, and that I may be examined upon it.
I confirm that this statement was prepared with the assistance of [[当事人全称]]'s external counsel, that I have reviewed it page by page, and that the additions made by counsel were limited to numbering, references to exhibits and the correction of language without altering the substance of what I say.
## V. Oath, Affirmation and Signature
~ I [[declare / affirm]] that the contents of this statement are true. Sworn/affirmed at [[地点，国家]] on [[date]].
~ [[证人签名占位]] — [[证人姓名占位]], [[职务]]
~ Date: [[date]] Place: [[地点]]
~ [[如程序令要求见证、公证或特定声明句式，其文本以程序令与适用规则官方文本核对，本处按核对结果替换]]
~ Translated into [[语言]] by [[译员姓名与资质]], on [[date]]; the [[language]] text prevails. Translator's certificate attached as [[Exh. C-__]].
## Annex VI — Version and Drafting Record
#! 本表不落卷，但庭上必然被问"这份陈述是怎么来的、改过没有"：证人依律师提问自写初稿→证人提供文件→律师加证据编号与格式→语言润饰→证人逐页审阅并签署回传，每一步留日期与经手人。签署后不得补写新事实；需要变化即出新版本并写明改了哪段、为何改、何时通知对方与仲裁庭。开庭前夜改核心事实等于把弹劾材料送给对方。
| Version | Date | Paragraphs changed | Reason for the change | Reviewed and signed by | Notified to |
|---|---|---|---|---|---|
| [[v1]] | [[date]] | [[全文]] | [[初次起草；来源见上列流程]] | [[证人姓名占位]] | [[对方代理人与仲裁庭，按程序令交换日]] |
| [[v2]] | [[date]] | [[段落号]] | [[仅限纠正笔误或与所引文件原文不符之处；实体事实变化不得以更正名义补写]] | [[证人姓名占位]] | [[__]] |
## Annex VII — Confidential Pre-Hearing Note to the Witness
#! 本附录是发给证人本人的保密工作文件：标注 Confidential — Attorney Working Document，不提交、不落卷、不带入庭审室；分发用加密邮件并编号份数、留回执，开庭前收回纸质本。内容只讲程序纪律，绝不出现答案内容或"关于某事你要说……"式表述；能否由律师在庭前准备证人须先按程序令与适用法域确认，程序令未写者列为待向仲裁庭确认事项。
- When you enter: give your name as instructed, confirm the authenticity of your statement, state whether you take an oath or affirmation, and say whether you wish to add or correct anything before you begin.
- Listening and answering: wait until the question is finished; if you do not follow it, ask only that it be repeated and do not adopt the alternative wording offered by the questioner; answer what was asked and then stop.
- Precision: distinguish "I do not know", "I do not recall", "I only know part of it" and "this is my guess"; use "to the best of my recollection"; avoid absolutes and do not guess dates.
- Documents: before commenting on a document, confirm its author, addressee and date, and ask to see it if it is not in front of you; if the record differs from your memory, say you may be wrong rather than insisting.
- Scope: if a question goes outside your professional knowledge or your own experience, say so to the Tribunal; the Tribunal will also put questions, and you should answer them directly and calmly.
- Conduct: do not read from notes, do not look to counsel for an answer, do not discuss your evidence with other witnesses, do not argue with the questioner, and stop when the Tribunal intervenes; if you need a break, ask for one.
- Drafting of your statement: you may describe truthfully the process recorded in Annex VI; where a question seeks material covered by legal professional privilege, say that you treat it as privileged and let counsel raise the objection.
