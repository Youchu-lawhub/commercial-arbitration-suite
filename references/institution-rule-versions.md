# 内置规则版本清单 / Built-in Rule Version Registry

本表列出套件内置知识所依据的各机构仲裁规则版本。用户可据此判断是否需要人工获取更新版本供套件核验。

版本标识、生效日期、置信度与抓取状态四列一律以 `assets/sources-registry.json` 为准；本表只是该登记表的可读视图，出现不一致时以登记表为准并回改本表，登记表未收录的版本标识不得出现在本表中。该一致性由 `scripts/rule_audit.py` 强制校验：列值漂移、重复行、未登记的版本标识、以及登记表中已收录却未进入本表的规则版本，都会使闸门失败。

This table lists the rule editions on which the suite's built-in knowledge is based. Users can refer to this table to determine whether a newer edition has been issued and whether manual download is needed.

---

## 使用说明

1. **版本判定**：合并文本的本体日期不等于每项修订日期；如登记 selection_from，自动筛选采用其与 effective 的较晚者，独立组件仍须核验时间与合意要求。套件启动时（冷配置阶段）按本案仲裁启动日期与 `sources-registry.json` 中登记的 `effective` 日期匹配适用版本，不凭印象取其一。
2. **核验状态**：`confidence: high` 表示已确认官方文本一致；`medium` 表示二手权威一致但未逐字核对；`low` 表示来源冲突必须人工确认。
3. **抓取状态**：`fetch: ok` 表示登记表配有官方 PDF 下载地址（`download`），套件可直接取文；`manual` 表示没有自动下载地址或需登录/验证码，须人工取文；`blocked` 表示站点明确阻断脚本访问。`manual` 与 `blocked` 均不影响已导入并逐条核验正文的引用。
4. **版本更新触发**：若官方发布了新版规则且生效日期晚于本表登记版本，套件不会自动替换——须用户确认后重新运行 `fetch_official.py fetch` 取新版本，再更新本表。
5. **降级披露**：当正文尚未导入或尚未核验时，套件在文书中不引用具体条号，改标 `[[待官方文本核对]]` 占位；已导入并核验的正文可按其来源状态正常引用。

---

## 全球机构 / Global Institutions

### ICC — 国际商会国际仲裁院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `icc-arb-2026` | ICC Rules of Arbitration (2026) | 2026-06-01 | high | ok |
| `icc-arb-2021` | ICC Rules of Arbitration (2021) | 2021-01-01 | high | ok |

> 两版并行：按本案启动日与官方过渡条款确定适用版本。

### LCIA — 伦敦国际仲裁院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `lcia-2020` | LCIA Arbitration Rules 2020 | 2020-10-01 | high | ok |
| `lcia-languages` | LCIA Rules 多语版本页 | — | high | manual |

> 英国 2025 年仲裁法已生效，LCIA 规则修订咨询进行中。多语版本页仅有 HTML，自动下载需人工确认 PDF 地址。

### AAA/ICDR — 美国仲裁协会 / 国际争议解决中心

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `icdr-2021` | ICDR International Dispute Resolution Procedures | 2021-03-01 | high | ok |
| `aaa-commercial-2022` | AAA Commercial Arbitration Rules | 2022-09-01 | high | ok |

> ICDR 国际规则与 AAA 国内商事规则并行，不得混引。

### Swiss — 瑞士仲裁中心

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `swiss-rules-2021` | Swiss Rules of International Arbitration 2021 | 2021-06-01 | high | ok |

> 另有 2025 年第三方资助补充规则（`swiss-tef-rules-2025`），与主规则分属不同文本。

### SCC — 斯德哥尔摩商会仲裁院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `scc-2023` | SCC Arbitration Rules (2023) | 2023-01-01 | high | ok |
| `scc-expedited-2023` | SCC Expedited Arbitration Rules (2023) | 2023-01-01 | high | ok |

### VIAC — 维也纳国际仲裁中心

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `vienna-rules-2021` | Vienna Rules 2021（2025-01-01 修正版） | 2025-01-01 | high | ok |

### DIS — 德国仲裁研究院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `dis-2018` | DIS Arbitration Rules 2018 | 2018-03-01 | high | ok |

### UNCITRAL/PCA — UNCITRAL 规则临时仲裁与常设仲裁法院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `uncitral-rules-2021` | UNCITRAL Arbitration Rules（含 2013、2021 年修正的官方合并版） | 2010-08-15 | high | ok |
| `pca-arbitration-rules` | PCA 仲裁规则 | — | high | manual |

> PCA 主站有 Cloudflare 反爬保护，登记条目仅有规则页而无稳定的官方 PDF 直链；自动下载需人工确认 PDF 地址。

### ICSID — 解决投资争端国际中心（世界银行集团）

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `icsid-arb-2022` | ICSID Arbitration Rules (2022) | 2022-07-01 | high | ok |
| `icsid-convention-2022` | ICSID Convention, Regulations and Rules (ICSID/15/Rev. 3) | 2022-07-01 | high | ok |
| `icsid-institution-rules-2022` | ICSID Institution Rules (2022) | 2022-07-01 | high | ok |
| `icsid-additional-facility-2022` | ICSID Additional Facility Rules (2022) | 2022-07-01 | high | ok |
| `icsid-admin-fin-regs-2022` | ICSID Administrative and Financial Regulations (2022) | 2022-07-01 | high | ok |

> 两条独立修订轨道须分别监测：Rules/Regs 修订由 Administrative Council 决议推动；Convention 本文修订依其自身修订条款。

---

## 行业仲裁 / Sectoral

### 伦敦海事与大宗商品仲裁

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `lmaa-terms` | LMAA Terms 2021 | 2021-05-01 | high | ok |
| `fosfa-2026` | FOSFA Rules of Arbitration and Appeal | 2026-04-01 | high | ok |

> 此类仲裁机构化程度低，时效（time-bar）与上诉/复审机制差异大；接案第一步须按适用规则官方文本核对时效与救济路径。

---

## 亚洲机构 / Asia-Pacific Institutions

### HKIAC — 香港国际仲裁中心

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `hkiac-admin-2024` | HKIAC Administered Arbitration Rules 2024 | 2024-06-01 | high | ok |
| `hkiac-domestic-2014` | HKIAC Domestic Arbitration Rules | — | low | manual |

> 简易程序门槛按启动日对应版本现取，不预载数值。

### SIAC — 新加坡国际仲裁中心

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `siac-2025` | SIAC Rules (7th edition, 2025) | 2025-01-01 | medium | blocked |

> 抓取状态 blocked 指自动 HTTP 管线：官网对脚本请求返回 403。技能包不附带该版官方全文，包内也没有可机器复核的取文摘要或逐项锚点核验记录，故置信度为 medium。运行时按 `scripts/fetch_official.py` 的口径由使用者人工下载原文存入 `data/official/`，经 `import` 与 `verify` 登记核验人、版本、定位和日期后才能引用；站点改版或规则换版时须重新取文回校，不沿用缓存文本。

### CIETAC — 中国国际经济贸易仲裁委员会

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `cietac-2024` | 中国国际经济贸易仲裁委员会仲裁规则（2024 版） | 2024-01-01 | high | ok |
| `cmac-maritime` | 中国海事仲裁委员会仲裁规则 | — | low | manual |

> 简易程序金额门槛、自贸区规则现行版本与 CMAC 规则年份须现查官方文本。CIETAC 自动下载使用登记表的官方中文 PDF（`pdf_zh`）；CMAC 仅有 HTML 规则页，自动下载需人工确认 PDF 地址。

### BAC/BIAC — 北京仲裁委员会

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `bac-intl-2026` | 北仲国际仲裁规则（2026 版） | 2026-01-01 | high | ok |

> 登记表已配置官方 PDF 下载地址，自动取文按该地址探测并要求返回 PDF；若站点改版或要求登录/验证码，自动取文会降级为人工取文，不写成自动成功。

### SHIAC — 上海国际经济贸易仲裁委员会

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `shiac-2024` | 上海国际经济贸易仲裁委员会仲裁规则（2024 版） | 2024-01-01 | high | ok |

> 勿与上海仲裁委员会（另一家机构）混淆。

### SCIA — 深圳国际仲裁院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `scia-2025` | 深圳国际仲裁院仲裁规则（2025 年修正） | 2025-07-01 | high | manual |

### SCIAHK — 华南国际仲裁中心（香港）

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `sciahk-2025` | SCIAHK Arbitration Rules 2025 | 2025-03-31 | high | manual |

> 深圳 SCIA 与港资 SCIAHK 名称极易混淆，文书必须写全称与注册地。两者均仅有 HTML 规则页，自动下载需人工确认 PDF 地址。

### KCAB — 大韩商调仲裁院国际仲裁院

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `kcab-2026` | KCAB International Arbitration Rules 2026 | 2026-01-01 | high | ok |

### JCAA — 日本商事仲裁协会

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `jcaa-2021` | JCAA Commercial Arbitration Rules 2021 | 2021-07-01 | high | manual |

> JCAA 主站 HTML 页面返回 423，登记条目未收录稳定的官方 PDF 直链；自动下载需人工确认 PDF 地址。

### AIAC — 亚洲国际仲裁中心（吉隆坡）

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `aiac-2026` | AIAC Arbitration Rules 2026 | 2026-01-01 | high | ok |

### 澳大利亚（ACICA / Resolution Institute）

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `acica-2021` | ACICA Arbitration Rules 2021 | 2021-03-01 | high | ok |
| `ri-2023` | Resolution Institute Arbitration Rules 2023 | 2023-01-01 | low | manual |

### 印度（MCIA 等）

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `mcia-2025` | MCIA Rules 2025 | — | high | ok |
| `lcia-miac-2018` | LCIA-MIAC Rules 2018 | 2018-07-27 | high | manual |

> LCIA India 已停管新案，仅历史案件适用。该机构仅有 HTML 规则页，自动下载需人工确认 PDF 地址。

---

## 西亚与北非 / West Asia & North Africa

### DIAC / arbitrateAD / QICCA / CRCICA / BCDR / SCA

| 版本标识 | 规则名称 | 生效日期 | 置信度 | 抓取状态 |
|---|---|---|---|---|
| `diac-2022` | DIAC Arbitration Rules 2022 | 2022-03-21 | high | ok |
| `arbitratead-2024` | arbitrateAD Arbitration Rules 2024 | 2024-02-01 | high | ok |
| `qicca-2024` | QICCA Arbitration Rules 2024 | 2025-01-01 | low | manual |
| `crcica-2024` | CRCICA Arbitration Rules 2024 | 2024-01-15 | high | ok |
| `bcdr-2022` | BCDR Rules of Arbitration 2022 | — | medium | manual |
| `sca-2023` | 沙特商事仲裁中心 Arbitration Rules 2023 | 2023-05-01 | high | ok |
| `sca-small-claims-2026` | SCA 小额程序规则 | 2026-08-01 | medium | manual |

---

## 版本更新流程

1. 套件冷启动时扫描本表，对 `next_check_due` 过期的条目运行 `fetch_official.py probe` 检查是否有新版本发布。
2. 若官方已发布新版规则：提示用户确认 → 运行 `fetch_official.py fetch <source-id>` 取新版本 → 更新本表。
3. 若官方未发布新版：续期 `checked_at`，继续使用当前内置知识。
4. 用户也可随时手动运行 `fetch_official.py fetch --all` 强制刷新全部缓存。

## 用户操作指引

- **抓取状态为 `ok` 的机构**：套件可自动取文核验，用户无需额外操作。
- **抓取状态为 `blocked` 或 `manual` 的机构**：用户需从官网下载规则 PDF，放入 `data/official/` 目录，然后运行 `fetch_official.py import <source-id> <文件路径>` 导入。导入后套件即可引用具体条号。
- **置信度为 `low` 的条目**：表示来源存在冲突或不确定性，建议用户自行提供官方文本供核验。
- **发现官方已更新规则版本**：通知套件重新取文，或直接下载新版 PDF 导入。

---

本表由 `sources-registry.json` 生成，最后更新：2026-10-24。
