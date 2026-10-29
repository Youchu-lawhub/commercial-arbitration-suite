---
title: Application to Challenge an Arbitrator
case: [[案件代号]] | [[机构名]] Case No. [[案号]]
workflow: 06-tribunal
profile: challenge
mode: legal
footer_left: [[Draft v1]] — [[日期]]
keep_sources: false
toc: true
---

# APPLICATION TO CHALLENGE AN ARBITRATOR

#! 本文件是骨架模板，复制到案件目录 deliverables/ 后逐段填写；所有 #! 行渲染时整行丢弃，永不进入 Word。
#! 适用子技能：06-tribunal 第 6 项动作（拟写挑战申请）与第 7 项（评估决定与救济空间）。产出名对应 06 的 outputs 之"挑战申请（含标准与举证）"。
#! 闸门未过不得使用：python3 <suite>/scripts/route.py --gate 06-tribunal --profile challenge --workdir <案件目录> --provided <案件目录>/case.json。缺"双方已提名或已指定人选与日期"或"候选人背景与潜在利益冲突线索"时，本轮只出《补充材料与信息确认清单》视图，不发本申请。
#! 先取官方文本（顺序执行）：python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <仲裁启动日> ；python3 <suite>/scripts/fetch_official.py check --inst <机构id> ；python3 <suite>/scripts/fetch_official.py fetch <规则版source_id> --to-md ；python3 <suite>/scripts/fetch_official.py lookup <规则版source_id> --pattern "challenge|objection|disclosure|justifiable doubts|time limit|decision" --max 12 。软法分类另跑：python3 <suite>/scripts/fetch_official.py lookup iba-conflicts-2024 --pattern "List|waivable|non-exploitable|disclosure" --max 12 。
#! 渲染与核验：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json> ；再跑 python3 <suite>/scripts/verify_suite.py --workdir <交付目录> --mode submission，并配一份同目录中文审阅说明。
#! 现实预期：挑战成功率低、代价高。败诉后的信用成本是真实的——仲裁庭对反复或包装过的异议会记入程序裁量与费用考量，己方后续每一项程序请求的说服力都会下降。因此本申请只在可证事实直接落到规则标准时使用，不做"商业不便"包装。
#! 顺序价值：先要求补充信息，再决定是否挑战。问询函把事实基础固定下来、把期限起算与不计入异议期的请求写清，并让对方无法以"你方早知道"抗辩；跳过这一步直接挑战，常因事实不足被驳，且失去一次书面固定事实的机会。
#! 不得混入的无效事由：仲裁员专业背景不利、法律观点不合我方预期、由对方提名、其国籍——这些都不构成独立性事由，混入会被驳回并削弱己方整体可信度。

## I. Case Block

~ To: [[机构名]] Arbitration Secretariat — attention [[部门或收件人]]（如决定机关为仲裁庭，则按 [[Rule/决定机关条号以适用规则版本官方文本核对]] 改投）
~ Copy to: [[对方代理人全称]]，[[邮箱]]
~ Claimant: [[申请人全称，取自用户材料]]
~ Respondent: [[被申请人全称，取自用户材料]]
~ Arbitration: [[案件代号]] / Case No. [[案号]]，[[适用规则版本]]
~ Seat: [[仲裁地]] | Language: [[程序语言]]
~ [[日期]]
~ **Application to challenge arbitrator [[仲裁员全名]] pursuant to [[Rule/挑战程序条号以适用规则版本官方文本核对]]**

## II. The Challenged Arbitrator and the Nominating Party

The challenged arbitrator is [[仲裁员全名]]，[[国籍]]，appointed in [[角色：首席或共同仲裁员]] by [[指定方：己方或对方或机构]] on [[指定或确认日期]]。

The challenge is directed at the arbitrator personally and not at the appointing party, and it does not import any submission that the nomination itself was irregular.

#! 本段只写身份与指定链条，不写评价性形容词；对方提名这一事实本身不作为异议理由，写明即可。

## III. Timeliness: Self-Proving the Time Limit

Our client received the disclosure statement dated [[披露函日期]] on [[收到日期与时刻]]，as evidenced by [[送达凭证：邮件时间戳或收件确认，附件号]]。

This application is submitted on [[提出日期]]，within [[期限以适用规则条号官方文本核对]] running from receipt, and, where the period was interrupted or extended, by reference to [[补充信息请求函日期]] and [[Rule/期限起算与中断条号以适用规则版本官方文本核对]]。

Any objection not raised in this application is reserved, and our client states expressly that it does not waive any right under [[Rule/放弃异议条款条号以适用规则版本官方文本核对]]。

#! 期限段是本申请的准入门槛：把"收到日"与"提出日"两段事实与凭证逐条对上，并单列补充信息请求的日期与期间不计入的主张。期限条文号未取得官方文本前保持占位，不得凭记忆写天数。

## IV. Statement of Facts

Each fact below is confined to what is verifiable and is followed by its evidential anchor; abstract assertions of incompatibility are not pleaded.

| 序号 | 事实：关系性质 | 存续期间 | 业务领域与标的关联 | 经济利益与关联方 | 信息隔离 | 证据锚点 |
|---|---|---|---|---|---|---|
| F1 | [[与一方或代理人的关系性质]] | [[起始日至终止日，是否仍存续]] | [[是否同一业务领域]] | [[持股、收费或分成安排]] | [[办公室层面隔离措施]] | [[附件号]] |
| F2 | [[与另一方或代理人的关系性质]] | [[时间段]] | [[是否与本案标的相连]] | [[关联方与实体全称]] | [[隔离或未隔离的证据]] | [[附件号]] |
| F3 | [[既有仲裁 involvement：案号、年份、角色、方别]] | [[时间段]] | [[与本案争点的重合度]] | [[费用安排]] | [[本人是否参与该业务]] | [[附件号]] |

Further facts established by the request for supplementary information: [[答复要点与日期]]。Facts which remain unexplained after the request are identified as [[待澄清事项]] and are relied on only as matters within the arbitrator's own knowledge.

#! 逐条切割对方将提出的减损事实：本人未参与该业务、无经济利益、与本案标的不相关、已采取隔离措施。每一条要么有附件支撑，要么明确标注为未获答复，不要写成推测。

## V. The Applicable Standard

The standard is [[Rule/独立公正义务与异议标准条号以适用规则版本官方文本核对]]，namely whether the disclosed circumstances give rise to justifiable doubts as to the arbitrator's impartiality or independence, assessed objectively.

The assessment is made from the standpoint of a reasonable third observer who knows the facts, not from the arbitrator's own subjective belief and not from the perspective of the challenging party. Abstract assurances of impartiality carry little weight against specific facts.

Where soft-law situation lists are cited, they are cited only as classification language for the type of circumstance; the conclusion rests on the rules applicable to this case, quoted from the official text fetched above.

#! 软法不具拘束力，不得替代规则作为准许或驳回的依据；结论必须落回规则标准并带来源标记。

## VI. Anticipated Objections and Our Replies

| 对方最可能的反驳 | 我方回应 | 支撑证据 |
|---|---|---|
| 本人未实际参与相关业务 | [[切割该主张的具体事实]] | [[附件号]] |
| 不存在经济利益或持股 | [[收费安排与结算主体]] | [[附件号]] |
| 关系与本案标的无关 | [[同一业务领域或同一事项的证明材料]] | [[附件号]] |
| 已采取内部隔离与信息屏障 | [[隔离措施的实际覆盖范围与验证方式]] | [[附件号]] |
| 异议迟延，应由我方承担后果 | [[收到日、问询日与答复日的期间计算]] | [[附件号]] |

#! 仲裁庭关注点写在中文审阅说明里：挑战成功后的替代指定权归属、程序迟延的费用后果、我方过度挑战对后续程序裁量的影响。

## VII. Relief Requested

Our client respectfully requests that the deciding authority, being [[决定机关，Rule/条号以适用规则版本官方文本核对]]：

1. Uphold this challenge and find that the disclosed circumstances give rise to justifiable doubts as to the impartiality or independence of [[仲裁员全名]]。
2. Terminate the appointment of [[仲裁员全名]] with effect from the date of the decision.
3. Direct that the replacement arbitrator be appointed by [[补指定机制与主体，Rule/条号以适用规则版本官方文本核对]]。
4. Order that no further substantive step be taken pending the decision, to the extent permitted by [[Rule/条号以适用规则版本官方文本核对]]。
5. Direct the arbitrator or the nominating party to provide the outstanding information listed in section IV within [[期限以适用规则条号官方文本核对]]。

## VIII. Costs and Reservation of Rights

The costs of this application are reserved to be dealt with in the final award on costs, and our client does not seek an immediate costs order.

Our client reserves the right to raise any further circumstance arising after the date of this application, including continuing disclosure obligations, and to rely on this application in any subsequent setting-aside or non-enforcement stage.

#! 决定机关与其终局性必须先现查再写：机构作出的决定在多数规则下不可再诉，此时剩余空间通常在裁决撤销或不予执行阶段的正当程序抗辩（转 10-award-post）。是否同时向仲裁地法院申请指定或回避，须由 11-governing-law 出具该法域口径并标置信度后再落笔；[[法域依据须由 11-governing-law 出具并标置信度]]。

~ [[己方代理律所全称]] — [[签署人姓名与职务]]
~ Enclosures: [[附件清单]]
