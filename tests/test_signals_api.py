import asyncio

from fastapi.testclient import TestClient

from mcp_agent_mail.config import get_settings
from mcp_agent_mail.db import ensure_schema, get_session, reset_database_state
from mcp_agent_mail.http import build_http_app
from mcp_agent_mail.models import Project


async def _setup_project() -> int:
    reset_database_state()
    await ensure_schema()
    async with get_session() as session:
        proj = Project(slug="p-signals", human_key="p-signals")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        return int(proj.id)


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


def test_signal_import_dangerous(tmp_path) -> None:
    pid = asyncio.run(_setup_project())
    log = tmp_path / "dangerous_command_events.jsonl"
    log.write_text(
        "\n".join(
            [
                '{"event":"dangerous_command","command":"rm -rf /tmp"}',
                '{"event":"other"}',
            ]
        ),
        encoding="utf-8",
    )
    app = build_http_app(get_settings())
    client = TestClient(app)
    res = client.post(
        "/api/signals/import/dangerous",
        json={"path": str(log), "project_id": pid, "max_rows": 10},
    )
    assert res.status_code == 200
    assert res.json()["imported"] == 1
    listed = client.get("/api/signals").json()["signals"]
    assert any(s["type"] == "dangerous_command" for s in listed)
