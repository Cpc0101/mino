---
name: run-test-cases
description: 通过 Nexus 运行已写好的用例，读取执行 Scout 的记录和证据并汇报。用于跑用例、跟进任务或分析失败，区分接单、执行、断言和证据暂不可用。
---

# 执行用例并汇报

测试任务先读[测试质量、缺口求助与逐条回执](../mino/references/execution-discipline.md)：缺口立即查证或问人，不编账号、不改原文预期；正式终态逐条在可见对话回执，调试/准备不计正式通过。

**触发与读结果用 MCP；本机 Scout 运维用 CLI。** Nexus 管任务索引、设备/账号租约和状态投影；Scout 拉仓、独立执行并保存完整记录。Workbench 从 Nexus 取列表，经 Nexus 转发读取原执行 Scout 的详情。正式执行的 Git 副本、输出和证据保存在执行工作区的 task_id 目录下，不删除为临时副本；各 attempt 的 source/output 独立。旧记录继续可读。

认证、登录/OTP 排障、续接或租约冲突先读 [会话、认证与验证码闭环](../write-test-cases/references/session-authentication.md)。正式 run 不继承 debug context；显式 `account_id` 仅约束租号，不能替代本次认证。

本技能负责固定版本的正式执行。本机编写与保留现场的调试使用 write-test-cases 的 `debug_case` 流程。远端 Scout 只执行正式用例；执行输出目录以 `session_record` 返回的路径为准，不在编写工作区堆放运行数据。

执行 Mino 任务时，被测 UI 只经 MCP `case_run` → Scout 操作和取证。不得用 Computer Use、浏览器控制、Playwright、adb、Appium、WDA 或其他桌面自动化工具替代 Scout，也不得先手动点一遍再声称已由 Scout 验证。

开跑前用一两句话告诉用户：将跑哪些用例、哪台设备、哪个环境。

## 资源闭环

缺少测试资源、保存生成文件或恢复依赖用例时，必须遵循 [测试资产与主动准备](../mino/references/test-assets.md)。准备成功不替代正式验证；不要把“当前账号没有”直接收敛成任务结束。

## 全集范围门禁（开跑前）

用户说“继续测试”“跑所有用例”或“验收这个需求”时，执行范围仍是需求原文的全部用例，不是当前 `tests/` 目录里已经有的脚本。开跑前必须先从飞书 CLI 或其他原文来源机器读取完整用例 ID，并读取或初始化对应 workflow 的 `expected_units` 与 `coverage`；不得用 `case_list`、当前目录文件数或设备能跑通的子集反推需求全集。

`case_run` 的 `script_targets[].case_ids=[]` 只表示执行 `tests/<需求ID>/` 下当前已有的全部脚本，不表示原文 `expected_units` 已全部实现。执行前要把这批脚本的 ID 与 `coverage.missing` / `coverage.verification_missing` 对账：

- `missing` 非空时，不能把“现有脚本全部通过”写成“需求全部通过”或“需求现有用例全部通过”；必须写成“当前已实现 X/Y，剩余 ID ...”。
- 用户要求的是全集时，按 write-test-cases 的全集门禁继续实现缺失脚本，再分批执行；不能停在已存在的几条上。
- 如果用户明确只要求回归当前已有脚本，应在开跑前说明这是当前脚本子集，不能暗示原文全集已完成。
- 每条用例执行后读取真实 Scout 结果；只有有 `task_id` 和断言证据的 verification 才能计为 `formal_verified`，接单、动作完成或静态检查通过都不算。

正式 `case_run` 带 `script_targets` 时必须传 `workflow_id`，并保证 `project_id` 与本工作流一致；Nexus 会拒绝没有绑定成功 `case_source_read` 收据、范围未锁定、来源未验证或用例不在 `expected_units` 内的请求。401/400 `formal_run_requires_workflow_binding` 一类错误不是环境问题，先补 `agent_workflow_init` 再跑，不绕过门禁。

每批完成 5–10 条后重新读取 `agent_workflow_get.coverage`，从 `next_units` 自动继续。`verification_complete=true` 只表示当前验证阶段没有未处理项，仍可能含 `blocked_units`；正式全集通过必须满足 `all_verified=true`。否则只有所有剩余条目都有明确 blocked/failed/deferred 证据时才可结束本轮，并逐条报告缺口。`coverage.complete` 只是脚本实现阶段的兼容别名，不能证明正式测试已完成。

## 1. 执行

0. **确认执行节点**：先区分当前机与所选设备所属 Scout。本机 Scout 用 `mino-scout status` / `probe` 核验；远端节点以 Nexus 返回的节点/设备事实为准，不用当前机 CLI 状态推断远端。新记录流程需要执行 Scout 支持 `record_api_version=1`，缺能力时按节点升级流程处理。
1. **应用清单（MCP）**：`repo_apps_get(project_id)`；应用不在清单或 `revision` 落后刚 push 的提交 → `repo-config` §3。无 `repo_url` → `onboarding` 门禁 4 绑仓（`project_script_repo_set`），不要新建无关远程仓。  
2. 选设备：调 `device_list`（带 `app_id`、`env_profile`，用例指定了渠道就带 `env_surface`），拿到**当前账号名下**的设备实时列表，不要复用旧结果。看这几个字段：

   | 字段 | 含义 |
   |---|---|
   | `status` | `online` / `offline` |
   | `executable` | `true` 才是现在能立即用；以它为准 |
   | `busy_task_id` | 非空表示被这个任务占用，空串表示空闲 |
   | `blocking_code` / `blocked_reason` | 不能用的原因，如 `busy`、`node_offline`、`channel_offline`、`app_incompatible`、`capability_missing`、`not_owned`、`unclaimed` |
   | `platform` / `model` / `node_name` | 用来和用例要求的平台匹配、向用户说明 |

   规则：只选 `executable=true` 且平台和用例一致的设备；有多台就列给用户或按用户指定的选；web 设备不会被独占：Web 容量以当前服务返回的 lane 总数/空闲数和 executable/blocking_code 为准，不硬编码 4 个槽位，也不把 busy_task_id 为空当作一定可派；`web_parallel_full` 表示当前容量已满；全部 `busy` 就告诉用户谁占着（`busy_task_id`），**不要抢占、不要硬跑**；设备被隔离（`isolation`）时先按 §2 的隔离流程处理。设备是否空闲只由 Nexus 给出，Scout 不会替你判断。
3. **先装齐这次要用的渠道程序，再开跑（MCP）。** `scout_list` 找 `node_id`，`plugin_status(node_id)`。只补本次平台缺的：

   | 这次要跑 | 缺了才装 | 调用 |
   |---|---|---|
   | Web | Chromium | `node_channel_program(node_id, tool_id=chromium, action=install)` |
   | iOS | Appium | `node_channel_program(node_id, tool_id=appium, action=install)` |
   | Android 需要键盘输入 | ADB Keyboard | `node_channel_program(node_id, tool_id=adb.keyboard, action=install)` |

   `operation_id` 自定并记住；装完再用 `plugin_status` 确认。没装完不要 `case_run`。不要安装未列出的插件。
4. `case_run` 传 `script_targets`。`case_list` / `requirement_list` 只返回需求元数据与链接；脚本在 `tests/<需求ID>/<用例ID>.py`。`case_ids=[]` 只代表该目录下现有脚本全集，执行“所有用例”前必须先按上面的 coverage 门禁确认没有原文缺项。

   ```text
   case_run(
     app_id, sn, revision=<已 push 的 sha>,
     script_targets=[{requirement_id, case_ids}]
   )
   ```

   `case_ids` 为空表示该需求目录下全部脚本。未登记需求先 `requirement_save`。Nexus 不拉仓；Scout 用本机 git 凭据拉。
5. 记录返回的 task_id、case/session/attempt 与原执行 node_id，轮询 `task_get`，间隔 ≥5s。Scout 接单 `accepted`、Nexus queued/running 都不是测试通过。同一 attempt 重复投递不执行第二次；修改脚本后的受控重跑是新 attempt，不能覆盖前次证据。
6. 证据用 `session_events`，按返回的 `next_seq` 继续读取，不能只看第一页。截图用 `session_screenshot`；大节点树/原文快照可能在 JSON artifact 中，使用 `session_artifact` 按 offset/length 分段读取并核对 MIME、长度、哈希。RPC `record.*` 是 Nexus 与 Scout 之间的内部契约，不假设它们是已安装的 MCP 工具。

| `task_get.status` | 动作 |
|---|---|
| `queued` | 等 5s 再查；不重复 `case_run` |
| `running` | 可读事件；不打断、不改脚本 |
| `pass` | 汇报通过 |
| `fail` | 先看回执 `disposition`，再按归属处理；不要把所有失败都重跑 |
| `blocked` | 区分缺信息、无有效断言、节点断线或资源隔离；依据 reason_code 处理 |
| `cancelled` | 报告取消；不擅自重跑 |

任务级只有这几种状态。Scout 的 `declined` / `skipped` 在任务级聚合为 `fail`，区分在 `cases[].status`：

| `cases[].status` | 怎么说 |
|---|---|
| `declined` | “Scout 拒绝执行”，附 `reason_code`；不说环境故障 |
| `skipped` | “未执行”，说明前置条件 |
| `fail` | 失败，给失败的 do/check 标题 |
| `blocked` | 阻塞，说明等人还是等资源 |

禁止并发对同一 `case_id + sn` 重复运行、因 ACK 丢失创建新任务、或看到 fail 就盲目重跑。先读证据；脚本修复后在已授权范围内创建新 attempt，并说明改动及恢复到的前置。

取消请求只是 `cancel_requested`；等执行进程确实停止才报告 cancelled。即使 cancelled，`resource_isolated=true` / `execution_started=unknown` 仍表示最后写入结果需要核验。

## 2. 读结果

- `task_get`：`status`、`cases[]`、`pass_rate`、`resource_isolated`；
- `session_record`：实时摘要及封存的 `test_report`。内容分析直接读摘要与事件，不要求打开 Workbench 或截图报告页面；页面截图只用于排版验收。截图证据仅在原文需要视觉验证或现有结构化证据不足时按需读取。
- `session_events`：新记录返回 items（seq/ts/type/payload）、next_seq、high_watermark、has_more、sealed。`node/enter` / `node/leave` 对应作用域；动作有 `tool/call` / `tool/result`；有效断言是 `assertion/result`。按 source_ref/source_hash/step_id/observation_id 关联原文和证据，截图用 artifact_id。字段以实际返回为准，保留旧会话兼容。
- `run/snapshot` 保存本次从 `CASE_SOURCE` 指定位置读取的原文快照（兼容旧 YAML）、配置的脱敏快照与文件哈希。归因使用本次 snapshot，不拿后来修改的仓库内容替代历史原文。
- 执行 Scout 离线时，Nexus 可能仍显示最后同步结论；详情返回暂不可用。明确说明原节点和最后同步时间，不把空响应当作“没有错误”，不把离线当作测试失败，也不改用另一节点的记录。

需要特别处理的 `reason_code`：

| `reason_code` | 怎么办 |
|---|---|
| `locator_missing` / `control_unknown` | 改 `pages/<APP_KEY>/*.yaml`；脚本问题，不是产品缺陷 |
| `method_unknown` | 方法名写错，报错里有最相近的名字；改脚本 |
| `config_missing` | 脚本仓库的 `config.yaml` 缺这个应用或这个环境，见 `repo-config` |
| `app_not_in_repo_config` | Nexus 里没有同步这个应用，见 `repo-config` §3 |
| `otp_requires_human` | 账号无自带码，且 Nexus 项目环境配置没有可用的 fixed/Gmail 策略；先检查 `resource_env_get`，由 `resource_env_set` 修正策略后重跑，不要把验证码策略写进脚本仓 |
| `vlm_failed` | 视觉判定未通过，看 `script/note` 和截图，再判断是产品问题还是判定词问题 |
| `revision_missing` | Scout 在仓库里取不到这个提交：确认已 push；不要回退到分支最新 |
| `repo_unavailable` | 设备所在电脑拉不到仓库：本机没有 git，或没有该仓库的 git 凭据；让用户处理那台电脑 |
| `script_missing` / `script_ambiguous` | 仓库里找不到或有多份 `tests/**/<case_id>.py` |
| `assertion_missing` / `check_empty` | 记录存在，但没有完成有效预期验证；补注册断言，探路采集不得计入通过 |
| `source_read_failed` | 核对 CASE_SOURCE 的飞书链接、工作表、范围、稳定用例 ID、列位置及原执行 Scout 的飞书授权；不得退回历史原文冒充本次读取成功 |
| `source_coverage_missing` | 对照 snapshot.source_ref 补缺失实现；不删除原文预期消除错误 |
| `node_disconnected` / `scout_restarted` / `worker_interrupted` | 读取最后持久记录，确认执行边界；不自动重放 |
| `record_not_found` / `evidence_temporarily_unavailable` | 区分记录不存在与原 Scout 离线；不输出通过结论 |
| `write_outcome_unknown` | 保持隔离，先获取可确认的停止与设备状态证据 |

回执里的 `disposition` 决定下一步，不再把根因一律留成未确认：

| `disposition` | Agent 怎么做 |
|---|---|
| `script_repair` | 只改定位或脚本，静态检查后 push，用新的正式 `case_run` 只跑这些 `case_id`。不改原文预期，也不把它写成产品缺陷 |
| `bug` | 需求或设计稿要求的文案、要求的界面位置，或实际功能错误。保持失败，不改用例来掩盖。用 `agent_workflow_finding` 保存编辑中的草稿，不向外部缺陷系统提交 |
| `accepted_difference` | Agent 编写的用例和实际界面有小差异，且不是被要求的文案或位置。告诉用户差异，改用例和脚本，完成 authoring 后再正式跑这几条 |
| `product_mismatch` | 尚未分成 bug 或可接受差异。先看原文和设计稿是否要求了文案或位置，再改记为上面两类，不要直接停成产品缺陷 |
| `source_repair` | 按 `source_ref` 把操作和预期对齐。页面打开、登录通过不能充当另一条业务预期 |
| `precondition` | 能在界面里建立的，`agent_workflow_finish` 传 `disposition=precondition_creatable`，走准备任务；准备完成后再正式跑这几条。原文要的是历史样本时传 `precondition_historical` 并向用户求助，不能现造 |
| `build_mismatch` | 本次 `tested_build` 与 `case_run.expected_build` 不一致，或还没读到版本。有本地安装包就 `app.install` 后再 `version()`；没有包路径就求助。不要写成产品失败 |
| `excluded` | 核对为什么没执行。缺前置不要记成跳过 |
| `unconfirmed` | 先读封存记录里的 `test_report.attribution` 和断言。没有新事实不重跑 |
| `verified` | 封存证据有效，继续下一条 |

需求指定了构建时，`case_run` 传 `expected_build`。正式脚本在业务断言前调用 `app.version()`。Scout 写入 `tested_build`，并在与 `expected_build` 不一致或未读取时把这次执行收成 `build_mismatch`，不保留原先的通过。渠道不支持读版本时不能补写版本号。

界面外的预期在对应 `source_ref` 的 `check` 里调用 `case.nexus.fact(actual, expected)`。`actual is None` 是前置不足，不是产品失败。不要用 `on_page` 代替这条事实。

正式回执出来后，用同一 `workflow_id` 对这条用例 `agent_workflow_finish`，`stage=verification`，带上 Scout 的 `task_id` 和回执里的 `disposition`。`precondition` 要分成 `precondition_creatable` 或 `precondition_historical`。之后只从 `coverage.next_units` 取下一批正式用例。`script_repair` 和 `accepted_difference` 先改脚本或用例并完成一轮 authoring，才会出现在 `script_rerun` 和 `next_units`。`bug`、`precondition_historical`、`build_mismatch` 不要再放进 `case_run`。缺陷草稿用 `agent_workflow_finding` 保持 editing，把步骤、对应用例、预期、实际和截图证据写全，并在对话里原样给用户看；不要向外部缺陷系统提交。需求或设计稿要求的文案和界面位置记 `strict=true` 且 `kind=bug`。

需求可以结束的条件是 `coverage.testing_closed=true`。`all_verified=true` 仍表示全部正式通过。`testing_closed` 且未全部通过时，按 `disposition_counts` 报告通过、产品不符、待改脚本、可准备前置、历史样本、构建不符和未执行，不能合成一句「有缺口」。

其余按返回的 `summary` 原样转述。脚本问题改完要回到 `write-test-cases` 和 `check-test-cases`，重新 push 再跑。

### 隔离

`resource_isolated=true` 时保留隔离。取消受理、任务终态、节点重启、租约到期均不代表资源自动可用；后台恢复也必须取得原 Scout 的停止证据，不能建议等待 TTL 后硬跑或抢占。

- 先读取任务及 `task_write_safety`（以实际 MCP 工具名/返回为准）。只有用户要求恢复该任务资源时，才对本人已结束的 Web 任务调用 `task_resource_reconcile`；由原 Scout 核验执行停止与浏览器关闭，Nexus 按记录版本和租约代次原子释放资源及账号。
- `stop_evidence_required` 保留隔离并补停止证据；`evidence_temporarily_unavailable` 恢复原 Scout 连接后再核验；`resource_resolution_conflict` 重新读取当前版本；`resource_baseline_required` 走基线核验，不能把非 Web 任务送入 Web 释放接口。历史写结果未知时，仅在服务明确提供复核能力且用户明确要求恢复资源后调用 `task_write_safety_baseline`，不重放原写动作。
- 如实展示返回的 `reason_code`、`message`、`reason_detail` 和 HTTP 状态。请求成功、一次截图或 `resource_isolated=false` 不单独证明账号租约已经释放；应核对 `isolation_exit.committed=true` 及释放清单，再读取最新资源状态。响应缺少退出回执、请求失败或结果未知时，报告释放尚未确认，不自动重发或改请求 ID 绕过。

恢复动作不改变历史断言结论，也不证明业务复位或允许复跑；未确认释放时明确报告仍按隔离处理。

## 3. 在对话里怎么汇报

先读 `task_get.statistics` 并给测试结论：本次用例执行次数（多设备分别计）、实际通过/失败/阻塞/未执行数及原文预期的通过/未通过/未核验/未执行。新摘要 `test_report` 是 Scout 从本次事实生成的业务索引；其中 suspected_product 是有待归因的业务差异，不能说成已确认产品缺陷。断言总数包含页面身份及辅助检查，不能当作通过用例数或预期数。

具体问题逐项写「原文引用与要求 → 实际执行的判定 → 实际观察 → 判定与归因依据 → 证据」。`source_ref` 相同但判定内容不符时标为映射问题，不能把登录通过算作模板等业务预期通过；不调用模型给错误映射补一个肯定结论。单列自动化问题、环境阻塞、原文差异、未验证项。定位、等待、模型请求和编写修复只放诊断，不混入业务问题。带上阶段、环境、原执行 Scout、revision 和 attempt；编写探路不计作正式回归。优先使用服务返回的 Workbench report_url，不猜链接。

模型消耗分别汇报 LLM/VLM 次数、模型耗时和服务返回的 token；缺用量标明未报告。只有完整记录或封存索引才能统计完整范围，读取一页事件只能说明当前已读取部分。

规则：

- 使用封存的 `test_report` 给本次摘要结论；证据离线时说明保留的是索引，不能宣称已重新读取完整证据；部分事件不代表完整范围；
- 不把 `blocked` 说成 `failed`，不把 `declined` 说成环境故障；
- 归因是你的判断，说明依据，不确定就说不确定。

## 数据缺口与阶段收敛

多轮调试使用 [Agent 进度与预算](../mino/references/workflow-ledger.md) 的 Nexus MCP 记录：每轮先 agent_workflow_start、结束后 agent_workflow_finish，allowed=false 时按具体原因收敛；普通 task_get 轮询不算新调查。agent_workflow_get 分列分析、脚本、准备和验证，不能拿 Agent 阶段状态替代 Scout 的测试断言。

缺数据后由 Agent 使用账号数据记忆和当前 Scout 观察选择复用、构造或替代；缺标签/记忆不证明缺数据，不反复申请账号等待匹配。脚本只返回具体缺口并执行明确操作，不在 flows 内自动补数。未知创建结果先查询同一任务；没有新观察不重跑相同阻塞。继续推进独立用例，并分别报告分析、脚本、数据准备及正式验证的完成度。

正式统计只汇总 verification/regression；authoring 探针的执行失败和主动结束保留为诊断。引用明确 task_id/session_id/attempt_id/revision、原文预期结果及记录起止时间；重跑结果不覆盖历史 attempt，不按自由文本或“最新”称呼拼接不同任务。


数据准备闭环（只由 Agent 决策）：

1. 调用 `resource_account_select`，传 `project_id/env/app_id/data_requirements`；无记忆匹配仍返回候选。按登录身份与环境选账号，资产记录只作线索，不做库存盘点。
2. `case_run.case_inputs` 按用例 ID 或脚本路径传 `account_id`、模型等业务对象。脚本 `case.data.require` 缺输入返回 `data_missing`；从 `task_get.cases[].data_missing` 读取具体缺口。
3. 依据本次观察和授权选择明确准备脚本。通过 `case_run` 新建任务，`source_context={parent_task_id:原任务, purpose:"prepare", data_need:描述}`，`case_inputs` 固定相同账号。Nexus 不决定造数动作。
4. 读取准备任务 `cases[].data_outputs`，核对对象引用和账号、实际操作及断言。未通过也可能保留已产生对象，不能仅看输出就声称准备通过；写入结果未知先查同一 attempt。
5. 调用 `resource_account_data_save` 保存已确认对象，`source_task_id` 指向准备任务。使用新 `client_request_id` 再跑原用例，`purpose:"resume"` 指向原任务，传相同 `account_id` 和对象。续跑从脚本起点执行，不恢复旧 UI 句柄，也不覆盖原任务结论。
6. 每轮明确准备目标与预算；同一缺口且无新证据不重复申请或整例重跑。可据新证据调整明确操作，预算耗尽则交付具体缺口及下一步，推进独立用例。准备任务不进入正式通过/失败统计，原用例仍须真实断言和原文覆盖。

## 统计与报告一致性

`statistics.formal/authoring/preparation/unclassified` 分列，正式通过率只取 formal.pass_rate；无有效判定为 null，不写 0% 或 100%。拒绝、阻塞、跳过、取消、未核验分别列出；completed 是已结束，executed 才是有事实证明的脚本执行。execution_started=no 只说明未确认设备写动作，不能因此称整条脚本未执行。

用例执行次数、statistics.expectations 原文预期数、statistics.assertions 全部断言数、auxiliary_assertions 辅助断言数不能互相替换。检查 cases_reported/cases_missing，摘要不完整时说明缺失范围。申请范围 requested_total、已选执行 total 和原文用例总数单独表述。

每个结论绑定同一 task/session/attempt、revision、source_hash 和记录时间。准备与续跑分别列任务，不合并成原任务通过；历史局部预期单列 task/账号/版本，不能写进“本次已通过”。为过程描述明确指定任务，禁止把较早生成过程称作最新探针过程。

时间使用 statistics.timing 中的带时区记录，缺失写未提供。submitted_at 是提交时间，执行时间来自实际记录，状态同步时间不能当开始/结束。报告生成时间与执行时间分列；“最新”依据实际记录时间和任务身份，不从任务 ID、文件更新时间或当前 HEAD 推测。使用 result_status 判断正式结果，纯准备或探针 done 只表示该任务结束。
