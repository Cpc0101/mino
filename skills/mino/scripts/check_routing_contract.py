#!/usr/bin/env python3
"""在临时目录核对路由安装和显式测试会话 guard，不改用户配置。"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from install_codex_guard import GUARD_SCRIPT, _apply, _remove, inspect_guard, set_session
from install_routing_policy import PolicyConflict, _apply as apply_policy, inspect_policy


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="mino-routing-check-") as directory:
        root = Path(directory)
        hooks = root / "hooks.json"
        hooks.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "other", "hooks": []}]}}))
        _apply(hooks)
        assert inspect_guard(hooks)["state"] == "current"
        assert json.loads(hooks.read_text())["hooks"]["PreToolUse"][0]["matcher"] == "other"
        script = root / "hooks" / "mino_pre_tool_use.py"
        assert script.read_text() == GUARD_SCRIPT
        checks += 3

        def denied(payload: object) -> bool:
            result = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, capture_output=True, check=True)
            return bool(result.stdout.strip())

        ui = {"session_id": "qa/session", "tool_name": "mcp__cua_repl__js", "tool_input": {"code": "await cua.getState()"}}
        assert not denied(ui)
        set_session(hooks, "qa/session", True)
        assert denied(ui)
        assert not denied({**ui, "session_id": "other"})
        assert not denied({**ui, "session_id": ""})
        assert not denied([])
        assert not denied({"tool_name": "mcp__cua_repl__js"})
        assert not denied({**ui, "tool_name": "mcp__node_repl__js", "tool_input": {"code": "2 + 2"}})
        assert denied({**ui, "tool_name": "mcp__node_repl__js", "tool_input": {"code": "import('playwright')"}})
        assert denied({**ui, "tool_name": "mcp__codex_app__capture_screen_context"})
        checks += 9
        marker = next((root / "hooks" / "mino-test-sessions").glob("*.json"))
        state = json.loads(marker.read_text())
        marker.write_text(json.dumps({**state, "expires_at": time.time() - 1}))
        assert not denied(ui)
        marker.write_text('[]')
        assert not denied(ui)
        set_session(hooks, "qa/session", False)
        assert not denied(ui)
        _remove(hooks)
        assert json.loads(hooks.read_text())["hooks"]["PreToolUse"] == [{"matcher": "other", "hooks": []}]
        checks += 4
        policy = root / "AGENTS.md"
        policy.write_text("# User instructions\nKeep me.\n")
        apply_policy(policy)
        assert inspect_policy(policy)["state"] == "current"
        assert policy.read_text().startswith("# User instructions\nKeep me.\n")
        assert not apply_policy(policy)["changed"]
        policy.write_text(policy.read_text() + "<!-- mino-routing:start -->\n")
        try:
            apply_policy(policy)
        except PolicyConflict:
            checks += 1
        else:
            raise AssertionError("duplicate markers must fail closed")
        checks += 3
    print(f"routing_contract: {checks} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
