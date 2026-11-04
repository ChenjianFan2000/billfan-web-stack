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
    login = client.post("/api/auth/login", json={"username": "其华", "password": "jclcgs"})
    assert login.status_code == 200
    return client


def _new_conversation(client):
    resp = client.post("/api/agent/conversations", json={"title": "聊天测试"})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_chat_basic_text_response(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)
    conv_id = _new_conversation(client)

    def fake_model(_payload):
        return {"content": "你好，我在。"}

    monkeypatch.setattr(agent, "_invoke_chat_model", fake_model)

    resp = client.post(
        "/api/agent/conversations/{}/chat".format(conv_id),
        json={"content": "你好"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert '"type": "done"' in resp.text
    assert "你好，我在。" in resp.text

    with connect_db(str(db_path)) as db:
        rows = db.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conv_id,),
        ).fetchall()
    assert len(rows) == 2
    assert rows[0]["role"] == "user"
    assert rows[1]["role"] == "assistant"


def test_chat_triggers_tool_call(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)
    conv_id = _new_conversation(client)

    with connect_db(str(db_path)) as db:
        db.execute("INSERT INTO categories (id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)", (1, "A", 0))
        db.commit()

    state = {"n": 0}

    def fake_model(_payload):
        state["n"] += 1
        if state["n"] == 1:
            return {"tool_calls": [{"name": "list_categories", "arguments": {}}]}
        return {"content": "工具完成"}

    monkeypatch.setattr(agent, "_invoke_chat_model", fake_model)

    resp = client.post(
        "/api/agent/conversations/{}/chat".format(conv_id),
        json={"content": "列出分类"},
    )
    assert resp.status_code == 200
    assert '"type": "tool_call"' in resp.text
    assert "list_categories" in resp.text
    assert "工具完成" in resp.text

    with connect_db(str(db_path)) as db:
        row = db.execute(
            "SELECT content FROM messages WHERE conversation_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
            (conv_id,),
        ).fetchone()
    assert row is not None
    assert row["content"] == "工具完成"


def test_chat_image_attachment_sent_as_vision(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)
    conv_id = _new_conversation(client)

    image_path = tmp_path / "a.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00IHDR")

    with connect_db(str(db_path)) as db:
        db.execute(
            """
            INSERT INTO chat_attachments (id, message_id, type, file_path, text_cache, processed_data)
            VALUES (?, NULL, ?, ?, NULL, NULL)
            """,
            (1, "image", str(image_path)),
        )
        db.commit()

    captured = {}

    def fake_model(payload):
        captured["payload"] = payload
        return {"content": "已看到图片"}

    monkeypatch.setattr(agent, "_invoke_chat_model", fake_model)

    resp = client.post(
        "/api/agent/conversations/{}/chat".format(conv_id),
        json={"content": "看图", "attachment_ids": [1]},
    )
    assert resp.status_code == 200
    assert "已看到图片" in resp.text

    sent = captured["payload"]["images"]
    assert isinstance(sent, list)
    assert len(sent) == 1
    assert sent[0]["attachment_id"] == 1
    assert len(sent[0]["base64"]) > 10


def test_chat_pdf_attachment_uses_text_cache(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)
    conv_id = _new_conversation(client)

    pdf_path = tmp_path / "a.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    with connect_db(str(db_path)) as db:
        db.execute(
            """
            INSERT INTO chat_attachments (id, message_id, type, file_path, text_cache, processed_data)
            VALUES (?, NULL, ?, ?, ?, NULL)
            """,
            (1, "pdf", str(pdf_path), "这是缓存正文，用于直接问答。"),
        )
        db.commit()

    captured = {}

    def fake_model(payload):
        captured["payload"] = payload
        return {"content": "已读取附件"}

    monkeypatch.setattr(agent, "_invoke_chat_model", fake_model)

    resp = client.post(
        "/api/agent/conversations/{}/chat".format(conv_id),
        json={"content": "讲讲这篇论文", "attachment_ids": [1]},
    )
    assert resp.status_code == 200
    assert "已读取附件" in resp.text

    messages = captured["payload"]["messages"]
    assert messages
    assert messages[-1]["role"] == "user"
    assert "这是缓存正文，用于直接问答。" in messages[-1]["content"]


def test_chat_with_paper_ids_injects_library_fulltext(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)
    conv_id = _new_conversation(client)

    text_path = tmp_path / "paper-1.txt"
    text_path.write_text("第二章主要介绍实验设计与数据采样。", encoding="utf-8")

    with connect_db(str(db_path)) as db:
        db.execute(
            """
            INSERT INTO papers (id, title, authors, text_cache_path, abstract_original)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "测试论文", "[]", str(text_path), "摘要"),
        )
        db.commit()

    captured = {}

    def fake_model(payload):
        captured["payload"] = payload
        return {"content": "已读取论文正文"}

    monkeypatch.setattr(agent, "_invoke_chat_model", fake_model)

    resp = client.post(
        "/api/agent/conversations/{}/chat".format(conv_id),
        json={"content": "请讲一下第二章", "paper_ids": [1]},
    )
    assert resp.status_code == 200
    assert "已读取论文正文" in resp.text

    messages = captured["payload"]["messages"]
    assert messages
    assert messages[-1]["role"] == "user"
    assert "[LIBRARY_PAPER:1:测试论文]" in messages[-1]["content"]
    assert "第二章主要介绍实验设计与数据采样。" in messages[-1]["content"]


def test_upload_image_attachment_route(tmp_path):
    db_path = tmp_path / "db.sqlite"
    chat_dir = tmp_path / "chat_files"
    init_db(str(db_path))
    client = _make_client(db_path)

    from app import agent as agent_module

    prev_chat_dir = agent_module.os.getenv("APP_CHAT_FILES_DIR")
    agent_module.os.environ["APP_CHAT_FILES_DIR"] = str(chat_dir)
    try:
        resp = client.post(
            "/api/agent/attachments",
            files={"file": ("a.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00IHDR", "image/png")},
        )
    finally:
        if prev_chat_dir is None:
            del agent_module.os.environ["APP_CHAT_FILES_DIR"]
        else:
            agent_module.os.environ["APP_CHAT_FILES_DIR"] = prev_chat_dir

    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "image"
    assert isinstance(body["attachment_id"], int)

    with connect_db(str(db_path)) as db:
        row = db.execute("SELECT type, file_path FROM chat_attachments WHERE id = ?", (body["attachment_id"],)).fetchone()
    assert row is not None
    assert row["type"] == "image"
    assert str(row["file_path"]).startswith(str(chat_dir))


def test_upload_pdf_attachment_route_runs_processing(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    chat_dir = tmp_path / "chat_files"
    init_db(str(db_path))
    client = _make_client(db_path)

    from app import agent as agent_module

    monkeypatch.setenv("APP_CHAT_FILES_DIR", str(chat_dir))
    monkeypatch.setattr(
        agent_module,
        "_process_chat_pdf_attachment",
        lambda db, pdf_path: {
            "text_cache": "缓存正文",
            "processed_data": {
                "title": "测试论文",
                "authors": ["Alice"],
                "year": 2026,
                "publisher": "Conf",
                "doi": "",
                "abstract_original": "A",
                "abstract_zh": "中",
                "summary_one_line": "一行",
                "recommended_category": "",
            },
        },
    )

    resp = client.post(
        "/api/agent/attachments",
        files={"file": ("paper.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "pdf"
    assert body["processed_data"]["title"] == "测试论文"

    with connect_db(str(db_path)) as db:
        row = db.execute(
            "SELECT type, text_cache, processed_data FROM chat_attachments WHERE id = ?",
            (body["attachment_id"],),
        ).fetchone()
    assert row is not None
    assert row["type"] == "pdf"
    assert row["text_cache"] == "缓存正文"
