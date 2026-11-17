from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_skills


class InstallSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.root = self.base / "skills"
        (self.source / "skills" / "mino").mkdir(parents=True)
        (self.source / "skills" / "mino" / "SKILL.md").write_text("new mino\n", encoding="utf-8")
        (self.source / "skills" / "update-skills").mkdir(parents=True)
        (self.source / "skills" / "update-skills" / "SKILL.md").write_text("update\n", encoding="utf-8")
        (self.source / "VERSION").write_text("0.1.19\n", encoding="utf-8")
        (self.source / "CHANGELOG.md").write_text("changes\n", encoding="utf-8")

    def test_installs_real_directories_and_preserves_third_party_skills(self) -> None:
        third_party = self.root / "third-party"
        third_party.mkdir(parents=True)
        (third_party / "SKILL.md").write_text("keep\n", encoding="utf-8")
        old_mino = self.root / "mino"
        old_mino.mkdir()
        (old_mino / "SKILL.md").write_text("old\n", encoding="utf-8")

        result = install_skills.install_from_source(self.source, self.root, "0.1.19")

        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], "0.1.19")
        self.assertEqual((self.root / "VERSION").read_text(encoding="utf-8").strip(), "0.1.19")
        self.assertEqual((self.root / "mino" / "SKILL.md").read_text(encoding="utf-8"), "new mino\n")
        self.assertEqual((third_party / "SKILL.md").read_text(encoding="utf-8"), "keep\n")
        self.assertFalse((self.root / "mino").is_symlink())
        self.assertFalse(any(path.is_symlink() for path in self.root.rglob("*")))

    def test_version_mismatch_does_not_modify_root(self) -> None:
        original = self.root / "mino" / "SKILL.md"
        original.parent.mkdir(parents=True)
        original.write_text("old\n", encoding="utf-8")

        with self.assertRaises(install_skills.InstallError):
            install_skills.install_from_source(self.source, self.root, "0.1.20")

        self.assertEqual(original.read_text(encoding="utf-8"), "old\n")

    def test_source_symlink_is_rejected(self) -> None:
        link = self.source / "skills" / "mino" / "linked.md"
        link.symlink_to(self.source / "VERSION")

        with self.assertRaises(install_skills.InstallError):
            install_skills.install_from_source(self.source, self.root, "0.1.19")

        self.assertFalse(self.root.exists())

    def test_failure_after_first_commit_rolls_back_all_changes(self) -> None:
        existing = self.root / "mino"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("old\n", encoding="utf-8")
        real_commit = install_skills._commit_path
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated failure")
            return real_commit(*args, **kwargs)

        with mock.patch.object(install_skills, "_commit_path", side_effect=fail_second):
            with self.assertRaises(install_skills.InstallError):
                install_skills.install_from_source(self.source, self.root, "0.1.19")

        self.assertEqual((existing / "SKILL.md").read_text(encoding="utf-8"), "old\n")
        self.assertFalse((self.root / "update-skills").exists())


if __name__ == "__main__":
    unittest.main()
