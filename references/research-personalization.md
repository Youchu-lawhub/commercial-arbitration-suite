# 个性化法律检索能力槽

保留 law_retrieval 作为配置总入口，在用户指定的个人配置目录或案件目录保存 research-profile.json。槽按能力而非品牌拆分：coverage（覆盖发现）、legislation（法规）、case_law（案例）、full_text（全文）、citation_check（引注定位）、treatment（后续裁判处理）。一个槽可有多个后端，同一后端可承担多个槽。先复用用户已有官方或商业数据库，LDH 不享有默认优先权。

## 冷启动与按需配置

先读取用户已指定配置、可见连接和此前偏好；没有选择时只问一个合并问题：“本案涉及哪些法域？已有或希望优先使用哪些法律数据库/MCP？也可以暂用官方公开来源，进入具体法域时再配置。”已知信息直接预填，不要求购买或配置全部清单。只展示本案相关的两三项候选，并提供自定义数据库/暂不配置的路径。

进入新法域、请求的新能力未覆盖、原接口失效或用户要求切换时，只补该项。记录选择适用范围：默认、指定法域或本轮任务；任务优先于法域，法域优先于默认。覆盖为替换整个该槽列表；空列表表示本层明确不选择，不偷偷继承默认。未设置的能力仍继承上层。

用户自购数据库可用 MCP/API、登录网页或用户导出的授权资料。网页登录不伪称 MCP；人工导出不伪称自动抓取。订阅不等于 API 授权，也不等于已包含全文和案例后续处理。只存连接别名或凭证引用，账户密码、token、客户检索结果不放技能包。

## 配置与选择

```bash
python3 <suite>/scripts/research_profile.py catalogue
python3 <suite>/scripts/research_sources.py plan --jurisdiction SG --config <research-profile.json> --capability case_law --task jurisdiction-objection
```

catalogue 动态列出既有登记表所有通道，故增加通道无需修改业务模块。目录中的能力是待核实标签，绝非现行可用证明。选择不会安装或调用外部服务；实际调用由宿主已连接工具执行。

```json
{
 "schema":"rulesuite-research-profile/1",
 "providers":[
  {"id":"legal-data-hunter-remote","status":"auth_required","connection_ref":"用户的LDH连接"},
  {"id":"my-sg-database","title":"用户已购新加坡数据库","connection":"web",
   "jurisdictions":["SG"],"capabilities":["legislation","case_law","full_text"],
   "status":"unverified","connection_ref":"用户指定官方登录入口","credential_ref":"host-managed",
   "acceptance":[]}
 ],
 "default":{"coverage":["legal-data-hunter-remote"]},
 "jurisdictions":{"SG":{"legislation":["my-sg-database"],"case_law":["my-sg-database","legal-data-hunter-remote"]}},
 "tasks":{"jurisdiction-objection":{"case_law":["my-sg-database"]}}
}
```

首次使用先发现覆盖时间、法院层级、资料类型和权限，用不含客户信息的公开问题验收。成功后记录 status=ready 与 acceptance 项：capability、jurisdiction、date（ISO）、result=passed、evidence（实际工具/检索记录路径）。每项能力分别验收，不能用搜索成功推定全文或后续处理成功。选择器要求目标法域及能力的近90日验收记录；本案引用仍要核实具体原文与时效。连接失效立即更新状态，不等90日届满。

## 上传 MCP 清单的吸收方式

用户提供的《境外法律检索 Skill — MCP 配置清单》（2026-09-09）仅作为候选目录。LDH、DingDuff、CourtListener、台湾法社区项目及 open-legal-compliance-mcp 均可配置；Ansvar 国别仓库已归档且不附数据库，改走登记表中的 `ansvar-gateway-*`（OAuth 网关、按量计费）。当前登记表已有项直接选对应 ID，没有的先自定义登记。不得按 country 名拼接包名并自动执行，也不把社区包装器称为数据库官方接口。

该清单中同一服务同时出现远端连接与社区安装片段，客户端配置语法也可能不同。安装前逐一打开供应商/仓库当前文档，验证确切包名、入口、许可证、客户端语法、认证及运行时；无法核实的命令只留作线索。无需为了配置选择而先安装所有候选。法律检索覆盖不等同工商登记覆盖。

选择及验收后的槽行示例：`slot(law_retrieval): degraded (research-profile.json; case_law pending acceptance)`。全部本轮所需能力已验收后才登记 bound；无研究任务时 skipped。不要新增六个全局强制闸门，使普通文书任务被无关数据库配置阻塞。

用户选择新接口或请求接入时，按 `references/mcp-onboarding.md` 完成探测、最小提问、准备变更、合并配置、认证交接、真实工具验收与回滚；不能只交供应商名单或把写配置等同连接成功。
