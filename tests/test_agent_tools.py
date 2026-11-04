import json
import os

from app import agent
from app.db import connect_db, init_db


def _seed_base_data(db, tmp_path):
    db.execute(
        "INSERT INTO categories (id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)",
        (1, "分类A", 0),
    )
    db.execute(
        "INSERT INTO categories (id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)",
        (2, "分类B", 1),
    )
    db.execute(
        """
        INSERT INTO papers (
            id, title, authors, year, publisher, doi,
            abstract_original, abstract_zh, summary_one_line,
            category_id, file_path, text_cache_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "论文A",
            json.dumps(["Alice", "Bob"], ensure_ascii=False),
            2024,
            "TestConf",
            "10.1000/a",
            "Abstract A",
            "摘要A",
            "一句话A",
            1,
            str(tmp_path / "paper-a.pdf"),
            str(tmp_path / "paper-a.txt"),
        ),
    )
    db.execute(
        """
        INSERT INTO papers (
            id, title, authors, year, publisher, doi,
            abstract_original, abstract_zh, summary_one_line,
            category_id, file_path, text_cache_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            2,
            "论文B",
            json.dumps(["Carol"], ensure_ascii=False),
            2023,
            "JournalX",
            "10.1000/b",
            "Abstract B",
            "摘要B",
            "一句话B",
            2,
            str(tmp_path / "paper-b.pdf"),
            str(tmp_path / "paper-b.txt"),
        ),
    )

    db.execute(
        """
        INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("upload", "paper", 1, json.dumps({"a": 1}), "success", "ok"),
    )
    db.execute(
        """
        INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("paper_edit", "paper", 1, json.dumps({"b": 2}), "success", "ok"),
    )
    db.execute(
        """
        INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("upload", "paper", 2, json.dumps({"c": 3}), "error", "failed"),
    )
    db.commit()


def test_tool_list_categories(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        result = agent.tool_list_categories(db)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["count"] == 1


def test_tool_list_papers_filtered(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        result = agent.tool_list_papers(db, category_id=1)

    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["category_id"] == 1
    assert result[0]["category_ids"] == [1]


def test_tool_move_paper(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        out = agent.tool_move_paper(db, paper_id=1, target_category_id=2)
        row = db.execute("SELECT category_id FROM papers WHERE id = 1").fetchone()
        links = db.execute("SELECT category_id FROM paper_categories WHERE paper_id = 1").fetchall()

    assert out["paper_id"] == 1
    assert row["category_id"] == 2
    assert [item["category_id"] for item in links] == [2]


def test_tool_update_paper_info(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        out = agent.tool_update_paper_info(db, paper_id=1, fields={"title": "新标题"})
        row = db.execute("SELECT title FROM papers WHERE id = 1").fetchone()

    assert out["title"] == "新标题"
    assert row["title"] == "新标题"


def test_tool_create_category(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        out = agent.tool_create_category(db, name="新分类", parent_id=None)
        row = db.execute("SELECT id, name FROM categories WHERE id = ?", (out["id"],)).fetchone()

    assert out["name"] == "新分类"
    assert row["name"] == "新分类"


def test_tool_rename_category(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        db.execute(
            "INSERT INTO categories (id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)",
            (1, "旧名字", 0),
        )
        db.commit()
        out = agent.tool_rename_category(db, category_id=1, new_name="改名后")
        row = db.execute("SELECT name FROM categories WHERE id = 1").fetchone()

    assert out["name"] == "改名后"
    assert row["name"] == "改名后"


def test_tool_search_arxiv(tmp_path):
    _ = tmp_path

    def fake_get(_url):
        return """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<feed xmlns=\"http://www.w3.org/2005/Atom\">
  <entry>
    <id>http://arxiv.org/abs/2501.00001</id>
    <title> Transformer Paper </title>
    <summary> Great results </summary>
    <published>2025-01-01T00:00:00Z</published>
    <author><name>Alice</name></author>
    <link title=\"pdf\" href=\"http://arxiv.org/pdf/2501.00001.pdf\"/>
  </entry>
</feed>
"""

    out = agent.tool_search_arxiv(query="transformer", max_results=3, http_get=fake_get)

    assert len(out) == 1
    assert "title" in out[0]
    assert out[0]["authors"] == ["Alice"]


def test_tool_exa_search(tmp_path):
    _ = tmp_path

    def fake_post(_url, headers, payload):
        assert headers["x-api-key"] == "test-key"
        assert payload["query"] == "LLM survey"
        return {
            "results": [
                {
                    "title": "A",
                    "url": "https://example.com/a",
                    "text": "aaa",
                    "publishedDate": "2026-01-01",
                }
            ]
        }

    out = agent.tool_exa_search(
        query="LLM survey",
        max_results=3,
        http_post=fake_post,
        api_key="test-key",
    )

    assert len(out) == 1
    assert out[0]["url"] == "https://example.com/a"


def test_tool_get_paper_fulltext(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    text_file = tmp_path / "paper-a.txt"
    text_file.write_text("这是完整正文" * 20, encoding="utf-8")

    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        db.execute("UPDATE papers SET text_cache_path = ? WHERE id = 1", (str(text_file),))
        db.commit()
        out = agent.tool_get_paper_fulltext(db, paper_ids=[1], max_chars=200)

    assert len(out) == 1
    assert out[0]["paper_id"] == 1
    assert len(out[0]["text"]) > 0


def test_tool_search_local_papers_fuzzy_query(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    text_file = tmp_path / "paper-a.txt"
    text_file.write_text("service innovation full text", encoding="utf-8")

    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        db.execute("UPDATE papers SET text_cache_path = ? WHERE id = 1", (str(text_file),))
        db.commit()
        out = agent.tool_search_local_papers(db, query="alic", max_results=5)

    assert len(out) >= 1
    assert out[0]["id"] == 1
    assert "authors" in out[0]["matched_fields"]
    assert out[0]["text_available"] is True


def test_tool_get_paper_fulltext_by_query(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    text_file = tmp_path / "paper-b.txt"
    text_file.write_text("这是论文B正文" * 20, encoding="utf-8")

    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        db.execute("UPDATE papers SET text_cache_path = ? WHERE id = 2", (str(text_file),))
        db.commit()
        out = agent.tool_get_paper_fulltext(db, title_query="论文B", max_papers=1, max_chars=180)

    assert len(out) == 1
    assert out[0]["paper_id"] == 2
    assert "text_cache_path" in out[0]
    assert len(out[0]["text"]) > 0


def test_tool_inspect_library_metadata(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    pdfs_dir = tmp_path / "pdfs"
    texts_dir = tmp_path / "texts"
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    texts_dir.mkdir(parents=True, exist_ok=True)

    linked_pdf = pdfs_dir / "linked.pdf"
    linked_pdf.write_bytes(b"%PDF-1.4")
    linked_text = texts_dir / "linked.txt"
    linked_text.write_text("linked text", encoding="utf-8")
    orphan_pdf = pdfs_dir / "orphan.pdf"
    orphan_pdf.write_bytes(b"%PDF-1.4")
    orphan_text = texts_dir / "orphan.txt"
    orphan_text.write_text("orphan text", encoding="utf-8")

    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        db.execute(
            "UPDATE papers SET file_path = ?, text_cache_path = ? WHERE id = 1",
            (str(linked_pdf), str(linked_text)),
        )
        db.execute(
            "UPDATE papers SET file_path = ?, text_cache_path = ? WHERE id = 2",
            (str(tmp_path / "missing.pdf"), str(tmp_path / "missing.txt")),
        )
        db.commit()
        out = agent.tool_inspect_library_metadata(
            db,
            pdfs_dir=str(pdfs_dir),
            texts_dir=str(texts_dir),
            sample_limit=10,
        )

    assert out["papers_total"] == 2
    assert out["missing_pdf_count"] == 1
    assert out["missing_text_count"] == 1
    assert out["orphan_pdf_count"] == 1
    assert out["orphan_text_count"] == 1


def test_tool_get_system_logs(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))
    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        out = agent.tool_get_system_logs(db, operation="upload", last_n=5)

    assert len(out) == 2
    assert all(item["operation"] == "upload" for item in out)


def test_tool_add_chat_pdf_to_library(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    source_pdf = tmp_path / "chat-source.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\\n1 0 obj\\n<<>>\\nendobj\\ntrailer\\n<<>>\\n%%EOF")

    pdfs_dir = tmp_path / "pdfs"
    texts_dir = tmp_path / "texts"

    with connect_db(str(db_path)) as db:
        _seed_base_data(db, tmp_path)
        processed = {
            "title": "来自聊天的论文",
            "authors": ["Zed"],
            "year": 2025,
            "publisher": "ConfY",
            "doi": "10.1000/chat",
            "abstract_original": "abc",
            "abstract_zh": "中文",
            "summary_one_line": "总结",
            "recommended_categories": ["分类A"],
            "recommended_category": "分类A",
        }
        db.execute(
            """
            INSERT INTO chat_attachments (id, message_id, type, file_path, text_cache, processed_data)
            VALUES (1, NULL, ?, ?, ?, ?)
            """,
            (
                "pdf",
                str(source_pdf),
                "这里是缓存文本",
                json.dumps(processed, ensure_ascii=False),
            ),
        )
        db.commit()

        out = agent.tool_add_chat_pdf_to_library(
            db,
            attachment_id=1,
            category_id=None,
            pdfs_dir=str(pdfs_dir),
            texts_dir=str(texts_dir),
        )

        paper = db.execute(
            "SELECT id, title, category_id, file_path, text_cache_path FROM papers WHERE id = ?",
            (out["paper_id"],),
        ).fetchone()
        attach = db.execute("SELECT paper_id FROM chat_attachments WHERE id = 1").fetchone()
        links = db.execute("SELECT category_id FROM paper_categories WHERE paper_id = ?", (out["paper_id"],)).fetchall()

    assert paper is not None
    assert paper["title"] == "来自聊天的论文"
    assert paper["category_id"] == 1
    assert os.path.exists(paper["file_path"])
    assert paper["text_cache_path"] is not None
    assert os.path.exists(paper["text_cache_path"])
    assert [item["category_id"] for item in links] == [1]
    assert attach["paper_id"] == out["paper_id"]
