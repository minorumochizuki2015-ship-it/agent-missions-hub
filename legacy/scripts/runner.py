from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

DEFAULT_TIMEOUTS = {
    "short": 300,
    "medium": 1200,
    "long": 1800,
}
PROTECTED_GIT_SUBCOMMANDS = {"add", "commit", "push"}
DELETE_COMMANDS = {"rm", "remove-item"}


def _parse_args() -> argparse.Namespace:
    """runner.py 専用の CLI 引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="テスト・ビルドを安全に実行するためのガード付きラッパー"
    )
    parser.add_argument(
        "--profile",
        choices=tuple(DEFAULT_TIMEOUTS.keys()),
        default="short",
        help="想定コスト別のタイムアウト設定 (short=5分/medium=20分/long=30分)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="秒指定タイムアウト(profile より優先)",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="実行ディレクトリ (省略時は現在のカレントディレクトリ)",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="実行したいコマンド。runner.py の引数の後ろに -- を挟むと確実です。",
    )
    args = parser.parse_args()
    if not args.command:
        parser.error("実行するコマンドを指定してください (例: runner.py -- pytest -q)")
    return args


def _enforce_guardrails(argv: Sequence[str]) -> None:
    """危険コマンドの実行可否をチェックし、禁止なら例外を送出する。"""
    allow_git_write = os.getenv("RUNNER_ALLOW_GIT_WRITE") == "1"
    allow_delete = os.getenv("RUNNER_ALLOW_DELETE") == "1"
    first = argv[0].lower()

    if first == "git" and len(argv) > 1:
        sub = argv[1].lower()
        if sub in PROTECTED_GIT_SUBCOMMANDS and not allow_git_write:
            raise PermissionError(
                "git add/commit/push は RUNNER_ALLOW_GIT_WRITE=1 指定時のみ実行できます。"
            )
        if sub == "rm" and not allow_delete:
            raise PermissionError("git rm は RUNNER_ALLOW_DELETE=1 指定時のみ実行できます。")

    if first in DELETE_COMMANDS and not allow_delete:
        raise PermissionError(f"{argv[0]} は RUNNER_ALLOW_DELETE=1 指定時のみ実行できます。")


def _current_ts() -> str:
    """UTC 基準のタイムスタンプ文字列を生成する。"""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _log_entry(entry: dict) -> None:
    """実行結果を JSON Lines 形式で保存する。"""
    log_dir = Path("data") / "logs" / "current" / "runner"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"runner_{_current_ts()}.jsonl"
    log_path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    """runner のエントリーポイント。"""
    args = _parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("実行コマンドが空です (-- の後ろにコマンドを置いてください)", file=sys.stderr)
        return 2

    try:
        _enforce_guardrails(command)
    except PermissionError as err:
        entry = {
            "status": "blocked",
            "reason": str(err),
            "command": command,
            "cwd": str(args.cwd),
            "ts": _current_ts(),
        }
        _log_entry(entry)
        print(str(err), file=sys.stderr)
        return 126

    timeout = args.timeout or DEFAULT_TIMEOUTS[args.profile]
    start = datetime.now(timezone.utc)
    result: dict[str, object] = {
        "command": command,
        "cwd": str(args.cwd),
        "profile": args.profile,
        "timeout_sec": timeout,
        "ts_start": start.isoformat(),
    }

    try:
        proc = subprocess.run(
            command,
            cwd=args.cwd,
            timeout=timeout,
            check=False,
        )
        result["exit_code"] = proc.returncode
        result["status"] = "ok" if proc.returncode == 0 else "error"
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["exit_code"] = None
        exit_code = 124
    except KeyboardInterrupt:
        result["status"] = "interrupted"
        result["exit_code"] = 130
        exit_code = 130

    end = datetime.now(timezone.utc)
    result["ts_end"] = end.isoformat()
    result["duration_sec"] = (end - start).total_seconds()
    _log_entry(result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
