from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth, settings
from app.db import connect_db, init_db
from app.settings_store import CLASSIFICATION_GUIDANCE_KEY, DEFAULT_CLASSIFICATION_GUIDANCE


def _make_client(db_path):
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(settings.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    app.dependency_overrides[settings.get_db] = override_get_db

    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login.status_code == 200
    return client


def test_get_classification_guidance_default(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.get("/api/settings/classification-guidance")

    assert resp.status_code == 200
    assert resp.json()["content"] == DEFAULT_CLASSIFICATION_GUIDANCE


def test_update_classification_guidance(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    content = "测试分类指导"
    update = client.put("/api/settings/classification-guidance", json={"content": content})
    assert update.status_code == 200
    assert update.json()["content"] == content

    fetched = client.get("/api/settings/classification-guidance")
    assert fetched.status_code == 200
    assert fetched.json()["content"] == content

    with connect_db(str(db_path)) as db:
        row = db.execute(
            "SELECT value FROM user_settings WHERE user_id = 1 AND key = ?",
            (CLASSIFICATION_GUIDANCE_KEY,),
        ).fetchone()
    assert row is not None
    assert row["value"] == content


def test_user_guidance_isolated_and_can_be_blank(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    with connect_db(str(db_path)) as db:
        # Simulate another user guidance and global fallback existing.
        db.execute(
            "UPDATE app_settings SET value = ? WHERE key = ?",
            ("global-guidance", CLASSIFICATION_GUIDANCE_KEY),
        )
        db.execute(
            """
            INSERT INTO user_settings (user_id, key, value, created_at, updated_at)
            VALUES (2, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """,
            (CLASSIFICATION_GUIDANCE_KEY, "global-guidance"),
        )
        db.execute("UPDATE user_settings SET value = ? WHERE user_id = 2 AND key = ?", ("bill-only-guidance", CLASSIFICATION_GUIDANCE_KEY))
        db.commit()

    # Current user (其华, id=1) can keep independent blank value.
    update = client.put("/api/settings/classification-guidance", json={"content": ""})
    assert update.status_code == 200
    assert update.json()["content"] == ""

    fetched = client.get("/api/settings/classification-guidance")
    assert fetched.status_code == 200
    assert fetched.json()["content"] == ""

    with connect_db(str(db_path)) as db:
        qh = db.execute(
            "SELECT value FROM user_settings WHERE user_id = 1 AND key = ?",
            (CLASSIFICATION_GUIDANCE_KEY,),
        ).fetchone()
        bill = db.execute(
            "SELECT value FROM user_settings WHERE user_id = 2 AND key = ?",
            (CLASSIFICATION_GUIDANCE_KEY,),
        ).fetchone()
    assert qh is not None and qh["value"] == ""
    assert bill is not None and bill["value"] == "bill-only-guidance"
