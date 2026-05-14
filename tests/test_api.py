from fastapi.testclient import TestClient

from taskboard.main import app

client = TestClient(app)


def _register(email: str = "u1@example.com", password: str = "password12") -> None:
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text


def _token(email: str = "u1@example.com", password: str = "password12") -> str:
    r = client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_register_and_login() -> None:
    _register()
    token = _token()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "u1@example.com"


def test_register_duplicate_email() -> None:
    _register()
    r = client.post("/auth/register", json={"email": "u1@example.com", "password": "otherpass12"})
    assert r.status_code == 400


def test_login_wrong_password() -> None:
    _register()
    r = client.post(
        "/auth/token",
        data={"username": "u1@example.com", "password": "wrongpass1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_board_crud_flow() -> None:
    _register()
    token = _token()
    h = {"Authorization": f"Bearer {token}"}
    created = client.post("/boards", json={"title": "Sprint", "description": "Q2"}, headers=h)
    assert created.status_code == 201
    bid = created.json()["id"]
    lst = client.get("/boards", headers=h)
    assert len(lst.json()) == 1
    upd = client.put(f"/boards/{bid}", json={"title": "Sprint 2"}, headers=h)
    assert upd.status_code == 200
    assert upd.json()["title"] == "Sprint 2"
    client.delete(f"/boards/{bid}", headers=h)
    assert client.get("/boards", headers=h).json() == []


def test_board_not_owned() -> None:
    _register("a@ex.com")
    tok_a = _token("a@ex.com")
    b = client.post("/boards", json={"title": "B"}, headers={"Authorization": f"Bearer {tok_a}"})
    bid = b.json()["id"]
    _register("b@ex.com", "password12")
    tok_b = _token("b@ex.com", "password12")
    r = client.get(f"/boards/{bid}", headers={"Authorization": f"Bearer {tok_b}"})
    assert r.status_code == 404


def test_lists_cards_comments_analytics() -> None:
    _register()
    token = _token()
    h = {"Authorization": f"Bearer {token}"}
    bid = client.post("/boards", json={"title": "Home"}, headers=h).json()["id"]
    lid = client.post(f"/boards/{bid}/lists", json={"title": "Todo", "position": 0}, headers=h).json()["id"]
    card = client.post(f"/lists/{lid}/cards", json={"title": "Task", "position": 0}, headers=h)
    assert card.status_code == 201
    cid = card.json()["id"]
    com = client.post(f"/cards/{cid}/comments", json={"body": "note"}, headers=h)
    assert com.status_code == 201
    analytics = client.get(f"/analytics/boards/{bid}", headers=h)
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["total_cards"] == 1
    assert body["total_comments"] == 1
    assert body["lists_count"] == 1


def test_move_card_between_lists() -> None:
    _register()
    token = _token()
    h = {"Authorization": f"Bearer {token}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h).json()["id"]
    l1 = client.post(f"/boards/{bid}/lists", json={"title": "A", "position": 0}, headers=h).json()["id"]
    l2 = client.post(f"/boards/{bid}/lists", json={"title": "B", "position": 1}, headers=h).json()["id"]
    cid = client.post(f"/lists/{l1}/cards", json={"title": "Move me"}, headers=h).json()["id"]
    moved = client.put(f"/cards/{cid}", json={"list_id": l2}, headers=h)
    assert moved.status_code == 200
    assert moved.json()["list_id"] == l2


def test_admin_requires_flag() -> None:
    _register()
    token = _token()
    r = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_list_after_promotion(monkeypatch: pytest.MonkeyPatch) -> None:
    from taskboard.database import SessionLocal

    _register()
    db = SessionLocal()
    try:
        from taskboard.models import User

        u = db.query(User).filter(User.email == "u1@example.com").one()
        u.is_admin = True
        db.commit()
    finally:
        db.close()
    token = _token()
    r = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert len(r.json()) >= 1
