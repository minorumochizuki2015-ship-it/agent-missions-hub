from __future__ import annotations

import json
import os
import time
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
    """Start FastAPI server (agent_missions_hub.http:build_app)."""

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
) -> None:
    """Call MISSIONS HUB API endpoint and print JSON response."""

    url = _compose_url(base_url, endpoint)
    method_norm = method.upper()
    payload = json.loads(data) if data else None
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
    try:
        typer.echo(resp.json())
    except Exception:
        typer.echo(resp.text)

    # Log CLI call to ci_evidence for observability
    _log_cli_call_evidence(url, endpoint, method_norm, resp.status_code, duration)

    if resp.status_code >= 400:
        raise typer.Exit(code=1)


def _log_cli_call_evidence(
    url: str, endpoint: str, method: str, status_code: int, duration_ms: int
) -> None:
    """Log CLI call event to observability/policy/ci_evidence.jsonl."""
    import hashlib
    from datetime import datetime, timezone
    from pathlib import Path

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
        "url_hash": hashlib.sha256(url.encode()).hexdigest()[:16],
    }
    
    try:
        with evidence_path.open("a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception:  # pragma: no cover - IO failures
        pass  # Best-effort logging, don't crash CLI on evidence write failure


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
