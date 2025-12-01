from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_ready(url: str, timeout: float = 20.0) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            r = httpx.get(url, timeout=2.0)
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(0.5)
            continue
        time.sleep(0.5)
    raise RuntimeError(f"Server not ready: {url}")


def test_cli_call_missions_e2e(tmp_path: Path) -> None:
    port = _get_free_port()
    env = dict(**os.environ)
    env["MISSIONS_HUB_API_BASE"] = f"http://127.0.0.1:{port}"

    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "agent_missions_hub.http:build_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    server = subprocess.Popen(
        uvicorn_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith("win") else 0,
    )
    try:
        _wait_ready(f"http://127.0.0.1:{port}/api/missions")

        cli_cmd = [
            sys.executable,
            "-m",
            "orchestrator.cli",
            "call",
            "--endpoint",
            "/api/missions",
            "--method",
            "GET",
            "--base-url",
            f"http://127.0.0.1:{port}",
        ]
        run = subprocess.run(cli_cmd, capture_output=True, text=True, env=env, timeout=20)
        assert run.returncode == 0, f"stdout={run.stdout}, stderr={run.stderr}"
        assert "status=200" in run.stdout
        # JSON配列であることを確認
        payload_line = run.stdout.strip().splitlines()[-1]
        payload = json.loads(payload_line)
        assert isinstance(payload, list)
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
