from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_routing_policy as routing


class RoutingPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "AGENTS.md"

    def test_check_does_not_create_target(self) -> None:
        result = routing.inspect_policy(self.target)

        self.assertEqual(result["state"], "missing")
        self.assertFalse(self.target.exists())

    def test_apply_is_idempotent_and_preserves_other_content(self) -> None:
        self.target.write_text("# Existing rules\n\nKeep this line.\n", encoding="utf-8")

        first = routing._apply(self.target)
        second = routing._apply(self.target)
        text = self.target.read_text(encoding="utf-8")

        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertTrue(text.startswith("# Existing rules\n\nKeep this line.\n"))
        self.assertEqual(routing.inspect_policy(self.target)["state"], "current")

    def test_apply_refreshes_only_managed_block(self) -> None:
        self.target.write_text("before\n", encoding="utf-8")
        routing._apply(self.target)
        text = self.target.read_text(encoding="utf-8")
        outdated = text.replace("Mino routing policy", "Old Mino routing policy")
        self.target.write_text("prefix\n" + outdated + "suffix\n", encoding="utf-8")

        self.assertEqual(routing.inspect_policy(self.target)["state"], "outdated")
        result = routing._apply(self.target)
        refreshed = self.target.read_text(encoding="utf-8")

        self.assertTrue(result["changed"])
        self.assertTrue(refreshed.startswith("prefix\n"))
        self.assertTrue(refreshed.endswith("suffix\n"))
        self.assertNotIn("Old Mino routing policy", refreshed)
        self.assertEqual(routing.inspect_policy(self.target)["state"], "current")

    def test_conflicting_markers_are_rejected(self) -> None:
        self.target.write_text(
            f"{routing.START_MARKER}\n{routing.START_MARKER}\n{routing.END_MARKER}\n",
            encoding="utf-8",
        )

        with self.assertRaises(routing.PolicyConflict):
            routing.inspect_policy(self.target)

    def test_default_target_respects_codex_home(self) -> None:
        codex_home = Path(self.temp.name) / "custom-codex"
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
            self.assertEqual(routing.default_target(), codex_home / "AGENTS.md")


if __name__ == "__main__":
    unittest.main()
