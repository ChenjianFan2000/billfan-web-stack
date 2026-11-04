import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth, categories, papers
from app.db import connect_db, init_db


def _make_client(db_path):
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(categories.router)
    app.include_router(papers.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    app.dependency_overrides[categories.get_db] = override_get_db
    app.dependency_overrides[papers.get_db] = override_get_db

    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login.status_code == 200
    return client


def _insert_category(db_path, name):
    with connect_db(str(db_path)) as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, parent_id, order_index) VALUES (?, NULL, 0)",
            (name,),
        )
        conn.commit()
        return cur.lastrowid


def _insert_paper(db_path, **kwargs):
    defaults = {
        "title": "Paper",
        "authors": json.dumps(["Alice", "Bob"], ensure_ascii=False),
        "year": 2024,
        "publisher": "TestConf",
        "doi": "10.1000/test",
        "abstract_original": "original",
        "abstract_zh": "中文摘要",
        "summary_one_line": "一句话",
        "category_id": None,
        "file_path": "/tmp/paper.pdf",
        "text_cache_path": "/tmp/paper.txt",
    }
    defaults.update(kwargs)

    with connect_db(str(db_path)) as conn:
        cur = conn.execute(
            """
            INSERT INTO papers (
                title, authors, year, publisher, doi,
                abstract_original, abstract_zh, summary_one_line,
                category_id, file_path, text_cache_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                defaults["title"],
                defaults["authors"],
                defaults["year"],
                defaults["publisher"],
                defaults["doi"],
                defaults["abstract_original"],
                defaults["abstract_zh"],
                defaults["summary_one_line"],
                defaults["category_id"],
                defaults["file_path"],
                defaults["text_cache_path"],
            ),
        )
        conn.commit()
        return cur.lastrowid


def test_list_papers_empty(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.get("/api/papers")

    assert resp.status_code == 200
    assert resp.json() == []


def test_list_papers_filter_by_category(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    cat_a = _insert_category(db_path, "A")
    cat_b = _insert_category(db_path, "B")

    _insert_paper(db_path, title="A1", category_id=cat_a)
    _insert_paper(db_path, title="A2", category_id=cat_a)
    _insert_paper(db_path, title="B1", category_id=cat_b)

    resp = client.get(f"/api/papers?category_id={cat_a}")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(cat_a in item["category_ids"] for item in data)


def test_get_paper_detail(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    paper_id = _insert_paper(
        db_path,
        title="Test Title",
        authors=json.dumps(["作者甲", "作者乙"], ensure_ascii=False),
        year=2023,
    )

    resp = client.get(f"/api/papers/{paper_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Test Title"
    assert body["authors"] == ["作者甲", "作者乙"]
    assert body["year"] == 2023
    assert isinstance(body["category_ids"], list)
    assert "file_path" in body
    assert "text_cache_path" in body


def test_update_paper_multi_categories(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    cat_a = _insert_category(db_path, "A")
    cat_b = _insert_category(db_path, "B")
    paper_id = _insert_paper(db_path, title="Multi", category_id=cat_a)

    resp = client.put(
        f"/api/papers/{paper_id}",
        json={"category_ids": [cat_a, cat_b]},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["category_ids"] == [cat_a, cat_b]
    assert body["category_id"] == cat_a

    filtered = client.get(f"/api/papers?category_id={cat_b}")
    assert filtered.status_code == 200
    items = filtered.json()
    assert any(item["id"] == paper_id for item in items)


def test_get_paper_file_preview(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    paper_id = _insert_paper(db_path, title="Preview Paper", file_path=str(pdf_file))

    resp = client.get(f"/api/papers/{paper_id}/file?mode=preview")

    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/pdf")
    assert "inline" in (resp.headers.get("content-disposition", "").lower())


def test_get_paper_file_download(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    pdf_file = tmp_path / "sample2.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    paper_id = _insert_paper(db_path, title="Download Paper", file_path=str(pdf_file))

    resp = client.get(f"/api/papers/{paper_id}/file?mode=download")

    assert resp.status_code == 200
    disposition = resp.headers.get("content-disposition", "").lower()
    assert "attachment" in disposition
    assert "download%20paper.pdf" in disposition


def test_get_paper_file_returns_404_when_missing(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    missing_path = tmp_path / "missing.pdf"
    paper_id = _insert_paper(db_path, title="Missing File", file_path=str(missing_path))

    resp = client.get(f"/api/papers/{paper_id}/file")
    assert resp.status_code == 404
    assert "paper file not found" in resp.text


def test_get_paper_file_rejects_invalid_mode(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    pdf_file = tmp_path / "sample3.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    paper_id = _insert_paper(db_path, file_path=str(pdf_file))

    resp = client.get(f"/api/papers/{paper_id}/file?mode=raw")

    assert resp.status_code == 422
    assert "invalid mode" in resp.text


def test_update_paper_fields(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    paper_id = _insert_paper(db_path, title="Old", summary_one_line="Old summary")

    resp = client.put(
        f"/api/papers/{paper_id}",
        json={"title": "New", "summary_one_line": "New summary"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "New"
    assert body["summary_one_line"] == "New summary"

    with connect_db(str(db_path)) as conn:
        row = conn.execute(
            "SELECT title, summary_one_line, publisher FROM papers WHERE id = ?",
            (paper_id,),
        ).fetchone()
        assert row["title"] == "New"
        assert row["summary_one_line"] == "New summary"
        assert row["publisher"] == "TestConf"


def test_delete_paper_removes_files(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    pdf_file = tmp_path / "sample.pdf"
    txt_file = tmp_path / "sample.txt"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    txt_file.write_text("cached text", encoding="utf-8")

    paper_id = _insert_paper(
        db_path,
        file_path=str(pdf_file),
        text_cache_path=str(txt_file),
    )

    resp = client.delete(f"/api/papers/{paper_id}")

    assert resp.status_code == 200
    assert not pdf_file.exists()
    assert not txt_file.exists()

    with connect_db(str(db_path)) as conn:
        row = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,)).fetchone()
        assert row is None


def test_delete_paper_with_related_rows_cleans_dependencies(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    paper_id = _insert_paper(db_path, title="HasDeps")

    with connect_db(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (paper_id, "done"),
        )
        conn.execute(
            "INSERT INTO chat_attachments (type, file_path, paper_id) VALUES (?, ?, ?)",
            ("pdf", "/tmp/att.pdf", paper_id),
        )
        conn.commit()

    resp = client.delete(f"/api/papers/{paper_id}")
    assert resp.status_code == 200

    with connect_db(str(db_path)) as conn:
        paper = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,)).fetchone()
        jobs = conn.execute("SELECT id FROM processing_jobs WHERE paper_id = ?", (paper_id,)).fetchall()
        attachments = conn.execute("SELECT paper_id FROM chat_attachments").fetchall()

    assert paper is None
    assert jobs == []
    assert attachments
    assert all(row["paper_id"] is None for row in attachments)


def test_stats_counts_correctly(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    cat_a = _insert_category(db_path, "A")
    cat_b = _insert_category(db_path, "B")

    _insert_paper(db_path, title="P1", category_id=cat_a)
    _insert_paper(db_path, title="P2", category_id=cat_a)
    _insert_paper(db_path, title="P3", category_id=cat_b)

    resp = client.get("/api/stats")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3

    by_name = {item["name"]: item["count"] for item in body["categories"]}
    assert by_name["A"] == 2
    assert by_name["B"] == 1


def test_paper_edit_operations_write_logs(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)
    paper_id = _insert_paper(db_path, title="日志论文")

    assert client.put(f"/api/papers/{paper_id}", json={"title": "日志论文2"}).status_code == 200
    assert client.delete(f"/api/papers/{paper_id}").status_code == 200

    with connect_db(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT id FROM system_logs WHERE operation = ? AND entity_id = ? ORDER BY id ASC",
            ("paper_edit", paper_id),
        ).fetchall()
    assert len(rows) >= 2
