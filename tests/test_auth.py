from datetime import timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth
from app.db import connect_db, init_db


def _make_client(db_path):
    app = FastAPI()
    app.include_router(auth.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    return TestClient(app)


def test_get_users_returns_list(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.get("/api/auth/users")

    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert {"username": "其华"} in users


def test_login_success_sets_cookie(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )

    assert resp.status_code == 200
    assert "access_token=" in resp.headers.get("set-cookie", "")


def test_login_wrong_password_returns_401(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "wrong"},
    )

    assert resp.status_code == 401


def test_me_without_cookie_returns_401(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.get("/api/auth/me")

    assert resp.status_code == 401


def test_me_with_valid_cookie_returns_user(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    login_resp = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login_resp.status_code == 200

    me_resp = client.get("/api/auth/me")

    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["username"] == "其华"
    assert isinstance(body["id"], int)


def test_logout_clears_cookie(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    login_resp = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login_resp.status_code == 200

    logout_resp = client.post("/api/auth/logout")

    assert logout_resp.status_code == 200
    cookie_header = logout_resp.headers.get("set-cookie", "")
    assert "access_token=" in cookie_header
    assert "Max-Age=0" in cookie_header or "expires=" in cookie_header.lower()


def test_expired_token_returns_401(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    with connect_db(str(db_path)) as conn:
        # Ensure default user exists via list route equivalent behavior.
        client.get("/api/auth/users")
        row = conn.execute("SELECT id, username FROM users WHERE username = ?", ("其华",)).fetchone()

    token = auth.create_access_token(
        user_id=row["id"],
        username=row["username"],
        expires_delta=timedelta(seconds=-1),
    )

    client.cookies.set("access_token", token)
    resp = client.get("/api/auth/me")

    assert resp.status_code == 401
