"""Tests for ConPTY wrapper module."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

from orchestrator.conpty_wrapper import spawn_agent_cli


def test_spawn_agent_cli_success(tmp_path: Path) -> None:
    """Test successful agent CLI spawn with trace logging."""
    mission_id = uuid4()
    run_id = uuid4()

    # Mock command: Python echo
    result = spawn_agent_cli(
        command=[sys.executable, "-c", "print('test output')"],
        mission_id=mission_id,
        run_id=run_id,
        trace_dir=tmp_path,
        timeout=10.0,
    )

    assert result.returncode == 0
    assert "test output" in result.stdout

    # Verify trace file created
    trace_file = tmp_path / f"{run_id}.log"
    assert trace_file.exists()

    content = trace_file.read_text(encoding="utf-8")
    assert str(mission_id) in content
    assert str(run_id) in content
    assert "RETURN CODE" in content
    assert "STDOUT" in content


def test_spawn_agent_cli_failure(tmp_path: Path) -> None:
    """Test agent CLI spawn with non-zero exit code."""
    mission_id = uuid4()
    run_id = uuid4()

    result = spawn_agent_cli(
        command=[sys.executable, "-c", "import sys; sys.exit(1)"],
        mission_id=mission_id,
        run_id=run_id,
        trace_dir=tmp_path,
    )

    assert result.returncode == 1

    # Verify trace file logged failure
    trace_file = tmp_path / f"{run_id}.log"
    assert trace_file.exists()
    content = trace_file.read_text()
    assert "RETURN CODE" in content
    assert "1" in content


def test_spawn_agent_cli_command_not_found(tmp_path: Path) -> None:
    """Test spawn with non-existent command."""
    mission_id = uuid4()
    run_id = uuid4()

    with pytest.raises(FileNotFoundError):
        spawn_agent_cli(
            command=["nonexistent_command_12345"],
            mission_id=mission_id,
            run_id=run_id,
            trace_dir=tmp_path,
        )

    # Verify error logged to trace file
    trace_file = tmp_path / f"{run_id}.log"
    assert trace_file.exists()
    content = trace_file.read_text()
    assert "ERROR" in content
