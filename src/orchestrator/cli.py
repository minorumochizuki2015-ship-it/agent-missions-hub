# ruff: noqa: B008
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, cast
from uuid import UUID, uuid4

import httpx
import typer
import uvicorn

from orchestrator.conpty_stream import (
    get_stream_session_meta,
    send_stream_line,
    spawn_stream_session,
    terminate_stream_session,
    wait_stream_session,
)
from orchestrator.conpty_wrapper import load_engine_config, spawn_agent_cli
from orchestrator.message_bus import append_message, read_messages
from orchestrator.safeops import should_auto_approve_dangerous
from scripts.shadow_audit_emit import emit_event

DEFAULT_BASE = os.getenv("MISSIONS_HUB_API_BASE", "http://127.0.0.1:8000")
DEFAULT_SIGNALS_BASE = os.getenv("MISSIONS_HUB_SIGNALS_BASE", "http://127.0.0.1:3020")
DEFAULT_AUTOMATION_LEVEL = "manual"

app = typer.Typer(help="CLI entrypoint for Missions Hub orchestrator.")


def _compose_url(base: str, endpoint: str) -> str:
    base = base.rstrip("/")
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    return f"{base}{endpoint}"


def _emit_shadow_audit_event(
    event: str, mission_id: UUID, run_id: UUID, roles: list[str], status: str
) -> None:
    """Shadow Audit に PLAN/TEST/PATCH/APPLY を簡易記録する。"""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": "WORK",
        "event": event,
        "rule_ids": ["WORK_rules"],
        "policy_refs": ["project_rules"],
        "reasoning_digest": f"orchestrator run {event.lower()} 状態={status}",
        "inputs_hash": str(mission_id),
        "outputs_hash": str(run_id),
        "approval_state": "none",
        "approvals_row_id": "",
        "metadata": {"roles": roles, "status": status},
    }
    with contextlib.suppress(Exception):
        emit_event(record)


def _post_dangerous_signal(
    *,
    signals_base_url: str,
    project_id: Optional[int],
    mission_id: UUID,
    run_id: UUID,
    roles: list[str],
    description: str,
) -> None:
    """危険コマンドの pending シグナルを送信する (自動承認なしの場合)。"""
    if project_id is None:
        return
    url = _compose_url(signals_base_url, "/api/signals")
    payload = {
        "project_id": project_id,
        "mission_id": str(mission_id).replace("-", ""),
        "type": "dangerous_command",
        "severity": "warning",
        "status": "pending",
        "message": f"run_id={run_id} mission_id={mission_id} roles={','.join(roles)} 内容={description}",
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(url, json=payload)
    except Exception:
        pass

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
        typer.echo(f"api_up=false engine={engine} run_id={run_id}")
        raise typer.Exit(code=1) from exc

    duration = int((time.monotonic() - start) * 1000)
    typer.echo(f"status={resp.status_code} duration_ms={duration}")
    typer.echo(f"api_up=true engine={engine} run_id={run_id}")
    typer.echo(f"workflow_run_ref={run_id}")
    typer.echo(f"workflow_run_ref logged to cli_runs/{run_id}.log")

    _write_cli_run_log(run_id, engine, endpoint, resp.status_code, duration)
    typer.echo(f"cli_run_log=cli_runs/{run_id}.log")

    try:
        payload = resp.json()
        typer.echo(json.dumps(payload, ensure_ascii=False))
    except Exception:
        typer.echo(resp.text)

    _log_cli_call_evidence(
        url, endpoint, method_norm, resp.status_code, duration, engine, run_id
    )

    if resp.status_code >= 400:
        typer.echo(f"api_up=false engine={engine} run_id={run_id}")
        raise typer.Exit(code=1)


@app.command()
def run(
    roles: str = typer.Option(
        "planner,coder,tester", help="起動する役割をカンマ区切りで指定"
    ),
    engine: str = typer.Option("codex_cli", help="engines.yaml に定義されたエンジン名"),
    mission: Optional[str] = typer.Option(
        None, help="Mission UUID。未指定なら自動生成"
    ),
    timeout: float = typer.Option(300.0, help="各CLIのタイムアウト(秒)"),
    trace_dir: Path = typer.Option(
        Path("data/logs/current/audit/cli_runs"), help="ログ保存先"
    ),
    parallel: bool = typer.Option(
        False, help="役割ごとにエージェント CLI を並列起動するかどうか"
    ),
    max_workers: Optional[int] = typer.Option(
        None, help="並列起動時のスレッド数(省略時 roles 数)"
    ),
    workflow_endpoint: Optional[str] = typer.Option(
        None,
        help="WorkflowEngine に run を連携するエンドポイント(例: /missions/{id}/run)",
    ),
    chat_mode: bool = typer.Option(False, help="chat/stream モードの PoC を有効化する"),
    message_bus_path: Path = typer.Option(
        Path("data/logs/current/audit/message_bus.json"),
        help="role 間 handoff に使用するメッセージバス JSON",
    ),
    role_config: Path = typer.Option(
        Path("config/roles.json"),
        help="role プロファイル定義(プロンプト/許可コマンド/workdir)",
    ),
    signals_project_id: Optional[int] = typer.Option(
        None, help="signals 送信用 project_id(未指定なら送信しない)"
    ),
    signals_base_url: str = typer.Option(
        DEFAULT_SIGNALS_BASE, help="signals POST 先の base URL"
    ),
) -> None:
    """指定した roles を起動し、run_id+index でログを分離する(必要に応じ並列)。"""

    role_list = [r.strip() for r in roles.split(",") if r.strip()]
    if not role_list:
        typer.echo("roles が空です", err=True)
        raise typer.Exit(code=2)

    mission_id = UUID(mission) if mission else uuid4()
    run_id = uuid4()
    run_status = "pending"
    engine_cfg = load_engine_config(engine)
    command = engine_cfg.get("command")
    if not isinstance(command, list) or not command:
        typer.echo(f"engine config invalid: {engine}", err=True)
        raise typer.Exit(code=2)

    trace_root = trace_dir / str(run_id)
    trace_root.mkdir(parents=True, exist_ok=True)
    plan_payload = {
        "mission_id": str(mission_id),
        "run_id": str(run_id),
        "roles": role_list,
        "status": run_status,
    }
    (trace_root / "plan.json").write_text(
        json.dumps(plan_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _emit_shadow_audit_event("PLAN", mission_id, run_id, role_list, run_status)

    role_profiles: Dict[str, Dict[str, str]] = {}
    bus_path = (
        message_bus_path
        if isinstance(message_bus_path, Path)
        else Path("data/logs/current/audit/message_bus.json")
    )
    role_config_path = (
        role_config if isinstance(role_config, Path) else Path("config/roles.json")
    )
    if role_config_path.exists():
        try:
            role_profiles = json.loads(role_config_path.read_text(encoding="utf-8"))
        except Exception:
            role_profiles = {}

    def _apply_role(command_list: list[str], role_name: str) -> list[str]:
        """ロール名に応じてコマンドを置換し、プロンプト/作業ディレクトリを付与する。"""
        updated_command = [arg.replace("{ROLE}", role_name) for arg in command_list]
        profile = role_profiles.get(role_name, {})
        workdir = profile.get("workdir")
        prompt_env = profile.get("prompt")
        if workdir:
            updated_command = updated_command.copy()
            updated_command.insert(0, f"--workdir={workdir}")
        if prompt_env:
            prompt_text = f"[role={role_name}] {prompt_env}"
            updated_command = [*updated_command, prompt_text]
        return updated_command

    def _run_single(idx: int, role_name: str) -> subprocess.CompletedProcess[str]:
        result = spawn_agent_cli(
            command=_apply_role(list(command), role_name),
            mission_id=mission_id,
            run_id=run_id,
            trace_dir=trace_dir,
            timeout=timeout,
            command_index=idx,
            role=role_name,
        )
        return result

    def _record_handoff(role_name: str, status: str) -> None:
        append_message(
            bus_path,
            {
                "mission_id": str(mission_id),
                "run_id": str(run_id),
                "role": role_name,
                "status": status,
            },
        )

    def _call_workflow_endpoint() -> None:
        if not workflow_endpoint:
            return
        try:
            url = _compose_url(DEFAULT_BASE, workflow_endpoint)
            with httpx.Client(timeout=5.0) as client:
                client.post(
                    url,
                    json={
                        "mission_id": str(mission_id),
                        "run_id": str(run_id),
                        "roles": role_list,
                    },
            )
        except Exception:
            pass

    def _finalize_trace(status: str) -> None:
        payload = {
            "mission_id": str(mission_id),
            "run_id": str(run_id),
            "roles": role_list,
            "status": status,
        }
        for name in ("test_report", "audit"):
            (trace_root / f"{name}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        for ev in ("TEST", "PATCH", "APPLY"):
            _emit_shadow_audit_event(ev, mission_id, run_id, role_list, status)

    if not should_auto_approve_dangerous(
        "orchestrator_run",
        str(mission_id),
        automation_level=DEFAULT_AUTOMATION_LEVEL,
    ):
        _post_dangerous_signal(
            signals_base_url=signals_base_url,
            project_id=signals_project_id,
        mission_id=mission_id,
        run_id=run_id,
        roles=role_list,
        description="orchestrator run 実行は manual 承認待ち",
    )

    if chat_mode and len(role_list) != 1:
        typer.echo("chat-mode は単一ロール専用です", err=True)
        raise typer.Exit(code=2)
    if chat_mode and parallel:
        typer.echo("chat-mode では parallel オプションを使用できません", err=True)
        raise typer.Exit(code=2)

    if chat_mode:
        role_name = role_list[0]
        session = spawn_stream_session(
            command=_apply_role(list(command), role_name),
            mission_id=mission_id,
            run_id=run_id,
            trace_dir=trace_dir,
            timeout=timeout,
            command_index=0,
            role=role_name,
        )
        typer.echo(f"chat_run_id={run_id}")
        _, trace_path = session
        typer.echo(f"cli_run_log={trace_path}")
        try:
            exit_code = wait_stream_session(session, timeout=timeout)
            run_status = "ok" if exit_code == 0 else "failed"
        except subprocess.TimeoutExpired:
            run_status = "timeout"
            exit_code = terminate_stream_session(session, timeout=5.0)
        _record_handoff(role_name, "completed" if exit_code == 0 else "failed")
        _log_chat_run_evidence(
            run_id=str(run_id),
            engine=engine,
            roles=role_list,
            status=run_status,
            mission_id=str(mission_id),
            log_path=trace_path,
        )
        _post_signal_event(
            signals_base_url=signals_base_url,
            project_id=signals_project_id,
            mission_id=str(mission_id),
            run_id=str(run_id),
            roles=role_list,
        )
        _finalize_trace(run_status)
        if exit_code != 0:
            raise typer.Exit(code=1)
        return

    if parallel:
        worker_count = max_workers or len(role_list)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(_run_single, idx, role_name): role_name
                for idx, role_name in enumerate(role_list)
            }
            failed_roles: list[str] = []
            for fut in as_completed(futures):
                role_name = futures[fut]
                proc = fut.result()
                _record_handoff(
                    role_name, "completed" if proc.returncode == 0 else "failed"
                )
                if proc.returncode != 0:
                    failed_roles.append(role_name)
            if failed_roles:
                run_status = "failed"
                _finalize_trace(run_status)
                raise typer.Exit(code=1)
    else:
        for idx, role in enumerate(role_list):
            proc = _run_single(idx, role)
            _record_handoff(role, "completed" if proc.returncode == 0 else "failed")
            if proc.returncode != 0:
                run_status = "failed"
                _finalize_trace(run_status)
                raise typer.Exit(code=1)

    run_status = "ok" if run_status == "pending" else run_status
    if role_list:
        _call_workflow_endpoint()
        read_messages(bus_path)
    _post_signal_event(
        signals_base_url=signals_base_url,
        project_id=signals_project_id,
        mission_id=str(mission_id),
        run_id=str(run_id),
        roles=role_list,
    )
    _finalize_trace(run_status)


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


def _log_chat_run_evidence(
    *,
    run_id: str,
    engine: str,
    roles: list[str],
    status: str,
    mission_id: str,
    log_path: Path,
) -> None:
    """chat/stream 実行を ci_evidence.jsonl に記録する。"""
    import hashlib

    evidence_path = Path("observability/policy/ci_evidence.jsonl")
    if not evidence_path.exists():
        return

    log_path_str = log_path.as_posix()
    log_hash = hashlib.sha256(log_path_str.encode("utf-8")).hexdigest()[:16]

    git_sha = os.environ.get("GITHUB_SHA")
    if git_sha is None:
        try:
            git_sha = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
                .strip()
                or None
            )
        except Exception:
            git_sha = None

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "orchestrator_chat_run",
        "run_id": run_id,
        "mission_id": mission_id,
        "engine": engine,
        "roles": roles,
        "status": status,
        "log_path": log_path_str,
        "log_path_hash": log_hash,
    }
    if git_sha:
        event["git_sha"] = git_sha

    try:
        with evidence_path.open("a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception:  # pragma: no cover - IO failures
        pass


@app.command()
def attach(
    run_id: str = typer.Option(..., help="chat/stream セッションの run_id"),
    line: Optional[str] = typer.Option(
        None, help="1 行だけ送信する場合に指定 (省略時は標準入力から送信)"
    ),
) -> None:
    """既存 chat/stream セッションへ TTY でアタッチする。"""
    try:
        session, role, mission_id = get_stream_session_meta(run_id)
    except KeyError as err:
        typer.echo(f"run_id={run_id} のセッションが見つかりません", err=True)
        raise typer.Exit(code=1) from err

    _, trace_path = session
    typer.echo(f"attach run_id={run_id} log={trace_path}")
    if line:
        send_stream_line(session, line)
    else:
        typer.echo("標準入力からの行を送信します。Ctrl+D/Ctrl+Z で終了。")
        try:
            for stdin_line in sys.stdin:
                send_stream_line(session, stdin_line.rstrip("\n"))
        except KeyboardInterrupt:
            pass
    _log_chat_attach_evidence(
        run_id=run_id,
        mission_id=mission_id,
        role=role,
        log_path=trace_path,
    )


def _log_chat_attach_evidence(
    *,
    run_id: str,
    mission_id: str,
    role: str | None,
    log_path: Path,
) -> None:
    """chat/stream attach を ci_evidence.jsonl に記録する。"""
    import hashlib

    evidence_path = Path("observability/policy/ci_evidence.jsonl")
    if not evidence_path.exists():
        return

    log_path_str = log_path.as_posix()
    log_hash = hashlib.sha256(log_path_str.encode("utf-8")).hexdigest()[:16]

    git_sha = os.environ.get("GITHUB_SHA")
    if git_sha is None:
        try:
            git_sha = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
                .strip()
                or None
            )
        except Exception:
            git_sha = None

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "orchestrator_chat_attach",
        "run_id": run_id,
        "mission_id": mission_id,
        "role": role,
        "log_path": log_path_str,
        "log_path_hash": log_hash,
    }
    if git_sha:
        event["git_sha"] = git_sha

    try:
        with evidence_path.open("a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception:  # pragma: no cover - IO failures
        pass


def _post_signal_event(
    *,
    signals_base_url: str,
    project_id: Optional[int],
    mission_id: str,
    run_id: str,
    roles: list[str],
) -> None:
    """run 終了を signals API にベストエフォートで送信する。"""
    if project_id is None:
        return
    url = _compose_url(signals_base_url, "/api/signals")
    mission_clean = mission_id.replace("-", "")
    payload = {
        "project_id": project_id,
        "mission_id": mission_clean,
        "type": "orchestrator_run",
        "severity": "info",
        "status": "pending",
        "message": f"run_id={run_id} mission_id={mission_id} roles={','.join(roles)}",
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code >= 400:
                typer.echo(f"signals_post_failed status={resp.status_code}", err=True)
            else:
                typer.echo(f"signals_posted id={resp.json().get('id')} status=pending")
    except Exception:
        typer.echo("signals_post_failed exception", err=True)


def _echo_health_check(host: str, port: int, run_id: str) -> None:
    """serve 起動時に /health の疎通を1行ログ出力する。"""
    url = f"http://{host}:{port}/health"
    status_text = "NG"
    try:
        resp = httpx.get(url, timeout=2.0)
        status_text = str(resp.status_code)
    except Exception:  # pragma: no cover - network errors
        typer.echo(f"health_check_error run_id={run_id}")
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
