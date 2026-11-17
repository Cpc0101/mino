# mino

给 AI agent 用的 Mino 技能（Agent Skills：每个技能一个目录，入口 `SKILL.md`）。

产品能做什么、覆盖哪些场景、当前边界与覆盖率口径，见 [Mino 产品能力与场景覆盖矩阵](CAPABILITY_COVERAGE.md)。

当前目标：把已有人工用例转换成可执行、可复用的 Python 自动化脚本。原文快照、真实定位和有效断言保持关联，静态校验、路径执行和业务预期验证分别说明。

| 技能 | 一句话 |
|---|---|
| `mino` | **统一入口**：安装 `AGENTS.md` 持久路由、禁止静默改用 Computer Use、启动更新预检 |
| `overview` | 分工、MCP vs mino-scout CLI、agent 硬约束 |
| `onboarding` | 注册、接 MCP、`scout_install_token` 确认后装 Scout、建项目绑仓 |
| `repo-config` | 已绑定仓写 `config.yaml` / pages；`check` + `repo_apps_sync` |
| `analyze-test-case` | 固定人工用例原文，识别前置/操作/预期与缺口 |
| `write-test-cases` | 编写 Python、复用流程并关联 source_ref 和有效断言 |
| `check-test-cases` | 语法、导入、页面引用、原文映射与明显无效断言自检 |
| `run-test-cases` | MCP 触发 → Scout 留证 → 读取真实结果并汇报 |
| `update-skills` | 从 GitHub 安装/更新 Codex、Cursor 技能，并检查 Scout（**禁止软链**） |

入口先读 `mino`；之后按 `overview` → `onboarding` → `repo-config` → `analyze-test-case` → `write-test-cases` → `check-test-cases` → `run-test-cases`。

Nexus 保存任务索引和设备/账号租约，Scout 独立执行并按 task_id 保留完整本地记录，Workbench 经 Nexus 读取原执行 Scout 的详情。Git 临时 workspace 可清理；记录不随之删除。节点离线时详情暂不可读，接单成功不等于测试通过。

## 安装给 Codex / Cursor

从 GitHub **复制**到 `~/.codex/skills/` 或 `~/.cursor/skills/`（真实目录，不要软链到本机开发仓）。步骤见技能 `update-skills`。

Codex 首次配置还要检查 `~/.codex/AGENTS.md` 是否含 Mino 托管路由块。安装器在用户确认后才写入，只替换自己的标记区间，不覆盖其他规则；写入后新开会话生效。没有这层持久规则时，Skill 和 MCP instructions 仍可能输给平台内置 Computer Use。

也可对 agent 说：

> 帮我从 https://github.com/pengchengluoyi/mino.git 安装 Mino Skill 到 ~/.codex/skills（复制，不要软链）。装好后按 onboarding 带我上手。

装完后**新开一个会话**。版本见已装目录里的 `VERSION`、`CHANGELOG.md`。

从 `0.1.15` 或更早版本首次升级时，旧安装还没有 `mino` 统一入口，需手动执行一次上面的更新流程；从 `0.1.16` 起，新会话可按 `mino` 技能的启动门禁检查 Skill、Scout 与持久路由。

## 更新

再跑一遍 `update-skills` 里的安装命令（重新 clone + 覆盖复制）。开始 Mino 工作流时，`mino` 技能的 `scripts/check_updates.py` 会只读检查 Skill、本机 Scout 和持久路由状态；`overall_state=unknown` 表示检查未完成，不是已最新。技能更新后按提示刷新 `AGENTS.md` 托管块。不要 `ln -s` 到 `code/mino`。

如果客户端总是抢用 Computer Use，可让 agent 先执行 `skills/mino/scripts/install_routing_policy.py --check`，说明差异并征得同意后再 `--apply`。需要强制禁用其他工具时，还要在客户端或组织管理策略中关闭它们；“优先 Mino”的提示本身不能覆盖硬权限策略。

## 前提

- Scout：按 `onboarding` 用 MCP 申请安装命令并确认后安装，CLI 验收；  
- MCP：`https://nexus.minocc.top/mcp`（启动预检与路由检查后，进入业务前先 `agent_guide`）；
- Workbench：`https://workbench.minocc.top`；  
- 写作用法以本机 `mino_scout/runtime/script_exec.py` 为准。

## 目录规范

- 目录名等于 `SKILL.md` 的 `name`；  
- `SKILL.md` 文件名全大写。
