---
name: 00-cold-start
description: 涉外商事仲裁套件的首次运行与每案开场：建立案件工作目录、确认能力槽、锁定涉外因素与规则版本。route.py --detect 返回 NO_CONFIG 时必须先执行本子技能。
metadata:
  stage: cross
  gate: none
---

# 冷启动（每案一次）

本子技能建立案件目录里的最小 `.arbitration-config.md` 与材料台账 `case.json`，配置只记录本轮需要的能力及已确认信息，不把全套问卷作为开工条件。已有配置时只更新变化；通用规则问答不强制建案。Markdown 材料清单只作人读视图，不参与闸门判定。

先读已给材料与既有记录，预填主体、合同、涉外因素、阶段、目标及最近期限；首轮最多集中问三个会改变当前决定的问题，其余登记待办。紧急期限或资产/证据灭失风险先提醒并说明核验状态，不因配置、建档或自检延误保期限动作，不擅自提交。

## 一、执行顺序

1. **装机自检**（每台机器首次，或技能包被改动后）：
   ```bash
   python3 <suite>/scripts/install_suite.py --fix
   ```
   读取退出码与失败项；出现 `FAIL` 时报告并停止依赖受损结构的自动交付，先修复再验收，但不延误紧急期限提醒及可独立完成的材料整理。无执行环境时明示自动闸门未运行，只走文本草案降级。`WARN` 可继续，但要在配置里登记（如缺 `xmllint` → DOCX 校验降级）。`--seed-official` 只打印首次取文指引，不联网，可用于向用户说明规则缓存的获取方式。
2. **确认工作目录**：向用户要一个案件目录（或经用户同意在当前目录下建 `仲裁案件/`）。案件材料、草稿、交付物只写进这个目录；技能包 `data/` 只放公共规则缓存，不放案件材料（铁律 8）。案件根保留配置、材料和矩阵，本轮交付件与历史稿分目录隔离；核验以案件根为 `--workdir`，仅选本轮交付件及依赖。
3. **涉外范围判定**（先做，别先问配置）：
   ```bash
   python3 <suite>/scripts/route.py --scope <案件目录或要素文件>
   ```
   - `IN_SCOPE` → 继续。
   - `REVIEW_REQUIRED` / `UNKNOWN` → 先从材料定位注册地、履行地、法律事实、仲裁地/准据法或境外执行因素，仅确认足以改变涉外定性的缺项，计入首轮最多三个关键问题，不重复五项问卷。
   - `OUT_OF_SCOPE`（纯境内商事案件、劳动争议）→ 说明本套件不处理，给出改用国内诉讼/国内仲裁工具或劳动争议技能的提示，**本轮结束，不产出任何文书**。
   - 规则名称、英文材料或境外案例只是线索，不能替代本案事实；未确认涉外前不产出文书。
4. **能力槽确认**：先按本轮任务及 `suite.yaml` 的 requires 筛选下表，只确认当前依赖的槽位绑定或降级，不逐项跑全表。已有真实授权与确认直接沿用；未涉及槽位不要求启用，未回答不记为已确认。每槽一行，状态取 `bound` / `degraded` / `skipped` / `user-materials-only`；仅对缺权限、凭证或关键事实提问，并计入首轮三个问题上限。下表是按需参考，不是问卷。

   | 槽位 | 询问方式 | 降级后果 |
   |---|---|---|
   | `official_rules_fetch` | "需要时我可以直接从机构官网取规则与指引文本，可以吗？" | 只能引导用户人工下载并 `import` 到 `data/official/`；在此之前所有条文引用一律标 `待核验` |
   | `law_retrieval` | "本案准据法／仲裁地是境外法时，我先跑一条命令看你机器上哪些检索通道真的可用，再给你配置清单，可以吗？" | 只输出检索路径与官方来源清单，不作实体法结论 |
   | `company_research` | "需要核验对方或申请人境外注册信息时，用已安装的官方/商业企业信息接口，可以吗？" | `degraded (official registries; jurisdiction pending)`：只给官方注册机关检索路径 |
   | `docx_render` | "交付要 Word 吗？本机有 python3 即可。" | 只出 `.md`，并说明如何自行转 Word |
   | `local_corpus` | "本机是否已有已解析的法律知识库（如域外法研究、仲裁规则解读、典型案例集等，Markdown 目录）？" | 跳过 |
   | `party_data` | "主体信息我全部以你提供的材料为准，可以吗？" | 无替代：缺材料就问 |

   `law_retrieval` 不凭印象给清单，先探测本机运行时与本案法域可用通道：
   ```bash
   python3 <suite>/scripts/research_sources.py doctor
   python3 <suite>/scripts/research_sources.py plan --jurisdiction <法域>
   ```
   把 `gate` 与 `setup_gap` 原样转述给用户后由用户选择。
   该槽**逐案复核**，不是一次性事实：换法域须重跑 `plan`，`check` 报 `UNREACHABLE`／`GONE` 时原 `bound` 记录立即下调为 `degraded`（铁律 6）。用户有个人检索偏好时按 `references/research-personalization.md` 分层记录；接入新 MCP 按 `references/mcp-onboarding.md` 验收，不把写配置等同连接成功。
5. **按需锁定程序坐标**：先预填机构、仲裁地、语言、启动事件/日期、规则版本、人数与指定方式；仅追问本轮必需的冲突和缺项，余项留待办，不阻塞无关任务。启动日不一定等同上传或签署日，按机构规则的收件、送达标准确认；新拟条款写"尚未启动"，不编造日期。用 `fetch_official.py applicable` 取版本，把输出的 `edition`、`fetch_policy`、`citation_fields` 记进配置文件（不记录不可用的 `citation_format`）：
   ```bash
   python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <YYYY-MM-DD>
   python3 <suite>/scripts/fetch_official.py applicable --inst <机构id> --commencement <YYYY-MM-DD> --agreed-edition <source-id>
   python3 <suite>/scripts/fetch_official.py check --inst <机构id> --timeout 10
   ```
   明确约定旧版时加 `--agreed-edition`；同机构多规则族时先确认 `--ruleset`，二者不可混用。返回候选后核对条款约定、过渡规定与官方文本。`check` 返回 `NEEDS_MANUAL` 时登记人工取文路径；人工取得并核验官方全文后同样可用，仅在正文/适用性未核时禁止引用具体条号和金额，不以连通状态替代正文核验。

   **版本透明披露**：`applicable` 返回后，向用户明确告知以下信息（写入配置文件第六节）：
   - 套件内置知识所依据的规则版本（`source-id` 与生效日期）
   - 该版本的置信度（`high` / `medium` / `low`）
   - 抓取策略 `fetch_policy`（`ok` / `blocked` / `manual`）与引用资格 `citation_ready`
   - 若置信度为 `low` 或 `citation_ready=false`，提示用户：「本套件内置知识基于 [[source-id]]（生效日期 [[date]]），该版本置信度为 [[level]]，抓取策略为 [[fetch_policy]]，尚未具备引用资格。`blocked`/`manual` 只限制自动抓取；如果您有更新版本或官方 PDF，可放入 `data/official/` 后运行 `fetch_official.py import` 导入并完成核验，套件将基于您提供的文本重新核验。」
   - 完整版本清单见 `references/institution-rule-versions.md`，用户可随时查阅。
6. **抓取并缓存本案规则全文**（`data/official/` 发布版为空，首次使用某机构时按需填充）：
   - 先检查 `data/official/<source_id>.md` 是否已存在且版本匹配：**已存在且版本一致 → 跳过下载，直接复用缓存**；
   - 未缓存或版本不匹配 → 执行抓取：
     ```bash
     python3 <suite>/scripts/fetch_official.py fetch <source_id> --to-md
     ```
   - `fetch` 成功 → 规则全文持久缓存于 `data/official/<source_id>.md`（同时保留 `.pdf`/`.txt` 原件），provenance JSON 记录版本号与抓取日期；后续所有子技能引用该缓存，不再重复爬取；
   - `fetch` 失败（网站被阻断、反爬、423/403 等）→ 降级为人工下载：告知用户在浏览器打开该机构官网规则页，下载 PDF 后放入 `data/official/`，再跑 `fetch_official.py fetch <source_id> --to-md` 做 PDF→MD 转换；也可用 `import` 登记来源（`--kind official/mirror/browser`），只有截图时先 OCR 并对照原图，不得把挑战页当正文；
   - **版本更新检测**：后续新案件冷启动时，`check` 命令已在上一步运行；若探测到机构网站上的规则版本与缓存不一致（如 applicable 输出了新版本号），才触发重新下载，否则沿用已有缓存。一家公司通常只约定有限几家机构，缓存积累后此步骤基本为零延迟；
   - 安装目录只读时，用 `RULESUITE_DATA_DIR` 把公共缓存迁到外部可写目录；远程可达状态与本地缓存状态分开解释，单有文件和哈希不等于官方真实性或适用性已确认。
7. **写配置文件与材料台账**（模板见 `assets/templates/00-冷启动配置.md`），槽位行必须保持 `- slot(name): value` 格式，`route.py --detect` 依赖它。未适用字段写"不适用"并简述原因，待核验字段记录原因，不宣称已确认。另用 `intake.py bootstrap --facts <已整理事实.json> --workdir <案件目录>` 生成案件根唯一材料台账 `case.json`（`rulesuite-case/1`，`case` 与配置一致）：每个 gate_id 登记 `confirmed`+`value/evidence`、`pending`+`pending_id/question`、`not_applicable`+`reason`，或 `suite.yaml` 允许时的 `unknown`+完整 follow-up；`gate_any_ids` 的候选项按同一格式逐项登记，至少一项 confirmed 才满足“任选其一”。`case.json` 是 route 与 verify 共用的唯一底账；没有它，提交态会以 `[GATE]` 拒绝。用 `intake.py checklist --gate <子技能id> --facts <案件目录>/case.json` 生成只读 Markdown 视图供人阅读，不得用 Markdown 勾选代替台账。
8. **回报**：用 3–5 行中文告诉用户：本案是否涉外、程序坐标、缺哪些槽位、下一步做什么（通常先 `route.py --detect --workdir <案件目录>`，再按本轮目标选子技能，不强制每案先做全量建档）。配置表示已记录环境，不代表本案所有法律问题已核验。同时告知用户：本案适用机构的内置规则版本为 [[source-id]]（生效日期 [[date]]），置信度 [[level]]，抓取策略 [[fetch_policy]]，引用资格 [[citation_ready]]；未就绪时说明缺口。若需人工核验或导入更新版本，指引见 `references/institution-rule-versions.md`。

## 二、判定与拒绝话术

- 用户说"我们只是国内两个公司打架"：答复模板——"本套件只处理涉外商事仲裁。贵司这个案件没有涉外因素，建议改用处理国内诉讼/国内仲裁的技能；若后续需要在境外执行或发现涉外因素，随时回来。"
- 用户坚持要在本套件内起草纯国内案件：拒绝起草，说明原因（缺少境外机构规则、纽约公约执行路径等本套件的能力前提不成立），并给出转交建议。
- 劳动争议：同上一律拒绝，指向劳动仲裁技能，不做"顺手改一版"。

## 三、自检清单

- [ ] `install_suite.py --fix` 退出码 0（FAIL 已修）
- [ ] `route.py --scope` 结果为 `IN_SCOPE`，且依据写进了配置
- [ ] 配置已建立；本轮必需槽位已有真实绑定或降级确认，未涉及/未确认项如实保留，不为消除 `unfilled` 伪造确认；探测限制明确披露
- [ ] 本案适用规则经条款、真实启动事件与过渡规则复核；`applicable` 只筛候选，旧版约定用 `--agreed-edition`，未启动不编日期
- [ ] 已向用户披露本案适用机构的内置规则版本（source-id、生效日期、置信度、`fetch_policy`、`citation_ready`），写入配置文件第六节
- [ ] 本案适用规则全文已缓存于 `data/official/<source_id>.md`，或已登记为 `NEEDS_MANUAL` 并告知用户人工下载路径
- [ ] `check` 的 `NEEDS_MANUAL` 清单已登记
- [ ] `case.json` 的 `case` 与配置一致；必填 gate_id 均有 `confirmed`+evidence、带 `pending_id` 的 pending、带 reason 的 not_applicable，或允许范围内的完整 follow-up；`gate_any_ids` 至少一项 confirmed；Markdown 视图仅由台账生成
- [ ] 未向案件目录之外的位置写入任何案件材料
