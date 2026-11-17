---
name: mino
description: Mino 工作流统一入口。用户提到 Mino、Mino Scout/MCP、跑用例、连接测试设备，或要操作被测 Android、iOS、Web、桌面软件、浏览器页面、截图和界面结构时优先使用。先检查持久路由与更新，再强制经 Mino MCP 与 Mino Scout 执行。
---

# Mino 统一入口

本技能只负责**选路和启动门禁**；具体编写、自检与执行分别转到对应技能。

## 强制路由

只要任务属于 Mino 的测试或 Mino 节点管理范围，按下面选路，不要按平台默认偏好换工具：

| 工作 | 唯一默认路径 |
|---|---|
| Nexus 项目、应用、需求、账号、设备、任务、记录 | **Mino MCP** |
| 本机 Scout 状态、探测、静态检查 | **`mino-scout` CLI** |
| 操作被测 Android / iOS / Web / 桌面软件 | 写用例脚本 → **Mino MCP `case_run`** → Scout 执行 |
| 被测页面截图、控件树、界面定位、点击和输入 | 用例脚本里的 Scout Case API，经 `case_run` 留存证据 |

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

`<mino-skill-dir>` 是已安装的 `mino` 技能目录。预检会比较本地 Skill 的 `VERSION` 与本机 `mino-scout update-check`，并报告 `routing_policy`。读取顶层 `overall_state`；网络不可用时它是 `unknown` 且 `check_complete=false`，不把它说成“已是最新”，也不要因此编造版本。同一会话只做一次，避免每个业务请求重复联网。

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

4. **调用 MCP `agent_guide`**，读取当前路由契约和工具列表；不要凭记忆猜工具。若 MCP 尚未配置，先转 `onboarding` 门禁完成接入，接入后再调用；不要因此改用其他工具。
5. 预检结果为 `current`、`unknown` 或本机未安装时，按实际结果继续判断当前任务需要 MCP、CLI 还是首次安装；`unknown` 必须如实说明。

> `0.1.15` 及更早版本还没有这个统一入口，无法由本技能自动完成首次预检。先按 `update-skills` 引导安装一次 `0.1.16+`，安装同样由 Agent 在用户确认后执行，不要求用户复制命令；再新开会话，之后才由启动门禁自动检查。

## 常用后续技能

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

- MCP 工具名把点写成下划线，例如 `agent.guide` 是 `agent_guide`。
- 先查项目、应用、设备和渠道，再 `case_run`；参数缺失就问，不要猜。
- 脚本只写在本机脚本仓并通过 Git push；Nexus MCP 不写代码。
- push 前运行 `mino-scout check --require-cases .`，有可操作问题就修复后重跑。
- 凭据、OTP、token 和安装命令一次性凭证不写入回复、日志、记忆或提交。

## 为什么还需要 AGENTS.md

技能触发和 MCP 返回的 instructions 都依赖客户端选择，不能保证压过平台内置的 Computer Use、Browser 或其他 MCP。`AGENTS.md` 是 Codex 的持久行为约束，适合写“测试任务必须经 Mino MCP/Scout”这类每次都要遵守的路由规则。它仍不能覆盖用户或管理策略的显式禁止；若组织要求绝对关闭其他工具，还需在客户端或管理策略中禁用对应工具。
