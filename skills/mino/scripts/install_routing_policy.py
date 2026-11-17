#!/usr/bin/env python3
"""检查、安装或移除 AGENTS.md 中的 Mino 持久路由策略块。"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

START_MARKER = "<!-- mino-routing:start -->"
END_MARKER = "<!-- mino-routing:end -->"
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_DIR / "assets" / "mino-routing.md"


def default_target() -> Path:
    """优先遵循 CODEX_HOME，未设置时使用标准 Codex 目录。"""
    codex_home = os.environ.get("CODEX_HOME", "").strip() or "~/.codex"
    return Path(codex_home).expanduser() / "AGENTS.md"


class PolicyConflict(RuntimeError):
    """目标文件中的托管标记无法安全解析。"""


def _template_block() -> str:
    try:
        text = TEMPLATE_PATH.read_bytes().decode("utf-8")
    except OSError as exc:
        raise PolicyConflict(f"无法读取策略模板 {TEMPLATE_PATH}: {exc}") from exc
    text = text.replace("\r\n", "\n")
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise PolicyConflict("策略模板必须恰好包含一对 Mino 路由标记")
    if text.index(START_MARKER) >= text.index(END_MARKER):
        raise PolicyConflict("策略模板标记顺序错误")
    return text.strip("\n") + "\n"


def _detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _render_block(newline: str) -> str:
    return _template_block().replace("\n", newline)


def _read_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return ""
    except (OSError, UnicodeDecodeError) as exc:
        raise PolicyConflict(f"无法读取 {path}: {exc}") from exc


def _managed_span(text: str) -> tuple[int, int] | None:
    starts = text.count(START_MARKER)
    ends = text.count(END_MARKER)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise PolicyConflict("目标文件中的 Mino 路由标记缺失或重复")

    lines = text.splitlines(keepends=True)
    start_line = end_line = -1
    for index, line in enumerate(lines):
        token = line.rstrip("\r\n").strip()
        if token == START_MARKER:
            start_line = index
        elif token == END_MARKER:
            end_line = index
    if start_line < 0 or end_line < 0 or start_line >= end_line:
        raise PolicyConflict("目标文件中的 Mino 路由标记顺序错误")

    start = sum(len(line) for line in lines[:start_line])
    end = sum(len(line) for line in lines[: end_line + 1])
    return start, end


def _status(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "state": "missing", "changed": False}
    if not path.exists():
        result["reason"] = "AGENTS.md 不存在"
        return result
    text = _read_text(path)
    span = _managed_span(text)
    if span is None:
        result["reason"] = "未安装 Mino 托管块"
        return result
    current = text[span[0] : span[1]]
    expected = _render_block(_detect_newline(text))
    if current == expected:
        result["state"] = "current"
    else:
        result["state"] = "outdated"
        result["reason"] = "Mino 托管块与当前 Skill 不一致"
    return result


def inspect_policy(path: str | Path | None = None) -> dict[str, Any]:
    """返回托管块状态，不创建或修改目标文件。"""
    target = default_target() if path is None else Path(path).expanduser()
    return _status(target)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temp_name = tempfile.mkstemp(prefix=".mino-routing-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8"))
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


def _write_target(path: Path) -> Path:
    if not path.is_symlink():
        return path
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise PolicyConflict(f"目标文件是失效软链，拒绝替换软链本身: {path}") from exc
    if not resolved.is_file():
        raise PolicyConflict(f"软链目标不是普通文件: {resolved}")
    return resolved


def _separator(text: str, newline: str) -> str:
    if not text:
        return ""
    if text.endswith(newline + newline):
        return ""
    if text.endswith("\n") or text.endswith("\r"):
        return newline
    return newline + newline


def _apply(path: Path) -> dict[str, Any]:
    existing = _read_text(path)
    newline = _detect_newline(existing)
    block = _render_block(newline)
    span = _managed_span(existing)
    if span is None:
        updated = existing + _separator(existing, newline) + block
    else:
        updated = existing[: span[0]] + block + existing[span[1] :]
    changed = updated != existing
    if changed:
        _atomic_write(path, updated)
    return {
        "path": str(path),
        "state": "current",
        "changed": changed,
        "requires_new_session": changed,
    }


def _remove(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "state": "missing", "changed": False}
    existing = _read_text(path)
    span = _managed_span(existing)
    if span is None:
        return {"path": str(path), "state": "missing", "changed": False}
    updated = existing[: span[0]] + existing[span[1] :]
    _atomic_write(path, updated)
    return {
        "path": str(path),
        "state": "removed",
        "changed": True,
        "requires_new_session": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="只读检查（默认）")
    action.add_argument("--apply", action="store_true", help="安装或刷新托管块")
    action.add_argument("--remove", action="store_true", help="只移除托管块")
    parser.add_argument(
        "--path",
        default="",
        help="目标文件，默认 $CODEX_HOME/AGENTS.md（未设置时为 ~/.codex/AGENTS.md）",
    )
    args = parser.parse_args(argv)
    path = Path(args.path).expanduser() if args.path else default_target()

    try:
        if args.apply:
            result = _apply(_write_target(path))
        elif args.remove:
            result = _remove(_write_target(path))
        else:
            result = _status(path)
    except PolicyConflict as exc:
        result = {"path": str(path), "state": "conflict", "changed": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    except OSError as exc:
        result = {"path": str(path), "state": "error", "changed": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result["path"] = str(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.check:
        return 0 if result.get("state") == "current" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
