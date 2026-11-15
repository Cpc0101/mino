# mino

给 AI agent 用的 Mino 技能（Agent Skills：每个技能一个目录，入口 `SKILL.md`）。

产品能做什么、覆盖哪些场景、当前边界与覆盖率口径，见 [Mino 产品能力与场景覆盖矩阵](CAPABILITY_COVERAGE.md)。

当前目标：把已有人工用例转换成可执行、可复用的 Python 自动化脚本。原文快照、真实定位和有效断言保持关联，静态校验、路径执行和业务预期验证分别说明。

| 技能 | 一句话 |
|---|---|
| `overview` | 分工、MCP vs mino-scout CLI、agent 硬约束 |
| `onboarding` | 注册、接 MCP、`scout_install_token` 确认后装 Scout、建项目绑仓 |
| `repo-config` | 已绑定仓写 `config.yaml` / pages；`check` + `repo_apps_sync` |
| `analyze-test-case` | 固定人工用例原文，识别前置/操作/预期与缺口 |
| `write-test-cases` | 编写 Python、复用流程并关联 source_ref 和有效断言 |
| `check-test-cases` | 语法、导入、页面引用、原文映射与明显无效断言自检 |
| `run-test-cases` | MCP 触发 → Scout 留证 → 读取真实结果并汇报 |
| `update-skills` | 从 GitHub 安装/更新技能（Cursor：**禁止软链**） |

推荐顺序：`overview` → `onboarding` → `repo-config` → `analyze-test-case` → `write-test-cases` → `check-test-cases` → `run-test-cases`。

Nexus 保存任务索引和设备/账号租约，Scout 独立执行并按 task_id 保留完整本地记录，Workbench 经 Nexus 读取原执行 Scout 的详情。Git 临时 workspace 可清理；记录不随之删除。节点离线时详情暂不可读，接单成功不等于测试通过。

## 安装给 Cursor

从 GitHub **复制**到 `~/.cursor/skills/`（真实目录，不要软链到本机开发仓）。步骤见技能 `update-skills`。

也可对 agent 说：

> 帮我从 https://github.com/pengchengluoyi/mino.git 安装 Mino Skill 到 ~/.cursor/skills（复制，不要软链）。装好后按 onboarding 带我上手。

装完后**新开一个会话**。版本见已装目录里的 `VERSION`、`CHANGELOG.md`。

## 更新

再跑一遍 `update-skills` 里的安装命令（重新 clone + 覆盖复制）。不要 `ln -s` 到 `code/mino`。

## 前提

- Scout：按 `onboarding` 用 MCP 申请安装命令并确认后安装，CLI 验收；  
- MCP：`https://nexus.minocc.top/mcp`（先 `agent_guide`）；  
- Workbench：`https://workbench.minocc.top`；  
- 写作用法以本机 `mino_scout/runtime/script_exec.py` 为准。

## 目录规范

- 目录名等于 `SKILL.md` 的 `name`；  
- `SKILL.md` 文件名全大写。
