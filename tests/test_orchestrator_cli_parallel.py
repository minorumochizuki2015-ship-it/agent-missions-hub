from __future__ import annotations

import subprocess
import time
from pathlib import Path

from orchestrator import cli


def test_run_parallel_reduces_total_time(monkeypatch, tmp_path: Path) -> None:
    """並列オプションで実行時間が短縮されることを確認する。"""

    def fake_engine_config(engine_name: str = "demo") -> dict[str, object]:
        return {"command": ["echo", "demo"], "workdir": None}

    def fake_spawn(
        *,
        command: list[str],
        mission_id,
        run_id,
        trace_dir: Path | None,
        timeout: float,
        command_index: int | None,
        role: str | None,
    ) -> subprocess.CompletedProcess[str]:
        time.sleep(0.05)
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout="ok", stderr=""
        )

    monkeypatch.setattr(cli, "load_engine_config", fake_engine_config)
    monkeypatch.setattr(cli, "spawn_agent_cli", fake_spawn)

    start_seq = time.perf_counter()
    cli.run(
        roles="planner,coder",
        engine="demo",
        mission=None,
        timeout=5.0,
        trace_dir=tmp_path,
        parallel=False,
    )
    seq_duration = time.perf_counter() - start_seq

    start_par = time.perf_counter()
    cli.run(
        roles="planner,coder",
        engine="demo",
        mission=None,
        timeout=5.0,
        trace_dir=tmp_path,
        parallel=True,
        max_workers=2,
    )
    par_duration = time.perf_counter() - start_par

    assert par_duration < seq_duration * 0.8
