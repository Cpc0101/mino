## 0.1.30 · 2026-11-28

- 测试文件放在本机 Scout 库，生成、复用和用例执行分开。
- 正式回执按归属决定下一次只跑该跑的用例；需求收口看 testing_closed 和分类计数。
- 需求或设计稿要求的文案和位置记为缺陷草稿，只在 Mino 中编辑查看，不向外部提交。其余小差异改用例后再测。
- 配套 MinoScout 0.1.177、MinoNexus 0.1.151、MinoWorkbench 0.0.82；安装后新会话加载。

## 0.1.29 · 2026-11-27

- 区分会话、执行片段及当前/历史请求，按原请求时钟和停止证据续接。
- 账号槽位与执行身份一致，认证前置检查业务响应，登录与兴趣引导分别判断。
- OTP 原请求进度只读，禁止并行取码；显式输入与 request 隔离输出避免跨会话覆盖。
- 配套 MinoScout 0.1.176、MinoNexus 0.1.148、MinoWorkbench 0.0.80；安装后新会话加载。

## 0.1.28 · 2026-11-27

- 明确取消、重启与租约到期不能代替停止证明；按原 Scout 停止证据与 Nexus 原子退出回执判断资源释放。
- 恢复错误保留原因码与细节；未知历史写结果走显式复核，不让用户等待 TTL 硬重试。

# 更新记录

每个版本写清需要的 Scout / Nexus 版本。技能说的和实际对不上时，先核对这里。

## 0.1.27

- 按当前用户测试意图启用工作流：产品开发、审查、部署、域名/TLS 运维和普通对话不自动创建测试看板。
- 控制面诊断保留 MCP 路由，但只读调用不绑定新业务测试。
- Codex UI guard 改为显式会话级开关，默认不阻断，结束/切换任务后关闭；失效标记不影响普通会话。

技能与持久路由更新后需新开会话加载。

## 0.1.26

- 测试看板先发送后执行：显式声明 startup_delivered，测试和工作流入口校验业务任务绑定；跨上下文保持原 task_id。
- 上报阶段、范围、环境、当前业务动作和下一步；独立 MCP 调用移入诊断，不覆盖业务动作及待回答状态。
- 源用例未关联或未锁定禁止 debug_execute/正式执行；先补写发布回读锁定。

需要 MinoNexus `0.1.134`、MinoWorkbench `0.0.73`；技能更新后需新开会话加载。发送声明不证明用户已读。

## 0.1.25

- 来源补写：来源确实为空时先 `agent_workflow_bootstrap` 登记，`agent_workflow_draft` 记录当前动作与原文未明确的问题；补写人工用例并通过已配置文档工具发布、回读后，再用 `agent_workflow_init` 锁定来源。读取失败不是空表。
- 交互与上下文：每批读取 `help_requests.answer` 与 `contexts`，人工答案只作调查依据，不是原文变更或通过证据。
- 报告：`agent_workflow_report(final=true)` 封存交付快照；成功、失败、阻塞、取消、预算耗尽都要先结束活跃调查再交付，`delivered_with_gaps` 不等于通过。
- Agent 运行看板：多步任务先 `agent_task_start` 登记，后续 Mino 工具带 `agent_task_id`；本地不可见动作显式 `agent_task_event`，缺数据用 `agent_task_question`，心跳不冒充进展；60 秒无心跳显示 unknown。
- 终态门禁：关联工作流的外部 Agent 任务必须先封存最终报告才能结束；补充证据会生成新回执 ID，续接仅确认原问题，不吞掉新问题。
- 可见交付完整性：多步任务先 `agent_task_start`，立即把 `startup_message` 与 `board_url` 发到可见对话；回执完整输出 `case_receipts[].text`；结束时交付六章报告、报告 ID 与看板链接。
- 告警、暂停与批次准入：群聊系统告警是环境观测，不归因、不解释根因；用户暂停某需求后不再执行该需求；批量执行前先给可执行/阻塞清单和耗时预估。

需要 MinoNexus `0.1.132`、MinoScout `0.1.169`；技能更新后需新开会话加载。

## 0.1.24

- 正式 `case_run` 增加 workflow 绑定门禁：带 `script_targets` 时必须传 `workflow_id`，且项目、`case_source_read` 收据、范围锁定与 `expected_units` 一致；`workflow_not_found` / `workflow_scope_unlocked` / `workflow_source_unverified` / `case_not_in_workflow_scope` 都是配置错误，不得绕过。
- `task_get.observability.active_cases` 增加 `started_at`、`elapsed_ms`、`step`、`waiting_on`、`last_evidence`、`heartbeat_due_sec` 等字段；技能要求每 60 秒输出固定格式心跳，终态逐条带 `receipt_id`。
- 禁止脚本硬编码邮箱、手机号、`password=` 等账号字面量；Nexus 静态检查与 Scout 运行时都会以 `hardcoded_account_literal` / `hardcoded_account` 拦截，debug 同样生效。仅允许同行 `# account-literal-ok:` 豁免。
- 飞书来源查询固定阶梯：wiki 节点 → 文档/表格正文 → `im +chat-search --query` 找群后读消息；权限拒绝或范围截断保存原始失败，不用截图替代。
- 新账号 0→1 与老账号历史基线分开建立结论，缺历史样本时求助而不是重置老账号。

需要 MinoNexus `0.1.127`、MinoScout `0.1.168`；技能更新后需新开会话加载。

## 0.1.23

- 测试质量门禁：正式通过必须绑定 Scout 原文覆盖、断言和执行身份；准备、探针与正式验证分开，不以动作成功替代测试通过。
- 累计调查时间预算与结构化求助，缺口先核对可追溯来源，不编造账号，不擅改原文预期；区分新账号初态和历史账号基线。
- 每条用例结束即时输出可见回执，去重关联 task/session/attempt/revision；未确认客户端展示时不得宣称已送达。
- 工作流范围以服务端成功的 case_source_read 回执为准，正式验证完成须核对同项目、同身份的真实任务证据。

需要 MinoNexus `0.1.120`，沿用 MinoScout `0.1.167`；本版不发布 Scout 或 Workbench。技能更新后需新开会话加载。

## 0.1.22

- “写所有用例”“继续测试”“跑全部用例”增加全集门禁：先从飞书 CLI 或其他原文机器读取完整用例 ID，再把同一清单作为 `agent_workflow_init.expected_units` 锁定；禁止用当前 `tests/` 文件反推全集，禁止用 Computer Use 或浏览器截图代替飞书 CLI 正文读取。`case_run.script_targets[].case_ids=[]` 只表示当前需求目录脚本全集，不表示原文用例全集。
- Nexus `agent.workflow.init` 现在要求 `source`；`units` 必须是 `expected_units` 的子集，省略时默认声明全集。默认总预算至少为 `expected_units × 4`，42 条用例即至少 168 轮，既有工作流迁移时自动扩展到完整范围的最低预算。
- `agent_workflow_get/start/finish` 返回机器可读的 `coverage`，含 `missing`、`verification_missing`、`blocked_units`、`next_units`、`implemented`、`path_validated`、`formal_verified`、`implementation_complete`、`verification_complete`、`all_implemented` 和 `all_verified`。`implementation_complete`/`verification_complete` 表示当前阶段已无未处理项但仍可能含终态阻塞；只有 `all_implemented=true` 才能说脚本全集写齐，只有 `all_verified=true` 才能说正式全集通过。`complete` 保留为 `implementation_complete` 的兼容别名。每批 5–10 条后从 `coverage.next_units` 自动续跑；只有当前交付阶段完成、剩余条目均有明确阻塞/失败/延期结论、需要用户输入、Scout 不可用或预算耗尽才能停。
- `mino-scout check` 只证明现有脚本静态合格，不证明全集覆盖；交付前必须同时核对 `coverage.missing`、静态检查和 Scout 正式证据。
- 新增可撤销的 Codex `PreToolUse` guard：阻断 `cua_repl`、屏幕捕获，以及 `node_repl` 中夹带的 Playwright/Puppeteer/Selenium 等浏览器自动化；普通 JS 计算和文件处理保留。预检把 guard 状态列入 `codex_guard`，未安装/过期时只生成确认动作；不会静默写入用户目录。安装后需新开会话并在 `/hooks` 中审查、信任用户级 hook，否则 Codex 会跳过。guard 是本地 guardrail，不撤销插件暴露，也不等同于管理员级 `requirements.toml` 强制禁用。

需要 MinoNexus `0.1.117`。本版不要求重新打包 MinoScout 或 MinoWorkbench；技能及路由更新后需新开会话加载。

## 0.1.21

- 本机编写通过保留现场的 debug_case 分段观察、验证定位和刷新 pages/flows；远端 Scout 仅执行正式用例。
- 编写与执行工作区分开，输出和证据按任务/attempt 保存；正式源码副本保留。
- debug_case_checkpoint 固定草稿、完整实现和路径验证阶段，绑定实际代码版本与执行证据；case_run.debug_origin 关联固定 commit，并在设备动作前核对版本。
- 调试取消、重置与结束分别管理，未知写仅允许读取核验；片段成功不计正式通过率。
- 更新 Agent 流程和路由模板：先观察、再实现，再从独立初始状态正式执行。

需要 MinoScout `0.1.154`、MinoNexus `0.1.89`、MinoWorkbench `0.0.60`。技能及路由更新后，新开会话加载。

## 0.1.20

- 缺数据的查找、构造和续跑决策只归 Agent；账号标签和对象台账辅助选数，缺记录不阻塞执行。
- 用例使用运行时数据绑定和动态对象定位；应用 flows 复用 Scout SDK 阶段观察、有限等待和对象验证，明确生成模板随 Scout 分发。
- Agent 四阶段进度和调查预算通过 Nexus MCP agent_workflow_* 保存到服务端数据库；移除技能仓新增的三个 Python 执行脚本及本地进度数据库。
- 探针、准备和正式验证分开统计，报告绑定原 task/session/attempt/revision 和带时区时间，后续成功不覆盖旧任务。

需要 MinoScout `0.1.153`、MinoNexus `0.1.88`、MinoWorkbench `0.0.59`。技能更新后需要新开会话加载。

## 0.1.19

- Mino 启动预检升级到 schema 3：需要本机变更时返回 `consent_required=true` 和逐项 `consent_actions`，包含稳定的 `id`、中文问题、影响、可执行命令、是否需新会话及服务中断标记；预检本身仍严格只读。
- Skill 更新不再要求用户复制 clone / `rm` / `cp` 命令。用户确认后由 Agent 直接运行新增的 `install_skills.py`：校验 GitHub 源 `VERSION`、复制真实目录、拒绝软链、保留第三方技能，并在中途失败时整体回滚。
- 本机缺少 Scout 时新增 `install_scout` 确认动作。用户同意后再进入 `onboarding`，通过 Mino MCP `scout_install_token` 获取一次性本机安装请求；不得提前申请 token 或在对话中暴露凭证。
- Codex Skill 根目录和 `AGENTS.md` 路由目标都优先遵循 `$CODEX_HOME`，未设置时回退 `~/.codex`。路由仍只替换 Mino 托管标记区间，不覆盖用户其他规则。
- 最新 Skill 版本优先读取 GitHub Contents API，失败时回退 raw，降低分支刚发布时 CDN 旧缓存造成的误判；Scout 更新仍只使用预检返回的固定 `build_id` / `release_tag`。

需要 MinoScout `0.1.152`、MinoNexus `0.1.87`。本版仅更新 Skill 与其更新预检，不要求重新打包 Scout、Nexus 或 Workbench。

## 0.1.18

- 将技能版本检查、安装文档与示例地址切换到迁移后的正式仓 `https://github.com/Cpc0101/mino.git`。旧仓库路径的 raw 内容仍有独立 CDN 缓存，会继续返回 `0.1.16`，正式地址已返回新版本；启动预检不再依赖旧路径。
- 本版仅修复 Skill 发布源地址，继续要求 MinoScout `0.1.152`、MinoNexus `0.1.87`，不要求 MinoWorkbench 升级。

## 0.1.17

- 修复 `mino` 启动更新预检在部分 Python 环境中因系统根证书缺失导致的 `SSL: CERTIFICATE_VERIFY_FAILED`。检查器现在优先使用 `certifi` CA，无法通过 urllib 获取时再用系统 `curl` 兜底；联网成功时不再把 Skill 状态误报为 `unknown`。
- 本版仅为 Skill 更新检查修复，继续要求 MinoScout `0.1.152`、MinoNexus `0.1.87`，不要求 MinoWorkbench 升级。

## 0.1.16

- 新增 `mino` 统一入口技能：Nexus 控制面只走 Mino MCP，本机 Scout 只走 `mino-scout`，被测 Android / iOS / Web / 桌面软件和页面操作必须写成用例脚本并经 `case_run` 交给 Scout；不得因为平台提供 Computer Use 而静默换工具。
- 新增经用户确认的 `AGENTS.md` 持久路由托管块：Skill/MCP 作为软引导，跨会话路由写入 `~/.codex/AGENTS.md`；安装器可幂等检查、应用、移除，只改自己的标记区间。
- 新会话首次进入 Mino 工作流时，先运行 `scripts/check_updates.py` 只读比较本地 Skill、`mino-scout update-check` 与路由策略，再处理更新和持久路由，最后调用 `agent_guide` 进入业务；输出 `overall_state` / `check_complete` / `unknown_checks`，未知不再被误读为已最新。Skill 更新后需新会话生效；Scout 更新必须使用固定构建并向用户说明中断影响。
- `update-skills` 覆盖 Codex、Cursor、Claude等(如有)，动态复制 `skills/*/`，禁止软链。

需要 MinoScout `0.1.152`、MinoNexus `0.1.87`。本次不要求 MinoWorkbench 升级。

## 0.1.15

- 用例编写与自检说明对齐确定性断言、原生节点和本地 OCR；模型调用须明确声明策略与预算，断言和原文映射保存在用例自己的文件中。
- 新增断言与模型使用参考，明确元素、文本、视觉断言的选择以及无有效断言、模型无结果的阻塞语义。
- 执行汇报使用业务报告与原始证据，保留失败、阻塞和资源隔离状态。

需要 MinoScout `0.1.151`、MinoNexus `0.1.86`、MinoWorkbench `0.0.58`。

## 0.1.14

- 把单文件业务归属规则并入 `mino-scout check`。仓库中每条用例必须由自己的文件直接承载 `prep/do/check`、原文映射、业务断言和阻塞路径；共享 `flows/`、`scripts/` 只能提供机制或纯计算，不能接收整个 `case`、按用例编号分派、调用 `case.nexus.*` 业务事件或写业务断言。
- `case_isolation` 现在是 `mino-scout check` 的 finding 类型，并与语法、导入、config、pages、原文映射和断言检查使用同一套英文输出、warning 语义和退出码；不再安装或调用独立的 `check_case_isolation.py`。
- `check-test-cases` 与 `write-test-cases` 都只要求运行 `mino-scout check --require-cases .`，不再描述“两层检查”或“任意 Python 环境检查器”。该命令需要已安装的 MinoScout CLI，不能脱离 Scout 运行时单独执行用例。
- 新用例不再创建同名原文 YAML；`CASE_SOURCE` 是唯一的新脚本原文来源。旧 YAML 仅为已有仓库运行时兼容。
- 增加脚本仓 push 强制门禁：`mino-scout check --require-cases .` 的 `error` 和可操作 `warning` 会以非零退出码阻止 push；`source_remote/info` 是每条 `CASE_SOURCE` 固定的静态边界提示，不再是待解决问题，也不会因运行成功而消失。真实原文映射、页面定位、断言和设备行为仍由 `case_run` 单独核验。

需要 MinoScout `0.1.150`。本次不要求 MinoNexus 或 MinoWorkbench 升级。

## 0.1.13

- `write-test-cases` 新增 Web 分辨率用例配置：`case.init(case.config.<KEY>, web_resolution="2K")`，默认 `1080P`，支持 `720P`、`1080P`/`1K`、`2K`、`3K/4K`。分辨率是具体用例配置，不是跑批参数；一个分辨率一份用例，定位、坐标、显隐和断言按该视口分别维护。
- `write-test-cases` / `check-test-cases` 对齐 `case.init` 的唯一额外关键字 `web_resolution`，并覆盖 1280×720、1920×1080、2560×1440、3840×2160 四档视口。
- Web 的 `app.screenshot()` 默认 `full_page=True`，截取完整文档；仅明确需要当前视口时传 `full_page=False`。
- Nexus 读取 Web 截图时区分完整文档尺寸与交互视口，避免 full-page 图片高度影响坐标和定位判断。

需要 MinoScout `0.1.145`、MinoNexus `0.1.84`。本次不要求 MinoWorkbench 升级。

## 0.1.12

- 新增 `analyze-test-case`：保留原文版本与 P/S/E 编号，先厘清输入、前置、动作、预期、未知项，再由 Agent 编写普通 Python；不新增强制测试 DSL。
- 用例同名 YAML 保存原文，`prep/do/check(source_ref=...)` 建立映射；静态映射、实际执行及有效断言分别核对，原文缺失与未覆盖不会冒充完成。
- Scout 将事件、截图、界面节点、原文快照、断言与文件哈希保存在账号隔离的本地执行目录。`script.submit` 先持久接单，独立进程执行，通过可重传、可确认的摘要同步完成。
- Nexus 的 Python / Cloudflare 启动方式采用同一记录协议：保存准入、归属、资源占用、路由及最后确认摘要，代理读取原 Scout 的详情；取消确认与资源隔离分开处理。
- Workbench 任务页按需读取事件和媒体，显示离线、过期、分页及同步状态；任务返回可直接打开的 `report_url`。
- 云端账号池接通，`case.nexus.account(requirements=..., prefer=...)` 区分硬条件与偏好。动态业务标签只参与选择，不能证明设备登录态或业务初态。
- 空校验、零断言、失败设备动作及陈旧截图判定不能产生正式通过；观测脚本可以保存证据，但结果为 blocked，后续补齐断言再交付。

需要 MinoScout `0.1.144`、MinoNexus `0.1.83`、MinoWorkbench `0.0.56`。

本批需配套更新 Scout、所用 Nexus 后端与 Workbench；旧节点保留同步执行兼容路径。验证包含隔离数据库、模拟协议节点、独立 worker 和浏览器场景；真实账号与真实设备仍需单独联调。

## 0.1.11

- **`update-skills` / README**：Cursor 安装改为从 GitHub **复制**到 `~/.cursor/skills/`；**明确禁止**软链到本机开发仓。

## 0.1.10

- **约束 agent**：`overview` 硬约束（先告知再动手、禁止擅自建远程仓、不把 `app_create` 当完成）。
- **MCP vs CLI**：本机 `mino-scout`（status / probe / check），云端 MCP。
- **`onboarding` 门禁**：注册 → MCP → **`scout_install_token` 申请安装命令 → 确认弹窗 → 本机安装**（禁止 Workbench 抄命令 / 用户粘贴）→ `project_create` / 绑仓 / sync（直接调 MCP，不写「没工具就去网页」绕路）→ 需求与用例关系说明；示例 key 用 `baidu_*`。
- **`repo-config` / `write-test-cases` / `run-test-cases` / `check-test-cases`**：对齐绑仓、CLI 探活、需求列表不含用例正文。

需要线上 MCP 含：`project_create`、`scout_install_token`（`POST /runtime/nodes/install-token`）、`project_script_repo_set`、`repo_apps_sync` / `get`、`app_delete` 等（与 Cloudflare README / HTTP 对齐）。

## 0.1.9

- `run-test-cases`：开跑前先 `plugin_status`，缺的渠道程序按需装完再 `case_run`。执行用 `script_targets`（需求 ID + 用例 ID），不从用例库取正文。
- `onboarding`：脚本仓库用 `project_script_repo_set`；需求用 `requirement_save`，`case_list` 返回需求链接。
- `update-skills`：更新改为在 mino 检出里 `git pull`，不把技能文件复制到本地技能目录。

需要已部署的 Cloudflare Nexus（含 `script_targets`、`requirement_list`、`project_script_repo_set`、`repo_apps_sync`）和 Scout 0.1.143（`script.list`）。

## 0.1.8

- `repo-config`：新增 §0「新增应用：先问齐再写」——加安卓 / iOS / Web 前必须问清项目环境与各环境 package / bundle_id / url；完成态是写 `config.yaml` + push + `repo_apps_sync`，**仅 `app_create` 不算完成**。
- `onboarding` 第四节补「先确认环境再加应用」；`overview` 路由表增加「加应用 / 配包名」指向 `repo-config`。

需要 Scout / Nexus 版本同 0.1.7（Scout 0.1.141、Nexus 0.1.80）。

## 0.1.7

- 脚本仓优先：`config.yaml` 只认应用 key，**不再要求 `app_id` / `project_id`**；`repo_apps_sync` 可不传 `app_id`，Nexus 按 key 对齐或自动创建应用。
- MCP 边界写清：只通信（查询、同步元数据、触发跑数），不写脚本；脚本由 agent 本机编写并 Git 推送。
- 固定验证码迁到脚本仓：可选 `otp.code`；不写则 `case.scout.otp` 报 `otp_requires_human`，向人要码。同步载荷禁止带 `otp`。
- 登录动作仍在 `flows/`；账号仍由 Nexus 号池租用。

需要 Scout 0.1.141、Nexus 0.1.80。

## 0.1.6

- 技能安装：把仓库地址交给 agent，按该 agent 惯用方式安装（技能在 `skills/`）。
- `overview`：说明 Nexus / Workbench / Scout 三端分工；用户电脑只装 Scout，本地状态在 `~/.mino/`。

需要已部署的 Cloudflare Nexus（`nexus.minocc.top`）与 Workbench Pages。

## 0.1.5

- `onboarding` / `overview` / `README`：默认使用线上 MCP 与 Workbench 地址。

需要已部署的 Cloudflare Nexus（`nexus.minocc.top`）与 Workbench Pages。

## 0.1.4

- 写用例先选定一台可执行设备。页面定位、点击、截图和界面结构都写在用例脚本里，由 `case_run` 交给 Scout 的 `script.run`。
- `locator_spec` 只从这次运行 `tool/result` 里 `capability_id=hierarchy` 的 `nodes` 或 `hierarchy_text` 抄。写完覆盖原文的脚本后，用同一台设备再跑一次调试。

需要 Scout 0.1.136、Nexus 0.1.78 把 `app.hierarchy()` 的 `nodes` / `hierarchy_text` 写入该次 `tool/result`。

## 0.1.3

- `run-test-cases` 只写通过 `case_run` 跑脚本仓。
- `overview` 里 Nexus 的职责与现在的派发方式一致：下发仓库、提交和设备，脚本在 Scout 执行。
- `onboarding`、`overview`、`README`：MCP 接入是浏览器里的 OAuth。配置只写 `<NEXUS>/mcp`。

需要 Scout 0.1.134、Nexus 0.1.76。

## 0.1.2

- `write-test-cases`：前置写成 `prep`，操作和预期至少各覆盖原文每一条，一条可以拆成 `2-1`、`2-2`；清理缓存用 `app.clear_cache()`。没有动作要做时也写一条 `prep`，标题说明为什么。
- `locator_spec` 只抄设备界面节点上的 `resource_id`、`text` 或 `content_desc`。没有节点就不写选择器，也不写对应的 `tap` / `input`。
- `check-test-cases`：`tests/` 下的用例必须有 `prep`，标题只写「无」不算。自检不证明选择器来自真机。
- `run-test-cases`：通过 `case_run` 跑项目脚本仓。

需要 Scout 0.1.134、Nexus 0.1.76。`prep` 的标题沿用现有步骤回调写入 Nexus。

## 0.1.1

首版，七个技能：`overview`、`onboarding`、`repo-config`、`write-test-cases`、`check-test-cases`、`run-test-cases`、`update-skills`。

需要的 Scout 和 Nexus 版本及变更：
- Scout 0.1.133 起、Nexus 0.1.75 起；
- `script.run` 改为下发 `repo_url` / `branch` / `revision`，Scout 自己拉仓库；
- `case.init(case.config.<KEY>)` 的 `app` / `case.scout` / `case.nexus` 写法，`case.nexus.do("标题")`；
- `mino-scout check`；
- MCP 工具 `repo_apps_sync`（差异更新）、`repo_apps_get`、`app_create`；`config.yaml` 每个应用带 `app_id`。
