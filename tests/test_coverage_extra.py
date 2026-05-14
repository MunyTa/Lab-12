"""Дополнительные тесты для веток и покрытия (порог 90% в CI)."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import taskboard.database as taskboard_db
from taskboard.main import app
from taskboard.models import Comment, User

client = TestClient(app)


def _session():
    """SessionLocal из модуля (после патча conftest указывает на тестовый engine)."""
    return taskboard_db.SessionLocal()


def _reg_token(email: str, password: str = "password12") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_get_me_invalid_token_sub_not_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("taskboard.deps.decode_token", lambda _t: "not-an-int")
    r = client.get("/auth/me", headers={"Authorization": "Bearer fake"})
    assert r.status_code == 401


def test_get_me_valid_sub_missing_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("taskboard.deps.decode_token", lambda _t: "999991")
    r = client.get("/auth/me", headers={"Authorization": "Bearer fake"})
    assert r.status_code == 401


def test_get_db_generator_close_runs_finally() -> None:
    gen = taskboard_db.get_db()
    session = next(gen)
    assert session is not None
    gen.close()


def test_create_engine_non_sqlite_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ветка без connect_args: не тянем psycopg2 — мокаем create_engine."""
    import taskboard.database as dbmod

    fake_engine = MagicMock()

    def fake_create_engine(url: str, **kwargs: object) -> MagicMock:
        fake_create_engine.last_url = url
        fake_create_engine.last_kwargs = kwargs
        return fake_engine

    monkeypatch.setattr(dbmod, "create_engine", fake_create_engine)

    class _Cfg:
        database_url = "postgresql://user:pass@localhost:5432/db"

    monkeypatch.setattr(dbmod, "get_settings", lambda: _Cfg())
    eng = dbmod._create_engine()
    assert eng is fake_engine
    assert str(fake_create_engine.last_url).startswith("postgresql")
    assert "connect_args" not in fake_create_engine.last_kwargs


def test_update_board_description_only() -> None:
    tok = _reg_token("bdesc@ex.com")
    h = {"Authorization": f"Bearer {tok}"}
    bid = client.post("/boards", json={"title": "T", "description": "old"}, headers=h).json()["id"]
    r = client.put(f"/boards/{bid}", json={"description": "new"}, headers=h)
    assert r.status_code == 200
    assert r.json()["description"] == "new"
    assert r.json()["title"] == "T"


def test_list_cards_unknown_list() -> None:
    tok = _reg_token("lc404@ex.com")
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/lists/999999/cards", headers=h).status_code == 404


def test_update_card_not_found() -> None:
    tok = _reg_token("c404@ex.com")
    h = {"Authorization": f"Bearer {tok}"}
    assert client.put("/cards/999999", json={"title": "x"}, headers=h).status_code == 404


def test_delete_comment_not_found() -> None:
    tok = _reg_token("cm404@ex.com")
    h = {"Authorization": f"Bearer {tok}"}
    assert client.delete("/comments/999999", headers=h).status_code == 404


def test_analytics_board_not_owned() -> None:
    tok_a = _reg_token("anA@ex.com")
    h_a = {"Authorization": f"Bearer {tok_a}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h_a).json()["id"]
    tok_b = _reg_token("anB@ex.com")
    h_b = {"Authorization": f"Bearer {tok_b}"}
    assert client.get(f"/analytics/boards/{bid}", headers=h_b).status_code == 404


def test_owner_cannot_delete_other_users_comment() -> None:
    tok_owner = _reg_token("own@ex.com")
    _reg_token("other@ex.com")
    h = {"Authorization": f"Bearer {tok_owner}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h).json()["id"]
    lid = client.post(f"/boards/{bid}/lists", json={"title": "L"}, headers=h).json()["id"]
    cid = client.post(f"/lists/{lid}/cards", json={"title": "C"}, headers=h).json()["id"]

    db = _session()
    try:
        other = db.query(User).filter(User.email == "other@ex.com").one()
        c = Comment(body="from other", card_id=cid, user_id=other.id)
        db.add(c)
        db.commit()
        db.refresh(c)
        cid_del = c.id
    finally:
        db.close()

    r = client.delete(f"/comments/{cid_del}", headers=h)
    assert r.status_code == 403


def test_admin_deletes_another_user() -> None:
    tok_adm = _reg_token("adm2@ex.com")
    _reg_token("vic@ex.com")
    db = _session()
    try:
        adm = db.query(User).filter(User.email == "adm2@ex.com").one()
        adm.is_admin = True
        vic = db.query(User).filter(User.email == "vic@ex.com").one()
        vid = vic.id
        db.commit()
    finally:
        db.close()

    h = {"Authorization": f"Bearer {tok_adm}"}
    assert client.delete(f"/admin/users/{vid}", headers=h).status_code == 204


def test_ensure_list_wrong_board_owner() -> None:
    """Колонка есть, но текущий пользователь не владелец доски — ветка в _ensure_list."""
    tok_a = _reg_token("lstA@ex.com")
    _reg_token("lstB@ex.com")
    h_a = {"Authorization": f"Bearer {tok_a}"}
    bid = client.post("/boards", json={"title": "B"}, headers=h_a).json()["id"]
    lid = client.post(f"/boards/{bid}/lists", json={"title": "L"}, headers=h_a).json()["id"]

    db = _session()
    try:
        from taskboard.models import Board

        b = db.get(Board, bid)
        assert b is not None
        other = db.query(User).filter(User.email == "lstB@ex.com").one()
        b.owner_id = other.id
        db.commit()
    finally:
        db.close()

    assert client.get(f"/lists/{lid}/cards", headers=h_a).status_code == 404


def test_delete_list_not_found() -> None:
    tok = _reg_token("dlist404@ex.com")
    h = {"Authorization": f"Bearer {tok}"}
    assert client.delete("/lists/999999", headers=h).status_code == 404


def test_admin_delete_unknown_user() -> None:
    tok = _reg_token("adm404@ex.com")
    db = _session()
    try:
        u = db.query(User).filter(User.email == "adm404@ex.com").one()
        u.is_admin = True
        db.commit()
    finally:
        db.close()
    h = {"Authorization": f"Bearer {tok}"}
    assert client.delete("/admin/users/999999", headers=h).status_code == 404


def test_admin_delete_unknown_card() -> None:
    tok = _reg_token("admc404@ex.com")
    db = _session()
    try:
        u = db.query(User).filter(User.email == "admc404@ex.com").one()
        u.is_admin = True
        db.commit()
    finally:
        db.close()
    h = {"Authorization": f"Bearer {tok}"}
    assert client.delete("/admin/cards/999999", headers=h).status_code == 404


def test_app_lifespan_runs_with_test_client() -> None:
    from taskboard.main import create_app

    app_local = create_app()
    with TestClient(app_local) as ac:
        assert ac.get("/health").status_code == 200
