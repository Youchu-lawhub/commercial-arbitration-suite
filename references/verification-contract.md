# 本轮交付与来源核验

仅在正式文书交付、程序 profile 筛查或来源维护时读取本文件。先沿用当前案卷，以下记录均由 Agent 在案件目录维护；不要求用户手工编辑 JSON 或运行脚本。记录真实核验，不自行填写虚构核验人或把自动计算冒充人工审阅。

## 1. 本轮文件清单

在案件根写 `delivery.json`，仅列本轮实际文件。历史稿、原始材料、旧版本与无关矩阵不要列入。`--workdir` 保持案件根；清单及其文件均必须位于该目录，使用相对路径，不接受越界或符号链接。

```json
{
  "schema": "rulesuite-delivery/1",
  "documents": [
    {"document": "交付/A-letter.docx", "review_note": "交付/A-letter-中文审阅说明.docx"}
  ],
  "attachments": ["交付/A-guide.md"]
}
```

- 每个正式文书明确配一份说明 DOCX；内部件依原有 `pair: false` 规则处理，可省略 review_note。不得给对外文书套内部件豁免。
- 说明、原始记稿与 `.paras.json` 一并保留。每个 DOCX 的渲染记录必须含 source_sha256、docx_sha256；修改记稿、Word 或来源后重新渲染。
- 申请仲裁、重写与补正另在清单中写 `filing_guide: "交付/A-guide.md"`，脚本会自动检查指引内容和占位；不能靠省略 --filing-guide 跳过。
- `attachments` 可省略；只列本轮 Markdown/DOCX 指引等辅助文件，其引用和提交态占位也参与检查。原始证据、扫描件不塞进该字段，另按案件根 `case.json` 的已核事实及证据索引核对。
- 提交模式自动读取案件根 `delivery.json`，也可显式传 `--delivery-manifest <案件根内路径>`；没有清单即不可提交。旧 `--pairs` 仅用于兼容结构检查，不能与交付清单并用。
- 旧命令中的 `--case/--delivery` 已移除，统一改用 `--mode submission`（argparse 会以 unrecognized arguments 拒绝旧参数，不会静默降级）。文书是否核对矩阵只看自身 frontmatter 的 `workflow/profile/matrix` 声明，不再用 `--case` 表达。

```bash
python3 <suite>/scripts/verify_suite.py --workdir <案件目录> --mode submission
python3 <suite>/scripts/verify_suite.py --workdir <案件目录> --mode draft --pending <pending.json>
```

完成实际逐页查看后，将视觉复核写回同一清单的 `visual_review`：`reviewer` 为实际复核人，`date` 为实际日期，`files` 为“各 DOCX 相对路径 → {sha256, pages, status: "passed"}”映射。覆盖本轮全部主文与说明，记录实际页数与所看文件哈希；没有实际查看或发现缺字/分页问题时不得填 passed。文件改版后旧记录失效。未登记有效记录时，提交模式返回 `VERIFY_INCOMPLETE` 且退出码 2；`DRAFT_OK` 仅表示草案结构可用。

| 模式 | 条件 | decision | 退出码 | submission_ready |
|---|---|---|---|---|
| draft | 无硬错误 | `DRAFT_OK` | 0 | false |
| draft | 有硬错误 | `VERIFY_FAILED` | 2 | false |
| submission | 全部满足 | `VERIFIED` | 0 | true |
| submission | 仅有未完成项（缺清单、视觉复核、矩阵提交态） | `VERIFY_INCOMPLETE` | 2 | false |
| submission | 有硬错误 | `VERIFY_FAILED` | 2 | false |

`VERIFIED` 仅当 `submission_ready=true`；`DRAFT_OK` 与 `VERIFY_INCOMPLETE` 都不是提交验收。`problems` 记录硬错误，`gate_issues` 单独列出未完成项，两者都阻断提交。

本机缺中文字体时，安装器和交付检查会提示。可在具备中文字体的实际查看环境完成 PDF 转换与逐页检查后登记；仅字体检测成功也不算视觉验收。

仍按文书自身 workflow/profile/matrix 核对依赖；清单不会取消案件构建、立案指引或执行材料的实质要求。`VERIFIED` 表示所声明范围内的自动检查通过，不证明事实真实、法源适用、已完成视觉复核或已获提交授权。

## 2. 公开官方文本的核验记录

继续通过 fetch/import/lookup 取得和核对全文。完成真实核验后，按文书内部来源标记使用的精确版本标签，登记版本、核验范围与定位；多个定位重复传参。

```bash
python3 <suite>/scripts/fetch_official.py verify <source-id> --by <实际核验人> --scope <实际核验范围> --edition <精确版本标签> --locator <已核定位>
```

提交态来源检查要求：已取文本、原始缓存与核验文本哈希一致、核验人和日期有效、版本标签一致、定位被核验范围覆盖。旧凭证未记录版本时重做对应范围的真实核验，不直接替来源补造确认。`check` 只是可达性检测；不得用其代替法律核验。官方抓取状态 blocked/manual 不阻止已经合法导入并实际核验的正文使用。

引用标记必须有顺序固定、均非空的五项：ID、版本、定位、URL、校验日期。不得用空定位或只有网站首页冒充定位。`cite` 是唯一被认可的标记生成器：引用日期取 `verified_at`（核验日），不是 `_checked_at`（抓取日），也不是生成当天；`--locator` 必须落在 `verified_locators` 或 `verified_scope` 覆盖范围内。来源存在但未核验时停在受控草案；需要保留的待确认内容登记 pending，不包装成提交完成。

## 3. 新机构、法律或判例的案件本地来源

不必为了一个案件改动技能包的公共来源表。将实际取得的正文放在案件目录，建立 `case-sources.json`。登记已完成的核验可用：

```bash
python3 <suite>/scripts/case_sources.py --workdir <案件目录> --id <案件来源id> --text <目录内正文相对路径.md> --origin <真实官方HTTPS地址> --edition <精确版本标签> --locator <已核定位> --by <实际核验人> --scope <核验范围> --date <实际核验日期>
```

若保留扫描件或官方 PDF，增加 `--original <目录内原件相对路径>`，同时绑定原件与正文哈希。正文与原件、网页与发布日期、本案时间适用性应实际对照。URL 格式、登记成功或哈希一致均不独立证明该来源的权威性；仍按 11 判断权威层级和依赖范围。

本案来源会参与相同的提交闸门。案件记录只放案件目录；公共缓存只放公开官方文本，不放客户检索结果或案件事实。匿名化来源 ID 不含当事方名称或争议细节。

## 4. 程序 profile 的条件图复核

案件输入增加 `workdir`，用于读取本案来源记录；相对路径以输入 JSON 所在目录解析。`profile_file` 同样按输入文件目录解析。继续使用 `rulesuite-procedure-profile/1`，并补齐：

- 每个 outcomes 项有 `basis: {locator: "…", quote: "…"}`；分别核对该条件对应的原文、金额口径、换汇及例外，不拿一段无关原文替整个条件图背书。
- `review` 含实际 `by`、`date` 和 `profile_sha256`。指纹覆盖 review 之外的全部字段，条件、阈值、计算字段或依据变化后原复核失效。
- 来源本身须满足第2或第3节的正文、哈希、版本和范围要求；只复制一段同名本地文本不能得到 VERIFIED。

```bash
python3 <suite>/scripts/procedure_track.py --input <profile.json> --fingerprint
```

此命令只计算指纹；必须实际复核条件图后才把指纹与核验人、日期写进 review。再通过案件事实输入运行筛查。不要把 fact 确认字段强行改成 true。SCREENED 只是依已核 profile 作条件筛查，不能视为机构决定，也不代表提交验收完成。

**材料台账与提交闸门的互校（不得双轨）**

`case.json` 是唯一材料台账。`route.py --gate` 与 `verify_suite.py` 都调用同一个 `intake.evaluate`：

- **提交态**：每份文书的 frontmatter `workflow/profile` 必须能映射到 `suite.yaml` 子技能；缺失或无法映射即 `[GATE]` 硬错误，不得以“未声明”跳过。选中 spec 有 `gate_ids`/`gate_any_ids` 时，以案件根 `case.json` 运行 `evaluate(..., "submission")`。缺 `case.json`、缺 `.arbitration-config.md`、`submission_ready=false`、`pending`、`conflict`、profile 无效/缺失、redirect，均记为 `[GATE]`，提交退出 2；不得因未提供台账而跳过检查。`route.py --gate` 的退出码在提交态与 `submission_ready` 一致，在草案态与 `allowed_to_draft` 一致。
- **任选其一闸门**：`gate_any_ids` 与 `gate_any` 等长配对，每个 ID 指向 `case.json.facts` 的一项来源基础。至少一项 `confirmed`（有 value 与 evidence）即满足；无 confirmed 时，`conflict`、`pending`、`unknown` 按各自状态进入阻断或受控草案，全部缺失才记一条 `gate_any` 缺项。`intake.py checklist` 逐项列出并附 `record`，不得只在 Markdown 中勾选。
- **不适用与未知**：`not_applicable` 必须写 `reason`，写明的视为已核并通过；`allow_unknown` 的 `unknown` 须有明确回答的 evidence 与 `follow_up.action/owner/due`，只允许受控草案，不使提交态就绪。
- **草案态**：按 `evaluate(..., "draft")` 允许带 `pending_id/question` 的 pending 与上述 allow_unknown；缺项、冲突、无效 profile、缺台账仍阻断。文书层另建 pending.json，Q 编号与本台账一致。
- **案件代号与配置**：`case.json` 的 `case` 必须与 `.arbitration-config.md` 及文书 frontmatter 一致。非 `00-cold-start` 任务缺配置、配置无法读取、为符号链接/目录、缺 `case:` 行或代号不一致，均为 `[GATE]` 硬错误。
- **人读清单**：Markdown 勾选清单只作视图，不是台账；把未核项勾成已确认以绕过闸门，视为伪造确认。
- **输出**：`verify_suite.py` 的 `material_gate_checks` 逐文书列出 subskill/profile/decision 与 missing/pending/conflict/not_applicable/unknown 字段 ID，不回显案件值或问题文本。

官方缓存统一服从 `RULESUITE_DATA_DIR`，各工具从同一地址读取。切换缓存目录后先确认正文和凭证均已迁移。

## 5. 历史版本与合并文本

规则登记可增加 `selection_from`（该合并版本进入按启动日自动筛选的下界）、`base_effective`（规则本体起点）和 `components`（独立修订/附录的时间信息）。脚本按 effective 与 selection_from 的较晚者筛选，不将规则本体的旧日期当新增内容的生效时间。

这仍只是候选筛选。组件是否适用、是否需要当事人合意、是否有过渡条款，要在本案适用正文中核对。历史版本未覆盖时取得当时文本和过渡依据；不回填当前合并版，也不把尚未启动的拟提交日写成真实启动事实。

## 6. 安装与回归验证

Python ≥3.9、PyYAML 为原有基础要求；PDF 解析和完整 OOXML/视觉检查依赖环境能力。先运行安装器，再按本案需要绑定能力。安装器检查默认不要求案件配置，detect 只验证已填配置；任务 gate 根据 suite.yaml 的 requires 要求必要槽位。未涉及槽位可以暂不配置。

```bash
python3 <suite>/scripts/install_suite.py
```

无执行环境继续按根技能的明确降级流程处理。
