---
title: Request for Arbitration
case: "[[case code]]"
workflow: 04-commencement
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
toc: false
---
#! ===== 使用说明：以下所有 #! 行只给起草人看，渲染时整行丢弃，绝不进入 Word =====
#! 归属 04-commencement；依 suite.yaml 原文登记材料并运行 route.py --gate 04-commencement --workdir <案件目录> --provided <案件目录>/case.json，本任务无 profile。缺项列补充清单，可按 pending/Q 机制出不可提交草案，未核关键依据不得进入提交态。
#! 先读当前案件档案/case-matrix.yaml；事实及实质论证段按 04 技能写 F/E/EV/R/A 的 #! 锚点：追溯行，仅列真实编号，不用 [[F]]。提交前留对抗审查，自审标 self_review；case 仅写稳定代号。
#! 先用 fetch_official.py 取文本再动笔：applicable --inst <机构> --commencement <拟提交日> 定适用规则版本；fetch <rules-source-id> --to-md；lookup <rules-source-id> --pattern "Request for Arbitration"（必载项、副本份数、答辩期、程序起算点）；lookup <rules-source-id> --pattern "advance on costs"（费用分档与费率）。机构立案页、费用表与 practice note 属另一来源，与规则本文分别标记并分别记取值日；未取得文本前不得落任何条号、份数、天数或费率（铁律 1、2），本文书此类位置一律写 [[Rule/期限/费用以适用规则版本官方文本核对]]，替换后逐处挂来源标记。
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --toc --strict --manifest <x.paras.json>；退出码 3＝仍有占位未填，本轮不交付，未经用户确认不得关闭 --strict；英文定稿必须同出《中文审阅说明》（铁律 5）。
#! 变体三选一，判据＝金额与复杂度／是否需要紧急措施／是否要以立案文书施加和解压力。简洁版＝本模板默认（金额中等、事实清楚、无紧迫行为）：事实与请求写全，实体论辩不展开，写太满会提前暴露策略并压缩己方修正空间。
#! 合并紧急救济版＝对方正在转移资产、兑付保函、销毁证据或抢占许可：在 VI. Language 之前插入一节，编号为新的 VI "Application for Urgent Interim Relief"（原 VI、VII 顺次后移为 VII、VIII），内部按 所请求措施原文（祈使句，对象＋行为＋期限＋违反后果，可直接执行）→表面成立的权利→紧迫性（为何不能等待组庭）→不可弥补损害（须论证金钱不足以弥补，不是"我方会受损"）→利益衡量→不预断实体→生效时点与径行送达双方 排布；独立成节控制在数页内，把紧迫性埋在事实长文里会被认定"可等待组庭"；只对被申请人设义务，不得请求仲裁庭命令第三人（银行、承运人、登记机关）；同时保留向法院申请保全的权利；主文分列 (a) 实体请求与 (b) 临时措施请求；该机构是否设紧急仲裁员机制及其适用条件（版本差异或约定排除）先现查。
#! 详尽版＝高金额、多合同、技术或事实争点复杂，或需以立案文书施压：front matter 改 toc: true 并加 --toc 渲染；在 I 之前插入一节 "Summary of the Dispute"（A. The Parties' Contract 逐条引述关键条款／B. The Dispute 时间线／C. Summary of Amounts Claimed 汇总表），并把 VII. Request for Relief 前置到摘要之后，让机构与仲裁庭先看到要什么再看为什么；实体深度止于"足以说明争议"而非"完成举证"，页数与机构立案惯例及程序令限制对齐；多合同须逐份指出条款并论证可一并处理，否则只就条款明确的合同请求。
#! 六项必载与缺项如何拖慢程序（逐项须能在文书中指出落位）：① 当事人识别与可用电话邮箱——机构通知送不出，起算日被推后，时效风险落我方；② 争议性质与发生情形——机构无法判定主管与程序类型，反复补正；③ 救济请求及可量化金额——费用按保守档核定，预缴通知来回调整；④ 仲裁协议文本逐字引述并指明合同与条款号——形式审查与表见管辖判断被卡；⑤ 组庭提名相关信息（人数、指定方式、候选人）——组庭延后，机构径行代指，提名机会丧失；⑥ 仲裁地、语言与准据法（未定项写 to be fixed 不留空）——程序令阶段重开争点，被动接受默认规则。
#! 通则：条款存在病理（机构表述冲突、前置协商条件、多合同不一致）时主动点出并给出我方论证，同时预判对方的另一种解读与仲裁庭关注点（铁律 7）；主体信息一律以用户材料为准，未确认即留占位，不得推测（铁律 3）；证人陈述与专家报告不进申请书，留到实体书状阶段，附件只放合同与附录、仲裁条款、催告与往来函件、账目与付款记录，按 C-1、C-2 连续编号并在正文逐段引用，避免"有证据无锚点"。
# Request for Arbitration
~ [[date of submission; format 31 January 2026 or ISO, one choice used consistently throughout]]; submitted pursuant to [[Rule/期限/费用以适用规则版本官方文本核对]] of the Rules, by and on behalf of the Claimant.
## THE PARTIES
#! 必载项①落位处。逐行 ~ 取消编号，四拍固定：法定全称→法律形式与注册地/主要营业地→送达地址与邮箱→代理人。全称、法律形式或注册地写错、关联公司混用，会在承认与执行阶段被指主体不适格；缺电话或邮箱＝程序起点被推后。被申请人地址取其合同通知条款指定或双方实际使用过的地址并附备选送达方式；多个被申请人时逐个重复下述四拍，并在管辖一节说明每个主体与条款的关系，漏列主体会使裁决对其无拘束力。
~ [[Claimant full statutory name]],
~ a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]] and its principal place of business at [[principal place of business]];
~ for all notices and communications in this arbitration: [[address for notices]], telephone [[number]], e-mail [[e-mail]], for the attention of [[name and title]];
~ represented by [[law firm name]], [[firm address]], telephone [[number]], e-mail [[e-mail]], for the attention of [[lead counsel name and title]].
~ Claimant,
~ versus
~ [[Respondent full statutory name]],
~ a company organized and existing under the laws of [[jurisdiction of incorporation]], having its registered office at [[registered office address]];
~ for all notices and communications in this arbitration: [[address from the notice clause of the Contract or from the Respondent's own prior correspondence]], telephone [[number]], e-mail [[e-mail]]; alternative means of service: [[courier address / local agent / last used e-mail]].
~ not at present represented by counsel in this matter, so far as the Claimant is aware [[state the Respondent's counsel if known]].
~ Respondent.
## PROCEDURAL PARTICULARS AT A GLANCE
#! 首页要素栏（必载项⑥落位处），非正文；未定项写 to be fixed 不留空。条款约定旧版本而启动日落在新版本时，两说都记下并先向用户确认，不得静默取其一。
~ The Claimant's particulars for the purpose of opening the file
| Particular | Position adopted in this Request |
|---|---|
| Rules and version claimed to apply | [[Rules name and version/year per the fetch_official applicable output]] |
| Place of arbitration | [[seat city and jurisdiction; or to be fixed]] |
| Language of the arbitration | [[language; or to be fixed]] |
| Nationality of the parties | Claimant [[nationality]]; Respondent [[nationality]] |
| Nationality of counsel | [[nationality; or to be advised]] |
| Law of the arbitration agreement | [[jurisdiction; 法域依据须由 11-governing-law 出具并标置信度]] |
| Law of the Contract | [[jurisdiction; 法域依据须由 11-governing-law 出具并标置信度]] |
| Subject matter of the dispute | [[one sentence on the transaction and the breach]] |
| Amount in dispute, quantified | [[currency]] [[amount]] plus interest on the basis stated below |
## I. STATEMENT OF FACTS
#! 必载项②落位处。合同—履行—违约—损害四拍，一段一事实，只写事实、不引法条不论辩；每个日期对得上附件号，金额一律"币种＋数字＋期间"。
### A. The Contract
The Claimant and the Respondent entered into [[contract name and number]], dated [[date]] (the "Contract"), under which the Claimant agreed to [[scope of performance]].
### B. Performance
The Claimant performed, in particular [[each delivery, milestone or payment as a separate fact, each anchored to an exhibit number in the list of exhibits]].
### C. Breach
On [[date]] the Respondent [[act or omission constituting the breach]], notwithstanding the Claimant's notice of [[date]] at C-[[n]] requiring cure within [[period fixed by the Contract]].
### D. Loss
By reason of the above the Claimant has suffered loss of [[currency]] [[amount]] for the period from [[date]] to [[date]], computed as stated in the section on relief and summarized at C-[[n]].
## II. APPLICABLE LAW
#! 合同准据法与仲裁协议准据法分两小节写，二者可以不同；条款未作选择时说明将依何种连接点主张，不留空。本套件不作境外法实体判断：涉境外法处保留占位并转 11-governing-law 分层给结论与置信度。
### A. Law Governing the Contract
The Contract is governed by [[law designated in the governing-law clause of the Contract]]. [[法域依据须由 11-governing-law 出具并标置信度]].
### B. Law Governing the Arbitration Agreement
The arbitration agreement is governed by [[law expressly designated or, absent designation, the law of the seat or such other jurisdiction as the Claimant will contend, with the connecting factor stated]]. [[法域依据须由 11-governing-law 出具并标置信度]].
## III. LEGAL BASIS FOR THE CLAIM
#! 必载项③落位处。按请求事项逐项列依据（合同条款号＋法律或原则依据），点到为止，本阶段不完成举证。
The claims rest on the following grounds, outlined without full argument at this stage: (a) [[breach of the Contract entitling the Claimant to payment of the price]]; (b) [[non-performance giving rise to damages]]; (c) [[entitlement to interest on the contractual or, failing agreement, the to-be-determined basis]].
#! 下面一句为必写句：漏写则后期扩大请求、追加证据容易被指为程序突袭。
The Claimant reserves the right to supplement, amplify or amend its claims, evidence and arguments.
## IV. JURISDICTION
#! 必载项④落位处。条款逐字引述（> 缩进段）并指明所在合同、条款号与签署日期；引述版本必须与实际签署合同一致（附旧模板条款是常见失分点）。机构管辖依据条号留占位，取到官方文本后替换并挂来源标记。请求的救济不得超出条款范围，也不得把只能由法院作出的措施请求命令第三人。
### A. The Arbitration Agreement
Article [[clause number]] of the Contract, executed on [[date]] and filed at C-[[n]], provides as follows:
> "[[verbatim text of the arbitration clause, transcribed exactly from the Contract as filed]]"
### B. Basis of Jurisdiction
The dispute falls within the scope of that arbitration agreement because [[scope argument tied to the exact words quoted above]], and the institution is competent to administer the arbitration under [[Rule/期限/费用以适用规则版本官方文本核对]].
### C. Points Capable of Contention
#! 主动点出条款病理（比被对方提出后再解释更有利），并同时写出对方的另一种解读与仲裁庭关注点。
The Claimant anticipates that the Respondent may contend that [[conflicting institutional reference]] or that [[the clause does not extend to this contract]] or that [[a condition precedent such as amicable consultation has not been satisfied]]. The Claimant's position is that [[the clause remains operative]] and that [[consultation was in fact attempted in the correspondence of a date to be cited at an exhibit to be numbered]].
## V. APPOINTMENT OF THE CLAIMANT'S ARBITRATOR
#! 必载项⑤落位处。先取得被提名人本人书面同意并索取简历与联系方式，才把姓名写进文书；未经同意即提名，事后撤回会推翻整个组庭。部分机构要求提名时一并提交简历与同意，条号现查。三人庭须写清主席产生机制；就首席只提客观标准（语言、行业、法域经验、可用性），不得有倾向性表述。
### A. Number of Arbitrators
The Contract provides for [[number]] arbitrator(s) [[or, the Contract being silent, the Claimant proposes a number supported by the amount in dispute and the complexity of the case]]. Failing agreement, the number falls to be fixed under [[Rule/期限/费用以适用规则版本官方文本核对]].
### B. Nomination
The Claimant nominates as arbitrator [[full name]], [[nationality]], resident of [[place]], telephone [[number]], e-mail [[e-mail]], whose curriculum vitae is filed at C-[[n]]. The nominee has confirmed in writing his or her willingness to serve and will furnish the statement of independence and disclosure required under [[Rule/期限/费用以适用规则版本官方文本核对]].
### C. Presiding Arbitrator
Where a tribunal of [[number]] is constituted, the presiding arbitrator shall be appointed in the manner provided by [[clause number or Rule/期限/费用以适用规则版本官方文本核对]]. The Claimant suggests the following objective criteria: [[proficiency in the language of the arbitration; experience of the relevant industry; experience of the governing law; availability]].
## VI. LANGUAGE OF THE PROCEEDINGS
#! 必载项⑥落位处。条款有约定即引约定条文；无约定时给可操作理由（合同与履行文件语言、证人语言、仲裁地惯例），情绪化偏好无效。
The arbitration shall be conducted in [[language]], being the language stipulated in the Contract and the language in which the Contract and the whole transactional record are expressed and in which the witnesses will give evidence.
## VII. REQUEST FOR RELIEF
#! 主文逐项与矩阵 R 及请求台账一致；仅保留本案实际请求。金钱项核金额、币种及实际主张的利息依据，非金钱项仅写对象、行为、范围、期限，不强加币种或利息；删除不适用的金钱/利息段并同步首页要素栏。
#! 金额量化决定费用档级：多数机构的行政管理费与仲裁员报酬按争议金额分档（分档与费率条号现查，费用表取值日须记录），未量化即按保守档核定，事后调整既误时又影响策略；口径上注意反请求与抵销是否并入计算、选择性请求按主请求计、汇率取值日、连带责任不重复计，均按适用规则现查，并预判对方若提出反请求会把案件推入哪一档、是否触发或脱离简易程序。利息写满四要素：基数、利率或口径、起算日、单利或复利直至实际支付日。
The Claimant respectfully requests that the arbitral tribunal:

(a) order the Respondent to pay [[currency]] [[principal amount]], with interest at [[rate or basis]] from [[date]] to the date of actual payment, on a [[simple / compound]] basis;

(b) order the Respondent to pay damages of [[currency]] [[amount]] for the period from [[date]] to [[date]], with interest at [[rate or basis]] from [[date]] to the date of actual payment;

(c) grant the non-monetary relief sought, namely [[specific performance / delivery / release of security / declaration]], within [[period]];

(d) direct that the Respondent bear the costs of this arbitration in full, being the institution's administrative charges, the arbitrators' fees and expenses and the Claimant's legal and other costs, with interest at [[rate or basis]] from [[date]] to actual payment; and

(e) grant any other or further relief to which the Claimant may show itself entitled, the Claimant expressly reserving its rights under the preceding paragraphs.
## RESERVATIONS, SERVICE AND SIGNATURE
#! 送达与份数：依适用规则判定由机构转送还是申请人自行向被申请人送达并向机构交副本；自行送达必须留送达凭证，因为部分规则把起算点放在对方收到日而非发出日。核对副本份数（按当事人、仲裁员、机构各份）、提交渠道（线上立案系统/邮件/纸质）与格式要求（可检索 PDF、单一文件、命名规则、附件合订），逐条落到 04-立案材料包.md 的核对表。
The Claimant files this Request by [[filing channel and format required under Rule/期限/费用以适用规则版本官方文本核对]] in [[number of copies to be confirmed against the applicable version]], and serves a copy on the Respondent at the address stated above, retaining proof of despatch because [[the applicable rules may fix the commencement of the proceedings on receipt rather than on despatch]].
#! 下面一句为保留权利必写句。
The Claimant reserves all of its rights and claims, including the right to add to, particularize, amend or increase the facts, the evidence, the amounts claimed and the relief requested.
#! 签名块四项齐备：授权签字人姓名、职务、签署地、签署日期。PoA 须覆盖提名仲裁员、签署文书、提出与回应请求、和解、收款、指定证人与专家、申请临时措施等权能，有效期覆盖至程序（含执行）终结；公证、认证与译本等形式要求属当地法判断，转 11-governing-law 出结论。
~ Dated: [[date]]
~ Place of signature: [[city, jurisdiction]]
~ For and on behalf of [[Claimant full statutory name]]
~ [[signature]]
~ [[name and title of the authorized signatory]], duly authorized
<pagebreak>
## LIST OF EXHIBITS
#! 附件编号与正文逐段引用一一对照；本阶段不放证人陈述与专家报告。
| Exhibit | Document | Date | Referred to at |
|---|---|---|---|
| C-1 | [[Contract with all annexes and schedules]] | [[date]] | paragraph [[n]] |
| C-2 | [[Extract of the Contract bearing the arbitration clause]] | [[date]] | paragraph [[n]] |
| C-3 | [[Demand or cure notice and proof of despatch]] | [[date]] | paragraph [[n]] |
| C-4 | [[Correspondence establishing the course of performance]] | [[date]] | paragraph [[n]] |
| C-5 | [[Invoices, accounts and payment records supporting the amounts]] | [[date]] | paragraph [[n]] |
| C-6 | [[Curriculum vitae and written consent of the nominee]] | [[date]] | paragraph [[n]] |
| C-7 | [[Power of attorney evidencing the signatory's authority]] | [[date]] | paragraph [[n]] |
| C-8 | [[Payment slip for the advance on costs, with amount and account reference]] | [[date]] | paragraph [[n]] |

#! 标题和结构按机构适用版本的官方文本选取，启动文书名称与必备附件先核验；不要机械保留通用 Request 标题。先核程序轨道再写任命方案。每次交付同时使用 04-立案申请指引.md。
