# 材料预填、待确认草案与金额检查

## 一、从材料启动

先读原材料，自动提取明示事实及文件页段；只就冲突、歧义或影响本轮工作的缺项问用户。不要将提取等同法律认定，不要求用户重复确认白纸黑字的机构、地址等字段。扫描件解析失败要列清，不得把解析失败说成材料不存在。

```bash
python3 <suite>/scripts/intake.py extract --input <原材料目录> --out <案件目录>/extracted.json
python3 <suite>/scripts/route.py --scope <案件目录>/extracted.json
python3 <suite>/scripts/intake.py checklist --gate 04-commencement
python3 <suite>/scripts/intake.py bootstrap --facts <已整理事实.json> --workdir <案件目录>
python3 <suite>/scripts/route.py --gate 04-commencement --workdir <案件目录> --provided <案件目录>/case.json --mode draft
```

事实文件格式如下；字段 ID 从 checklist 获取，多个阶段共用同一个 ID。`confirmed` 表示有明确材料或用户指示支持的记录，不表示已完成法律证明。自动提取后要核对对应页段再登记；不要根据关键词自动生成勾选结论。`not_applicable` 必须写 `reason`，写明的视为已核并通过；`unknown` 只在 `suite.yaml` 的 `allow_unknown` 允许时有效，且须有明确回答的 evidence 与完整 follow-up。`case.json` 是唯一材料台账，`route --gate` 与 `verify_suite` 共用同一 `intake.evaluate`；Markdown 清单只是由台账生成的只读视图。

```json
{"schema":"rulesuite-case/1","case":"DEMO","facts":{
 "contract.arbitration_clause":{"status":"confirmed","value":"SIAC, seat Singapore","evidence":["contract.pdf p12 clause18"]},
 "authority.status":{"status":"pending","pending_id":"Q1","question":"签署人姓名与授权范围？"}
}}
```

bootstrap 仅建立能力实际状态与事实账，不宣称已访谈，也不自行决定规则版本。启动日未定时记录候选版本与适用假设，不把预计提交日伪装成已确认启动事件。旧 Markdown 逐字清单仅作人读视图，不能作为提交核验的材料台账；新案件统一使用稳定字段 ID 的 `case.json`，`checklist` 输出可整段复制的 Markdown 视图。

## 二、草案与提交态

用户要求先出稿或保留手填项时，使用显式草案模式。每个占位符必须登记责任人、问题、案件、文件范围和唯一 Q 编号；不是通过换成“填写：”避开核验。未登记遗漏、来源错误、同步错误和结构错误仍阻断。

在案件根目录保存 pending.json，正文使用 `[[Q1:签署人姓名]]`，记稿 frontmatter 的 `case` 必须等于清单案件代号：

```json
{"schema":"rulesuite-pending/1","case":"DEMO","items":[
 {"id":"Q1","placeholder":"Q1:签署人姓名","question":"请确认授权签署人","owner":"申请人法务","status":"open","files":["申请书.md","申请书-中文审阅说明.md"]}
]}
```

```bash
python3 <suite>/scripts/render_docx.py --in <案件目录>/申请书.md --out <案件目录>/申请书.docx --mode legal --draft --pending <案件目录>/pending.json
python3 <suite>/scripts/render_docx.py --in <案件目录>/申请书-中文审阅说明.md --out <案件目录>/申请书-中文审阅说明.docx --mode memo --draft --pending <案件目录>/pending.json
python3 <suite>/scripts/verify_suite.py --workdir <案件目录> --mode draft --pending <案件目录>/pending.json
```

DRAFT_OK 仅表示草案登记及结构通过，不能提交。草案自动加不可提交标识；清单或记稿改变后须重渲染。确认后替换实际事实，将事项登记 resolved，去掉 --draft，使用 --strict 重渲染，最终运行 `--mode submission`；只有 `VERIFIED` 且退出 0 才是提交态，`VERIFY_INCOMPLETE` 不是。正式提交前仍须视觉检查与法律复核。工作目录只放本轮交付件，避免旧版本参与校验。

## 三、缓存及官网受阻

lookup 可以直接读取本地 PDF 并懒提取 txt/md；缺少解析器或扫描件时返回具体解析状态。单有文件和哈希不等于官方真实性或适用性已确认。

```bash
python3 <suite>/scripts/fetch_official.py import <source-id> --file <原件.pdf> --origin <实际来源URL> --kind official --retrieved <YYYY-MM-DD>
python3 <suite>/scripts/fetch_official.py lookup <source-id> --pattern "Notice|Fee"
```

mirror 用于转载，browser 用于浏览器保存的可见文本快照。费用表受阻时只读浏览官方页面，保存正文及截图、币种、税费、档级与访问日期后导入；只有截图时先 OCR 并对照原图。不得把挑战页当正文、绕过访问限制或伪造实时核验。check 的远程状态与 cached 本地状态分开解释。安装检查只检查结构，不为全库未缓存报警；本案只查需要的来源。

## 四、利息与程序轨道

金额调节使用 `assets/templates/04-金额调节与利息台账.md`；利息脚本读取显式单利分段 JSON，金额/利率使用字符串，年利率 5% 写 `"0.05"`。先确认付款冲抵、单复利、日数和截止日；不同口径分别运行，不把脚本计算当合法性结论。

先按案由确定"金额结构"，再决定是否拆票：

| 中国出海企业常见案由／金额结构 | 计息分段单位 | 逐票分配 |
|---|---|---|
| 国际货物买卖、大宗贸易、服务费、保理等票据或往来账 | 每张票的到期日，付款按约定冲抵本金 | 适用 |
| 航运、租约、提单、造船 | 按航次、租期或提单批次；滞期费、滞箱费单列 | 运费发票流可用；租金、滞期费不套用 |
| 借款、融资租赁、分期付款、多笔提款 | 每次提款／每期应付本金 | 多笔提款可逐笔，不是逐票 |
| EPC、国际工程、设备供货 | 付款证书、里程碑、变更令；保留金单列 | 通常不适用，改按付款证书分段 |
| 公司／股东、合资、股权回购、M&A、对赌／earn-out | 单笔本金或价款分期；估值与交割日敏感 | 不适用 |
| 能源、矿业、长期供货（LNG、矿石、电力购买） | 按交付批次、合同期或价格回顾节点；照付不议与最低采购量单列 | 通常不适用 |
| 技术许可、特许经营、分销佣金 | 特许权期间或销售报告期 | 不适用，按期间分段 |
| 投资条约、征收补偿 | 估值基准日至裁决日／实际支付日 | 不适用 |
| 禁令、继续履行、确认之诉等非金钱请求 | 不计利息；费用与迟延履行后果单列 | 不适用 |

> **类型依据（取数日 2026-10-23；仅用于确定分段结构，不作个案频率判断）**：贸仲 2025 年受理 5,736 件（涉外 806 件），类型覆盖建筑工程及房地产、买卖合同、金融、公司／企业治理、服务合同、租赁等 12 大类 70 余种；SIAC 2025 年贸易类占 39%，中国为第一大外国当事人来源；HKIAC 2025 年公司／股东 23.6%、海事 19.9%、国际贸易 14.2%；ICC 2025 年建筑工程 28%、能源 15%；商务部《2024 年度中国对外直接投资统计公报》显示批发零售、租赁商务服务、制造、金融、采矿流量均超百亿美元。各机构分类口径不同、一案可跨类、占比逐年变动，引用前按当年官网更新。投资条约／征收补偿不在上述商事机构统计内，单列是因为出海企业存在条约保护路径。

违约金、罚息、资金占用费如属独立请求，不并入利息台账；其性质、上限与可调减性按准据法另核。无明确本金、利率口径与起止日的请求，先补事实，不运行脚本。

```bash
python3 <suite>/scripts/interest_schedule.py --input <利息输入.json>
python3 <suite>/scripts/procedure_track.py --input <轨道事实.json>
```

interest 输入：schema=`rulesuite-interest/1`、currency、method=`simple`、interval=`start-inclusive-end-exclusive`、basis=`ACT/365F`、`ACT/360` 或 `ACT/ACT-year`；segments 每段含 claim_id/start/end/principal/annual_rate/basis_evidence；reconciliation 含 face_principal、claimed_principal、adjustments（每项 amount/reason/evidence）。同请求的调息和本金变化按日拆连续段，不能重叠或漏算；每币种单独运行。输出每段、合计及票面到净额调节差。

track 输入分两部分：案件事实与案件本地 profile。事实侧至少含 institution、rules_version；profile 侧由使用者按本案适用官方文本填写，或用 `profile_file` 指向案件目录内的 JSON。profile 必须含 schema=`rulesuite-procedure-profile/1`、institution、rules_version、basis_source、source_url、source_locator、source_quote、verified_at、required、confirmations、outcomes、references。`source_quote` 是从官方文本复制的原文片段；须按 `references/verification-contract.md` 增加每项 outcomes 的 basis、条件图 review 指纹及案件 workdir。脚本从统一缓存或本案来源记录读取正文，同时验证引文、哈希、版本、核验范围与复核指纹，缓存位置服从 RULESUITE_DATA_DIR；未取回文本、引文不命中或校验日期超过刷新周期时返回 `PROFILE_UNVERIFIED`，不得继续套用条件。事实字段的类型与确认项由 profile 的 `required`、`confirmations` 定义；金额口径包括哪些请求、抵销、利息及费用，换汇日与汇率先按原文确认，脚本不推定。

脚本不内置任何机构门槛、条号或默认机制，也不从来源登记表读取条件。条件语言仅支持 fact/all/any/not/lte/lt/gte/gt/eq；按序匹配，不执行任意代码。`NO_PROFILE`、`PROFILE_INVALID`、`PROFILE_UNVERIFIED`、`PROFILE_MISMATCH`、`NEEDS_FACTS`、`NEEDS_REVIEW` 均不构成程序结论，继续人工查证与草案路径；只有 `SCREENED` 才表示该 profile 已核验并命中一个配置结果，且仍须人工复核。

## 五、数据处理与格式一致性

当材料含调查报告、个人证件、住址、金融或其他敏感信息，并拟向境外机构、律师、证人或服务商传送时，主动列数据流：来源地／接收地与主体／目的／必要字段／脱敏或删减／访问权限与留存。按相关法域转 11 核查合法依据、保密和传输要求；仅有新加坡仲裁地不意味着所有处理只适用 PDPA。没有实际传输任务时不强制全量隐私访谈，不阻断本地草案。

三条一致性规则：当事人按注册号/法定名称区分关联主体；金额带明确币种及计算口径（S$ 可归一 SGD，单独 $ 不猜币种）；关键日期保留事件含义、时区和原始证据（ISO 与英文长日期归一，歧义数字日期须澄清）。说明段落引用以主文 manifest 为准，不能复制虚高编号绕过检查。

脚本自身设置网络及子进程超时，不依赖 GNU timeout；Linux/macOS 使用 python3 命令，外部 OCR/浏览器/付费接口分别标明可用状态。

**逐票分配是条件性子模式**：仅在票据／往来账型金钱债权中使用 `python3 <suite>/scripts/interest_schedule.py --input <案件目录/interest.json> --allocation`；工程、合资、股权、许可、投资条约等按上表的分段单位改为普通 `segments`，不得把付款证书或里程碑硬套成发票。
输入沿用 schema/currency/method/interval/basis，另填 as_of、annual_rate、basis_evidence、allocation_scope（必须为 `invoice_or_running_account`）、allocation_policy（oldest_first 或 designated）、payment_application（principal_only）；invoices 每项填 invoice_id/amount/due_date，payments 每项填 date/amount，可填 invoice_id；designated 时每笔必须指定。金额与利率均为十进制字符串；提前付款降低其指定或按顺序分配的本金，超过余额部分单列未分配额，不推定法律效果。

机构与法域适配采用通用流程：分别确认机构/管理分支、规则版本、仲裁地法、协议准据法、实体准据法与执行地；按任务选择官方来源和法律检索能力槽。机构要求不得替代法域强制规定，冲突进入待确认清单。
`procedure_track.py` 只读取案件本地 profile，包内不预置任何机构的门槛、条号或默认机制。profile 由使用者在具体案件中从官方文本生成并保存于案件目录；条件仅支持 fact/all/any/not/lte/lt/gte/gt/eq，按序匹配，不执行任意代码。无 profile、profile 未绑定官方文本、引文未命中或条件不覆盖时，分别返回 `NO_PROFILE` / `PROFILE_UNVERIFIED` / `NEEDS_REVIEW`，继续人工查证与草案路径，不默认套用别的门槛。
新增机构或法域：官方来源登记于两份 JSON；新增渠道使用既有字段并保持 unknown/manual 与原核查日期。规则生效和过渡依据、收件方式及费用分别核对；案件事实与用户订阅偏好保留在案件或个人配置，不进入公共登记表。
