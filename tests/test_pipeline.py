import json
import os

from app import pipeline
from app.db import connect_db, init_db


class _FakeReader:
    def __init__(self, metadata):
        self.metadata = metadata


def test_step0_extracts_embedded_metadata(tmp_path):
    pdf_path = tmp_path / "meta.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    def fake_reader_factory(_):
        return _FakeReader({"/Title": "Expected Title", "/Author": "Alice; Bob", "/Subject": "AI"})

    hints = pipeline.extract_pdf_metadata_hints(str(pdf_path), reader_factory=fake_reader_factory)

    assert hints["title"] == "Expected Title"
    assert hints["authors"] == ["Alice", "Bob"]
    assert hints["subject"] == "AI"


def test_step0_returns_empty_on_no_meta(tmp_path):
    pdf_path = tmp_path / "no_meta.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    def fake_reader_factory(_):
        return _FakeReader({})

    hints = pipeline.extract_pdf_metadata_hints(str(pdf_path), reader_factory=fake_reader_factory)
    assert hints == {}


class _FakePage:
    def __init__(self, text):
        self._text = text

    def get_text(self, _mode):
        return self._text


class _FakeDoc:
    def __init__(self, pages):
        self._pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def __iter__(self):
        return iter(self._pages)


class _FakeFitz:
    def __init__(self, pages):
        self._pages = pages

    def open(self, _pdf_path):
        return _FakeDoc(self._pages)


def test_step1_extracts_text_from_native_pdf(tmp_path):
    pdf_path = tmp_path / "native.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    long_text = "A" * 300
    fitz_module = _FakeFitz([_FakePage(long_text)])

    result = pipeline.extract_text_pymupdf(str(pdf_path), fitz_module=fitz_module)

    assert len(result["text"]) > 200
    assert result["needs_ocr"] is False


def test_step1_detects_garbled_as_needs_ocr(tmp_path):
    pdf_path = tmp_path / "garbled.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    garbled = "\ufffd" * 250
    fitz_module = _FakeFitz([_FakePage(garbled)])

    result = pipeline.extract_text_pymupdf(str(pdf_path), fitz_module=fitz_module)

    assert result["needs_ocr"] is True


class _FakePlumberPage:
    def __init__(self, tables):
        self._tables = tables

    def extract_tables(self):
        return self._tables


class _FakePlumberPDF:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


class _FakePdfPlumber:
    def __init__(self, pages):
        self._pages = pages

    def open(self, _pdf_path):
        return _FakePlumberPDF(self._pages)


def test_step1_pdfplumber_extracts_tables(tmp_path):
    pdf_path = tmp_path / "table.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    table = [["Method", "Accuracy"], ["A", "0.9"]]
    fake = _FakePdfPlumber([_FakePlumberPage([table])])

    tables_md = pipeline.extract_tables_pdfplumber(str(pdf_path), pdfplumber_module=fake)

    assert "| Method | Accuracy |" in tables_md


class _FakePixmap:
    def __init__(self, payload):
        self._payload = payload

    def tobytes(self, _fmt):
        return self._payload


class _FakeOCRPage:
    def __init__(self, payload):
        self._payload = payload

    def get_pixmap(self, dpi=150):
        return _FakePixmap(self._payload + str(dpi).encode("utf-8"))


def test_step2_ocr_called_only_for_scanned(tmp_path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    fitz_module = _FakeFitz([_FakeOCRPage(b"p1"), _FakeOCRPage(b"p2")])
    called = []

    def fake_ocr(image_bytes, page_no):
        called.append((page_no, image_bytes))
        return "text-{}".format(page_no)

    result = pipeline.run_ocr_branch(str(pdf_path), fake_ocr, fitz_module=fitz_module)

    assert len(called) == 2
    assert "text-1" in result
    assert "text-2" in result


def test_step3_parses_valid_json_response():
    def fake_llm(_payload):
        return json.dumps(
            {
                "title": "T",
                "authors": ["A"],
                "year": 2024,
                "publisher": "P",
                "doi": "10.1/1",
                "abstract_original": "abs",
                "abstract_zh": "摘要",
                "summary_one_line": "一句话",
                "recommended_category": "NLP",
            },
            ensure_ascii=False,
        )

    result = pipeline.llm_extract_metadata("text", {}, ["NLP"], llm_callable=fake_llm)

    assert result["title"] == "T"
    assert result["authors"] == ["A"]
    assert result["year"] == 2024
    assert result["recommended_category"] == "NLP"


def test_step3_handles_malformed_json():
    def fake_llm(_payload):
        return "{bad json"

    result = pipeline.llm_extract_metadata("content", {"title": "Hint"}, ["A"], llm_callable=fake_llm)

    assert result["title"] in {"Hint", "content"[:200]}
    assert result["recommended_category"] == "A"


def test_step3_parses_multiple_recommended_categories_from_text():
    def fake_llm(_payload):
        return {
            "title": "T",
            "authors": ["A"],
            "year": 2024,
            "publisher": "P",
            "doi": "",
            "abstract_original": "abs",
            "abstract_zh": "摘要",
            "summary_one_line": "一句话",
            "recommended_category": "Innovation,Knowledge",
        }

    result = pipeline.llm_extract_metadata(
        "text",
        {},
        ["Innovation", "Knowledge"],
        llm_callable=fake_llm,
    )

    assert result["recommended_categories"] == ["Innovation", "Knowledge"]
    assert result["recommended_category"] == "Innovation"


def test_step4_updates_paper_and_job(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        paper_id = db.execute("INSERT INTO papers (file_path) VALUES (?)", ("/tmp/p.pdf",)).lastrowid
        job_id = db.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (paper_id, "pending"),
        ).lastrowid
        db.execute("INSERT INTO categories (name, parent_id, order_index) VALUES (?, NULL, 0)", ("NLP",))
        db.commit()

        pipeline.write_pipeline_result(
            db,
            paper_id=paper_id,
            job_id=job_id,
            result_dict={
                "title": "Updated",
                "authors": ["Alice"],
                "year": 2025,
                "publisher": "X",
                "doi": "10.1/x",
                "abstract_original": "AO",
                "abstract_zh": "AZ",
                "summary_one_line": "S",
                "recommended_category": "NLP",
            },
            text_cache_path="/tmp/p.txt",
            pdf_path="/tmp/p.pdf",
        )

    with connect_db(str(db_path)) as db:
        paper = db.execute(
            "SELECT title, authors, text_cache_path, category_id FROM papers WHERE id = ?",
            (paper_id,),
        ).fetchone()
        job = db.execute("SELECT status FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
        log = db.execute("SELECT operation, status FROM system_logs WHERE entity_id = ?", (paper_id,)).fetchone()
        links = db.execute(
            "SELECT category_id FROM paper_categories WHERE paper_id = ? ORDER BY category_id ASC",
            (paper_id,),
        ).fetchall()

    assert paper["title"] == "Updated"
    assert json.loads(paper["authors"]) == ["Alice"]
    assert paper["text_cache_path"] == "/tmp/p.txt"
    assert paper["category_id"] is not None
    assert len(links) == 1
    assert job["status"] == "done"
    assert log["operation"] == "upload"
    assert log["status"] == "success"


def test_full_pipeline_native_pdf(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    texts_dir = tmp_path / "texts"
    os.makedirs(str(texts_dir), exist_ok=True)
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        paper_id = db.execute("INSERT INTO papers (file_path) VALUES (?)", (str(tmp_path / "a.pdf"),)).lastrowid
        job_id = db.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (paper_id, "pending"),
        ).lastrowid
        db.execute("INSERT INTO categories (name, parent_id, order_index) VALUES (?, NULL, 0)", ("AI",))
        db.commit()

    monkeypatch.setattr(pipeline, "extract_pdf_metadata_hints", lambda _p: {"title": "T"})
    monkeypatch.setattr(
        pipeline,
        "extract_text_pymupdf",
        lambda _p: {"text": "hello world", "needs_ocr": False, "garbled_ratio": 0.0},
    )
    monkeypatch.setattr(pipeline, "extract_tables_pdfplumber", lambda _p: "")
    monkeypatch.setattr(
        pipeline,
        "llm_extract_metadata",
        lambda text, hints, categories, llm_callable=None: {
            "title": hints.get("title", ""),
            "authors": ["A"],
            "year": 2024,
            "publisher": "P",
            "doi": "",
            "abstract_original": text,
            "abstract_zh": "",
            "summary_one_line": "S",
            "recommended_category": categories[0] if categories else "",
        },
    )

    pipeline.process_pdf_job(
        db_path=str(db_path),
        paper_id=paper_id,
        job_id=job_id,
        pdf_path=str(tmp_path / "a.pdf"),
        texts_dir=str(texts_dir),
    )

    with connect_db(str(db_path)) as db:
        job = db.execute("SELECT status FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
        paper = db.execute("SELECT title, text_cache_path FROM papers WHERE id = ?", (paper_id,)).fetchone()

    assert job["status"] == "done"
    assert paper["title"] == "T"
    assert os.path.exists(paper["text_cache_path"])


def test_process_pdf_job_uses_default_callables(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    texts_dir = tmp_path / "texts"
    os.makedirs(str(texts_dir), exist_ok=True)
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        paper_id = db.execute("INSERT INTO papers (file_path) VALUES (?)", (str(tmp_path / "b.pdf"),)).lastrowid
        job_id = db.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (paper_id, "pending"),
        ).lastrowid
        db.execute("INSERT INTO categories (name, parent_id, order_index) VALUES (?, NULL, 0)", ("ML",))
        db.commit()

    monkeypatch.setattr(pipeline, "extract_pdf_metadata_hints", lambda _p: {"title": "Fallback T"})
    monkeypatch.setattr(
        pipeline,
        "extract_text_pymupdf",
        lambda _p: {"text": "", "needs_ocr": True, "garbled_ratio": 1.0},
    )
    monkeypatch.setattr(
        pipeline,
        "run_ocr_branch",
        lambda pdf_path, ocr_callable, fitz_module=None, max_pages=None: ocr_callable(b"png", 1),
    )

    called = {"ocr": 0, "llm": 0}

    def fake_default_ocr(_img, _page_no):
        called["ocr"] += 1
        return "OCR TEXT"

    def fake_default_llm(payload):
        called["llm"] += 1
        return json.dumps(
            {
                "title": "ByDefault",
                "authors": ["Alice"],
                "year": 2026,
                "publisher": "Conf",
                "doi": "",
                "abstract_original": payload.get("text") or "",
                "abstract_zh": "",
                "summary_one_line": "one line",
                "recommended_category": "ML",
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(pipeline, "default_ocr_callable", fake_default_ocr)
    monkeypatch.setattr(pipeline, "default_llm_callable", fake_default_llm)

    pipeline.process_pdf_job(
        db_path=str(db_path),
        paper_id=paper_id,
        job_id=job_id,
        pdf_path=str(tmp_path / "b.pdf"),
        texts_dir=str(texts_dir),
        ocr_callable=None,
        llm_callable=None,
    )

    assert called["ocr"] == 1
    assert called["llm"] == 1


def test_process_pdf_job_skips_duplicate_by_title(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    texts_dir = tmp_path / "texts"
    os.makedirs(str(texts_dir), exist_ok=True)
    init_db(str(db_path))
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    existing_pdf = tmp_path / "existing.pdf"
    existing_text = texts_dir / "existing.txt"
    existing_pdf.write_bytes(b"%PDF-1.4")
    existing_text.write_text("existing body", encoding="utf-8")

    incoming_pdf = tmp_path / "incoming.pdf"
    incoming_pdf.write_bytes(b"%PDF-1.4")

    with connect_db(str(db_path)) as db:
        existing_paper_id = db.execute(
            "INSERT INTO papers (title, file_path, text_cache_path) VALUES (?, ?, ?)",
            ("A Good Title", str(existing_pdf), str(existing_text)),
        ).lastrowid
        incoming_paper_id = db.execute(
            "INSERT INTO papers (file_path) VALUES (?)",
            (str(incoming_pdf),),
        ).lastrowid
        job_id = db.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (incoming_paper_id, "pending"),
        ).lastrowid
        db.commit()

    monkeypatch.setattr(pipeline, "extract_pdf_metadata_hints", lambda _p: {})
    monkeypatch.setattr(
        pipeline,
        "extract_text_pymupdf",
        lambda _p: {"text": "new body text " * 200, "needs_ocr": False, "garbled_ratio": 0.0},
    )
    monkeypatch.setattr(pipeline, "extract_tables_pdfplumber", lambda _p: "")
    monkeypatch.setattr(
        pipeline,
        "llm_extract_metadata",
        lambda text, hints, categories, llm_callable=None: {
            "title": "a   good title",
            "authors": [],
            "year": None,
            "publisher": "",
            "doi": "",
            "abstract_original": text[:120],
            "abstract_zh": "",
            "summary_one_line": "same",
            "recommended_category": "",
        },
    )

    pipeline.process_pdf_job(
        db_path=str(db_path),
        paper_id=incoming_paper_id,
        job_id=job_id,
        pdf_path=str(incoming_pdf),
        texts_dir=str(texts_dir),
    )

    with connect_db(str(db_path)) as db:
        job = db.execute("SELECT status, error_msg, paper_id FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
        incoming_paper = db.execute("SELECT id FROM papers WHERE id = ?", (incoming_paper_id,)).fetchone()
        existing_paper = db.execute("SELECT id FROM papers WHERE id = ?", (existing_paper_id,)).fetchone()
        log = db.execute(
            "SELECT detail FROM system_logs WHERE operation = ? ORDER BY id DESC LIMIT 1",
            ("upload",),
        ).fetchone()

    assert job["status"] == "skipped"
    assert job["paper_id"] == existing_paper_id
    assert "已存在 #{}".format(existing_paper_id) in (job["error_msg"] or "")
    assert incoming_paper is None
    assert existing_paper is not None
    assert not incoming_pdf.exists()
    assert not (texts_dir / "incoming.txt").exists()
    assert json.loads(log["detail"])["reason"] == "title_exact"


def test_process_pdf_job_skips_duplicate_by_text_similarity(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    texts_dir = tmp_path / "texts"
    os.makedirs(str(texts_dir), exist_ok=True)
    init_db(str(db_path))
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("PAPER_DUPLICATE_TEXT_SIM_THRESHOLD", "0.80")

    base_text = ("VR publishing value co-creation under 5G networks. " * 220).strip()
    existing_pdf = tmp_path / "existing2.pdf"
    existing_text = texts_dir / "existing2.txt"
    existing_pdf.write_bytes(b"%PDF-1.4")
    existing_text.write_text(base_text, encoding="utf-8")

    incoming_pdf = tmp_path / "incoming2.pdf"
    incoming_pdf.write_bytes(b"%PDF-1.4")

    with connect_db(str(db_path)) as db:
        existing_paper_id = db.execute(
            "INSERT INTO papers (title, file_path, text_cache_path) VALUES (?, ?, ?)",
            ("Existing Paper", str(existing_pdf), str(existing_text)),
        ).lastrowid
        incoming_paper_id = db.execute("INSERT INTO papers (file_path) VALUES (?)", (str(incoming_pdf),)).lastrowid
        job_id = db.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (incoming_paper_id, "pending"),
        ).lastrowid
        db.commit()

    monkeypatch.setattr(pipeline, "extract_pdf_metadata_hints", lambda _p: {})
    monkeypatch.setattr(
        pipeline,
        "extract_text_pymupdf",
        lambda _p: {"text": base_text + " appendix", "needs_ocr": False, "garbled_ratio": 0.0},
    )
    monkeypatch.setattr(pipeline, "extract_tables_pdfplumber", lambda _p: "")
    monkeypatch.setattr(
        pipeline,
        "llm_extract_metadata",
        lambda text, hints, categories, llm_callable=None: {
            "title": "Brand New Title",
            "authors": [],
            "year": None,
            "publisher": "",
            "doi": "",
            "abstract_original": text[:120],
            "abstract_zh": "",
            "summary_one_line": "similar body",
            "recommended_category": "",
        },
    )

    pipeline.process_pdf_job(
        db_path=str(db_path),
        paper_id=incoming_paper_id,
        job_id=job_id,
        pdf_path=str(incoming_pdf),
        texts_dir=str(texts_dir),
    )

    with connect_db(str(db_path)) as db:
        job = db.execute("SELECT status, paper_id FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
        incoming_paper = db.execute("SELECT id FROM papers WHERE id = ?", (incoming_paper_id,)).fetchone()
        log = db.execute(
            "SELECT detail FROM system_logs WHERE operation = ? ORDER BY id DESC LIMIT 1",
            ("upload",),
        ).fetchone()

    detail = json.loads(log["detail"])
    assert job["status"] == "skipped"
    assert job["paper_id"] == existing_paper_id
    assert incoming_paper is None
    assert detail["reason"] == "text_similarity"
    assert float(detail["similarity"]) >= 0.8


def test_process_pdf_job_keeps_non_duplicate_when_similarity_low(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    texts_dir = tmp_path / "texts"
    os.makedirs(str(texts_dir), exist_ok=True)
    init_db(str(db_path))
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("PAPER_DUPLICATE_TEXT_SIM_THRESHOLD", "0.95")

    existing_pdf = tmp_path / "existing3.pdf"
    existing_text = texts_dir / "existing3.txt"
    existing_pdf.write_bytes(b"%PDF-1.4")
    existing_text.write_text(("A" * 5000), encoding="utf-8")

    incoming_pdf = tmp_path / "incoming3.pdf"
    incoming_pdf.write_bytes(b"%PDF-1.4")

    with connect_db(str(db_path)) as db:
        db.execute(
            "INSERT INTO papers (title, file_path, text_cache_path) VALUES (?, ?, ?)",
            ("Existing", str(existing_pdf), str(existing_text)),
        )
        incoming_paper_id = db.execute("INSERT INTO papers (file_path) VALUES (?)", (str(incoming_pdf),)).lastrowid
        job_id = db.execute(
            "INSERT INTO processing_jobs (paper_id, status) VALUES (?, ?)",
            (incoming_paper_id, "pending"),
        ).lastrowid
        db.commit()

    monkeypatch.setattr(pipeline, "extract_pdf_metadata_hints", lambda _p: {})
    monkeypatch.setattr(
        pipeline,
        "extract_text_pymupdf",
        lambda _p: {"text": ("B" * 5000), "needs_ocr": False, "garbled_ratio": 0.0},
    )
    monkeypatch.setattr(pipeline, "extract_tables_pdfplumber", lambda _p: "")
    monkeypatch.setattr(
        pipeline,
        "llm_extract_metadata",
        lambda text, hints, categories, llm_callable=None: {
            "title": "Unique New Title",
            "authors": [],
            "year": 2026,
            "publisher": "",
            "doi": "",
            "abstract_original": text[:120],
            "abstract_zh": "",
            "summary_one_line": "new",
            "recommended_category": "",
        },
    )

    pipeline.process_pdf_job(
        db_path=str(db_path),
        paper_id=incoming_paper_id,
        job_id=job_id,
        pdf_path=str(incoming_pdf),
        texts_dir=str(texts_dir),
    )

    with connect_db(str(db_path)) as db:
        job = db.execute("SELECT status, paper_id FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
        incoming_paper = db.execute(
            "SELECT id, title, text_cache_path FROM papers WHERE id = ?",
            (incoming_paper_id,),
        ).fetchone()

    assert job["status"] == "done"
    assert job["paper_id"] == incoming_paper_id
    assert incoming_paper["title"] == "Unique New Title"
    assert os.path.exists(incoming_paper["text_cache_path"])
