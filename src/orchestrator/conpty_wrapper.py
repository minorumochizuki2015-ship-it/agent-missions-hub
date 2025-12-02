"""ConPTY wrapper for spawning agent CLI subprocesses with logging."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


def load_engine_config(engine_name: str = "demo") -> dict[str, Any]:
    """Load engine configuration from config/engines.yaml with fallback."""
    fallback = {"command": [sys.executable, "-c", "print('demo')"], "workdir": None}
    try:
        import yaml  # type: ignore
    except Exception:
        return fallback

    config_path = Path("config/engines.yaml")
    if not config_path.exists():
        return fallback

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        engines = data.get("engines", {}) if isinstance(data, dict) else {}
        engine = engines.get(engine_name, {}) if isinstance(engines, dict) else {}
        command = (
            engine.get("command", fallback["command"])
            if isinstance(engine, dict)
            else fallback["command"]
        )
        workdir = (
            engine.get("workdir", fallback["workdir"])
            if isinstance(engine, dict)
            else fallback["workdir"]
        )
        return {"command": command, "workdir": workdir}
    except Exception:
        return fallback


def spawn_agent_cli(
    command: list[str],
    mission_id: UUID,
    run_id: UUID,
    trace_dir: Path | None = None,
    timeout: float = 300.0,
    command_index: int | None = None,
    role: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    エージェント CLI を ConPTY で起動し、run_id 単位でトレースを残す。

    Args:
        command: 実行する CLI コマンド
        mission_id: ログ用 Mission UUID
        run_id: Workflow run UUID
        trace_dir: ログ保存先(省略時 data/logs/current/audit/cli_runs)
        timeout: タイムアウト(秒)
        command_index: 複数起動時のインデックス(ログ分離用)
        role: ロール名(任意、ログ用)
    """
    # Prepare trace directory and file
    target_dir = trace_dir or Path("data/logs/current/audit/cli_runs")
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_cmd{command_index}" if command_index is not None else ""
    trace_path = target_dir / f"{run_id}{suffix}.log"

    # Windows ConPTY support via CREATE_NEW_PROCESS_GROUP
    # On Linux/Mac, this flag is ignored
    creation_flags = (
        subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith("win") else 0
    )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=creation_flags,
        )

        # Save execution trace to log file
        _write_trace_log(
            trace_path,
            mission_id,
            run_id,
            command,
            result,
            None,
            command_index=command_index,
            role=role,
        )

        return result

    except Exception as e:
        # Log failure details
        _write_trace_log(
            trace_path,
            mission_id,
            run_id,
            command,
            None,
            e,
            command_index=command_index,
            role=role,
        )
        raise


def _write_trace_log(
    trace_path: Path,
    mission_id: UUID,
    run_id: UUID,
    command: list[str],
    result: subprocess.CompletedProcess[str] | None,
    error: Exception | None,
    command_index: int | None = None,
    role: str | None = None,
) -> None:
    """CLI 実行トレースをログに出力する。"""
    with trace_path.open("w", encoding="utf-8") as f:
        f.write(f"# Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"# Mission ID: {mission_id}\n")
        f.write(f"# Run ID: {run_id}\n")
        if command_index is not None:
            f.write(f"# Command Index: {command_index}\n")
        if role:
            f.write(f"# Role: {role}\n")
        f.write(f"# Command: {' '.join(command)}\n\n")

        if error:
            f.write(f"=== ERROR ===\n{error}\n")
        elif result:
            f.write(f"=== RETURN CODE ===\n{result.returncode}\n\n")
            f.write(f"=== STDOUT ({len(result.stdout)} chars) ===\n")
            f.write(result.stdout or "(empty)\n\n")
            f.write(f"=== STDERR ({len(result.stderr)} chars) ===\n")
            f.write(result.stderr or "(empty)\n")
