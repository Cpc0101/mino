#!/usr/bin/env python3
"""从 GitHub 将 Mino 技能安装为真实目录；不创建软链，也不改动其他技能。"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_REPO = "https://github.com/Cpc0101/mino.git"
SEMVER = re.compile(r"^[vV]?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


class InstallError(RuntimeError):
    """安装源无效或安装过程无法安全完成。"""


def default_skill_root() -> Path:
    """优先使用 CODEX_HOME，未设置时使用标准 Codex 技能目录。"""
    codex_home = os.environ.get("CODEX_HOME", "").strip() or "~/.codex"
    return Path(codex_home).expanduser() / "skills"


def _is_semver(value: str) -> bool:
    return bool(SEMVER.match(str(value or "").strip()))


def _read_version(source: Path) -> str:
    try:
        return (source / "VERSION").read_text(encoding="utf-8").strip().lstrip("vV")
    except OSError as exc:
        raise InstallError(f"无法读取安装源的 VERSION: {exc}") from exc


def _skill_names(source: Path) -> list[str]:
    skills_root = source / "skills"
    try:
        names = sorted(
            child.name
            for child in skills_root.iterdir()
            if child.is_dir() and (child / "SKILL.md").is_file()
        )
    except OSError as exc:
        raise InstallError(f"无法读取安装源技能目录 {skills_root}: {exc}") from exc
    if not names:
        raise InstallError(f"安装源中没有包含 SKILL.md 的技能目录: {skills_root}")
    for name in names:
        if name in {".", ".."} or "/" in name or "\\" in name:
            raise InstallError(f"安装源包含非法技能目录名: {name!r}")
    return names


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _remove_path(path: Path) -> None:
    if not _path_exists(path):
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _copy_tree(source: Path, destination: Path) -> None:
    links = [path for path in source.rglob("*") if path.is_symlink()]
    if links:
        raise InstallError(f"安装源包含软链，拒绝安装: {links[0]}")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")
    shutil.copytree(source, destination, symlinks=False, ignore=ignore)


def _prepare_staging(source: Path, names: list[str], staging: Path) -> None:
    staged_skills = staging / "staged"
    staged_skills.mkdir(parents=True)
    for name in names:
        _copy_tree(source / "skills" / name, staged_skills / name)
    for metadata in ("VERSION", "CHANGELOG.md"):
        source_file = source / metadata
        if source_file.is_file():
            shutil.copy2(source_file, staged_skills / metadata)


def _commit_path(staged: Path, target: Path, backup: Path, committed: list[tuple[Path, Path, bool]]) -> None:
    had_previous = _path_exists(target)
    if had_previous:
        backup.parent.mkdir(parents=True, exist_ok=True)
        os.replace(target, backup)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged, target)
    except Exception:
        if had_previous and _path_exists(backup):
            os.replace(backup, target)
        raise
    committed.append((target, backup, had_previous))


def _rollback(committed: list[tuple[Path, Path, bool]]) -> list[str]:
    errors: list[str] = []
    for target, backup, had_previous in reversed(committed):
        try:
            _remove_path(target)
            if had_previous and _path_exists(backup):
                os.replace(backup, target)
        except Exception as exc:
            errors.append(f"{target}: {exc}")
    return errors


def install_from_source(source: Path, root: Path, expected_version: str = "") -> dict[str, Any]:
    """从已检出的 Mino 源目录安装，成功后返回结构化结果。"""
    source = source.expanduser().resolve(strict=True)
    root = root.expanduser().absolute()
    if root.is_symlink():
        raise InstallError(f"技能根目录是软链，拒绝继续安装: {root}")

    version = _read_version(source)
    if not _is_semver(version):
        raise InstallError(f"安装源 VERSION 无效: {version!r}")
    expected = str(expected_version or "").strip().lstrip("vV")
    if expected and (not _is_semver(expected) or version != expected):
        raise InstallError(f"安装源版本 {version} 与期望版本 {expected or '<empty>'} 不一致")

    names = _skill_names(source)
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".mino-install-", dir=root.parent))
    committed: list[tuple[Path, Path, bool]] = []
    try:
        _prepare_staging(source, names, staging)
        root.mkdir(parents=True, exist_ok=True)
        staged_skills = staging / "staged"
        for name in names:
            backup = staging / "backup" / name
            _commit_path(staged_skills / name, root / name, backup, committed)
        for metadata in ("VERSION", "CHANGELOG.md"):
            staged = staged_skills / metadata
            if staged.is_file():
                backup = staging / "backup" / metadata
                _commit_path(staged, root / metadata, backup, committed)
    except Exception as exc:
        rollback_errors = _rollback(committed)
        if rollback_errors:
            raise InstallError(
                f"安装失败且回滚未完成: {exc}; 恢复目录保留在 {staging}; "
                + "; ".join(rollback_errors)
            ) from exc
        shutil.rmtree(staging, ignore_errors=True)
        raise InstallError(f"安装失败，已回滚: {exc}") from exc

    shutil.rmtree(staging, ignore_errors=True)
    return {
        "ok": True,
        "root": str(root),
        "version": version,
        "skills": names,
        "changed": True,
        "requires_new_session": True,
    }


def _clone_repository(repo: str, ref: str, destination: Path, timeout: float) -> Path:
    git = shutil.which("git")
    if not git:
        raise InstallError("PATH 中没有 git，无法从 GitHub 安装")
    checkout = destination / "mino"
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        [git, "clone", "--depth", "1", "--branch", ref, "--single-branch", repo, str(checkout)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise InstallError(f"git clone 失败: {detail}")
    return checkout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="", help="技能根目录；默认 $CODEX_HOME/skills 或 ~/.codex/skills")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub 仓库，默认 {DEFAULT_REPO}")
    parser.add_argument("--ref", default="main", help="Git 分支或标签，默认 main")
    parser.add_argument("--expected-version", default="", help="要求安装源精确匹配的版本")
    parser.add_argument("--source-dir", default="", help="使用已检出的源目录，仅供本地安装与测试")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--json", action="store_true", help="兼容参数；始终输出 JSON")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser() if args.root else default_skill_root()
    timeout = max(10.0, min(args.timeout, 600.0))
    try:
        if args.source_dir:
            result = install_from_source(Path(args.source_dir), root, args.expected_version)
        else:
            with tempfile.TemporaryDirectory(prefix="mino-install-clone-") as temp:
                checkout = _clone_repository(args.repo, args.ref, Path(temp), timeout)
                result = install_from_source(checkout, root, args.expected_version)
    except (InstallError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "root": str(root), "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
