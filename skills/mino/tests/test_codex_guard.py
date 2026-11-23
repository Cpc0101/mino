from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_codex_guard as guard


class CodexGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.hooks = Path(self.temp.name) / "codex" / "hooks.json"

    def test_check_does_not_create_files(self) -> None:
        result = guard.inspect_guard(self.hooks)

        self.assertEqual(result["state"], "missing")
        self.assertFalse(self.hooks.exists())
        self.assertFalse(guard.default_script_path(self.hooks).exists())

    def test_apply_preserves_existing_hooks_and_is_idempotent(self) -> None:
        self.hooks.parent.mkdir(parents=True)
        original = {
            "description": "existing",
            "hooks": {
                "PreToolUse": [{"matcher": "^Bash$", "hooks": [{"type": "command", "command": "echo ok"}]}],
                "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}],
            },
        }
        self.hooks.write_text(json.dumps(original), encoding="utf-8")

        first = guard._apply(self.hooks)
        second = guard._apply(self.hooks)
        payload = json.loads(self.hooks.read_text(encoding="utf-8"))

        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertTrue(first["trust_required"])
        self.assertEqual(first["activation"], "new_session_and_trust")
        self.assertIn("/hooks", first["next_step"])
        self.assertEqual(payload["description"], "existing")
        self.assertEqual(payload["hooks"]["PreToolUse"][0], original["hooks"]["PreToolUse"][0])
        self.assertIn("Stop", payload["hooks"])
        inspected = guard.inspect_guard(self.hooks)
        self.assertEqual(inspected["state"], "current")
        self.assertTrue(inspected["trust_required"])
        self.assertIn("/hooks", inspected["reason"])

    def test_guard_script_denies_ui_tools(self) -> None:
        guard._apply(self.hooks)
        script = guard.default_script_path(self.hooks)

        for tool_name in (
            "mcp__cua_repl__js",
            "mcp__codex_app__capture_screen_context",
        ):
            result = subprocess.run(
                [sys.executable, str(script)],
                input=json.dumps({"tool_name": tool_name}),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Mino Scout", decision["hookSpecificOutput"]["permissionDecisionReason"])

    def test_guard_script_denies_browser_automation_inside_node_repl(self) -> None:
        guard._apply(self.hooks)
        script = guard.default_script_path(self.hooks)

        result = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({
                "tool_name": "mcp__node_repl__js",
                "tool_input": {"code": "const { chromium } = await import('playwright');"},
            }),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("Mino Scout", decision["hookSpecificOutput"]["permissionDecisionReason"])

    def test_guard_script_allows_ordinary_node_repl(self) -> None:
        guard._apply(self.hooks)
        result = subprocess.run(
            [sys.executable, str(guard.default_script_path(self.hooks))],
            input=json.dumps({
                "tool_name": "mcp__node_repl__js",
                "tool_input": {"code": "const total = [1, 2, 3].reduce((a, b) => a + b, 0);"},
            }),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_guard_script_allows_unmatched_tool(self) -> None:
        guard._apply(self.hooks)
        result = subprocess.run(
            [sys.executable, str(guard.default_script_path(self.hooks))],
            input=json.dumps({"tool_name": "mcp__mino__agent_guide"}),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_remove_preserves_other_hooks(self) -> None:
        self.hooks.parent.mkdir(parents=True)
        self.hooks.write_text(json.dumps({"hooks": {"PreToolUse": []}}), encoding="utf-8")
        guard._apply(self.hooks)

        result = guard._remove(self.hooks)
        payload = json.loads(self.hooks.read_text(encoding="utf-8"))

        self.assertTrue(result["changed"])
        self.assertEqual(payload["hooks"]["PreToolUse"], [])
        self.assertFalse(guard.default_script_path(self.hooks).exists())

    def test_default_path_respects_codex_home(self) -> None:
        codex_home = Path(self.temp.name) / "home"
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
            self.assertEqual(guard.default_hooks_path(), codex_home / "hooks.json")


if __name__ == "__main__":
    unittest.main()
