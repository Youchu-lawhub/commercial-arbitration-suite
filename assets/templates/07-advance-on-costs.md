---
title: Advance on Costs, Reimbursement Award, Third-Party Funding and Costs Framework
case: [[案件代号]] | [[机构名]] Case No. [[案号]]
workflow: 07-measures-costs
profile: advance
mode: legal
footer_left: [[Draft v1]] — [[日期]]
keep_sources: false
toc: true
---

# ADVANCE ON COSTS AND COSTS FRAMEWORK

#! 本文件是骨架模板，复制到案件目录 deliverables/ 后逐段填写；所有 #! 行渲染时整行丢弃，永不进入 Word。五部分按需取用：Part I 催缴、Part II 替代缴纳后的单独偿还裁决请求、Part III 第三方资助披露与程序指示、Part IV 税项与 VAT 预缴核对表、Part V 费用分担主张框架。
#! 适用子技能：07-measures-costs 第 9 项（预缴款与费用杠杆）、第 10 项（第三方资助）、第 11 项（费用分担主张框架）。产出名对应 07 的 outputs 之"费用分担主张框架"。
#! 闸门未过不得使用：python3 <suite>/scripts/route.py --gate 07-measures-costs --profile advance --workdir <案件目录> --provided <案件目录>/case.json。缺"已发生与预计费用明细"或缺缴款通知与份额信息时，本轮只出《补充材料与信息确认清单》视图。
#! 先取官方文本（顺序执行）：python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <仲裁启动日> ；python3 <suite>/scripts/fetch_official.py check --inst <机构id> ；python3 <suite>/scripts/fetch_official.py fetch <规则版source_id> --to-md ；python3 <suite>/scripts/fetch_official.py lookup <规则版source_id> --pattern "advance|deposit|failure to pay|substitute|costs|funder|third-party funding" --max 12 ；费用表与税项另跑 lookup <费用表source_id> --pattern "fees|VAT|tax|withholding" --max 12 。
#! 渲染与核验：python3 <suite>/scripts/render_docx.py --in <draft.md> --out <draft.docx> --mode legal --strict --manifest <x.paras.json> ；再跑 python3 <suite>/scripts/verify_suite.py --workdir <交付目录> --mode submission；非中文文书另配中文审阅说明（本身用中文提交的文书不配）。
#! 顺序纪律：先走机构的催缴与替代缴纳机制并保留全部凭证（缴款通知、催缴函、付款回单、汇率与时点记录），再请求单独裁决。顺序颠倒会被指未用尽程序内救济，构成程序滥用抗辩的靶子。
#! 执行地资产线索一律来自用户材料，本套件不代为认定对方主体、资产位置或偿付能力；未取得的信息保持 [[占位]]。
#! 裁决签署前结清仲裁员报酬是常见实务风险：报酬与税项未结清时，机构通常不释放裁决草案，签署与送达整体延迟。相关处理与费用表口径必须现查规则与机构费用表后再写入文书，本模板不给任何天数或费率。

## Part I — Request that a Party Pay its Share of the Advance

### A. The Payments and the Default

| 事件 | 日期 | 金额与币种 | 凭证与附件号 |
|---|---|---|---|
| Decision or notice fixing the advance | [[日期]] | [[金额与币种]] | [[附件号]] |
| Share allocated to each party | [[份额]] | [[金额与币种]] | [[附件号]] |
| Payment due date under the rules | [[期限以适用规则条号官方文本核对]] | [[金额与币种]] | [[附件号]] |
| Reminder issued by the institution or the requesting party | [[日期]] | [[金额与币种]] | [[附件号]] |
| Non-payment by [[未缴方简称]] | [[日期]] | [[欠付金额]] | [[附件号]] |

### B. Relief

1. An order that [[未缴方简称]] pay its share of the advance, being [[币种与金额]]，within [[期限以适用规则条号官方文本核对]] pursuant to [[Rule/预缴义务与催缴条号以适用规则版本官方文本核对]]。
1. Directions that the Secretariat confirm the date of receipt of that payment and notify both parties.
1. In the alternative, leave to the requesting party to make a substitute payment under [[Rule/替代缴纳条号以适用规则版本官方文本核对]]，without prejudice to reimbursement and interest.
1. Costs of this request reserved to the final award on costs.

#! 同步评估机构依规则可采取的后果（中止、视为撤回、仅就已缴请求继续审理），把它写进己方时间表与部分请求策略，条号现查：[[Rule/未缴后果条号以适用规则版本官方文本核对]]。

## Part II — Request for a Separate Award Reimbursing an Advance Paid by the Other Party

### A. Why the Form of the Relief Matters

#! order 与 award 的区分是这部分的全部价值：程序命令（order）通常不能作为裁决依《纽约公约》获得承认与执行，而金钱裁决（award）可以。因此必须明示请求"以裁决作出"，并把执行可能性写实——对方资产位于另一法域、需要公约路径执行；空喊执行力只会削弱说服力。同时要说理：该裁决只处理已到期的垫付款返还，不预断实体，且避免程序整体停滞。部分规则或法域下此类中间裁决的定性存在争议（是否终局、可否单独撤销），己方立场应在本节先给出，依据取 [[Rule/裁决形式与终局性条号以适用规则版本官方文本核对]] 与 [[法域依据须由 11-governing-law 出具并标置信度]]。

### B. The Substitute Payment

The [[己方简称]] paid the sum of [[币种与金额]] on [[付款日期]] in place of the [[未缴方简称]]，as evidenced by [[银行回单与机构收款确认，附件号]]。The payment discharged the defaulting party's obligation under [[Rule/预缴与替代缴纳条号以适用规则版本官方文本核对]] and is immediately due and repayable.

The non-payment is a dilatory tactic rather than an inability to pay: [[对方财务能力线索，取用户材料，附件号]] and [[既往不配合程序记录，附件号]]。

### C. Interest

Interest is claimed on the principal sum from the date of payment to the date of receipt, at [[参考利率]] plus a margin of [[利差]]，the method being [[取值来源、复利或单利口径、计息基准与币种匹配说明]]. The rate is deliberately conservative and is supported by [[依据附件号]]，and the currency and the conversion date for any exchange element are [[汇率取值日与来源]]。

#! 利率要给出方法与保守取值并说明起算日、币种与汇兑口径；无据的高利率通常被下调，并给仲裁庭留下不良印象。

### D. Relief

1. A separate award, and not merely a procedural order, that [[未缴方简称]] pay the [[己方简称]] [[币种与金额]] by way of reimbursement of the advance paid on [[付款日期]]。
1. Interest as calculated in section C from [[起算日]] to the date of actual payment.
1. A declaration that this award decides only the reimbursement of a sum already due, does not prejudge the merits, and is intended to be capable of recognition and enforcement in the jurisdiction where [[执行地与资产线索，取用户材料]] is located.
1. The costs of this request to be included in the final award on costs.

<pagebreak>

## Part III — Third-Party Funding: Disclosure and Procedural Directions

### A. Where Our Client is the Funded Party

1. Disclosure of the existence of a funding arrangement and of whether the funder has an economic interest in the outcome, in the form required by [[Rule/资助披露范围与时点条号以适用规则版本官方文本核对]] and the applicable institutional guidance.
1. Submission that the identity of the funder and the commercial terms are not required for the purposes of the tribunal's assessment of independence or of security, with a redacted version enclosed as [[附件号]]。
1. Where a payment deadline is at issue: the stage reached in the funding negotiations ([[洽谈阶段与已完成步骤]])，the expected completion date ([[日期]])，and the alternative plan if funding is not obtained ([[分期、母公司担保或其他替代方案]])。

#! 披露义务的触发时点要现查：部分规则自资助协议订立即触发。机构对模糊的"正在筹资"容忍度低，延期请求必须写明已进行到的阶段与预计完成时点，并附阶段性证据。

### B. Where the Other Party is Funded

1. A request that the funder's identity and any relationship with the arbitrators or counsel be disclosed sufficiently to permit an assessment of independence, per [[Rule/披露范围条号以适用规则版本官方文本核对]]。
1. A continuing notification obligation for any change of funder, of the terms or of the economic interest, for the remainder of the proceedings.
1. Submission that the existence of funding bears on the impecuniosity element of any security application and that funding costs are not, as such, recoverable costs, having regard to [[Rule/可赔成本范围条号以适用规则版本官方文本核对]]。

## Part IV — Tax and VAT on Arbitrators' Fees: Checklist

| 核对项 | 本案情况与取值 | 依据与凭证 |
|---|---|---|
| Whether the remuneration is taxable in the relevant jurisdiction | [[是否应税与税种]] | [[Rule/税项处理条号与机构费用表以官方文本核对]] |
| Estimated amount to be pre-funded, by party and by share | [[估算区间与币种]] | [[费用表口径与仲裁员报酬估算]] |
| Account and heading to which the pre-funding is paid | [[账户与科目，与预缴款分列]] | [[机构指示函附件号]] |
| Deadline for pre-funding and consequence of default | [[期限以适用规则条号官方文本核对]] | [[附件号]] |
| Invoice addressee, issuer and VAT recovery route | [[开票主体与抬头]] | [[机构发票样例附件号]] |
| Withholding tax and cross-border payment responsibility | [[承担方与对份额分摊的影响]] | [[己方财务口径，本套件不代为认定]] |
| Settlement and true-up once remuneration is fixed | [[多退少补机制]] | [[Rule/费用表条号以官方文本核对]] |

#! 税项与预缴款分列账户与科目，防止核销混乱；估算口径（税率、计税基数、是否含共同仲裁员）要写清，避免事后差额争议。中国境内主体对外付汇路径、发票与代扣要求属财务操作，以用户及其财务口径为准。

## Part V — Costs Allocation Framework

| 主张路径 | 本案论证要点 | 需要的台账与凭证 |
|---|---|---|
| Costs follow the event | [[胜负面与请求逐项对应表]] | [[分阶段可赔性台账：阶段、事项、费率、凭证、币种]] |
| Each party bears its own costs | [[规则允许的平均分担口径与本案理由]] | [[Rule/费用裁量条号以适用规则版本官方文本核对]] |
| Proportionality | [[按请求成立比例分摊的计算式]] | [[请求金额与获支持金额的对照]] |
| Non-cooperation in the procedure | [[迟延、拒不披露、不缴预缴款、过度申请的具体行为与后果]] | [[行为时间线与己方因此增加的费用]] |
| Recoverability of in-house legal and expert costs | [[己方内法务与专家费用是否可赔的主张与保留]] | [[工时与内部成本记录、专家账单，Rule/可赔范围条号以官方文本核对]] |

The Claimant's or Respondent's position on each row is to be pleaded once the applicable rules text has been fetched, and the framework is maintained from the early stages so that the final costs submission rests on a complete ledger rather than reconstructed figures.

#! 程序性申请阶段应主动请求"本阶段费用留待最终裁决一并处理"，避免被裁令即时承担；庭后正式费用陈述转 assets/templates/09-post-hearing.md，四层结构为可赔范围、合理性、比例、行为不端的费用后果。

~ [[己方代理律所全称]] — [[签署人姓名与职务]]
~ List of Exhibits: [[附件清单]]
