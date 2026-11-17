# 更新记录

每个版本写清需要的 Scout / Nexus 版本。技能说的和实际对不上时，先核对这里。

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
