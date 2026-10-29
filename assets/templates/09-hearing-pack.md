---
title: Hearing Pack — Agenda, Opening, Cross-Examination, Closing, Pre-reading and Hearing-Day Checklist
case: "[[案件代号]]"
workflow: 09-hearing
profile: hearing
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
toc: true
---

# Hearing Pack (Master Template)

#! 适用 09-hearing / hearing；按 suite.yaml 本 profile 原文登记庭审日期、时长、形式（现场/远程）与仲裁庭指示，双方争点清单与证据清单终版，证人出庭安排与翻译需求，时间分配方案（time schedule）。运行 route.py --gate 09-hearing --profile hearing --workdir <案件目录> --provided <案件目录>/case.json；缺项可按 pending/Q 出不可提交草案。
#! 先读当前 case-matrix.yaml；实质段按 09 写 F/E/EV/R/A 的 #! 锚点：追溯行，不用 [[F]]，保留庭审记录页行与附件映射；纯否认不强造 CL/R，非金钱请求不强加币种利息。庭前/提交前对抗审查，自审标 self_review；内部盘问提纲及策略另件 pair: false，不入卷。
#! 先取官方文本：笔录与更正程序、证人不出庭的后果、可采性条款、演示材料截止日均以规则与庭审程序令原文为准，一律写 [[以适用规则版本/程序令官方文本核对]]。
#! python3 <suite>/scripts/fetch_official.py applicable --inst [[机构代号]] --commencement [[仲裁启动日]]
#! python3 <suite>/scripts/fetch_official.py fetch [[规则 source_id]] --to-md ；python3 <suite>/scripts/fetch_official.py lookup [[规则 source_id]] --pattern "witness"
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json>
#! 用法：本包各节按庭审程序令的条目顺序排列，交付前删去仲裁庭已经签发并覆盖了同一内容的条款，避免两份文本冲突；每节另配《中文审阅说明》。
#! 时间分配一律用小时，不用天数：可用水时 − 休息 − 程序讨论 − 开场陈述 − 仲裁庭提问 = 可分配询问时，双方各半并写明余数处理；每位证人主询问设上限，超时由仲裁庭直接切断；仲裁庭提问占用其自身时间；超过一两分钟的异议计入异议方时间；由秘书保存"平等用时"记录。用天数分配会导致一方以整日占用、己方证人被压缩。
#! 盘问提纲按仲裁员阅读顺序排列（争点 → 该争点的关键文件 → 文件页码 → 要证人确认的一句话），不按证人笔记本的时间顺序；每问先给出处再发问，封闭式、一事实一问。
#! 纪要与不利记录：庭审当日核对出席名单、证人出庭与盘问顺序、用时消耗、被驳回或被限制的提问、任何口头承诺；对方或仲裁庭口径进入纪要而与事实不符时，须在订正期内提出书面纠正并附记录页码，不当日提出即视为默认。
#! 仲裁庭初步非约束性意见：请求须双方联署或正式入卷，并明写"不作任何争点的结论、不影响裁决"；回复严格区分"接受商业框架"与"不放弃法律立场"，不得据其放弃权利或承认原本未认的事实；和解窗口与"不和解即恢复程序"的自动时间表一并写入记录。
## 1. Time Math and Allocation Rules
- Total time available: [[天数]] days × [[每日小时数]] hours = [[__]] hours, per Procedural Order No. [[__]].
- Deductions: breaks [[__]] hours; procedural discussion [[__]] hours; opening statements [[__]] hours per party; questions of the Tribunal [[__]] hours, taken from the Tribunal's own time.
- Time left for examination: [[__]] hours, divided equally, with the remainder dealt with as [[__]]; a running record of equal time is kept by [[秘书／庭审秘书]].
- Per-witness caps: examination-in-chief [[__]] hours; cross-examination [[__]] hours; re-examination limited to matters arising in cross [[__]] hours.
- Objections lasting more than [[__]] minutes are charged to the party making them; overruns are stopped by the Tribunal without argument.
## 2. Agenda
| Session | Topic | Who | Time | Materials |
|---|---|---|---|---|
| [[1]] | [[Opening statement of the Claimant]] | [[发言律师姓名占位]] | [[__]] hours | [[时间线幻灯片与编号；核心卷宗页码范围]] |
| [[2]] | [[Examination of the witness nominated by the Claimant — 证人姓名与提名方]] | [[提问律师姓名占位；证人姓名占位]] | [[主问／盘问／再盘问 各几小时，合计 __ 小时]] | [[Exh. C-__；该证人先前陈述段落号]] |
| [[3]] | [[Expert session, concurrent or traditional examination]] | [[专家与双方律师]] | [[__]] hours | [[专家报告与联合报告段落号]] |
| [[4]] | [[Closing statements and directions on post-hearing briefs and costs]] | [[双方代理人／仲裁庭]] | [[__]] hours | [[仲裁庭问题清单；庭后期限表]] |
## 3. Opening Statement
#! 以争点为轴、以证据编号为锚；一条主线首尾重复；每节开头一句说明接下来讲什么；己方弱点主动交代并给解释框架，抢在对方之前；明确列出仲裁庭必须回答的问题；每个论点指向一份核心证据及编号但不逐条念证据。绝不引入新证据或新请求；承诺范围不超过证人实际能证的内容——开盘问后落空即变成反证；结尾回到请求主文。时间只承诺能兑现的量，留出比程序令规定更短的余量给仲裁庭提问。
### 3.1 Story Theme
Our case is one sentence: [[合同 → 违约 → 损害 的主线一句话，全篇首尾重复]]. When this hearing ends, the matter the Tribunal should carry away is [[__]].
### 3.2 Issues Map
The Tribunal has to decide [[__]] questions: first, [[争点一，含可受理性／管辖层次]]; second, [[争点二]]; third, [[争点三，含金额与可执行性]]. [[被申请人侧用数字框架收敛议题，每点先复述对方断言再指出与之矛盾的原始文件及其页码。]]
### 3.3 Evidence Roadmap
Each issue will be proved by [[证人姓名占位]] on [[事实范围]] and by [[Exh. C-__ / R-__]], and we will not ask the Tribunal to accept anything that is not in those documents. Our own weakness on [[己方弱点]] is acknowledged now, and the explanation is [[解释框架]].
### 3.4 Relief
We ask at the end for the relief already pleaded: [[请求主文，逐条与书状一致，含币种、起算点与期限]].
## 4. Cross-Examination Outline — one table per witness
#! 重复本表，一位证人一张。四列要求：待证事实一句话；先前陈述必须给证人本人陈述的段落号与所引文件附件号并逐页复核；提问序列封闭式、一事实一问、先给出处再发问，并列出可能被对方以"无基础"拦下的问题与替代措辞；陷阱项写明不得提问的内容（不得要求猜测、不得复合问题、不得超出陈述范围、不得请证人评价法律后果、不得引入己方未提交的文件）。同一事实若出现在多份陈述中，先自查日期口径统一。
| Fact to be established | Prior statement / record reference | Question sequence (closed, one fact per question) | Do not ask / trap | Our objection line if challenged |
|---|---|---|---|---|
| [[某一争点项下的一个待证事实，一句话]] | [[证人陈述 paragraph 号；Exh. 编号与页码；庭审记录 page 号]] | [[逐问填写：先给出处再发问，封闭式、一事实一问。示例句式：问日期与在场人 → 问该人是否写过所引文件 → 问该句是否为其原意；并另附可能被指"无基础"的问题的替代措辞]] | [[要求解释文件"含义"、请其猜测他人动机、复合问题、引用未入卷文件]] | [[超出陈述范围／无基础／与可信度无关／已回答；各配一句事实依据，不作论辩；被驳回立即继续]] |
## 5. Witness Examination Sequence
| Witness | Nomination | Date of appearance | Language of testimony | Direct | Cross | Re-direct | Tribunal | Total |
|---|---|---|---|---|---|---|---|---|
| [[证人姓名占位]] | [[Claimant / Respondent]] | [[date]] | [[语言；是否需传译]] | [[__]] h | [[__]] h | [[__]] h | reserved | [[__]] h |
## 6. Closing Submissions
#! 把证据回接到法律要件，形成"规则章 + 适用章"的可抄写链条；结构自我宣告，方便仲裁庭按你的顺序起草裁决。每个争点收尾给出证据指向（关键问答 + 庭审记录页码）；不利证据正面处理并说明其法律意义；备位论证（即使认定责任，金额亦应限于…并给出可采数字）；请求主文与开场陈述一致，不得在结案时新增；费用单列一节，依据写对方的程序行为而非仅结果。不允许口头结案时，按指定页数与日期交书面最终意见并逐条回应仲裁庭归纳的问题。准据法解释规则章与任何外国法结论转 11-governing-law，本包不作实体结论：[[法域依据须由 11-governing-law 出具并标置信度]]。
### 6.1 Elements Mapped to Evidence
| Issue | Legal element to be established | Evidence relied on, with record reference | Adverse evidence and its answer | Fallback position |
|---|---|---|---|---|
| [[__]] | [[要件一句话]] | [[证人陈述 paragraph __；Exh. C-__；庭审记录 page __ 的关键问答]] | [[对方最强论点与文件不符之处；不回避]] | [[即使认定责任，金额亦应限于 __，可采数字与计算路径见 __]] |
### 6.2 Matters the Other Side Has Not Proved
The [[对方书状名称]] asserts [[__]] but no witness addressed it, no document was produced for it, and no question was put to our witnesses on it; the items are [[逐条编号列举其举证缺口]].
### 6.3 Relief Sought
Our request remains as stated at the opening and in the pleadings: [[逐条主文，与开场一致]]. Costs are addressed separately and rest on the conduct of the proceedings, namely [[对方的程序行为与其时间／费用后果]].
## 7. Pre-reading Letter to the Tribunal
#! 一页以内，实用加礼节文件，不是第 N 次论辩；只推荐"读一次就够"的核心段落，给准确段落号与卷宗页码；注明哪些旧材料已被替代；中立描述不作评价；必须抄送对方——单方联系仲裁庭本身就是程序瑕疵指控的来源。交叉引用统一使用同一分页编号体系；时间线不超过约 [[__]] 行；双方联合提交并注明 jointly agreed 更佳。
~ To: [[主席与共同仲裁员]]; cc: [[对方代理人]]; [[机构秘书处]]
~ Re: [[案件全称与编号]] — [[程序阶段]] — pre-reading for the hearing of [[date]]
We refer to the hearing fixed for [[date]] and to the bundles delivered on [[date]]; a fresh pagination consistent with the bound bundles is enclosed. We suggest the following pre-reading, and confirm that [[已被替代或撤回的文件]] need not be read again.
| Order | Document | Paragraph / section | Bundle page | Why this passage |
|---|---|---|---|---|
| [[1]] | [[无争议事实与时间线／程序令一号]] | [[__]] | [[__]] | [[框架与期限]] |
| [[2]] | [[书状名称]] | [[paragraph __]] | [[__]] | [[争点一的主张]] |
| [[3]] | [[证人陈述]] | [[paragraph __]] | [[__]] | [[该证人将出庭说明的事实]] |
| [[4]] | [[专家报告与联合报告]] | [[section __]] | [[__]] | [[unagreed 事项]] |
A short chronology of key dates is attached: [[签约／交付／违约／索赔／仲裁开始／程序令／开庭]].
## 8. Hearing-Day Checklist
| Item | Checked by | Status | Note |
|---|---|---|---|
| [[核心卷宗与全套 bundle 版本号、分页编号与目录]] | [[__]] | [[☐]] | [[庭上出示只用已按程序令提前提交的版本，远程不豁免]] |
| [[演示材料提交截止与"不得借此引入新论据或新证据"]] | [[__]] | [[☐]] | [[以程序令官方文本核对截止时刻]] |
| [[笔录／录音方式、订正程序与副本费用归属]] | [[__]] | [[☐]] | [[更正期限与提出对象以适用规则版本/程序令官方文本核对]] |
| [[出席名单、代理人与当事人代表名单、证人在出庭前不得在场]] | [[__]] | [[☐]] | [[核对纪要中的名单]] |
| [[传译与文件翻译责任、语言与预留时间]] | [[__]] | [[☐]] | [[同语言证人集中作证以省传译]] |
| [[用时表与平等用时记录、被限制或被驳回的提问登记]] | [[__]] | [[☐]] | [[为后续正当程序主张留痕]] |
| [[不利记录登记（己方承认、承诺的时限、被排除的材料）]] | [[__]] | [[☐]] | [[评估对裁决与撤销程序的影响，修补在庭后简报按问题处理，不另函辩解]] |
| [[远程或混合开庭的连接方式、备用通道、证件核验、录音录像禁止、各时区截止时刻]] | [[__]] | [[☐]] | [[技术安排不改变出示规则]] |
~ Prepared by [[代理人姓名占位]] on [[date]]; reviewed with [[用户法务负责人占位]].
