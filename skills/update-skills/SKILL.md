---
name: update-skills
description: 从 GitHub 安装或更新 Mino 技能到 Codex、Cursor（可选 Claude），检查并刷新 AGENTS.md 持久路由，或检查 Mino Skill 与 mino-scout 是否有新版本。用户说“更新技能”“技能过期了”“重新安装 mino skill”“检查 Mino 更新”，或 Mino 启动预检发现版本落后时使用。
---

# 更新 Mino 技能与检查 Scout

源仓库：`https://github.com/pengchengluoyi/mino.git`（技能在 `skills/`）。版本以根目录 `VERSION`、`CHANGELOG.md` 为准。

## 先做只读预检

从已安装的 `mino` 技能目录运行：

```bash
python3 "<mino-skill-dir>/scripts/check_updates.py" --json
```

输出分别给出每个技能根目录和本机 Scout 的 `current` / `latest` / `state`。以顶层 `overall_state` 判断：`current`、`update_available`、`unknown`、`not_installed`。`unknown` 时 `check_complete=false`，表示检查失败，不是已最新。Skill 有更新时，下面安装命令会处理；Scout 有更新时使用 `mino-scout update-check` 返回的固定值，执行前必须向用户说明并取得确认。

## 禁止软链

**禁止**把技能目录做成指向本机业务仓（如 `code/mino`）的符号链接。安装与更新都必须：**从 GitHub clone 一次 → 复制成真实目录/文件**。

## Codex 与 Cursor

先识别当前客户端要更新的根目录：

| 客户端 | 技能根目录 |
|---|---|
| Codex | `$HOME/.codex/skills` |
| Cursor | `$HOME/.cursor/skills` |
| Claude（仅在用户使用） | `$HOME/.claude/skills` |

不要把同一份本机业务仓软链到任一目录。对实际使用的根目录执行：

```bash
TMP=$(mktemp -d)
git clone --depth 1 https://github.com/pengchengluoyi/mino.git "$TMP/mino"
DEST="$HOME/.codex/skills"   # Cursor 改成 $HOME/.cursor/skills
mkdir -p "$DEST"
for d in "$TMP/mino/skills"/*/; do
  [ -f "$d/SKILL.md" ] || continue
  name=$(basename "$d")
  rm -rf "$DEST/$name"
  cp -R "$d" "$DEST/$name"
done
cp "$TMP/mino/VERSION" "$DEST/VERSION"
cp "$TMP/mino/CHANGELOG.md" "$DEST/CHANGELOG.md"
rm -rf "$TMP"
find "$DEST" -type l
cat "$DEST/VERSION"
```

`rm -rf` 只针对从同一 clone 枚举出的 Mino 技能名；不要清理根目录里的其他第三方技能。更新完成后报告 `CHANGELOG.md` 本版变化，并说明**需要新开会话**才会加载新内容。

## 持久路由策略（AGENTS.md）

Skill 与 MCP `initialize.instructions` 不能保证压过平台内置 Computer Use/Browser。Codex 需要在 `$HOME/.codex/AGENTS.md` 写入 Mino 托管块；安装器只替换 `<!-- mino-routing:start -->` 和 `<!-- mino-routing:end -->` 之间内容，不覆盖文件其他部分。

Skill 更新后先只读检查：

```bash
python3 "$DEST/mino/scripts/install_routing_policy.py" --check
```

- `current`：无需修改。
- `missing` / `outdated`：向用户说明这是跨会话路由规则，**取得确认后**再执行 `--apply`。
- `conflict`：停止；不要删除残缺标记或覆盖原文件，先让用户检查。

用户使用项目级规则或另一客户端时，可在确认后用 `--path <AGENTS.md>`。只有该客户端确实读取 `AGENTS.md` 时才安装；Cursor/Claude 的规则文件机制不同，不要伪造兼容。托管块变更后需要新开会话才生效；当前会话继续遵守 `mino` 技能，不因此改用其他 UI 工具。

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
