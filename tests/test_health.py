from fastapi.testclient import TestClient

from taskboard.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
