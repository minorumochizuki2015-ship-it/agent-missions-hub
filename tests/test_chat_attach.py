"""chat attach の最小検証。"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import orchestrator.conpty_stream as stream
from orchestrator.cli import attach


def test_attach_sends_stdin_and_records_log(monkeypatch, tmp_path: Path) -> None:
    """attach で STDIN が送信され、ログと ci_evidence に残ることを確認する。"""
    monkeypatch.chdir(tmp_path)
    run_id = uuid4()
    mission_id = uuid4()
    trace_dir = tmp_path / "logs"
    script = (
        "import sys, time;"
        "print('ready', flush=True);"
        "line=sys.stdin.readline();"
        "print('ack:'+line.strip(), flush=True);"
        "time.sleep(0.1)"
    )

    evidence_path = tmp_path / "observability/policy/ci_evidence.jsonl"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.touch()

    session = stream.spawn_stream_session(
        command=[sys.executable, "-c", script],
        mission_id=mission_id,
        run_id=run_id,
        trace_dir=trace_dir,
        command_index=0,
        role="tester",
    )

    attach(run_id=str(run_id), line="ping")
    exit_code = stream.wait_stream_session(session, timeout=5.0)

    log_path = next(trace_dir.glob(f"{run_id}*.log"))
    log_content = log_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "STDIN" in log_content and "ping" in log_content
    assert "ack:ping" in log_content

    assert evidence_path.exists()
    content = evidence_path.read_text(encoding="utf-8")
    assert "orchestrator_chat_attach" in content

    stream._STREAM_REGISTRY.pop(str(run_id), None)
