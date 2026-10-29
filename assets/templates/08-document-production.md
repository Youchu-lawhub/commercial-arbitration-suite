---
title: Document Production Pack — Proposed Procedural Order, Request, Redfern Schedule, Privilege Log and Confidentiality Proposal
case: "[[案件代号]]"
workflow: 08-evidence
profile: production
matrix: case
mode: legal
footer_left: Draft [[v1]] — [[date]]
keep_sources: false
---

# Document Production Pack

#! 适用 08-evidence / production；只按 suite.yaml 本 profile 核材料，运行 route.py --gate 08-evidence --profile production --workdir <案件目录> --provided <案件目录>/case.json。缺项登记 pending/Q，不合并证人或专家的材料闸门。
#! 先读 case-matrix.yaml；事实、要件、证据和权威用 F/E/EV/R/A 的 #! 锚点追溯，表格在底稿逐项映射，程序证据不强造实体要件。对抗审查须记录，单人自审标 self_review。
#! A/B/C/D/E 按本轮需要拆件，不默认生成五份；保留 workflow/profile/matrix，每份配套中文审阅说明。
#! A、E 是供当事人提出的拟议文本，不是仲裁庭已签发文件；正文保留 PROPOSED，未确认的会议、合意、决定及签名不得写成既成事实。真正签发的程序令由有权主体制作。
#! 程序依据先依本案规则版本和程序令核验；软法须确认是否及以何种方式被采用，不能把拟议条款声称为某软法原文。内部来源标记按主入口铁律2记录。
#! 每项取证连接任一方的争点、待证事实与证明目的；允许可识别的特定文件或狭窄类别。窗口、列数、日志及制裁依本案框架确定，不把模板建议变成法定门槛。
#! 渲染：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json>；提交前按12复核。

## PART A — PROPOSED PROCEDURAL ORDER NO. [[__]]
~ [[机构全称]] — Arbitration under [[本案适用规则名称及版本]]
~ Case No. [[案号]]
~ [[申请人]] / [[被申请人]]
~ Proposed by [[提出方或双方]] on [[date]] — subject to the Tribunal's determination

### A.1 Procedural Background

[[逐项写明已发生的立案、答辩、组庭和程序会议事实及记录依据；未发生者不填入历史。列出已同意安排、未决争议及提出方的立场，不把沉默视为同意。]]

### A.2 Applicable Framework

The proposing party requests the arrangements below under [[已核本案适用规则、仲裁地法及程序令依据]]. Any use of [[软法名称及版本，未使用则删除]] is proposed on the following basis: [[已约定适用／已由庭采用／仅拟作为参考及其范围]]. These proposals do not amend an existing direction unless the Tribunal so decides.

### A.3 Submissions and Exhibits
- Written submissions: [[提交方、书状、日期、截止时刻、时区、收件人及送达要求]].
- Length and format: [[已定要求或有理由的拟议限制，区分两者]].
- Extensions: [[申请方式、适用条件及对其他期限的影响]].
- Exhibits and authorities: [[双方编号、连续编号方式和精确引注要求]].

### A.4 Document Production

Production is proposed at [[本轮阶段及理由]], using [[已定或拟议表格格式]]. A request may identify a particular document or a narrowly described category. Each request shall explain its relevance to an issue, its materiality to the outcome, and the basis for believing that the requested party has possession, custody or control.

- Search scope and burden: [[检索范围、合理检索要求、比例及替代方案]].
- Objections: [[异议类型、提出期限及需说明的理由]]; privilege shall be assessed under [[已核适用标准与处理程序]], without requiring disclosure of the protected substance merely to assert the claim.
- Non-compliance: [[有权决定的后果、适用条件和陈述机会]]. An adverse inference is requested only where its legal and factual conditions are established; non-production is not automatically proof of the underlying claim.
- Further requests remain subject to the applicable timetable, governing framework and any permission required.

### A.5 Fact Witnesses
- Statements: [[身份关系、信息来源、文件引用、声明及签署要求]].
- Attendance and examination: [[出庭安排及不能出庭的处理，按适用依据填写]].
- Preparation and contact: [[适用伦理规范、法律及程序令允许的范围与限制]].
- Corrections or supplements: [[申请及版本留痕方式，不改写已签署版本]].

### A.6 Experts

Expert evidence is proposed on [[本案所需专门领域]], under [[指定方式、资格和独立性要求、适用职责及职权范围]]. The timetable for reports, any expert meeting and a record of agreed and disputed points is [[已定安排或拟议安排]]. Experts remain responsible for their own opinions and the assumptions supporting them.

### A.7 Measures and Costs

Pending applications and any proposed timetable for interim measures or security for costs are [[申请、状态、权限与日程]]. The proposing party requests no change to an existing order except [[具体拟议修改及依据；无则写明]].

### A.8 Hearing

The proposed hearing arrangements are [[日期、地点或远程形式、时区、预计时长、证人和专家顺序、口译、记录及访问安排]]. Any allocation of time is subject to the Tribunal's directions and a fair opportunity for each party to present its case.

### A.9 Post-Hearing Steps

[[是否允许庭后简报、问题范围、日期及费用陈述安排；既有指示与本方建议分别表述。]]

### A.10 Advances, Fees and Taxes

[[仅记录有凭据的通知、付款、余额、收款主体及期限；具体税费与各方负担依已核规则、通知和适用法填写，不代机构或仲裁庭作征收决定。]]

### A.11 Confidentiality and Further Directions

Confidentiality arrangements are addressed in [[既有程序令或本包PART E建议]]. Other unresolved procedural questions are [[问题及拟议处理方式]]. Any further direction is for the Tribunal to determine within its authority.

### A.12 Submission of Proposal
~ Submitted by [[提出方代理人]] on [[date]].
~ This proposal is not an issued order and carries no signature on behalf of the Tribunal.

### A.13 Annex — Timetable
| Stage | Responsible party | Deadline and time zone | Basis and status |
|---|---|---|---|
| [[程序事项]] | [[责任方]] | [[日期、时刻、时区]] | [[来源与已定／拟议状态；内部截稿另列]] |

## PART B — REQUEST FOR DOCUMENT PRODUCTION

### B.1 Issues and Requested Documents

[[请求方]] requests production of the documents identified in PART C under [[已核程序依据]]. Request No. [[编号]] concerns [[任一方争点或要件]], located at [[书状段落／矩阵事实及程序用途]]. The requested material would help establish or test [[待证事实]]. Its potential effect on the determination is [[重要性理由]].

### B.2 Possession, Control and Proportionality

The basis for believing that the requested party holds or controls the material is [[具体事实；不以集团关系替代控制证明]]. The requesting party's own access to the material is [[真实持有、可获取情况及仍需请求的理由]]. The proposed scope and any less burdensome alternative are [[限定、抽样或分阶段方案]].

### B.3 Prior Steps and Requested Direction

[[如有协商，写真实日期、请求、答复和记录；没有协商则说明本案是否要求及为何可直接申请，不编造被拒经过。]] The requesting party asks for [[具体制作／检索／说明命令及拟议期限]].

### B.4 Protection of Information

[[提出与敏感程度相适应的遮蔽、访问及用途方案；不得未经用户确认承诺放弃特权、扩大披露或对等提供文件。]]

### B.5 Relief Sought

The requesting party asks the Tribunal to determine Requests Nos. [[编号]] and the proposed safeguards in PART C. Any request for consequences of non-compliance shall identify the applicable authority, the facts relied on and the specific inference or measure sought, with an opportunity for the other party to respond.

## PART C — REDFERN SCHEDULE
#! 优先使用本案规定的列数；未规定时可提出以下五列。每项理由应足以审查，准确交叉引用可以辅助但不能代替必要说明。决定栏不由申请方预填。
| Request | Relevance and materiality; possession, custody or control | Objection | Reply or narrowed request | Tribunal's decision |
|---|---|---|---|---|
| [[编号、特定文件识别信息或狭窄类别、主体与时段]] | [[任一方争点与定位；相关性；对结论的重要性；持有或控制依据及己方获取情况]] | [[异议及事实和规范依据]] | [[逐项回应；必要且获授权的缩窄或保护措施]] | [[留给仲裁庭]] |

## PART D — PRIVILEGE LOG
#! 逐件或按类的要求先核本案框架；日志要说明特权依据但不泄露所保护的实质内容。日志不足时提出补充或审查措施，不直接宣告特权丧失。
| Request No. | Non-privileged description | Privilege claimed | Applicable basis and supporting facts | Redaction or review proposal |
|---|---|---|---|---|
| [[编号]] | [[日期、作者收件人、类型等可披露信息]] | [[具体类型]] | [[适用法／程序依据及满足条件的事实]] | [[可分割性、遮蔽范围或保密审查办法]] |

## PART E — PROPOSED CONFIDENTIALITY ARRANGEMENTS
#! 以下为按案拟定的条款建议，不是机构规则或软法原文。先核有无现存保密协议、规则义务和程序令；当事人协议不当然约束机构、仲裁庭或第三人。

### E.1 Status and Scope

[[提出方]] proposes protection for [[材料范围、保密理由及排除事项]]. The status of agreement is [[已同意的具体条款与证据／仍有分歧的条款]]. No agreement or prior direction is asserted beyond the record identified here.

### E.2 Proposed Undertakings

The parties propose that access to the identified material be limited to [[授权接收人及用途]]. A recipient may disclose it only within that agreed scope or where disclosure is required by law or necessary for [[经核验并同意的权利维护、监管、裁决救济和执行等用途]]. Where legally permitted and practicable, the disclosing party shall notify [[对象]] by [[合理方式及期限]] and limit disclosure to what is necessary. Nothing in this proposal requires notice prohibited by law or prevents compliance with a mandatory obligation. Duties of the Tribunal, institution and other persons must rest on their own applicable obligations or valid undertakings.

### E.3 Handling Arrangements
- Identification: [[标记及争议解决方法，误漏标记的后果另核]].
- Access and copying: [[人员、地点、复制权限、专家与证人所需访问，兼顾当事人陈述机会]].
- Hearing and record: [[闭门范围、引述方式、遮蔽及非保密版本]].
- Retention: [[返还、销毁、依法留存及救济执行所需保留，明确条件和期限]].

### E.4 Authority and Requested Action

The proposing party asks the Tribunal to [[在权限内确认安排或作出具体命令]], on the basis of [[已核权力依据]]. The legal consequences of any breach depend on the relevant obligation and available remedy; no automatic adverse inference, waiver or separate-proceedings requirement is assumed.

### E.5 Submission
~ Submitted by [[提出方代理人]] on [[date]] — PROPOSED, subject to determination.
