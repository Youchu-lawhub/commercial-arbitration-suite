# 中国企业涉外商事仲裁陪跑式专家（commercial-arbitration-suite）

为出海企业法务与涉外律师提供的仲裁文书起草与程序陪伴技能包。15 个子技能覆盖条款诊断、案件构建、仲裁程序与跨境执行；配套 Word 渲染、中文审阅说明和交付前质量闸门。

## 快速开始

- 入口、铁律与执行流程：[SKILL.md](SKILL.md)
- 安装自检：`python3 scripts/install_suite.py`
- 运行依赖：Python 3.9+、PyYAML；可选 xmllint（OOXML 校验）与 python-docx
- 交付清单生成：`python3 scripts/delivery.py build --workdir <案件目录>`，人工逐页复核后 `delivery.py attest --workdir <案件目录> --reviewer <姓名>`
- 发布打包：`python3 scripts/release.py --out <目标.zip>`（自动跑闸门、排除 .git 与缓存、写 sha256 并解包复验）
- 只读安装（技能目录不可写）须先设 `RULESUITE_DATA_DIR` 指向可写缓存目录，否则官方文本抓取无处落盘
- 子技能与输出定义：`suite.yaml`

## 运行时数据缓存

`data/` 是运行时生成的公共缓存目录（机构规则全文 `data/official/`、来源凭证 `data/_provenance/`），**不随技能包分发**，打包/复制技能包时必须排除。缓存一经抓取或 `import` 即可跨案件只读复用；把缓存目录迁移到其他位置时，用环境变量 `RULESUITE_DATA_DIR` 指向新路径。单有文件与哈希不等于官方真实性或适用性已确认，条文引用仍按各 source 的核验记录执行。

## 许可

本作品采用 **CC BY-NC 4.0 + 许可人补充授权**：个人收费办案、组织内部部署/修改/培训均无需申请或付费；对外商业化另需书面许可。**本作品不是 OSI 定义的开源软件许可。** 详见 [LICENSE](LICENSE)。

## 专业边界

本套件提供法律信息、流程与工具，不构成具体案件的执业法律意见，不建立律师—委托人关系。机构规则与法源结论须回到官方一手文本，按案件适用版本逐条核验。

## 联系

游初 (You Chu) · 994559732@qq.com · 微信 Cyruswcx
