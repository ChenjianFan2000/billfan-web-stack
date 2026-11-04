import json
import os
import zipfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth, export
from app.db import connect_db, init_db


def _make_client(db_path, exports_dir):
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(export.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    app.dependency_overrides[export.get_db] = override_get_db

    # export._DEFAULT_EXPORT_DIR is read at runtime by routes, patching here keeps tests isolated.
    export._DEFAULT_EXPORT_DIR = str(exports_dir)

    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "其华", "password": "jclcgs"})
    assert login.status_code == 200
    return client


def _seed_data(db, tmp_path):
    pdfs_dir = tmp_path / "pdfs"
    pdfs_dir.mkdir(exist_ok=True)
    texts_dir = tmp_path / "texts"
    texts_dir.mkdir(exist_ok=True)

    pdf_a = pdfs_dir / "a.pdf"
    pdf_b = pdfs_dir / "b.pdf"
    pdf_c = pdfs_dir / "c.pdf"
    txt_a = texts_dir / "a.txt"
    txt_b = texts_dir / "b.txt"
    txt_c = texts_dir / "c.txt"
    payload = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    pdf_a.write_bytes(payload)
    pdf_b.write_bytes(payload)
    pdf_c.write_bytes(payload)
    txt_a.write_text("Paper A full text", encoding="utf-8")
    txt_b.write_text("Paper B full text", encoding="utf-8")
    txt_c.write_text("Paper C full text", encoding="utf-8")

    db.execute(
        "INSERT INTO categories (id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)",
        (1, "深度学习", 0),
    )
    db.execute(
        "INSERT INTO categories (id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)",
        (2, "自然语言处理", 1),
    )

    db.execute(
        """
        INSERT INTO papers (id, title, authors, year, publisher, doi, category_id, file_path, text_cache_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (1, "Paper A", json.dumps(["Alice"], ensure_ascii=False), 2024, "ConfA", "10.1/a", 1, str(pdf_a), str(txt_a)),
    )
    db.execute(
        """
        INSERT INTO papers (id, title, authors, year, publisher, doi, category_id, file_path, text_cache_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (2, "Paper B", json.dumps(["Bob"], ensure_ascii=False), 2023, "ConfB", "10.1/b", 1, str(pdf_b), str(txt_b)),
    )
    db.execute(
        """
        INSERT INTO papers (id, title, authors, year, publisher, doi, category_id, file_path, text_cache_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (3, "Paper C", json.dumps(["Carol"], ensure_ascii=False), 2022, "ConfC", "10.1/c", 2, str(pdf_c), str(txt_c)),
    )
    db.commit()


def test_export_pdfs_zip_structure(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/pdfs", json={})

    assert resp.status_code == 201
    body = resp.json()
    path = body["file_path"]
    assert os.path.exists(path)

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

    assert any(name.startswith("深度学习/") for name in names)
    assert any(name.startswith("自然语言处理/") for name in names)

    download_resp = client.get(body["download_url"])
    assert download_resp.status_code == 200


def test_export_pdfs_only_includes_selected_categories(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/pdfs", json={"category_ids": [1]})

    assert resp.status_code == 201
    path = resp.json()["file_path"]

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

    assert names
    assert all(name.startswith("深度学习/") for name in names)


def test_export_filters_include_multi_category_paper(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)
        db.execute(
            "INSERT INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
            (3, 1),
        )
        db.commit()

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/pdfs", json={"category_ids": [1]})
    assert resp.status_code == 201
    path = resp.json()["file_path"]

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

    assert any("Paper C" in name for name in names)


def test_export_references_apa_format(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/references", json={"format": "apa", "output": "text"})

    assert resp.status_code == 200
    content = resp.json()["content"]
    assert "Alice" in content
    assert "(2024)." in content


def test_export_references_bibtex_format(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/references", json={"format": "bibtex", "output": "text"})

    assert resp.status_code == 200
    content = resp.json()["content"]
    assert "@article{" in content


def test_export_references_pdf_is_valid(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/references", json={"format": "apa", "output": "pdf"})

    assert resp.status_code == 200
    path = resp.json()["file_path"]
    assert os.path.exists(path)

    with open(path, "rb") as fh:
        payload = fh.read()
    assert payload.startswith(b"%PDF-")
    assert payload.rstrip().endswith(b"%%EOF")


def test_export_logs_to_system_logs(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/pdfs", json={})
    assert resp.status_code == 201

    with connect_db(str(db_path)) as db:
        rows = db.execute("SELECT id FROM system_logs WHERE operation = ?", ("export",)).fetchall()

    assert len(rows) >= 1


def test_export_texts_zip_structure(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/texts", json={})

    assert resp.status_code == 201
    body = resp.json()
    path = body["file_path"]
    assert os.path.exists(path)

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        payload = zf.read(next(name for name in names if name.endswith("Paper A.txt"))).decode("utf-8", errors="ignore")

    assert any(name.startswith("深度学习/") and name.endswith(".txt") for name in names)
    assert any(name.startswith("自然语言处理/") and name.endswith(".txt") for name in names)
    assert "Paper A full text" in payload


def test_export_texts_only_includes_selected_categories(tmp_path):
    db_path = tmp_path / "db.sqlite"
    exports_dir = tmp_path / "exports"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        _seed_data(db, tmp_path)

    client = _make_client(db_path, exports_dir)
    resp = client.post("/api/export/texts", json={"category_ids": [1]})
    assert resp.status_code == 201

    with zipfile.ZipFile(resp.json()["file_path"], "r") as zf:
        names = zf.namelist()
    assert names
    assert all(name.startswith("深度学习/") for name in names)
