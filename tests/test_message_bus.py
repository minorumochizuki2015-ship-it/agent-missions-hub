from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typer.testing import CliRunner
from orchestrator import message_bus
from orchestrator.cli import app

runner = CliRunner()


def test_send_receive_and_missing(tmp_path: Path) -> None:
    """送信した内容を取得でき、未作成ロールは空辞書を返す。"""
    payload = {"step": "plan", "status": "ok"}
    path = message_bus.send_message("planner", payload, base_dir=tmp_path)
    assert path.exists()
    assert message_bus.receive_message("planner", base_dir=tmp_path) == payload
    assert message_bus.receive_message("coder", base_dir=tmp_path) == {}


def test_run_roles_demo(tmp_path: Path) -> None:
    """runコマンドでdemoエンジンを起動し、複数ロールのログが分離されることを確認する。"""
    mission = str(uuid4())
    result = runner.invoke(
        app,
        ["run", "--roles", "planner,coder", "--engine", "demo", "--mission", mission, "--trace-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert list(tmp_path.glob("*_cmd0.log"))
    assert list(tmp_path.glob("*_cmd1.log"))
