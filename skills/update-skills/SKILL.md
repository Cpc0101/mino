---
name: update-skills
description: 从 GitHub 安装或更新 Mino 技能到 Codex、Cursor（可选 Claude），检查并刷新 AGENTS.md 持久路由，或检查 Mino Skill 与 mino-scout 是否有新版本。用户说“更新技能”“技能过期了”“重新安装 mino skill”“检查 Mino 更新”，或 Mino 启动预检发现版本落后时使用。
---

# 更新 Mino 技能与检查 Scout

源仓库：`https://github.com/Cpc0101/mino.git`（技能在 `skills/`）。版本以根目录 `VERSION`、`CHANGELOG.md` 为准。

## 先做只读预检

从已安装的 `mino` 技能目录运行：

```bash
python3 "<mino-skill-dir>/scripts/check_updates.py" --json
```

输出分别给出每个技能根目录和本机 Scout 的 `current` / `latest` / `state`。以顶层 `overall_state` 判断：`current`、`update_available`、`action_required`、`unknown`、`not_installed`。`unknown` 时 `check_complete=false`，表示检查失败，不是已最新。

`consent_required=true` 时，必须先读取 `consent_actions`，用其中的 `question` 和 `impact` 向用户询问。Skill、Scout、`AGENTS.md` 都属于本机持久状态，只有用户明确同意后才能更新；不要要求用户自己执行命令或编辑文件。用户同意后由 Agent 执行，客户端若弹出权限确认再由用户批准。

每个动作都带有稳定的 `id`。用户可一次同意全部动作，也可逐项同意；未同意的动作保持现状。`command` 是同意后由 Agent 执行的结构化命令：

- `update_skill` / `update_scout` / `install_routing_policy`：执行返回的 `command`；Scout 只认预检给出的固定版本。
- `install_scout`：先询问用户；同意后转到 `onboarding`，通过 MCP `scout_install_token` 申请本机安装请求，不要在对话中展示一次性凭证。
- `resolve_conflict` / `repair_error`：先只读诊断并解释，不要删除残缺标记、覆盖文件或伪造替代安装命令。

## 禁止软链

**禁止**把技能目录做成指向本机业务仓（如 `code/mino`）的符号链接。安装与更新都必须：**从 GitHub clone 一次 → 复制成真实目录/文件**。`install_skills.py` 会拒绝源或技能根目录里的软链。

## Codex 与 Cursor

先识别当前客户端要更新的根目录：

| 客户端 | 技能根目录 |
|---|---|
| Codex | `$CODEX_HOME/skills`（默认 `$HOME/.codex/skills`） |
| Cursor | `$HOME/.cursor/skills` |
| Claude（仅在用户使用） | `$HOME/.claude/skills` |

不要把同一份本机业务仓软链到任一目录。预检给出 Skill 更新动作时，用户确认后直接执行动作中的 `command`。该命令等价于：

```bash
python3 "$HOME/.codex/skills/mino/scripts/install_skills.py" \
  --root "$HOME/.codex/skills" \
  --ref main \
  --expected-version "<预检返回的 latest>"
```

安装器从正式仓 clone 临时副本，校验 `VERSION`，把 `skills/*/` 复制成真实目录，并保留技能根目录中的第三方技能。`--expected-version` 防止检查后远端又变化导致安装错版本。更新完成后报告 `CHANGELOG.md` 本版变化，并说明**需要新开会话**才会加载新内容。

`0.1.18` 及更早的已安装目录没有这个安装器。首次引导时，Agent 可把正式仓 clone 到临时目录，并直接运行源仓里的 `skills/mino/scripts/install_skills.py --source-dir <clone> --root <目标技能根目录>`；必须先询问用户，仍然不要要求用户手工执行。完成一次升级后，后续直接使用预检动作即可。

## 持久路由策略（AGENTS.md）

Skill 与 MCP `initialize.instructions` 不能保证压过平台内置 Computer Use/Browser。Codex 需要在 `$CODEX_HOME/AGENTS.md`（默认 `$HOME/.codex/AGENTS.md`）写入 Mino 托管块；安装器只替换 `<!-- mino-routing:start -->` 和 `<!-- mino-routing:end -->` 之间内容，不覆盖文件其他部分。

Skill 更新后先只读检查：

```bash
python3 "$DEST/mino/scripts/install_routing_policy.py" --check
```

- `current`：无需修改。
- `missing` / `outdated`：使用预检 `consent_actions` 中的问题询问用户；向用户说明这是跨会话路由规则，**取得确认后**再执行 `--apply`。
- `conflict`：停止；不要删除残缺标记或覆盖原文件，先让用户检查。

用户使用项目级规则或另一客户端时，可在确认后用 `--path <AGENTS.md>`。只有该客户端确实读取 `AGENTS.md` 时才安装；Cursor/Claude 的规则文件机制不同，不要伪造兼容。托管块变更后需要新开会话才生效；当前会话继续遵守 `mino` 技能，不因此改用其他 UI 工具。

默认目标优先使用 `$CODEX_HOME/AGENTS.md`，未设置时为 `~/.codex/AGENTS.md`。用户确认后由 Agent 直接执行安装器，不要让用户手工复制路径或命令。

```bash
python3 "$DEST/mino/scripts/install_routing_policy.py" --apply
```

## Scout

先只读检查：

```bash
mino-scout update-check
```

只有返回 `update_available: true` 才升级，并使用其中的固定 `build_id` 和 `release_tag`。正式安装且节点空闲时，由用户确认后使用：

```bash
mino-scout update --operation-id <唯一稳定id> --release-tag <release_tag> --build-id <build_id>
```

节点正在执行、更新门禁未清或结果未知时，不要强停、不要删除锁文件、不要重放设备动作。按 `update-status <operation-id>` 和 `docs/PACKAGING.md` 处理；离线或未确认不等于失败。

## 怎么知道装的是什么版本

看实际技能根目录的 `VERSION` 和 `CHANGELOG.md`，不要看本机正在开发的 `code/mino`，除非用户明确说在维护技能源仓。

## 发现技能有问题怎么办

1. 先把眼前任务做完；按实际情况处理，不要硬照错说明。
2. 不要直接改已安装目录来“修永久版”（下次更新会覆盖，也和发布源不一致）。
3. 整理技能名、段落、原文、实际行为和无敏感信息的证据，交给用户。

## 给维护技能的人

- 改 GitHub 源仓，更新 `VERSION` 与 `CHANGELOG.md`，push 后让使用者重新安装；
- 一个技能只做一件事；易变清单写“以运行时 / 接口返回为准”；
- `description` 必须写清何时触发，尤其是 `mino` 统一入口和 Computer Use 的路由边界。
