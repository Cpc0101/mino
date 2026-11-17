#!/usr/bin/env python3
"""只读检查 Mino Skill 与本机 mino-scout 是否有更新。"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

SKILL_VERSION_API_URL = "https://api.github.com/repos/Cpc0101/mino/contents/VERSION?ref=main"
SKILL_VERSION_URL = "https://raw.githubusercontent.com/Cpc0101/mino/main/VERSION"
SCOUT_MANIFEST_URL = "https://github.com/Cpc0101/MinoScout/releases/latest/download/manifest.json"
SEMVER = re.compile(r"^[vV]?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


def _semver(value: str) -> tuple[int, int, int] | None:
    match = SEMVER.match(str(value or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def _read_version(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip().lstrip("vV")
    except OSError:
        return ""


def _ssl_context() -> ssl.SSLContext:
    """优先使用 certifi，兼容 macOS Python 未配置系统根证书的环境。"""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError, ssl.SSLError):
        return ssl.create_default_context()


def _fetch_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "mino-skill-update-check/1"})
    context = _ssl_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.read().decode("utf-8").strip()
    except (OSError, ValueError) as urllib_error:
        # 部分 Python 发行版没有可用根证书；curl 会使用系统证书链。
        curl = shutil.which("curl")
        if not curl:
            raise
        result = subprocess.run(
            [
                curl,
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                f"{timeout:.3f}",
                "--user-agent",
                "mino-skill-update-check/1",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or "").strip()
            raise RuntimeError(f"{urllib_error}; curl 兜底失败: {detail}") from urllib_error
        return result.stdout.strip()


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    data = json.loads(_fetch_text(url, timeout))
    if not isinstance(data, dict):
        raise ValueError("manifest 不是对象")
    return data


def _github_content_version(payload: dict[str, Any]) -> str:
    """从 GitHub Contents API 的 base64 响应中读取 VERSION。"""
    if str(payload.get("encoding") or "").lower() != "base64":
        raise ValueError("GitHub Contents API 未返回 base64 内容")
    content = str(payload.get("content") or "").replace("\n", "").replace("\r", "").strip()
    if not content:
        raise ValueError("GitHub Contents API 未返回 VERSION 内容")
    try:
        text = base64.b64decode(content, validate=True).decode("utf-8").strip()
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("GitHub Contents API 返回的 VERSION 无法解码") from exc
    version = text.lstrip("vV")
    if not _semver(version):
        raise ValueError(f"GitHub Contents API 返回了无效版本: {text!r}")
    return version


def _fetch_latest_skill_version(timeout: float) -> tuple[str, str]:
    """优先用 GitHub API 避开 raw CDN 缓存，失败后再回退 raw。"""
    override = os.environ.get("MINO_SKILL_VERSION_URL", "").strip()
    if override:
        version = _fetch_text(override, timeout).lstrip("vV")
        if not _semver(version):
            raise ValueError(f"自定义版本地址返回了无效版本: {version!r}")
        return version, "override"

    errors: list[str] = []
    try:
        version = _github_content_version(_fetch_json(SKILL_VERSION_API_URL, timeout))
        return version, "github-api"
    except Exception as exc:
        errors.append(f"GitHub API: {exc}")

    try:
        version = _fetch_text(SKILL_VERSION_URL, timeout).lstrip("vV")
        if not _semver(version):
            raise ValueError(f"VERSION 内容无效: {version!r}")
        return version, "raw"
    except Exception as exc:
        errors.append(f"raw: {exc}")

    raise RuntimeError("; ".join(errors))


def _skill_roots() -> list[Path]:
    configured = os.environ.get("MINO_SKILL_ROOTS", "").strip()
    if configured:
        return [Path(item).expanduser() for item in configured.split(os.pathsep) if item.strip()]
    codex_home = os.environ.get("CODEX_HOME", "").strip() or "~/.codex"
    defaults = ("cursor", "claude")
    candidates = [Path(codex_home).expanduser() / "skills"]
    candidates.extend(Path(f"~/.{name}/skills").expanduser() for name in defaults)
    return [path for path in candidates if path.exists()]


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
    target = os.environ.get("MINO_ROUTING_POLICY_PATH", "").strip()
    policy_path = Path(target).expanduser() if target else (
        Path(os.environ.get("CODEX_HOME", "").strip() or "~/.codex").expanduser() / "AGENTS.md"
    )
    try:
        from install_routing_policy import PolicyConflict, inspect_policy
    except Exception as exc:
        return {"path": str(policy_path), "state": "error", "reason": str(exc)}
    try:
        result = inspect_policy(policy_path)
    except PolicyConflict as exc:
        return {"path": str(policy_path), "state": "conflict", "reason": str(exc)}
    except Exception as exc:
        return {"path": str(policy_path), "state": "error", "reason": str(exc)}
    result["requires_action"] = result.get("state") != "current"
    return result


def _routing_action(policy: dict[str, Any]) -> dict[str, Any] | None:
    state = str(policy.get("state") or "")
    if state == "current":
        return None
    path = str(policy.get("path") or "")
    if state == "conflict":
        return {
            "id": "routing_policy",
            "kind": "resolve_conflict",
            "requires_user_confirmation": True,
            "path": path,
            "question": (
                f"Mino 持久路由文件 {path} 的托管标记存在冲突。是否允许我协助你检查并修复？"
                "修复前不会覆盖现有文件。"
            ),
            "impact": "不修复时，后续会话可能继续优先使用平台 Computer Use。",
            "command": None,
        }
    if state == "error":
        return {
            "id": "routing_policy",
            "kind": "repair_error",
            "requires_user_confirmation": True,
            "path": path,
            "question": f"Mino 无法确认持久路由文件 {path} 的状态。是否允许我检查并修复？",
            "impact": "不修复时，后续会话可能继续优先使用平台 Computer Use。",
            "command": None,
        }
    installer = Path(__file__).resolve().with_name("install_routing_policy.py")
    return {
        "id": "routing_policy",
        "kind": "install_routing_policy",
        "requires_user_confirmation": True,
        "path": path,
        "question": (
            f"Mino 检测到跨会话路由尚未安装或需要刷新（{state}）。"
            f"是否允许我写入托管路由块到 {path}？"
        ),
        "impact": (
            "它会让后续 Codex 会话优先使用 Mino MCP/Scout，而不是平台 Computer Use；"
            "只修改 mino-routing 标记之间的内容，变更后建议新开会话。"
        ),
        "requires_new_session": True,
        "command": [sys.executable, str(installer), "--apply", "--path", path],
    }


def _build_consent_actions(
    skills: list[dict[str, Any]],
    scout: dict[str, Any],
    routing_policy: dict[str, Any],
) -> list[dict[str, Any]]:
    """生成需要用户逐项确认的安装/更新动作，不在检查阶段执行任何写入。"""
    actions: list[dict[str, Any]] = []
    for row in skills:
        if row.get("state") != "update_available":
            continue
        current = str(row.get("current") or "unknown")
        latest = str(row.get("latest") or "unknown")
        root = str(row.get("root") or "")
        installer = Path(__file__).resolve().with_name("install_skills.py")
        actions.append(
            {
                "id": f"skill:{root}",
                "kind": "update_skill",
                "requires_user_confirmation": True,
                "root": root,
                "current": current,
                "latest": latest,
                "question": (
                    f"检测到 Mino Skill 可从 {current} 更新到 {latest}，安装位置为 {root}。"
                    "是否允许我现在更新？更新后通常需要新开会话才能加载。"
                ),
                "impact": "未确认前不修改已安装 Skill；当前会话继续时仍按现有 Skill 约束执行。",
                "requires_new_session": True,
                "command": [
                    sys.executable,
                    str(installer),
                    "--root",
                    root,
                    "--ref",
                    "main",
                    "--expected-version",
                    latest,
                ],
            }
        )

    if scout.get("state") == "not_installed":
        actions.append(
            {
                "id": "scout",
                "kind": "install_scout",
                "requires_user_confirmation": True,
                "question": (
                    "本机尚未安装 Mino Scout。是否允许我通过 Mino MCP 申请一次性安装凭证，"
                    "并在这台电脑安装 Scout？"
                ),
                "impact": (
                    "安装会注册本机 Scout 服务并连接当前 Mino 账号；一次性安装凭证不会出现在对话中。"
                    "未确认前不会申请凭证或执行安装。"
                ),
                "requires_new_session": False,
                "next_step": "调用 agent_guide，再调用 MCP scout_install_token 获取本机安装请求。",
                "command": None,
            }
        )
    elif scout.get("state") == "update_available":
        current = str(scout.get("current") or "unknown")
        latest = str(scout.get("latest") or "unknown")
        build_id = str(scout.get("build_id") or "")
        release_tag = str(scout.get("release_tag") or "")
        digest = hashlib.sha256("|".join((current, latest, build_id, release_tag)).encode()).hexdigest()[:16]
        operation_id = f"mino-scout-{digest}"
        scout_exe = shutil.which("mino-scout")
        command: list[str] | None = None
        if scout_exe and scout.get("method") == "mino-scout update-check":
            command = [
                scout_exe,
                "update",
                "--release-tag",
                release_tag,
                "--build-id",
                build_id,
                "--operation-id",
                operation_id,
            ]
        actions.append(
            {
                "id": "scout",
                "kind": "update_scout",
                "requires_user_confirmation": True,
                "current": current,
                "latest": latest,
                "build_id": build_id,
                "release_tag": release_tag,
                "operation_id": operation_id,
                "question": (
                    f"检测到本机 MinoScout 可从 {current} 更新到 {latest}。"
                    "更新会停止或替换 Scout，可能中断正在执行的任务。是否允许我现在更新？"
                ),
                "impact": "必须使用预检返回的固定 build_id/release_tag；不要重放结果未知的写操作。",
                "requires_new_session": False,
                "service_interruption": True,
                "command": command,
            }
        )

    routing = _routing_action(routing_policy)
    if routing:
        actions.append(routing)
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="兼容参数；始终输出 JSON")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args(argv)
    timeout = max(1.0, min(args.timeout, 30.0))

    latest = os.environ.get("MINO_SKILL_LATEST_VERSION", "").strip().lstrip("vV")
    latest_source = "override" if latest else ""
    latest_error = ""
    if not latest:
        try:
            latest, latest_source = _fetch_latest_skill_version(timeout)
        except Exception as exc:
            latest_error = f"无法读取最新技能版本: {exc}"

    skills, needs_update = _check_skills(latest, latest_error)
    scout, scout_needs_update = _check_scout(timeout)
    routing_policy = _check_routing_policy()
    actions = _build_consent_actions(skills, scout, routing_policy)
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
    elif actions:
        overall_state = "action_required"
    else:
        overall_state = "current"
    out = {
        "schema": 3,
        "checked_at": int(time.time()),
        "overall_state": overall_state,
        "check_complete": not unknown_checks,
        "skill_latest_source": latest_source,
        "skills": skills,
        "scout": scout,
        "routing_policy": routing_policy,
        "update_available": bool(needs_update),
        "needs_update": needs_update,
        "consent_required": bool(actions),
        "consent_actions": actions,
        "unknown_checks": unknown_checks,
        "not_installed_checks": not_installed_checks,
        "startup_policy": (
            "consent_actions 非空时，Agent 必须先向用户说明影响并取得明确同意，不得静默安装或更新。"
            "Skill 更新需新开会话生效；Scout 必须使用固定 build_id/release_tag；"
            "routing_policy 不是 current 时询问用户后再用 install_routing_policy.py --apply。"
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
