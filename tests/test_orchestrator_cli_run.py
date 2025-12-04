"""orchestrator run の PLAN/TEST/PATCH/AUDIT スケルトンを最小確認する。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from subprocess import CompletedProcess

from typer.testing import CliRunner

import orchestrator.cli as cli

runner = CliRunner()


def test_run_writes_trace_and_shadow_audit(monkeypatch, tmp_path: Path) -> None:
    """run 実行時に trace と Shadow Audit イベントが残ることを確認する。"""
    events: list[dict] = []
    monkeypatch.setattr(cli, "emit_event", lambda record: events.append(record))
    monkeypatch.setattr(cli, "_post_signal_event", lambda **kwargs: None)
    monkeypatch.setattr(cli, "_post_dangerous_signal", lambda **kwargs: None)
    monkeypatch.setattr(cli, "append_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "read_messages", lambda *args, **kwargs: None)

    def _fake_load_engine_config(_: str) -> dict:
        return {"command": [sys.executable, "-c", "print('ok')"]}

    def _fake_spawn_agent_cli(**_: object) -> CompletedProcess[str]:
        return CompletedProcess(args=["echo"], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(cli, "load_engine_config", _fake_load_engine_config)
    monkeypatch.setattr(cli, "spawn_agent_cli", _fake_spawn_agent_cli)

    trace_dir = tmp_path / "trace"
    message_bus = tmp_path / "bus.json"
    result = runner.invoke(
        cli.app,
        [
            "run",
            "--roles",
            "coder",
            "--engine",
            "dummy",
            "--trace-dir",
            str(trace_dir),
            "--message-bus-path",
            str(message_bus),
            "--timeout",
            "5",
        ],
    )
    assert result.exit_code == 0

    run_dirs = list(trace_dir.iterdir())
    assert run_dirs
    run_root = run_dirs[0]

    plan = run_root / "plan.json"
    test_report = run_root / "test_report.json"
    audit = run_root / "audit.json"
    assert plan.exists() and test_report.exists() and audit.exists()

    plan_data = json.loads(plan.read_text(encoding="utf-8"))
    test_data = json.loads(test_report.read_text(encoding="utf-8"))
    audit_data = json.loads(audit.read_text(encoding="utf-8"))
    assert plan_data["status"] == "pending"
    assert test_data["status"] == "ok"
    assert audit_data["status"] == "ok"

    event_names = {ev["event"] for ev in events}
    assert {"PLAN", "TEST", "PATCH", "APPLY"}.issubset(event_names)
