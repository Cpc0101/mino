---
name: overview
description: 了解 Mino 是什么、Scout / Nexus / Workbench / Agent 各管什么、MCP 与 mino-scout CLI 怎么分工。用户问“系统怎么分工”“Scout 是什么”“该用 MCP 还是 CLI”，或你不确定该找哪一端时使用。
---

# Mino 总览

Mino 是自动化测试系统。当前重点是把已有人工用例转换成可靠、可复用的自动化脚本，并让每个结论能追溯原文和执行证据。

| 端 | 是什么 | 负责 | 不负责 |
|---|---|---|---|
| **Nexus** | 云端（`https://nexus.minocc.top`） | 项目/应用/需求元数据、账号池、设备租约、任务派发、状态索引、转发记录读取 | 写脚本；拉 Git；操作设备；长期保存完整执行明细和截图 |
| **Scout** | 执行器（`mino-scout`） | 连 Nexus、拉仓、独立进程执行、操作设备、断言和截图；按 task_id 持久保存完整记录，重连补报摘要 | 自行扩展测试范围；决定下一条测什么 |
| **Workbench** | 网页（`https://workbench.minocc.top`） | 从 Nexus 取任务列表，通过 Nexus 读取原执行 Scout 的详情，展示原文/动作/断言/证据 | 替代 Scout 执行或存储原始事实 |
| **Agent** | 对话侧 | 分析已有用例 → 固定原文 → 编写 Python/页面/流程 → 静态校验 → 真机验证 → 有证据地归因和交付 | 擅自新建远程仓、猜环境和定位、把采集或接单说成测试通过 |

本地状态在 `~/.mino/`。Scout 主动连 Nexus，不开放监听端口。

## MCP 与 mino-scout CLI（必分清）

| 事 | 用什么 | 例子 |
|---|---|---|
| 查 / 改 Nexus 控制面 | **MCP** | `project_list`、`project_create`、`project_script_repo_set`、`repo_apps_sync` / `get`、`scout_install_token`、`device_list`、`case_run`、`task_get`、渠道程序安装 |
| 本机 Scout | **`mino-scout` CLI** | 服务状态、`probe` 设备、仓根 `check` 自检（以本机 `--help` 为准） |
| 写文件与推送 | **本机 Git** | 编辑脚本仓 → commit → push；MCP **不写**仓 |

技能正文若只堆 MCP、不提 CLI，是错的：本机就绪与脚本质量靠 Scout CLI；云端编排靠 MCP。

## Agent 硬约束（所有技能共用）

1. **先读技能再动手**；缺信息就问，**不要猜**包名、URL、仓库地址、环境名。
2. **每进入一个大步骤，先用一两句话告诉用户**：将做什么、需要用户确认什么、成功长什么样；做完再报结果。不要闷头连调工具。
3. **禁止**在用户未明确说「新建仓库 / 创建 GitHub 仓」时 `gh repo create`、初始化并推到新远程。脚本仓地址必须用户给出，或明确授权新建。
4. **禁止**把「只调了 `app_create`」说成应用已配好。完成态见 `onboarding` / `repo-config`。
5. MCP 工具缺失或报错：**停住**，告诉用户缺哪个工具、卡在哪一步；不要改去刷 Workbench、编造 HTTP、或用探测应用「试接口」。
6. 会改系统的动作（装 Scout、装渠道程序、push、`case_run`）前要有用户意图；装 Scout 还必须用户同意执行安装命令。
7. 凭据、安装命令里的一次性 token：**不写入回复正文、日志、记忆、提交**。
8. **脚本仓推送门禁（强制）**：push 前必须在仓库根运行 `mino-scout check --require-cases .`。输出里只要还有任何一条需要解决的问题，就先解决并重跑；不能用“稍后验证”“已知问题”留下后继续 push。动态映射、定位、断言或业务证据需要运行确认时，先完成对应验证再 push。

## 一次测试的流向

1. 项目 + 脚本仓绑定 + 应用清单就绪（`onboarding` / `repo-config`）；
2. agent 在本机写脚本并 `mino-scout check`，再 push；
3. 改了 `config.yaml` 应用身份 → `repo_apps_sync`；
4. MCP `case_run` → Nexus 将固定仓提交、设备与 task/session/attempt 下发给 Scout；
5. Scout 持久接单后异步执行，完整记录保留本机，摘要经持久 ACK 同步到 Nexus；
6. Agent/Workbench 通过 Nexus 读取原 Scout 记录。只采集、静态通过、动作走通、预期通过分别说明，最后按真实证据交付。

Scout 不开放监听端口。Git 临时 workspace 可以删除，任务记录独立保留；节点离线时详情暂不可读，Nexus 的最后同步状态不能充当实时证据。取消、重连和重试不得重放结果未知的写操作。

## 该用哪个技能

| 你要做的事 | 技能 |
|---|---|
| 分工、MCP vs CLI、硬约束 | 本技能 |
| 注册、接 MCP、**MCP 装 Scout**、`project_create` / 绑仓 / sync | `onboarding` |
| 改 `config.yaml` / pages、加应用（问齐再写） | `repo-config` |
| 将已有人工用例整理为可实现、可判定的原文与方案 | `analyze-test-case` |
| 写用例脚本 | `write-test-cases` |
| `mino-scout check` | `check-test-cases` |
| 触发跑数、看任务、汇报 | `run-test-cases` |
| 更新技能 | `update-skills` |

Scout 安装：MCP `scout_install_token` 取命令 → 用户确认弹窗同意 → 本机执行；细节只在 `onboarding` 门禁 3。
