from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth, categories
from app.db import connect_db, init_db


def _make_client(db_path):
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(categories.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    app.dependency_overrides[categories.get_db] = override_get_db

    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login.status_code == 200
    return client


def test_get_empty_categories(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.get("/api/categories")

    assert resp.status_code == 200
    assert resp.json() == []


def test_create_root_category(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    create_resp = client.post(
        "/api/categories",
        json={"name": "深度学习", "order_index": 1},
    )
    assert create_resp.status_code == 201

    listing = client.get("/api/categories")
    assert listing.status_code == 200
    data = listing.json()
    assert len(data) == 1
    assert data[0]["name"] == "深度学习"


def test_create_child_category(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    root = client.post("/api/categories", json={"name": "AI"}).json()
    child_resp = client.post(
        "/api/categories",
        json={"name": "CV", "parent_id": root["id"]},
    )

    assert child_resp.status_code == 201

    listing = client.get("/api/categories")
    tree = listing.json()
    assert len(tree) == 1
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "CV"


def test_rename_category(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    created = client.post("/api/categories", json={"name": "CV"}).json()

    resp = client.put(f"/api/categories/{created['id']}", json={"name": "计算机视觉"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "计算机视觉"


def test_delete_category_with_papers_returns_409(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    cat = client.post("/api/categories", json={"name": "NLP"}).json()

    with connect_db(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO papers (title, category_id, file_path) VALUES (?, ?, ?)",
            ("Paper A", cat["id"], "/tmp/a.pdf"),
        )
        conn.commit()

    resp = client.delete(f"/api/categories/{cat['id']}")

    assert resp.status_code == 409


def test_category_paper_count_accurate(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    cat = client.post("/api/categories", json={"name": "RL"}).json()

    with connect_db(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO papers (title, category_id, file_path) VALUES (?, ?, ?)",
            ("A", cat["id"], "/tmp/a.pdf"),
        )
        conn.execute(
            "INSERT INTO papers (title, category_id, file_path) VALUES (?, ?, ?)",
            ("B", cat["id"], "/tmp/b.pdf"),
        )
        conn.execute(
            "INSERT INTO papers (title, category_id, file_path) VALUES (?, ?, ?)",
            ("C", cat["id"], "/tmp/c.pdf"),
        )
        conn.commit()

    listing = client.get("/api/categories")

    assert listing.status_code == 200
    data = listing.json()
    assert data[0]["count"] == 3


def test_category_paper_count_with_multi_categories(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    cat_a = client.post("/api/categories", json={"name": "A"}).json()
    cat_b = client.post("/api/categories", json={"name": "B"}).json()

    with connect_db(str(db_path)) as conn:
        paper_id = conn.execute(
            "INSERT INTO papers (title, category_id, file_path) VALUES (?, ?, ?)",
            ("shared", cat_a["id"], "/tmp/shared.pdf"),
        ).lastrowid
        conn.execute(
            "INSERT INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
            (paper_id, cat_a["id"]),
        )
        conn.execute(
            "INSERT INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
            (paper_id, cat_b["id"]),
        )
        conn.commit()

    listing = client.get("/api/categories")
    assert listing.status_code == 200
    roots = {item["name"]: item["count"] for item in listing.json()}
    assert roots["A"] == 1
    assert roots["B"] == 1


def test_category_operations_write_logs(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    created = client.post("/api/categories", json={"name": "日志分类"}).json()
    assert client.put(f"/api/categories/{created['id']}", json={"name": "日志分类2"}).status_code == 200
    assert client.delete(f"/api/categories/{created['id']}").status_code == 200

    with connect_db(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT operation, status FROM system_logs WHERE operation = ? ORDER BY id ASC",
            ("category_edit",),
        ).fetchall()
    assert len(rows) >= 3
