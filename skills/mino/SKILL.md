---
name: mino
description: Mino 工作流统一入口。用户提到 Mino、Mino Scout/MCP、跑用例、连接测试设备，或要操作被测 Android、iOS、Web、桌面软件、浏览器页面、截图和界面结构时优先使用。先检查持久路由与更新，再强制经 Mino MCP 与 Mino Scout 执行。
---

# Mino 统一入口

测试任务先读[测试质量、缺口求助与逐条回执](references/execution-discipline.md)：缺口立即查证或问人，不编账号、不改原文预期；正式终态逐条在可见对话回执，调试/准备不计正式通过。

本技能只负责**选路和启动门禁**；具体编写、自检与执行分别转到对应技能。

## 强制路由

只要任务属于 Mino 的测试或 Mino 节点管理范围，按下面选路，不要按平台默认偏好换工具：

| 工作 | 唯一默认路径 |
|---|---|
| Nexus 项目、应用、需求、账号、设备、任务、记录 | **Mino MCP** |
| 飞书需求正文、用例表格与节点信息 | **Mino MCP `cli_query` 的 `feishu` CLI** |
| 本机 Scout 状态、探测、静态检查 | **`mino-scout` CLI** |
| 本机编写、观察与调试 | **Mino MCP `debug_case` → `debug_case_execute`** → 本机 Scout 保留现场 |
| 正式执行 Android / iOS / Web / 桌面用例 | 固定脚本版本 → **Mino MCP `case_run`** → 本机或远端 Scout |
| 被测页面截图、控件树、界面定位、点击和输入 | 用例脚本里的 Scout Case API，经调试会话或 `case_run` 留存证据 |

**禁止默认改用**平台 Computer Use、浏览器控制、Playwright、adb、Appium、WDA 或桌面自动化工具来代替 Scout。调用工具成功、Scout 接单或动作走通都不等于测试通过；只有目标断言和证据成立才算通过。

只有两种例外：

1. 用户明确指定使用其他工具；
2. 已检查 Mino MCP/Scout，确认不可用，并先向用户说明原因。

不能因为当前客户端同时提供 Computer Use，就静默切走。Mino 不可用时先走 `onboarding` 修复，而不是用别的 UI 工具继续同一测试。

## 每个新会话首次开始 Mino 工作流

1. **先运行只读更新预检，再做业务操作**：

```bash
python3 "<mino-skill-dir>/scripts/check_updates.py" --json
```

`<mino-skill-dir>` 是已安装的 `mino` 技能目录。预检会比较本地 Skill 的 `VERSION` 与本机 `mino-scout update-check`，并报告 `routing_policy` 与 `codex_guard`。读取顶层 `overall_state`；网络不可用时它是 `unknown` 且 `check_complete=false`，不把它说成“已是最新”，也不要因此编造版本。同一会话只做一次，避免每个业务请求重复联网。

2. **需要安装或更新时，先询问，再由 Agent 执行**：
   - `consent_required=true` 时，逐项读取 `consent_actions`，使用其中的 `question` 询问用户并说明 `impact`。不要要求用户手工复制命令、运行脚本或编辑 `AGENTS.md`；这是本机持久状态变更，必须由 Agent 在用户明确同意后执行。
   - 用户可以一次同意全部动作，也可以逐项同意。未同意的动作保留现状，不得报告为已安装或已更新；客户端弹出的系统权限确认与这里的业务确认是两道独立门禁。
   - Skill 有更新：同意后执行该动作的 `command`，安装器会从 GitHub 复制真实目录，并校验目标版本与禁止软链。当前客户端通常不能热加载，更新完成后停止业务并请用户新开会话再继续。
   - Scout 有更新：同意后只使用预检返回的固定 `build_id` / `release_tag`，由 Agent 执行更新；先说明会停止或替换本机 Scout、可能中断执行。不要使用 `latest`，不要丢失运行中任务或重放结果未知的写操作。
   - Scout 未安装：使用 `kind=install_scout` 的动作先询问用户。同意后按 `onboarding` 调用 MCP `scout_install_token`，只在本机执行匹配系统的安装请求；一次性凭证不要写入对话、日志或提交。未同意时不得申请凭证或安装。
   - 旧版 `mino-scout` 不支持 `update-check` 或本地 manifest 不可用时，可在 MCP 可用后调用 `scout_release_meta` 获取最新版本信息，再用 `mino-scout status` 比较；仍无法确认就保持 `unknown`。

3. **检查持久路由策略**（预检输出中的 `routing_policy` 也可直接使用）：

```bash
python3 "<mino-skill-dir>/scripts/install_routing_policy.py" --check
```

`state` 不是 `current` 时，向用户说明：Skill 与 MCP `initialize.instructions` 是软引导，平台仍可能优先选择 Computer Use；写入 `$CODEX_HOME/AGENTS.md`（未设置时为 `~/.codex/AGENTS.md`）的托管块才会成为跨会话持久规则。**取得用户确认后**再执行 `--apply`，由 Agent 完成写入，不得静默修改用户主目录，也不要让用户自己复制路径或命令。目标客户端若使用其他 `AGENTS.md` 路径，显式传 `--path`；遇到 `conflict` 就停下，不覆盖原文件。规则变更后通常需要新开会话才生效。

4. **检查 Codex UI guard**（预检输出中的 `codex_guard`）：本机若仍暴露 `cua_repl`、屏幕捕获或可执行浏览器自动化的 `node_repl`，必须把“提示优先 Mino”与“工具已被阻断”分开陈述。`state` 不是 `current` 时，说明它会阻断 Computer Use、屏幕捕获和 `node_repl` 中的 Playwright/Puppeteer 等浏览器自动化，同时保留普通 JS 与其他 hooks；取得用户确认后执行 `install_codex_guard.py --apply`。它是可撤销的 `PreToolUse` guardrail，不是完整 sandbox，也不能替代管理员 `requirements.toml`；hook 失败或特殊/hosted tool 路径仍可能绕过。变更后需新开 Codex 会话，并在 `/hooks` 中审查、信任该用户级 hook；未信任时 Codex 会跳过。

5. **调用 MCP `agent_guide`**，读取当前路由契约和工具列表；不要凭记忆猜工具。若 MCP 尚未配置，先转 `onboarding` 门禁完成接入，接入后再调用；不要因此改用其他工具。
6. 预检结果为 `current`、`unknown` 或本机未安装时，按实际结果继续判断当前任务需要 MCP、CLI 还是首次安装；`unknown` 必须如实说明。

> `0.1.15` 及更早版本还没有这个统一入口，无法由本技能自动完成首次预检。先按 `update-skills` 引导安装一次 `0.1.16+`，安装同样由 Agent 在用户确认后执行，不要求用户复制命令；再新开会话，之后才由启动门禁自动检查。

## 常用后续技能

需要多轮需求分析、脚本编写、数据准备或执行调试时，使用 [Agent 进度与预算](references/workflow-ledger.md) 中的 Nexus MCP 记录。先记录本轮目标和预算，按返回的 allowed/next 收敛调查；相同缺口无新证据不重复申请或重跑。Agent 决定调查和补数方式，Nexus 只保存进度；进度不替代测试结论。

| 目标 | 技能 |
|---|---|
| 系统分工、工具边界 | `overview` |
| 首次接入、安装 Scout | `onboarding` |
| 配置脚本仓和应用 | `repo-config` |
| 整理人工用例 | `analyze-test-case` |
| 写脚本 | `write-test-cases` |
| 静态自检 | `check-test-cases` |
| 执行与证据汇报 | `run-test-cases` |
| 更新技能 | `update-skills` |

## 执行纪律

- 用户要求“写所有用例”“继续测试”或“跑全部用例”时，必须先用 Mino MCP `cli_query` 的 `feishu` CLI（或其他原文来源 CLI）机器读取完整 ID 清单，再以 `expected_units` 初始化 Nexus workflow；禁止用 Computer Use、浏览器截图或手工抄页面代替正文读取。每批从 `coverage.next_units` 继续；只有 `all_implemented=true` 才能说脚本全集写齐，只有 `all_verified=true` 才能说正式全集通过。`implementation_complete`/`verification_complete` 仍可能包含 blocked_units，`complete` 只是前者的兼容别名。当前文件数不是全集，`case_ids=[]` 也只代表当前目录脚本，不得只跑/写几条就报告全部完成。
- MCP 工具名把点写成下划线，例如 `agent.guide` 是 `agent_guide`。
- 先查项目、应用、设备和渠道，再 `case_run`；参数缺失就问，不要猜。
- 编写工作区由本机 Agent 编辑；`debug_case` 直接绑定该目录，不拉仓、不要求 commit。正式 `case_run` 从固定 Git 版本进入独立执行工作区，按 task_id / attempt 保存源码与运行数据。Nexus MCP 不编辑工作区文件。
- 新会话先观察并验证定位，再扩展用例；远端节点不承担编写调试。调试工具未部署时如实说明，不能宣称具备保留现场能力。
- push 前运行 `mino-scout check --require-cases .`，有可操作问题就修复后重跑。
- 凭据、OTP、token 和安装命令一次性凭证不写入回复、日志、记忆或提交。

## 为什么还需要 AGENTS.md

技能触发和 MCP 返回的 instructions 都依赖客户端选择，不能保证压过平台内置的 Computer Use、Browser 或其他 MCP。`AGENTS.md` 是 Codex 的持久行为约束，适合写“测试任务必须经 Mino MCP/Scout”这类每次都要遵守的路由规则。要阻止已知本地 UI 工具调用，可安装本技能的 Codex `PreToolUse` guard；要真正撤销工具暴露并形成不可由用户绕过的边界，仍必须由客户端管理员策略（如 `requirements.toml`）关闭 Computer Use/Browser。不要把三者混为同一等级的强制力。
