---
title: Application for Correction of the Award
case: [[内部案件代号]]
workflow: 10-award-post
profile: correction
mode: legal
footer_left: [[文书代号]] — [[日期]]（机构案件编号 [[编号]]）
keep_sources: false
toc: false
---

#! ===== 使用说明（本段全部以 #! 开头，渲染时整行丢弃，绝不进入 Word）=====
#! 归属子技能：10-award-post。三种申请共用本骨架：correction（更正）／interpretation（解释）／additional award（补充）。
#! **先定性再选标题**：算术、笔误、抄写或获准的类似错误→correction；适用规则允许解释的具体部分存在歧义→interpretation；
#!   已提出而未裁断、且可通过补充处理的请求→additional award。标题、请求用语与核验后的依据须一致。
#! 边界（写进文书，非中文文书再写进审阅说明）：更正纠错、解释澄清歧义，不借此重新裁判已决事实或法律；补充裁决处理已提交而未裁断的请求，可能需要进一步事实与法律论证。
#!   先按适用规则与仲裁地法核验授权、对象、当事人约定条件、时限和程序；补充不得夹带新请求、已被驳回的请求或借漏裁名义重审。
#!   超出获准范围时回 10 第五、六步核验其他救济及其窗口；不因需要事实或法律论证就自动转撤销／上诉，也不预设这些路径存在。
#! 期限分开核验：更正／解释／补充各自的申请期限，以及庭方主动动作的起算事件与期间，不将裁决作出日、转交日与收到日混用；
#!   数值、可否延展、经机构转送的份数与对象一律现查（fetch_official.py applicable + lookup --pattern "correction|interpretation|additional"），
#!   本模板所有条号、天数、份数位置留 [[…以适用版本官方文本核对]] 占位（铁律 1、2）。
#! 自证按期：核验后写明起算事件、裁决收到日、本函提交日与期间计算口径，登记送达凭证代号；未核验时保留占位，不预填按期结论。
#! 成果形式与效力：成立或驳回使用何种文书、是否构成裁决一部分及是否产生独立挑战窗口，逐项按适用法／规则核验，不统一预设 addendum／decision 的效果。
#! 合并或分别申请须核验程序要求并避免重复提交；涉利息起算点含混时，核验可否同时请求 correction + interpretation，并说明两者关系与先后。
#! 语言：本模板默认英文（与裁决工作语言一致）；纯中文程序改写为中文，并保留同一节次结构（术语对照见 references/glossary-en-zh.md）。
#! 交付：定稿后，申请文本为非中文时同出《中文审阅说明》（中文申请不另出，三句话直接写进矩阵 adversarial_review），给管理层的三句话固定为"最近不可回避的期限是哪天／本步两种策略与代价／需要谁在何时决定什么"。

# Application for Correction of the Award

#! 标题按定性结果三选一：Application for Correction／Interpretation／Additional Award（见使用说明"先定性再选标题"）。

~ Arbitration under the Rules of the [[机构全称]]
~ Case No. [[xxxx/xx]]
~ [[Claimant／Respondent 全称]] ("the [[Claimant]]") and [[对方全称]] ("the [[Respondent]]")
~ Date of the Award: [[date]]；Date of receipt by the Applicant: [[date]]

## I. THE APPLICATION

The [[Claimant]] applies to the Arbitral Tribunal, through the [[机构全称]], for [[correction of the Award／interpretation of a specified part of the Award／an additional award in respect of a claim — 按核验后的权限与对象选择，写明对象与日期]].

The Applicant received the Award on [[date]] and this application is submitted on [[date]]. [[期限自证：按适用规则与仲裁地法核验起算事件、期间、计算口径及届满日后说明是否按期；未核验标待核验]] [source:<rules-source-id> | <版本> | <页条段> | <URL> | 校验 <日期>].

#! 上一段是期限自证段，不可删：裁决后救济的第一个攻防点就是"有没有按期提出"。
#! 期间口径（是否含当日、经机构转送以何日为提出日）现查后写入，不得由常识推定。

The Applicant requests that the Arbitral Tribunal [[operative relief in one imperative sentence, e.g. "correct paragraph 3 of the dispositif of the Award so as to read USD 1,204,500"]] and [[further or alternative relief]].

## II. THE AWARD AND THE MATTER COMPLAINED OF

The Arbitral Tribunal rendered its Award on [[date]], deciding [[一句话说主文处理了什么]].

[[The specific passage: 逐字引述裁决原文（用 > 缩进段），标明页码与段落号]]

> "[[裁决原文逐字摘录]]" (Award, p. [[__]], paragraph [[__]])

## III. GROUNDS

#! 保留本次获准提出的路线，删除其余栏；合并请求须说明关系。更正列原文／拟改内容／凭证；解释列歧义／读法／实际影响；补充列已提交请求／漏裁对照／所需审理，均给页码与核验依据。

### A. Correction：算术或文字错误

The above passage contains an [[arithmetical／typographical／similar]] error. The correct [[figure／wording]] is [[…]], which follows from [[计算底稿或文字对应凭证：按错误类型列明计算输入项或拟改文字的来源，注明附件号与页码]].

The correction does not affect the substance of the Tribunal's decision: the Tribunal's finding on [[争点]] remains as decided, and the correction merely gives effect to it.

#! 更正按错误类型附计算底稿或文字对应凭证及页码，证明不涉及重审实体；不能只靠"不影响实体认定"的声明代替权限与事实核验。

### B. Interpretation：获准解释部分的歧义

Paragraph [[n]] of [[适用规则与仲裁地法允许解释的裁决部分]] is ambiguous in that [[歧义语句如何产生两种以上读法]]. The ambiguity affects [[具体权利义务及实际影响；涉及某法域执行效果时另列核验依据，不预设不可执行]].

The Applicant's position is that the paragraph means [[主张的解释]], because [[与裁决理由段、当事人请求项、庭审记录的对应关系，逐处给页码]].

#! 解释申请先核验可解释的部分，再指明其中的具体歧义及实际影响；对象不一律限于主文，仅对理由不满不构成解释事由。
#! 解释不得借澄清之名要求重新裁判已决事实或法律；需要其他救济时另核其是否存在及适用条件。

### C. Additional Award：已提出而未裁断的请求

The Applicant advanced the claim for [[请求名称 + 金额／救济类型]] in [[书状名称 + 段落号 + 日期]] and repeated it in [[Request for Relief 项号]]. That claim was not decided: [[逐项对照请求、裁决理由与主文的页段，说明并非已被驳回，也非仅未讨论某项论点]].

The Applicant requests an additional award in respect of that claim [[and, if the Tribunal considers further submissions necessary, directions to that effect]].

#! 漏裁与超裁分开：已提交未裁请求先核补充权限；超出提交范围的裁断另核撤销或执行抗辩事由、期限与对象，不自动认定路线可用。
#! 未决请求须给书状段落号、请求项编号和附件代号；补充审理可按庭方指令展开必要事实与法律论证，不增加新请求或重审已决请求。

## IV. RELIEF SOUGHT

The Applicant respectfully requests that the Arbitral Tribunal:

(a) [[具体、可直接执行的救济句式，含币种与数字]]；

(b) [[如需：按适用法／规则核验后的文书形式与效力表述；未核验标待核验，不预设均为 addendum 或均构成原裁决一部分]]；

(c) [[如需：备位请求，如 correction 不获准则就同一段落作出 interpretation，并说明两者关系]]；

(d) [[costs of this application，按本案规则口径写明可请求的项目]].

## V. RESERVATION OF RIGHTS

This application is made without prejudice to the Applicant's rights and contentions as to the merits, jurisdiction and admissibility of the claims, and does not constitute acceptance of the Award or of any finding therein save to the extent expressly stated above.

The Applicant reserves its right to seek [[set-aside／recognition and enforcement／resistance to enforcement]] to the extent available under the applicable law in each relevant jurisdiction. [[本申请及后续文书对相关期限的效果：逐路线、逐法域核验起算、中止、重启或不受影响后写入结论；未核验保留待核验占位]] [source:<id> | <版本> | <页条段> | <URL> | 校验 <日期>].

#! 保留权利声明本身不延展或保全任何期限。更正／解释／补充申请及后续文书对撤销、承认与执行、执行抗辩等相关期限的效果，须逐路线、逐法域核验，不预定中止、重启或不受影响。
#!   回矩阵（10-award-post-action-matrix.md）按核验依据更新各日历（执行地结论由 14 回填），未核验记 unknown 并列核验任务、负责人及内部截止；本函提交及后续文书收件分别登记，不以本申请为由搁置其他窗口保护。

~ [[机构案件团队／仲裁庭秘书邮箱：送达方式与份数说明]]
~ Attachments: [[A-1 裁决副本；A-2 对应路线的计算底稿／歧义对照／已提交未裁请求凭证页；A-3 收到裁决的快递／邮件凭证]]
