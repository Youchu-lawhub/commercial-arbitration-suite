# 可扩展海外法律检索适配

## 通用契约

将 `law_retrieval` 视为多后端能力槽。登记表 `assets/research-sources.json` 记录 provider ID、连接方式、权限、法域、能力、覆盖范围、文档来源及验收方式；不保存密钥或客户事实。新增供应商复用字段，不修改仲裁业务逻辑，不要求用户必须购买特定产品。

能力按 `coverage`（覆盖发现）、`search`、`full_text`、`resolve_citation` 分别验收；端点存活、握手成功、工具列表和正文成功是不同状态。通过宿主已连接工具执行，遵循实时工具 schema；不根据本文猜参数，不擅自编辑宿主设置或安装依赖。缺少某项能力时降级该项，不宣称整个服务完全可用。

统一检索记录：provider / query（脱敏）/ jurisdiction / document_type / coverage_dates / searched_at / source_id / document_id / official_url / title / court_or_issuer / decision_or_publication_date / effective_period / language / retrieved_passages / status / limitations。缺字段记未知，结果按官方 ID、案号或法规版本去重；不同供应商返回同一官方文本不是两条独立来源。原文与译文分开保存，明确机器翻译。

工作顺序：确认问题及法律层次 → 发现法域和时间覆盖 → 母语关键词与必要同义词检索 → 获取候选全文 → 精确解析引用 → 核对发布机关原文及版本 → 查修订废止、上诉及后续裁判处理 → 输出附段落定位的结论与未覆盖范围。没有后续处理数据库时明确未完成该项，不能声称案例仍为有效先例。对仲裁裁决还要区分公开与非公开、商事与投资仲裁。

失败分类：AUTH_REQUIRED / RATE_LIMITED / NOT_COVERED / SOURCE_UNAVAILABLE / NO_RESULTS / TEXT_UNAVAILABLE。按原因提示连接、稍后重试、缩小检索或官方来源路径；NO_RESULTS 不证明法律或案例不存在。收费、权限和供应商条款以用户账户当前约定为准。

## Legal Data Hunter 适配

登记 ID：`legal-data-hunter-remote`。供应商连接文档：https://legaldatahunter.com/connect 。远端 MCP：https://legaldatahunter.com/mcp 。使用宿主现有插件连接；未连接时登记 AUTH_REQUIRED，不自动变更客户端配置。

文档描述的能力映射：覆盖发现使用 discover_countries / discover_sources / get_filters；检索使用 search；全文使用 get_document；引注定位使用 resolve_reference。工具名与参数仍以连接后实际 schema 为准。先发现覆盖范围，再取全文并回核官方来源；不把索引全文误说成只能提供摘要，也不把供应商自身等同官方发布机关。索引规模、收费和免费额度不写死。

外部问题反馈 report_source_issue 属写入操作，不纳入自动研究流程；需要用户明确授权后才能发送，不夹带客户事实。

本项目仅维护原创适配说明与配置，不打包供应商代码、技能、语料、凭证或付费内容；根目录 LICENSE 中的 CC BY-NC 4.0 许可适用于本项目自身内容。参考供应商服务条款 https://legaldatahunter.com/terms ，部署时核对对应 API/MCP 与订阅条款；可公开访问不等于取得再分发许可。

## 降级与扩展

无法使用 LDH 时，复用登记表中的法域专属官方 API、法院判决库、立法机关与政府公报；再考虑已授权商业库。保存来源 URL、读取日期与缺口，不用搜索摘要代替全文。新增供应商先完成相同四类能力验收，再写入案件配置；一次公开法域验收不代表所有法域覆盖。主体登记查询走独立 company_research 槽，不能用法律检索结果代替工商核验。

## 无 MCP 的快速网页兜底（发布版）

运行 `python3 scripts/research_sources.py web --jurisdiction SG`，或直接读取 `research_sources.py plan` 的 `web_fallback`。仅返回离线预置的官方站点候选和三条全球导航入口，**不触发网页抓取、不收集案件信息、不证明网站在线或法律文本现行有效**。

研究顺序：先使用对应法域官网候选检索具体法规及条文；候选缺失才通过美国国会图书馆 Guide to Law Online 或中国司法部法通网、商务部全球法规网人工发现国别官网；再核对原发布机关、颁布与生效日期、修订史、适用版本和所引条文。商务部明确禁止自动化采集，绝不编写或调用爬虫采集该站；中文译本仅辅助定位。浏览器不能取得官网原文时不得编造，并转外部律师。

性能：每轮仅检索本案争点、法域和所需的一种法律层次；先 `web` 的单一国家结果、再 `plan` 的最多四条候选；检索命中后停止扩展，版本与后续效力核查不可略过。用户已提供原文的，不重新全网搜索。多个法域按争点逐个独立核验，不把 EU / HK / UK / US 联邦与州级法律混用。
