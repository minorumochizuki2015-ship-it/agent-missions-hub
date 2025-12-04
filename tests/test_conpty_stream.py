"""conpty_stream の最小ストリーム検証。"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from orchestrator.conpty_stream import spawn_stream_session, wait_stream_session


def test_stream_logs_stdout(tmp_path: Path) -> None:
    """STDOUT がログに記録されることを確認する。"""
    session = spawn_stream_session(
        command=[sys.executable, "-c", "print('hello')"],
        mission_id=uuid4(),
        run_id=uuid4(),
        trace_dir=tmp_path,
        command_index=None,
        role="tester",
    )
    proc, trace_path = session
    exit_code = wait_stream_session(session, timeout=5.0)
    assert exit_code == 0
    assert "hello" in trace_path.read_text(encoding="utf-8")
    assert proc.poll() is not None
