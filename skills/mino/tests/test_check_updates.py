from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_updates
import install_codex_guard


class CheckUpdatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_github_content_version_decodes_base64(self) -> None:
        payload = {
            "encoding": "base64",
            "content": base64.b64encode(b"0.1.19\n").decode("ascii"),
        }

        self.assertEqual(check_updates._github_content_version(payload), "0.1.19")

    def test_github_api_failure_falls_back_to_raw(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(check_updates, "_fetch_json", side_effect=ValueError("api down")):
                with mock.patch.object(check_updates, "_fetch_text", return_value="0.1.19"):
                    version, source = check_updates._fetch_latest_skill_version(1.0)

        self.assertEqual(version, "0.1.19")
        self.assertEqual(source, "raw")

    def test_routing_check_uses_codex_home_without_explicit_path(self) -> None:
        codex_home = self.base / "codex-home"
        codex_home.mkdir()
        agents = codex_home / "AGENTS.md"
        agents.write_text("outside\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=True):
            result = check_updates._check_routing_policy()

        self.assertEqual(result["path"], str(agents))
        self.assertEqual(result["state"], "missing")

    def test_skill_roots_use_codex_home_without_override(self) -> None:
        codex_home = self.base / "custom-codex"
        skill_root = codex_home / "skills"
        skill_root.mkdir(parents=True)
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=True):
            roots = check_updates._skill_roots()

        self.assertEqual(roots[0], skill_root)

    def test_consent_actions_include_executable_installers(self) -> None:
        skills = [
            {
                "root": str(self.base / "skills"),
                "current": "0.1.18",
                "latest": "0.1.19",
                "state": "update_available",
            }
        ]
        scout = {
            "state": "update_available",
            "current": "0.1.152",
            "latest": "0.1.153",
            "build_id": "build-123",
            "release_tag": "v0.1.153",
            "method": "mino-scout update-check",
        }
        routing = {"state": "outdated", "path": str(self.base / "AGENTS.md")}
        guard = {"state": "current", "path": str(self.base / "hooks.json")}
        with mock.patch.object(check_updates.shutil, "which", return_value="/tmp/mino-scout"):
            actions = check_updates._build_consent_actions(skills, scout, routing, guard)

        by_id = {action["id"]: action for action in actions}
        self.assertEqual(set(by_id), {f"skill:{self.base / 'skills'}", "scout", "routing_policy"})
        self.assertTrue(all(action["requires_user_confirmation"] for action in actions))
        skill_command = by_id[f"skill:{self.base / 'skills'}"]["command"]
        self.assertIn("install_skills.py", skill_command[1])
        self.assertIn("--expected-version", skill_command)
        self.assertEqual(by_id["scout"]["command"][0], "/tmp/mino-scout")
        self.assertEqual(by_id["scout"]["operation_id"], by_id["scout"]["operation_id"])
        self.assertIn("--build-id", by_id["scout"]["command"])
        self.assertIn("--release-tag", by_id["scout"]["command"])
        self.assertIn("install_routing_policy.py", by_id["routing_policy"]["command"][1])

    def test_missing_scout_creates_install_consent_action(self) -> None:
        actions = check_updates._build_consent_actions(
            [],
            {"state": "not_installed", "reason": "PATH 中没有 mino-scout"},
            {"state": "current", "path": str(self.base / "AGENTS.md")},
            {"state": "current", "path": str(self.base / "hooks.json")},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["kind"], "install_scout")
        self.assertTrue(actions[0]["requires_user_confirmation"])
        self.assertIsNone(actions[0]["command"])
        self.assertIn("scout_install_token", actions[0]["next_step"])

    def test_preflight_never_writes_skill_or_routing_state(self) -> None:
        skills_root = self.base / "skills"
        skills_root.mkdir()
        version_file = skills_root / "VERSION"
        version_file.write_text("0.1.18\n", encoding="utf-8")
        agents = self.base / "AGENTS.md"
        hooks = self.base / "hooks.json"
        scout = {"state": "current", "current": "0.1.152", "latest": "0.1.152"}
        env = {
            "MINO_SKILL_LATEST_VERSION": "0.1.19",
            "MINO_SKILL_ROOTS": str(skills_root),
            "MINO_ROUTING_POLICY_PATH": str(agents),
            "MINO_CODEX_HOOKS_PATH": str(hooks),
        }
        stdout = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(check_updates, "_check_scout", return_value=(scout, [])):
                with contextlib.redirect_stdout(stdout):
                    code = check_updates.main(["--json", "--timeout", "1"])

        output = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(version_file.read_text(encoding="utf-8"), "0.1.18\n")
        self.assertFalse(agents.exists())
        self.assertFalse(hooks.exists())
        self.assertTrue(output["consent_required"])
        self.assertEqual(output["skill_latest_source"], "override")
        self.assertEqual(output["routing_policy"]["state"], "missing")
        self.assertEqual(output["codex_guard"]["state"], "missing")

    def test_only_routing_change_reports_action_required(self) -> None:
        skills_root = self.base / "skills"
        skills_root.mkdir()
        (skills_root / "VERSION").write_text("0.1.19\n", encoding="utf-8")
        hooks = self.base / "hooks.json"
        install_codex_guard._apply(hooks)
        env = {
            "MINO_SKILL_LATEST_VERSION": "0.1.19",
            "MINO_SKILL_ROOTS": str(skills_root),
            "MINO_ROUTING_POLICY_PATH": str(self.base / "AGENTS.md"),
            "MINO_CODEX_HOOKS_PATH": str(hooks),
        }
        scout = {"state": "current", "current": "0.1.152", "latest": "0.1.152"}
        stdout = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(check_updates, "_check_scout", return_value=(scout, [])):
                with contextlib.redirect_stdout(stdout):
                    check_updates.main(["--json", "--timeout", "1"])

        output = json.loads(stdout.getvalue())
        self.assertEqual(output["overall_state"], "action_required")
        self.assertEqual([item["id"] for item in output["consent_actions"]], ["routing_policy"])

    def test_missing_guard_creates_revocable_consent_action(self) -> None:
        actions = check_updates._build_consent_actions(
            [],
            {"state": "current", "current": "0.1.164", "latest": "0.1.164"},
            {"state": "current", "path": str(self.base / "AGENTS.md")},
            {"state": "missing", "path": str(self.base / "hooks.json")},
        )

        self.assertEqual([action["id"] for action in actions], ["codex_guard"])
        action = actions[0]
        self.assertEqual(action["kind"], "install_codex_guard")
        self.assertTrue(action["requires_user_confirmation"])
        self.assertIn("install_codex_guard.py", action["command"][1])
        self.assertIn("不是完整 sandbox", action["impact"])
        self.assertIn("/hooks", action["impact"])
        self.assertIn("/hooks", action["next_step"])


if __name__ == "__main__":
    unittest.main()
