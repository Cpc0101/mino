#!/usr/bin/env python3
"""只读检查 Mino Skill 与本机 mino-scout 是否有更新。"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

SKILL_VERSION_URL = "https://raw.githubusercontent.com/pengchengluoyi/mino/main/VERSION"
SCOUT_MANIFEST_URL = "https://github.com/Cpc0101/MinoScout/releases/latest/download/manifest.json"
DEFAULT_SKILL_ROOTS = ("~/.codex/skills", "~/.cursor/skills", "~/.claude/skills")
DEFAULT_ROUTING_POLICY = "~/.codex/AGENTS.md"
SEMVER = re.compile(r"^[vV]?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


def _semver(value: str) -> tuple[int, int, int] | None:
    match = SEMVER.match(str(value or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def _read_version(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip().lstrip("vV")
    except OSError:
        return ""


def _fetch_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "mino-skill-update-check/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8").strip()


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    data = json.loads(_fetch_text(url, timeout))
    if not isinstance(data, dict):
        raise ValueError("manifest 不是对象")
    return data


def _skill_roots() -> list[Path]:
    configured = os.environ.get("MINO_SKILL_ROOTS", "").strip()
    if configured:
        return [Path(item).expanduser() for item in configured.split(os.pathsep) if item.strip()]
    return [Path(item).expanduser() for item in DEFAULT_SKILL_ROOTS if Path(item).expanduser().exists()]


def _compare_state(current: str, latest: str) -> str:
    current_semver = _semver(current)
    latest_semver = _semver(latest)
    if not current_semver or not latest_semver:
        return "unknown"
    return "update_available" if current_semver < latest_semver else "current"


def _check_skills(latest: str, latest_error: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    needs_update: list[str] = []
    for root in _skill_roots():
        current = _read_version(root / "VERSION")
        row: dict[str, Any] = {
            "root": str(root),
            "current": current,
            "latest": latest,
            "state": "not_installed" if not current else "unknown",
        }
        if not current:
            row["reason"] = "未找到技能根目录的 VERSION"
        elif not latest:
            row["reason"] = latest_error or "无法读取最新技能版本"
        else:
            row["state"] = _compare_state(current, latest)
            if row["state"] == "update_available":
                needs_update.append(f"skill:{root}")
        rows.append(row)
    return rows, needs_update


def _scout_status_version(timeout: float) -> str:
    exe = shutil.which("mino-scout")
    if not exe:
        return ""
    try:
        result = subprocess.run(
            [exe, "status"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        data = json.loads(result.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("version") or data.get("app_semver") or data.get("reported_version") or "").strip().lstrip("vV")


def _platform_arch() -> tuple[str, str]:
    os_name = {"Darwin": "darwin", "Windows": "win32", "Linux": "linux"}.get(platform.system(), "")
    machine = platform.machine().lower()
    arch = {"arm64": "arm64", "aarch64": "arm64", "amd64": "x64", "x86_64": "x64"}.get(machine, "")
    return os_name, arch


def _manifest_latest(manifest: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    want_os, want_arch = _platform_arch()
    items = manifest.get("items")
    if isinstance(items, list):
        for row in items:
            if not isinstance(row, dict) or not row.get("url"):
                continue
            if str(row.get("os") or "").lower() == want_os and str(row.get("arch") or "").lower() == want_arch:
                return str(row.get("version") or manifest.get("version") or "").strip().lstrip("vV"), row
        raise ValueError(f"manifest 中没有 {want_os}-{want_arch} 安装包")
    return str(manifest.get("version") or "").strip().lstrip("vV"), manifest


def _fallback_scout_check(timeout: float) -> dict[str, Any]:
    current = _scout_status_version(timeout)
    if not current:
        return {"state": "unknown", "reason": "旧版 mino-scout 不支持 update-check，且无法读取 status 版本"}
    url = os.environ.get("MINO_SCOUT_MANIFEST_URL", "").strip() or SCOUT_MANIFEST_URL
    try:
        manifest = _fetch_json(url, timeout)
        latest, row = _manifest_latest(manifest)
    except Exception as exc:
        return {
            "state": "unknown",
            "current": current,
            "reason": f"旧版 mino-scout 不支持 update-check；manifest 不可用: {exc}",
            "method": "status+manifest",
        }
    return {
        "state": _compare_state(current, latest),
        "current": current,
        "latest": latest,
        "build_id": str(manifest.get("build_id") or row.get("build_id") or latest),
        "release_tag": str(manifest.get("release_tag") or ("v" + latest if latest else "")),
        "manifest_url": url,
        "requires_confirmation": True,
        "method": "status+manifest",
    }


def _check_scout(timeout: float) -> tuple[dict[str, Any], list[str]]:
    exe = shutil.which("mino-scout")
    if not exe:
        return {"state": "not_installed", "reason": "PATH 中没有 mino-scout"}, []
    try:
        result = subprocess.run(
            [exe, "update-check"],
            capture_output=True,
            text=True,
            timeout=max(timeout, 15),
            check=False,
        )
        data = json.loads(result.stdout or "{}")
        if result.returncode == 0 and isinstance(data, dict) and data.get("ok"):
            data["state"] = "update_available" if data.get("update_available") else "current"
            data["method"] = "mino-scout update-check"
            return data, ["scout"] if data["state"] == "update_available" else []
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    fallback = _fallback_scout_check(timeout)
    return fallback, ["scout"] if fallback.get("state") == "update_available" else []


def _check_routing_policy() -> dict[str, Any]:
    target = os.environ.get("MINO_ROUTING_POLICY_PATH", "").strip() or DEFAULT_ROUTING_POLICY
    try:
        from install_routing_policy import PolicyConflict, inspect_policy

        result = inspect_policy(target)
    except PolicyConflict as exc:
        return {"path": target, "state": "conflict", "reason": str(exc)}
    except Exception as exc:
        return {"path": target, "state": "error", "reason": str(exc)}
    result["requires_action"] = result.get("state") != "current"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="兼容参数；始终输出 JSON")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args(argv)
    timeout = max(1.0, min(args.timeout, 30.0))

    latest = os.environ.get("MINO_SKILL_LATEST_VERSION", "").strip().lstrip("vV")
    latest_error = ""
    if not latest:
        url = os.environ.get("MINO_SKILL_VERSION_URL", "").strip() or SKILL_VERSION_URL
        try:
            latest = _fetch_text(url, timeout).lstrip("vV")
        except Exception as exc:
            latest_error = f"无法读取最新技能版本: {exc}"

    skills, needs_update = _check_skills(latest, latest_error)
    scout, scout_needs_update = _check_scout(timeout)
    routing_policy = _check_routing_policy()
    needs_update.extend(scout_needs_update)
    unknown_checks = [f"skill:{row.get('root')}" for row in skills if row.get("state") == "unknown"]
    if scout.get("state") == "unknown":
        unknown_checks.append("scout")
    not_installed_checks = [
        f"skill:{row.get('root')}" for row in skills if row.get("state") == "not_installed"
    ]
    if scout.get("state") == "not_installed":
        not_installed_checks.append("scout")
    installed_skill_states = [row.get("state") for row in skills if row.get("state") != "not_installed"]
    if needs_update:
        overall_state = "update_available"
    elif unknown_checks:
        overall_state = "unknown"
    elif not installed_skill_states or scout.get("state") == "not_installed":
        overall_state = "not_installed"
    else:
        overall_state = "current"
    out = {
        "schema": 2,
        "checked_at": int(time.time()),
        "overall_state": overall_state,
        "check_complete": not unknown_checks,
        "skills": skills,
        "scout": scout,
        "routing_policy": routing_policy,
        "update_available": bool(needs_update),
        "needs_update": needs_update,
        "unknown_checks": unknown_checks,
        "not_installed_checks": not_installed_checks,
        "startup_policy": (
            "有更新时先读 update-skills 更新技能；技能需新会话生效。"
            "Scout 用固定 build_id/release_tag 更新，执行前必须向用户说明影响并取得确认。"
            "routing_policy 不是 current 时，经用户确认后用 install_routing_policy.py --apply 安装；"
            "AGENTS.md 变更通常需要新会话生效。"
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
