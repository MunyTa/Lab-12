from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from taskboard.main import app

client = TestClient(app)


def _bootstrap_user_with_board() -> tuple[str, int, int, int]:
    client.post("/auth/register", json={"email": "ov@ex.com", "password": "password12"})
    r = client.post(
        "/auth/token",
        data={"username": "ov@ex.com", "password": "password12"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h).json()["id"]
    lid = client.post(f"/boards/{bid}/lists", json={"title": "L"}, headers=h).json()["id"]
    past = datetime.now(timezone.utc) - timedelta(days=1)
    cid = client.post(
        f"/lists/{lid}/cards",
        json={"title": "Late", "due_date": past.isoformat()},
        headers=h,
    ).json()["id"]
    return token, bid, lid, cid


def test_overdue_counted_in_analytics() -> None:
    token, bid, _, _ = _bootstrap_user_with_board()
    h = {"Authorization": f"Bearer {token}"}
    a = client.get(f"/analytics/boards/{bid}", headers=h).json()
    assert a["overdue_cards"] == 1


def test_unauthorized_me() -> None:
    assert client.get("/auth/me").status_code == 401
