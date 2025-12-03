import asyncio

from pathlib import Path

from fastapi.testclient import TestClient

from mcp_agent_mail.config import get_settings
from mcp_agent_mail.db import ensure_schema, reset_database_state, session_context
from mcp_agent_mail.http import build_http_app
from mcp_agent_mail.models import Project


async def _setup_project() -> int:
    reset_database_state()
    await ensure_schema()
    async with session_context() as session:
        proj = Project(slug="p-signals", human_key="p-signals")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        proj_id = proj.id
        if proj_id is None:
            raise RuntimeError("project id was not persisted")
        return int(proj_id)


def test_signal_create_and_list() -> None:
    pid = asyncio.run(_setup_project())
    app = build_http_app(get_settings())
    client = TestClient(app)

    create = client.post(
        "/api/signals",
        json={"project_id": pid, "type": "dangerous_command", "message": "rm -rf"},
    )
    assert create.status_code == 200
    signal_id = create.json()["id"]

    res = client.get("/api/signals?limit=10")
    assert res.status_code == 200
    ids = [s["id"] for s in res.json()["signals"]]
    assert signal_id in ids


def test_signal_import_dangerous(tmp_path: Path) -> None:
    asyncio.run(_setup_project())
    log = tmp_path / "dangerous_command_events.jsonl"
    log.write_text(
        "\n".join(
            [
                '{"event":"dangerous_command","command":"rm -rf /tmp"}',
                '{"event":"approval_required","command":"rm -rf /var"}',
                '{"event":"failing_test","command":"pytest failing"}',
            ]
        ),
        encoding="utf-8",
    )
    app = build_http_app(get_settings())
    client = TestClient(app)
    res = client.post(
        "/api/signals/import/dangerous",
        json={"path": str(log), "project": "p-signals", "max_rows": 10},
    )
    assert res.status_code == 200
    assert res.json()["imported"] == 3
    listed = client.get("/api/signals").json()["signals"]
    types = {s["type"] for s in listed}
    assert "dangerous_command" in types
    assert "approval_required" in types
    assert "failing_test" in types
