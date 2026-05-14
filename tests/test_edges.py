from fastapi.testclient import TestClient

from taskboard.main import app

client = TestClient(app)


def test_delete_list_cascade() -> None:
    client.post("/auth/register", json={"email": "dl@ex.com", "password": "password12"})
    tok = client.post(
        "/auth/token",
        data={"username": "dl@ex.com", "password": "password12"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h).json()["id"]
    lid = client.post(f"/boards/{bid}/lists", json={"title": "L"}, headers=h).json()["id"]
    cid = client.post(f"/lists/{lid}/cards", json={"title": "C"}, headers=h).json()["id"]
    assert client.delete(f"/lists/{lid}", headers=h).status_code == 204
    assert client.get(f"/lists/{lid}/cards", headers=h).status_code == 404


def test_admin_delete_card() -> None:
    from taskboard.database import SessionLocal
    from taskboard.models import User

    client.post("/auth/register", json={"email": "adm@ex.com", "password": "password12"})
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "adm@ex.com").one()
        u.is_admin = True
        db.commit()
    finally:
        db.close()
    tok = client.post(
        "/auth/token",
        data={"username": "adm@ex.com", "password": "password12"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h).json()["id"]
    lid = client.post(f"/boards/{bid}/lists", json={"title": "L"}, headers=h).json()["id"]
    cid = client.post(f"/lists/{lid}/cards", json={"title": "X"}, headers=h).json()["id"]
    assert client.delete(f"/admin/cards/{cid}", headers=h).status_code == 204


def test_admin_cannot_delete_self() -> None:
    from taskboard.database import SessionLocal
    from taskboard.models import User

    client.post("/auth/register", json={"email": "self@ex.com", "password": "password12"})
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "self@ex.com").one()
        uid = u.id
        u.is_admin = True
        db.commit()
    finally:
        db.close()
    tok = client.post(
        "/auth/token",
        data={"username": "self@ex.com", "password": "password12"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    r = client.delete(f"/admin/users/{uid}", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 400
