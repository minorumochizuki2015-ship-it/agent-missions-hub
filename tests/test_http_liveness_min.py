import pytest
from fastapi.testclient import TestClient

from mcp_agent_mail.http import app


@pytest.mark.parametrize("path", ["/health/liveness"])  # minimal read-only route
def test_liveness_ok(path):
    client = TestClient(app)
    res = client.get(path)
    assert res.status_code == 200
    assert res.json().get("status") in {"ok", "alive", "ready"}
