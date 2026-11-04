from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import agent, auth
from app.db import connect_db, init_db


def _make_client(db_path):
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(agent.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    app.dependency_overrides[agent.get_db] = override_get_db

    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login.status_code == 200
    return client


def test_create_conversation(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.post("/api/agent/conversations", json={"title": "第一次对话"})

    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body["id"], int)
    assert body["title"] == "第一次对话"


def test_list_conversations(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    c1 = client.post("/api/agent/conversations", json={"title": "A"}).json()["id"]
    c2 = client.post("/api/agent/conversations", json={"title": "B"}).json()["id"]
    c3 = client.post("/api/agent/conversations", json={"title": "C"}).json()["id"]

    # Force deterministic order by updated_at.
    with connect_db(str(db_path)) as db:
        db.execute("UPDATE conversations SET updated_at = '2026-03-01 00:00:01' WHERE id = ?", (c1,))
        db.execute("UPDATE conversations SET updated_at = '2026-03-01 00:00:02' WHERE id = ?", (c2,))
        db.execute("UPDATE conversations SET updated_at = '2026-03-01 00:00:03' WHERE id = ?", (c3,))
        db.commit()

    resp = client.get("/api/agent/conversations")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert [item["id"] for item in data] == [c3, c2, c1]


def test_get_messages_in_conversation(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    conv_id = client.post("/api/agent/conversations", json={"title": "对话"}).json()["id"]

    with connect_db(str(db_path)) as db:
        db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', '你好')",
            (conv_id,),
        )
        db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'assistant', '你好，我在')",
            (conv_id,),
        )
        db.commit()

    resp = client.get(f"/api/agent/conversations/{conv_id}/messages")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["role"] == "user"
    assert data[1]["role"] == "assistant"


def test_delete_conversation_cascades(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    conv_id = client.post("/api/agent/conversations", json={"title": "删我"}).json()["id"]

    with connect_db(str(db_path)) as db:
        db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', 'x')",
            (conv_id,),
        )
        db.commit()

    resp = client.delete(f"/api/agent/conversations/{conv_id}")
    assert resp.status_code == 200

    with connect_db(str(db_path)) as db:
        conv = db.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        msg = db.execute("SELECT id FROM messages WHERE conversation_id = ?", (conv_id,)).fetchone()

    assert conv is None
    assert msg is None


def test_auto_title_from_first_message(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        conv_id = agent.create_conversation_record(db)
        long_text = "这是一个超过三十个字符的用户首条消息用于自动标题测试内容"
        agent.append_message(db, conv_id, "user", long_text)

    with connect_db(str(db_path)) as db:
        row = db.execute("SELECT title FROM conversations WHERE id = ?", (conv_id,)).fetchone()

    assert row is not None
    assert row["title"] == long_text[:30]
