---
title: Application for Security for Costs and Objections Thereto
case: [[案件代号]] | [[机构名]] Case No. [[案号]]
workflow: 07-measures-costs
profile: security
mode: legal
footer_left: [[Draft v1]] — [[日期]]
keep_sources: false
toc: true
---

# SECURITY FOR COSTS

#! 本文件是骨架模板，复制到案件目录 deliverables/ 后逐段填写；所有 #! 行渲染时整行丢弃，永不进入 Word。Part I 为申请方骨架（被申请人就其费用担保），Part II 为异议方骨架（申请人反驳），交付时按立场保留其一或两版并行留档。
#! 适用子技能：07-measures-costs 第 7 项（担保费用申请侧）与第 8 项（抗辩侧）。产出名对应 07 的 outputs 之"担保费用申请或抗辩"。
#! 闸门未过不得使用：python3 <suite>/scripts/route.py --gate 07-measures-costs --profile security --workdir <案件目录> --provided <案件目录>/case.json。四项 gate 中"对方资产与履约能力线索"与"已发生与预计费用明细"缺任一项即不得起草本申请，改出《补充材料与信息确认清单》视图。
#! 先取官方文本（顺序执行）：python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <仲裁启动日> ；python3 <suite>/scripts/fetch_official.py check --inst <机构id> ；python3 <suite>/scripts/fetch_official.py fetch <规则版source_id> --to-md ；python3 <suite>/scripts/fetch_official.py lookup <规则版source_id> --pattern "security for costs|costs of the arbitration|discretion|advance" --max 12 。
#! 渲染与核验：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json> ；再跑 python3 <suite>/scripts/verify_suite.py --workdir <交付目录> --mode submission；非中文文书另配中文审阅说明（本身用中文提交的文书不配）。
#! 不得使用的理由：对方是外国公司、外资背景、规模小、是子公司或 SPV 本身，均不构成命令担保的依据；现代实践已摒弃纯国籍标准。以此类理由提出，会被驳回并削弱己方后续所有请求的可信度。
#! 主体与财务信息：全部以用户提供的材料为准，本套件不代为认定主体身份、股权结构或偿付能力；凡未从材料取得的数值与事实，一律保持 [[占位]] 并登记到 case.json 后刷新《补充材料与信息确认清单》视图。
#! 与临时措施申请的区分：本文件只覆盖费用担保，不覆盖争议标的的保全。混用会被要求拆分，并可能因要件错位同时损害两份申请。标的保全请用 assets/templates/07-interim-measures.md。

## Part I — Application by the Respondent

### A. Introduction

This application is submitted pursuant to [[Rule/仲裁庭就费用担保或程序措施的权力条号以适用规则版本官方文本核对]]。The Respondent requests that the Claimant provide security for the Respondent's costs of the arbitration in the amount and form set out in section G, and seeks no determination of the merits.

### B. Jurisdiction

1. The Tribunal's power to order security is founded on [[Rule/条号以适用规则版本官方文本核对]]，read with the law of the seat, whose express or interpreted basis is [[法域依据须由 11-governing-law 出具并标置信度]]。
1. The parties, by agreeing to arbitration under the applicable rules, accepted the procedural framework in which such an order may be made; the arbitration agreement remains in force and covers this application.
1. This application concerns procedure and costs only, and does not pre-empt any jurisdictional objection either party may raise.

### C. The Applicable Standard

The Tribunal has a wide discretion and orders security only with caution. The Respondent addresses each element directly rather than invoking any single factor.

1. Likely success on the merits: [[己方对实体请求的初步评估要点与证据附件号]]，supported by [[附件号]]。
1. Real risk of inability to pay a final costs award: established in section D.
1. Causation and timing of the financial deterioration: [[恶化发生于仲裁协议签订之后，或可归因于申请人所指责的行为，附时间轴与证据]].
1. Proportionality and effect on the substantive right: the security sought is [[比例说明]] and leaves the Claimant able to pursue its claims.

### D. Facts Establishing Impecuniosity or Risk

| 证据类别 | 本案具体事实与期间 | 来源与附件号 | 证明什么 |
|---|---|---|---|
| Financial statements | [[资不抵债、持续亏损、大额逾期应付款，取用户材料]] | [[附件号]] | [[偿付能力现状]] |
| Audit qualification | [[审计保留意见或无法表示意见的原文要点]] | [[附件号]] | [[持续经营疑虑]] |
| Striking-off, liquidation or restructuring | [[登记注销、清算或重整程序的主体与日期]] | [[附件号]] | [[程序性风险]] |
| Ratings and default records | [[评级下调、违约或展期记录]] | [[附件号]] | [[外部信用评价]] |
| Asset transfers and encumbrances | [[已完成的转让、质押或担保设定]] | [[附件号]] | [[责任财产减少]] |
| Prior non-enforcement of awards or judgments | [[可核查的未履行记录与执行地]] | [[附件号]] | [[裁决执行风险]] |
| Group structure | [[壳公司或无资产 SPV 架构，取用户材料]] | [[附件号]] | [[追索对象缺失]] |

### E. Estimate of the Respondent's Costs

| 费用分项 | 估算区间与币种 | 依据与方法 | 阶段假设 |
|---|---|---|---|
| Legal counsel fees | [[区间]] | [[费率协议与计费口径，附件号]] | [[预计程序阶段]] |
| Expert fees | [[区间]] | [[专家委托范围与市场费率依据]] | [[专家人数与报告轮次]] |
| Hearing and transcript costs | [[区间]] | [[机构费用表与庭审安排]] | [[庭审天数]] |
| Institutional fees and arbitrators' remuneration | [[区间]] | [[机构费用表，Rule/费用表以适用规则版本官方文本核对]] | [[争议金额对应的计算口径]] |

The estimate is given as a range with its method and stage assumptions so that it can be verified, and the Respondent will update it as the timetable develops.

#! 任意大数会被以不成比例驳回，并被对方在最终费用抗辩中反向使用；估算必须给区间、方法、阶段清单与费率依据，并同步附上己方预算与费率证明。

### F. Proportionality and Absence of Prejudice

1. The amount sought represents [[占争议金额与请求金额的比例说明]] and is not capable of extinguishing the Claimant's access to the Tribunal.
1. Security in the form of a bank guarantee or instalments preserves the Claimant's liquidity, as set out in section G.
1. The Respondent's costs would otherwise be met from its own resources while a costs award in its favour could not be satisfied against [[执行对象与资产地线索，取用户材料]]。

### G. Form, Timetable and Consequences

The Respondent requests security in the following form, which is achievable and verifiable: [[银行保函或保险或分期缴存，写明开立行、受益人、金额、币种、有效期与续期机制]] within [[期限以适用规则条号官方文本核对]] of the order.

#! "不提供即驳回请求"这类终局性后果仲裁庭通常不愿在实体前作出，慎用；优先请求中止相关请求或保留进一步程序指示的空间，并给出可达成期限。

### H. Relief Sought

1. An order that the Claimant provide security for the Respondent's costs in the amount of [[币种与金额或区间]] in the form described in section G, within [[期限以适用规则条号官方文本核对]]。
1. An order that, failing provision, the Tribunal consider [[后果：中止相关请求或程序指示，条号以适用规则版本官方文本核对]]。
1. Directions that the Claimant disclose [[与偿付能力有关的进一步信息类别]] and whether any third-party funding arrangement exists.
1. Costs of this application reserved to the final award on costs.

~ [[己方代理律所全称]] — [[签署人姓名与职务]]
~ List of Exhibits: [[附件清单]]

<pagebreak>

## Part II — Objections by the Claimant

### A. The Test Restated

The Claimant requests that the application be dismissed in full. Security is exceptional, the threshold is cumulative, and an order must not operate as a bar to the determination of the claims. The elements remain [[Rule/门槛条号以适用规则版本官方文本核对]]：likely success of the applicant, real impecuniosity, causation and timing, and proportionality.

#! 攻要件而不是重复"不应当"；只攻击估算金额而不攻击法律要件，命令仍会被作出，只是金额变小。完全拒绝披露任何财务信息，仲裁庭就只能依对方材料判断。

### B. Grounds of Objection and the Evidence Each Requires

| 抗辩路径 | 要证明什么 | 需要的证据与来源 |
|---|---|---|
| Hardness caused by the applicant's own conduct | [[停付、拒收、单方解约切断现金流的因果链]] | [[对方停付与解约函件、银行流水、订单取消记录，附件号]] |
| Known and accepted at the time of contracting | [[缔约时对方已知或已接受己方资信]] | [[尽调报告、往来邮件、既有交易与担保安排，附件号]] |
| Strong claim on the merits | [[削弱"很可能胜诉"要件的实体强度]] | [[合同条款、履行记录、验收与付款凭证，附件号]] |
| Respondent itself is solvent and recoverable | [[己方费用本可获得清偿]] | [[审计报告、银行资信、母公司支持函，附件号]] |
| Security approaching a denial of justice | [[命令将使请求落空，比例原则]] | [[金额与现金流测算、融资不可得证据，附件号]] |
| Estimate inflated and unsupported | [[估算虚高、方法与阶段假设缺失]] | [[己方对程序阶段的对照测算与费率比较，附件号]] |

1. Third-party funding: [[资助的存在、性质与是否对裁决结果有经济利益，遮蔽版附件号]]，which bears on the impecuniosity element and on the necessity of security; disclosure scope is governed by [[Rule/资助披露范围与时点条号以适用规则版本官方文本核对]]。

### C. Alternative Submissions

1. If the Tribunal is minded to order security, the amount should be reduced to the minimum necessary, namely [[降额后的区间与依据]]。
1. The form should be [[保函加分期，写明开立行、金额、每期金额与到期日]] and the period should be [[期限以适用规则条号官方文本核对]]。
1. If the Respondent obtains a final award in its favour, the security shall be released and the sums refunded with interest, calculated on [[利率与利差的取值方法与保守取值]]。
1. A request for counter-security is made only in the alternative and is not pressed where the Claimant's own position [[慎用理由：请求反向担保会同时把己方置于可能被要求担保的位置，除非己方资信明显优于对方]].

### D. Procedure and Costs

The Claimant requests that this application be determined on [[书面审理或听证，二选一]] without suspension of the substantive timetable, that the Respondent disclose the documents underlying its estimates, and that the costs of the application be reserved to the final award.

~ [[己方代理律所全称]] — [[签署人姓名与职务]]
~ List of Exhibits: [[附件清单]]
