import sqlite3

from app.db import INDEX_STATEMENTS, init_db


EXPECTED_TABLES = {
    "users",
    "categories",
    "papers",
    "paper_categories",
    "processing_jobs",
    "system_logs",
    "conversations",
    "messages",
    "chat_attachments",
    "app_settings",
    "user_settings",
}


def _fetch_table_names(db_path):
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return {r[0] for r in rows if not r[0].startswith("sqlite_")}


def _fetch_index_names(db_path):
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    return {r[0] for r in rows}


def test_init_creates_all_tables(tmp_path):
    db_path = tmp_path / "db.sqlite"

    init_db(str(db_path))

    table_names = _fetch_table_names(db_path)
    assert EXPECTED_TABLES.issubset(table_names)


def test_init_idempotent(tmp_path):
    db_path = tmp_path / "db.sqlite"

    init_db(str(db_path))
    init_db(str(db_path))

    table_names = _fetch_table_names(db_path)
    assert EXPECTED_TABLES.issubset(table_names)


def test_wal_mode_enabled(tmp_path):
    db_path = tmp_path / "db.sqlite"

    init_db(str(db_path))

    with sqlite3.connect(str(db_path)) as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    assert str(journal_mode).lower() == "wal"


def test_indexes_exist(tmp_path):
    db_path = tmp_path / "db.sqlite"

    init_db(str(db_path))

    index_names = _fetch_index_names(db_path)
    expected_indexes = {
        stmt.split(" ")[5] for stmt in INDEX_STATEMENTS
    }
    assert expected_indexes.issubset(index_names)
