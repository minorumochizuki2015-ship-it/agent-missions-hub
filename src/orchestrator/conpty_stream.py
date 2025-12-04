from __future__ import annotations

import contextlib
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO
from uuid import UUID

StreamSession = tuple[subprocess.Popen[str], Path]
_STREAM_REGISTRY: dict[str, tuple[StreamSession, str | None, str]] = {}


def _append(trace_path: Path, label: str, content: str) -> None:
    """ストリーム行をログへ追記する。"""
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(f"[{label}] {content}")


def spawn_stream_session(
    *,
    command: list[str],
    mission_id: UUID,
    run_id: UUID,
    trace_dir: Path | None,
    command_index: int | None,
    role: str | None,
    timeout: float | None = None,
    register: bool = True,
) -> StreamSession:
    """ストリームモードで CLI を起動し、ヘッダ付きログを作成する。"""
    target_dir = trace_dir or Path("data/logs/current/audit/cli_runs")
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_cmd{command_index}" if command_index is not None else ""
    trace_path = target_dir / f"{run_id}{suffix}.log"
    header = [
        f"# Timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"# Mission ID: {mission_id}",
        f"# Run ID: {run_id}",
        f"# Command: {' '.join(command)}",
    ]
    if role:
        header.append(f"# Role: {role}")
    trace_path.write_text("\n".join(header) + "\n", encoding="utf-8")

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith("win") else 0
        ),
    )

    def _pump(stream: TextIO, label: str) -> None:
        """標準出力/標準エラーを行単位で追記する。"""
        for line in iter(stream.readline, ""):
            _append(trace_path, label, line)
        with contextlib.suppress(Exception):
            stream.close()
    for stream, label in ((proc.stdout, "STDOUT"), (proc.stderr, "STDERR")):
        if stream:
            threading.Thread(target=_pump, args=(stream, label), daemon=True).start()
    session = (proc, trace_path)
    if register:
        _STREAM_REGISTRY[str(run_id)] = (session, role, str(mission_id))
    return session


def get_stream_session(run_id: UUID | str) -> StreamSession:
    """run_id をキーにセッションを取得する。"""
    handle = _STREAM_REGISTRY.get(str(run_id))
    if handle is None:
        raise KeyError(f"run_id not found: {run_id}")
    return handle[0]


def get_stream_session_meta(run_id: UUID | str) -> tuple[StreamSession, str | None, str]:
    """セッションと role, mission_id を取得する。"""
    handle = _STREAM_REGISTRY.get(str(run_id))
    if handle is None:
        raise KeyError(f"run_id not found: {run_id}")
    return handle


def wait_stream_session(session: StreamSession, timeout: float | None = None) -> int:
    """終了を待ち、戻り値をログに記録する。"""
    proc, trace_path = session
    code = proc.wait(timeout=timeout)
    _append(trace_path, "RETURN", f"{code}\n")
    return code


def terminate_stream_session(session: StreamSession, timeout: float | None = None) -> int:
    """タイムアウト付きで終了させ、戻り値を記録する。"""
    proc, trace_path = session
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        code = proc.wait(timeout=timeout or 5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        code = proc.wait()
    _append(trace_path, "RETURN", f"{code}\n")
    return code


def send_stream_line(session: StreamSession, text: str) -> None:
    """stdin に1行を書き込み、ログにも残す。"""
    proc, trace_path = session
    if proc.stdin is None or proc.stdin.closed:
        raise RuntimeError("stdin が利用できません")
    line = text if text.endswith("\n") else f"{text}\n"
    proc.stdin.write(line)
    proc.stdin.flush()
    _append(trace_path, "STDIN", line)
