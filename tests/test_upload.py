from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth, upload
from app.db import connect_db, init_db


def _make_client(db_path):
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(upload.router)

    def override_get_db():
        conn = connect_db(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[auth.get_db] = override_get_db
    app.dependency_overrides[upload.get_db] = override_get_db

    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"username": "其华", "password": "jclcgs"},
    )
    assert login.status_code == 200
    return client


def _pdf_bytes():
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def test_upload_saves_file(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    pdf_dir = tmp_path / "pdfs"
    init_db(str(db_path))

    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_PDFS_DIR", str(pdf_dir))

    def fake_process_pdf_job(db_path, paper_id, job_id, pdf_path):
        return None

    monkeypatch.setattr(upload.pipeline, "process_pdf_job", fake_process_pdf_job)

    client = _make_client(db_path)
    resp = client.post(
        "/api/upload",
        files={"file": ("paper.pdf", _pdf_bytes(), "application/pdf")},
    )

    assert resp.status_code == 200
    body = resp.json()

    with connect_db(str(db_path)) as conn:
        row = conn.execute("SELECT file_path FROM papers WHERE id = ?", (body["paper_id"],)).fetchone()

    assert row is not None
    assert row["file_path"].startswith(str(pdf_dir))


def test_upload_creates_db_records(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    pdf_dir = tmp_path / "pdfs"
    init_db(str(db_path))

    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_PDFS_DIR", str(pdf_dir))

    def fake_process_pdf_job(db_path, paper_id, job_id, pdf_path):
        return None

    monkeypatch.setattr(upload.pipeline, "process_pdf_job", fake_process_pdf_job)

    client = _make_client(db_path)
    resp = client.post(
        "/api/upload",
        files={"file": ("paper.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert resp.status_code == 200

    body = resp.json()

    with connect_db(str(db_path)) as conn:
        paper_row = conn.execute("SELECT id FROM papers WHERE id = ?", (body["paper_id"],)).fetchone()
        job_row = conn.execute("SELECT status FROM processing_jobs WHERE id = ?", (body["job_id"],)).fetchone()

    assert paper_row is not None
    assert job_row is not None
    assert job_row["status"] in {"pending", "done", "processing"}


def test_upload_returns_job_id(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    pdf_dir = tmp_path / "pdfs"
    init_db(str(db_path))

    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_PDFS_DIR", str(pdf_dir))

    def fake_process_pdf_job(db_path, paper_id, job_id, pdf_path):
        return None

    monkeypatch.setattr(upload.pipeline, "process_pdf_job", fake_process_pdf_job)

    client = _make_client(db_path)
    resp = client.post(
        "/api/upload",
        files={"file": ("paper.pdf", _pdf_bytes(), "application/pdf")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["job_id"], int)
    assert isinstance(body["paper_id"], int)


def test_job_status_pending_then_done(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    pdf_dir = tmp_path / "pdfs"
    init_db(str(db_path))

    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_PDFS_DIR", str(pdf_dir))

    def fake_process_pdf_job(db_path, paper_id, job_id, pdf_path):
        with connect_db(db_path) as conn:
            conn.execute(
                "UPDATE processing_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("done", job_id),
            )
            conn.commit()

    monkeypatch.setattr(upload.pipeline, "process_pdf_job", fake_process_pdf_job)

    client = _make_client(db_path)
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("paper.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert upload_resp.status_code == 200

    job_id = upload_resp.json()["job_id"]
    status_resp = client.get(f"/api/jobs/{job_id}")

    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "done"


def test_job_not_found_returns_404(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.get("/api/jobs/99999")

    assert resp.status_code == 404


def test_upload_non_pdf_returns_422(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    client = _make_client(db_path)

    resp = client.post(
        "/api/upload",
        files={"file": ("not_pdf.txt", b"hello", "text/plain")},
    )

    assert resp.status_code == 422


def test_upload_writes_in_progress_log(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    pdf_dir = tmp_path / "pdfs"
    init_db(str(db_path))
    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_PDFS_DIR", str(pdf_dir))
    monkeypatch.setattr(upload.pipeline, "process_pdf_job", lambda db_path, paper_id, job_id, pdf_path: None)

    client = _make_client(db_path)
    resp = client.post(
        "/api/upload",
        files={"file": ("paper.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert resp.status_code == 200
    paper_id = resp.json()["paper_id"]

    with connect_db(str(db_path)) as conn:
        row = conn.execute(
            "SELECT operation, status FROM system_logs WHERE operation = ? AND entity_id = ? ORDER BY id DESC LIMIT 1",
            ("upload", paper_id),
        ).fetchone()
    assert row is not None
    assert row["status"] in {"in_progress", "success"}
