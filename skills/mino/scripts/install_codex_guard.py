#!/usr/bin/env python3
"""安装可撤销的 Codex PreToolUse guard，阻断 Mino 测试中绕过 Scout 的 UI 工具。

该 guard 是本地 guardrail，不是 Codex 管理策略级 sandbox。它只处理经过
PreToolUse 的本地函数/MCP 工具；hosted tool、特殊工具路径和 hook 失败仍可能
绕过。需要绝对禁用时，应由管理员配置 requirements.toml。
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

GUARD_FILENAME = "mino_pre_tool_use.py"
MATCHER = (
    r"^mcp__(?:cua_repl|node_repl)__.*$"
    r"|^mcp__codex_app__capture_screen_context$"
)
BLOCKED_PREFIXES = ("mcp__cua_repl__",)
BLOCKED_EXACT = {"mcp__codex_app__capture_screen_context"}
NODE_REPL_PREFIX = "mcp__node_repl__"
BROWSER_AUTOMATION_MARKERS = (
    "playwright",
    "puppeteer",
    "selenium",
    "webdriver",
    "chrome-remote-interface",
    "chromedriver",
    "browser.newpage",
    "page.goto(",
    "page.screenshot(",
    "page.locator(",
    "chromium.launch",
    "firefox.launch",
    "webkit.launch",
)

GUARD_SCRIPT = '''#!/usr/bin/env python3
"""Block Codex UI tools that bypass Mino Scout for target UI work."""
from __future__ import annotations

import json
import sys

BLOCKED_PREFIXES = ("mcp__cua_repl__",)
BLOCKED_EXACT = {"mcp__codex_app__capture_screen_context"}
NODE_REPL_PREFIX = "mcp__node_repl__"
BROWSER_AUTOMATION_MARKERS = (
    "playwright", "puppeteer", "selenium", "webdriver",
    "chrome-remote-interface", "chromedriver", "browser.newpage",
    "page.goto(", "page.screenshot(", "page.locator(",
    "chromium.launch", "firefox.launch", "webkit.launch",
)


def browser_automation(payload: dict) -> bool:
    try:
        rendered = json.dumps(payload.get("tool_input", ""), ensure_ascii=False).lower()
    except (TypeError, ValueError):
        rendered = str(payload.get("tool_input", "")).lower()
    return any(marker in rendered for marker in BROWSER_AUTOMATION_MARKERS)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    tool_name = str(payload.get("tool_name") or "") if isinstance(payload, dict) else ""
    blocked_ui = tool_name.startswith(BLOCKED_PREFIXES) or tool_name in BLOCKED_EXACT
    blocked_browser = tool_name.startswith(NODE_REPL_PREFIX) and browser_automation(payload)
    if blocked_ui or blocked_browser:
        reason = (
            "Mino target UI work must use Mino MCP debug_case/debug_case_execute "
            "for local authoring, or case_run for formal execution, routed to Mino Scout. "
            "Computer Use, screen capture, and browser automation are not valid substitutes. "
            "Do not bypass this guard through shell commands or another automation tool. "
            "Call agent_guide and use Scout; disable this guard only after an explicit user request."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def default_hooks_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip() or "~/.codex"
    return Path(codex_home).expanduser() / "hooks.json"


def default_script_path(hooks_path: str | Path | None = None) -> Path:
    target = default_hooks_path() if hooks_path is None else Path(hooks_path).expanduser()
    return target.parent / "hooks" / GUARD_FILENAME


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取 hooks 配置: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("hooks 配置必须是 JSON 对象")
    return payload


def _atomic_write(path: Path, content: str, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _command(script: Path) -> str:
    if os.name == "nt":
        return f'"{sys.executable}" "{script}"'
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"


def _managed_hook(hook: Any) -> bool:
    return isinstance(hook, dict) and GUARD_FILENAME in str(hook.get("command") or "")


def _managed_group(group: Any) -> bool:
    if not isinstance(group, dict):
        return False
    hooks = group.get("hooks")
    return isinstance(hooks, list) and any(_managed_hook(hook) for hook in hooks)


def _groups(payload: dict[str, Any]) -> list[Any]:
    hooks = payload.get("hooks")
    if hooks is None:
        return []
    if not isinstance(hooks, dict):
        raise ValueError("hooks 必须是 JSON 对象")
    groups = hooks.get("PreToolUse")
    if groups is None:
        return []
    if not isinstance(groups, list):
        raise ValueError("hooks.PreToolUse 必须是数组")
    return groups


def _desired_group(script: Path) -> dict[str, Any]:
    return {
        "matcher": MATCHER,
        "hooks": [
            {
                "type": "command",
                "command": _command(script),
                "statusMessage": "Blocking non-Mino target UI tools",
                "timeout": 3,
            }
        ],
    }


def inspect_guard(hooks_path: str | Path | None = None) -> dict[str, Any]:
    """只读检查 guard 配置和脚本状态。"""
    target = default_hooks_path() if hooks_path is None else Path(hooks_path).expanduser()
    script = default_script_path(target)
    result: dict[str, Any] = {
        "path": str(target),
        "script": str(script),
        "state": "missing",
        "changed": False,
        "matcher": MATCHER,
        "activation": "new_session_and_trust",
        "trust_required": True,
    }
    try:
        groups = _groups(_read_json(target))
    except ValueError as exc:
        result.update(state="conflict", reason=str(exc))
        return result
    managed = [group for group in groups if _managed_group(group)]
    if not managed:
        result["reason"] = "未安装 Mino PreToolUse guard"
        return result
    if len(managed) != 1:
        result.update(state="outdated", reason="存在重复的 Mino guard")
        return result
    desired = _desired_group(script)
    if managed[0] != desired:
        result.update(state="outdated", reason="Mino guard 配置与当前版本不一致")
        return result
    try:
        current_script = script.read_text(encoding="utf-8")
    except OSError:
        result.update(state="outdated", reason="guard 脚本缺失或不可读")
        return result
    if current_script != GUARD_SCRIPT:
        result.update(state="outdated", reason="guard 脚本与当前版本不一致")
        return result
    result.update(state="current", reason="已安装；新开会话并在 /hooks 中信任后才会生效")
    return result


def _apply(hooks_path: Path) -> dict[str, Any]:
    payload = _read_json(hooks_path)
    hooks = payload.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks 必须是 JSON 对象")
    groups = hooks.setdefault("PreToolUse", [])
    if not isinstance(groups, list):
        raise ValueError("hooks.PreToolUse 必须是数组")

    script = default_script_path(hooks_path)
    _atomic_write(script, GUARD_SCRIPT, 0o700)
    hooks["PreToolUse"] = [group for group in groups if not _managed_group(group)] + [_desired_group(script)]
    updated = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    previous = hooks_path.read_text(encoding="utf-8") if hooks_path.exists() else ""
    changed = previous != updated
    if changed:
        mode = stat.S_IMODE(hooks_path.stat().st_mode) if hooks_path.exists() else 0o600
        _atomic_write(hooks_path, updated, mode)
    return {
        "path": str(hooks_path),
        "script": str(script),
        "state": "current",
        "changed": changed,
        "requires_new_session": changed,
        "activation": "new_session_and_trust",
        "trust_required": True,
        "next_step": "新开 Codex 会话，在 /hooks 中审查并信任该用户级 hook；未信任时 Codex 会跳过。",
    }


def _remove(hooks_path: Path) -> dict[str, Any]:
    if not hooks_path.exists():
        return {"path": str(hooks_path), "state": "missing", "changed": False}
    payload = _read_json(hooks_path)
    groups = _groups(payload)
    retained = [group for group in groups if not _managed_group(group)]
    changed = len(retained) != len(groups)
    if changed:
        payload["hooks"]["PreToolUse"] = retained
        mode = stat.S_IMODE(hooks_path.stat().st_mode)
        _atomic_write(hooks_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n", mode)
    script = default_script_path(hooks_path)
    if script.exists():
        script.unlink()
        changed = True
    return {
        "path": str(hooks_path),
        "script": str(script),
        "state": "removed" if changed else "missing",
        "changed": changed,
        "requires_new_session": changed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="只读检查（默认）")
    action.add_argument("--apply", action="store_true", help="安装或刷新 guard")
    action.add_argument("--remove", action="store_true", help="移除 Mino guard，保留其他 hooks")
    parser.add_argument("--path", default="", help="hooks.json 路径，默认 $CODEX_HOME/hooks.json")
    args = parser.parse_args(argv)
    target = Path(args.path).expanduser() if args.path else default_hooks_path()
    try:
        if args.apply:
            result = _apply(target)
        elif args.remove:
            result = _remove(target)
        else:
            result = inspect_guard(target)
    except (OSError, ValueError) as exc:
        result = {"path": str(target), "state": "conflict", "changed": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.check:
        return 0 if result.get("state") == "current" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
