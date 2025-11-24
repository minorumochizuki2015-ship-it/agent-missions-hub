import pytest
from fastapi.testclient import TestClient

from mcp_agent_mail.http import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_mission_not_found(client):
    res = client.get("/missions/nonexistent-id")
    assert res.status_code in {404, 422}


def test_create_artifact_missing_fields(client):
    payload = {"mission_id": "missing", "type": "file"}
    res = client.post("/artifacts", json=payload)
    assert res.status_code in {400, 422}


def test_promote_knowledge_invalid_id(client):
    res = client.post("/artifacts/nonexistent-id/promote")
    assert res.status_code in {404, 422}
