# MCP 通道的案件级能力验收

## 一、权威边界

登记表中的 `VERIFIED_REMOTE_MCP`、`VERIFIED_KEYLESS` 是**历史探测状态**，只足以提供优先候选线索。连接、握手、工具发现、能够返回搜索结果、取得官方原文、验证版本与在本案可引用是六个不同层次。不得把前四者的成功表述为最后两者。

`research_sources.py plan` 提供法域检索方案；`mcp-route` 提供**只读、案件级能力建议**，不能替代材料、来源与交付闸门，也不会写入公共目录。

## 二、默认快速流程

1. 先确定本次的法域、争点、任务所需能力、法律时点及公开/保密边界。任务只涉及内部模板时不探测 MCP。
2. 用 `python3 scripts/research_sources.py mcp-route --jurisdiction SG --capability full_text` 看候选。无观测时所有历史握手记录均不可直接标为 READY。
3. 如宿主已经连接相关 MCP，且用户授权向其发送本次必要的**脱敏查询**，执行一次工具发现、一次目标查询与正文核验。通过后，把观测记录写入用户**案件目录**，绝不写入 Skill 包、公共缓存或来源登记表。
4. 再用 `--observations /path/to/case/mcp-observations.json` 重新选路。`READY` 仅意味着本任务能力验收记录的**必要字段齐备且尚未过期**，并不担保记录真实或法律结论正确；正式引证仍须打开原文核查。
5. 缺 MCP、认证失败、超时、拿不到正文等：**立即**走 `research_sources.py web --jurisdiction XX` 返回国别官方源和宿主浏览器计划。严禁反复尝试需要登录或无法访问的通道，禁止绕过验证码和门户的自动化采集限制。
6. 无论何种通道，法律事实、适用法、条文、裁判均按 `references/verification-contract.md` 留存案件级证据；未取得原文按受控草案规则办理，不编造。

## 三、观测记录规范

下列仅为**结构示例**，不代表真实验收，也不能用示例数据制造 READY 状态：

```json
{
  "observations": {
    "mcp-source-id": {
      "jurisdiction": "SG",
      "capability": "full_text",
      "connected": true,
      "tool_discovered": true,
      "query_succeeded": true,
      "full_text_returned": false,
      "official_origin_url": "",
      "pinpoint": "",
      "version_checked": false,
      "checked_at": "2026-10-29T19:00:00+08:00"
    }
  }
}
```

此示例应判 `PARTIAL`，因为没有核验官方正文。认证材料、访问令牌、客户原始事实、合同全文不写入该记录。状态采用 `READY`/`PARTIAL`/`AUTH_REQUIRED`/`UNAVAILABLE`，有效窗口默认 24 小时。源登记的 `auth` 和历史运行时状态属于发现线索，不能替代当前宿主测试。

## 四、性能预算

默认仅检查当前法域及能力，最多优先试用 2 个候选；首轮目标官网不超过 3 个。某通道认证失败/明确无正文，当前任务不重试相同前提；宿主如具备真正并发能力，可并行发起彼此独立的公开源验证。延迟预算由宿主结合任务设置，不硬编码为法律核验时限。完成可引用法律结论前不得因超时放松版本或引证要求。

## 五、本案验收的阻断条件

- 无 MCP：通过目标法域官方导航取得原文及定位；拿不到正文时不写未经核验的实体结论。
- 仅返回标题或摘要：记为 PARTIAL，不得标 READY。
- 需要登录、超时或拒绝访问：安全降级，不循环尝试，不把网络不可达混同于反爬限制。
- 返回法域不符或观测已过期：重新验收，不复用 READY。
- 未获对应外发授权：不向第三方发送本案材料；公共目录始终不得存放案件数据。

状态工具仅检查记录条件。真实工具调用、正文取得、版本适用及法律命题仍须在本案逐项核验。
