from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

import httpx
import typer
import uvicorn

DEFAULT_BASE = os.getenv("MISSIONS_HUB_API_BASE", "http://127.0.0.1:8000")

app = typer.Typer(help="CLI entrypoint for Missions Hub orchestrator.")


def _compose_url(base: str, endpoint: str) -> str:
    base = base.rstrip("/")
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    return f"{base}{endpoint}"


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
) -> None:
    """FastAPI サーバーを起動する。"""

    run_id = str(int(time.time() * 1000))
    typer.echo(f"serve_start host={host} port={port} run_id={run_id}")
    _echo_health_check(host, port, run_id)
    uvicorn.run(
        "agent_missions_hub.http:build_app",
        factory=True,
        host=host,
        port=port,
        reload=False,
    )


@app.command()
def call(
    endpoint: str = typer.Option("/missions", help="API endpoint path"),
    method: str = typer.Option("GET", help="HTTP method (GET/POST)"),
    data: Optional[str] = typer.Option(None, help="JSON string for POST body"),
    base_url: str = typer.Option(
        DEFAULT_BASE, help="Base URL (env MISSIONS_HUB_API_BASE で上書き可)"
    ),
    timeout: float = typer.Option(10.0, help="HTTP timeout seconds"),
    engine: str = typer.Option(
        "codex_cli", help="使用するエンジン名 (codex_cli|claude_cli)"
    ),
) -> None:
    """MISSIONS HUB API を呼び出し、レスポンスを表示する。"""

    url = _compose_url(base_url, endpoint)
    method_norm = method.upper()
    payload = json.loads(data) if data else None
    run_id = str(int(time.time() * 1000))
    typer.echo(f"cli_run_id={run_id}")
    start = time.monotonic()
    try:
        with httpx.Client(timeout=timeout) as client:
            if method_norm == "GET":
                resp = client.get(url)
            elif method_norm == "POST":
                resp = client.post(url, json=payload)
            else:
                typer.echo(f"Unsupported method: {method_norm}", err=True)
                raise typer.Exit(code=2)
    except Exception as exc:  # pragma: no cover - network failures
        typer.echo(f"Request failed: {exc}", err=True)
        raise typer.Exit(code=1)

    duration = int((time.monotonic() - start) * 1000)
    typer.echo(f"status={resp.status_code} duration_ms={duration}")
    typer.echo(f"api_up=true engine={engine} run_id={run_id}")
    typer.echo(f"workflow_run_ref={run_id}")
    typer.echo(f"workflow_run_ref logged to cli_runs/{run_id}.log")
    try:
        typer.echo(resp.json())
    except Exception:
        typer.echo(resp.text)

    _write_cli_run_log(run_id, engine, endpoint, resp.status_code, duration)
    typer.echo(f"cli_run_log=cli_runs/{run_id}.log")
    _log_cli_call_evidence(
        url, endpoint, method_norm, resp.status_code, duration, engine, run_id
    )

    if resp.status_code >= 400:
        raise typer.Exit(code=1)


def _write_cli_run_log(
    run_id: str, engine: str, endpoint: str, status_code: int, duration_ms: int
) -> None:
    """CLI 実行結果を最小限に1行ログとして記録する。"""
    try:
        log_dir = Path("cli_runs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{run_id}.log"
        line = (
            f"run_id={run_id} engine={engine} endpoint={endpoint} "
            f"status={status_code} duration_ms={duration_ms} api_up=true\n"
        )
        log_path.write_text(line, encoding="utf-8")
    except Exception:  # pragma: no cover - IO failures
        pass


def _log_cli_call_evidence(
    url: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: int,
    engine: str,
    run_id: str,
) -> None:
    """CLI call イベントを ci_evidence.jsonl に追記する。"""
    import hashlib
    from datetime import datetime, timezone

    evidence_path = Path("observability/policy/ci_evidence.jsonl")
    if not evidence_path.exists():
        return  # Skip if evidence file doesn't exist

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "cli_call",
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "engine": engine,
        "run_id": run_id,
        "url_hash": hashlib.sha256(url.encode()).hexdigest()[:16],
    }

    try:
        with evidence_path.open("a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception:  # pragma: no cover - IO failures
        pass  # Best-effort logging, don't crash CLI on evidence write failure


def _echo_health_check(host: str, port: int, run_id: str) -> None:
    """serve 起動時に /health の疎通を1行ログ出力する。"""
    url = f"http://{host}:{port}/health"
    status_text = "NG"
    try:
        resp = httpx.get(url, timeout=2.0)
        status_text = str(resp.status_code)
    except Exception:  # pragma: no cover - network errors
        status_text = "NG"
    typer.echo(f"health_check run_id={run_id} status={status_text}")
    try:
        log_dir = Path("cli_runs")
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{run_id}_health.log").write_text(
            f"run_id={run_id} status={status_text}\n", encoding="utf-8"
        )
        typer.echo(f"health_log=cli_runs/{run_id}_health.log")
    except Exception:  # pragma: no cover - IO failures
        pass
def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
