import os
import sqlite3
from typing import Generator, Optional

from app.settings_store import ensure_default_settings

DEFAULT_DB_PATH = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")

TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY,
        username      TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at    TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id          INTEGER PRIMARY KEY,
        user_id     INTEGER NOT NULL DEFAULT 1,
        name        TEXT NOT NULL,
        parent_id   INTEGER REFERENCES categories(id),
        order_index INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS papers (
        id                INTEGER PRIMARY KEY,
        user_id           INTEGER NOT NULL DEFAULT 1,
        title             TEXT,
        authors           TEXT,
        year              INTEGER,
        publisher         TEXT,
        doi               TEXT,
        abstract_original TEXT,
        abstract_zh       TEXT,
        summary_one_line  TEXT,
        category_id       INTEGER REFERENCES categories(id),
        file_path         TEXT,
        text_cache_path   TEXT,
        created_at        TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS paper_categories (
        paper_id    INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
        category_id INTEGER NOT NULL REFERENCES categories(id),
        PRIMARY KEY (paper_id, category_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS processing_jobs (
        id         INTEGER PRIMARY KEY,
        user_id    INTEGER NOT NULL DEFAULT 1,
        paper_id   INTEGER REFERENCES papers(id),
        status     TEXT DEFAULT 'pending',
        error_msg  TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS system_logs (
        id          INTEGER PRIMARY KEY,
        user_id     INTEGER NOT NULL DEFAULT 1,
        operation   TEXT NOT NULL,
        entity_type TEXT,
        entity_id   INTEGER,
        detail      TEXT,
        status      TEXT,
        message     TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id         INTEGER PRIMARY KEY,
        user_id    INTEGER NOT NULL DEFAULT 1,
        title      TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id              INTEGER PRIMARY KEY,
        conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        role            TEXT NOT NULL,
        content         TEXT,
        attachments     TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat_attachments (
        id             INTEGER PRIMARY KEY,
        user_id        INTEGER NOT NULL DEFAULT 1,
        message_id     INTEGER REFERENCES messages(id) ON DELETE CASCADE,
        type           TEXT NOT NULL,
        file_path      TEXT NOT NULL,
        text_cache     TEXT,
        processed_data TEXT,
        paper_id       INTEGER REFERENCES papers(id),
        created_at     TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key         TEXT PRIMARY KEY,
        value       TEXT NOT NULL,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_settings (
        id          INTEGER PRIMARY KEY,
        user_id     INTEGER NOT NULL,
        key         TEXT NOT NULL,
        value       TEXT NOT NULL,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, key)
    )
    """,
]

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id, order_index, id)",
    "CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_papers_user ON papers(user_id, created_at, id)",
    "CREATE INDEX IF NOT EXISTS idx_papers_user_category ON papers(user_id, category_id)",
    "CREATE INDEX IF NOT EXISTS idx_papers_user_quarantine ON papers(user_id, is_quarantined, created_at, id)",
    "CREATE INDEX IF NOT EXISTS idx_paper_categories_category ON paper_categories(category_id, paper_id)",
    "CREATE INDEX IF NOT EXISTS idx_paper_categories_paper ON paper_categories(paper_id)",
    "CREATE INDEX IF NOT EXISTS idx_system_logs_operation ON system_logs(operation, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status)",
    "CREATE INDEX IF NOT EXISTS idx_processing_jobs_user ON processing_jobs(user_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at, id)",
    "CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_chat_attachments_user ON chat_attachments(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_user_settings_user_key ON user_settings(user_id, key)",
]


def _migrate_multi_category(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO paper_categories (paper_id, category_id)
        SELECT id, category_id
        FROM papers
        WHERE category_id IS NOT NULL
        """
    )
    conn.execute(
        """
        UPDATE papers
        SET category_id = (
            SELECT pc.category_id
            FROM paper_categories pc
            LEFT JOIN categories c ON c.id = pc.category_id
            WHERE pc.paper_id = papers.id
            ORDER BY COALESCE(c.order_index, 999999), pc.category_id
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM paper_categories pc2 WHERE pc2.paper_id = papers.id
        )
        """
    )


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set:
    rows = conn.execute("PRAGMA table_info({})".format(table_name)).fetchall()
    return {str(row[1]) for row in rows}


def _add_column_if_missing(conn: sqlite3.Connection, table_name: str, column_clause: str, column_name: str) -> None:
    existing = _table_columns(conn, table_name)
    if column_name in existing:
        return
    conn.execute("ALTER TABLE {} ADD COLUMN {}".format(table_name, column_clause))


def _migrate_user_scoped_columns(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(conn, "categories", "user_id INTEGER NOT NULL DEFAULT 1", "user_id")
    _add_column_if_missing(conn, "papers", "user_id INTEGER NOT NULL DEFAULT 1", "user_id")
    _add_column_if_missing(conn, "processing_jobs", "user_id INTEGER NOT NULL DEFAULT 1", "user_id")
    _add_column_if_missing(conn, "system_logs", "user_id INTEGER NOT NULL DEFAULT 1", "user_id")
    _add_column_if_missing(conn, "conversations", "user_id INTEGER NOT NULL DEFAULT 1", "user_id")
    _add_column_if_missing(conn, "chat_attachments", "user_id INTEGER NOT NULL DEFAULT 1", "user_id")
    _add_column_if_missing(conn, "papers", "is_quarantined INTEGER NOT NULL DEFAULT 0", "is_quarantined")
    _add_column_if_missing(conn, "papers", "quarantine_reason TEXT", "quarantine_reason")


def _migrate_user_scoped_data(conn: sqlite3.Connection) -> None:
    user_rows = conn.execute("SELECT id, username FROM users ORDER BY id ASC").fetchall()
    if not user_rows:
        return

    username_to_id = {str(row["username"]): int(row["id"]) for row in user_rows}
    fallback_user_id = int(user_rows[0]["id"])
    qihua_user_id = username_to_id.get("其华", fallback_user_id)
    bill_user_id = username_to_id.get("bill_rheston")

    paper_total = int(conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0])
    non_default_scoped = int(
        conn.execute(
            "SELECT COUNT(*) FROM papers WHERE user_id IS NOT NULL AND user_id NOT IN (0, 1)"
        ).fetchone()[0]
    )
    if bill_user_id is not None and paper_total > 0 and non_default_scoped == 0:
        # One-time migration rule for existing shared dataset: assign current library to bill_rheston.
        conn.execute("UPDATE papers SET user_id = ?", (bill_user_id,))
    else:
        conn.execute(
            "UPDATE papers SET user_id = ? WHERE user_id IS NULL OR user_id <= 0",
            (qihua_user_id,),
        )

    conn.execute(
        """
        UPDATE processing_jobs
        SET user_id = COALESCE(
            (SELECT p.user_id FROM papers p WHERE p.id = processing_jobs.paper_id),
            user_id,
            ?
        )
        """,
        (qihua_user_id,),
    )
    conn.execute(
        "UPDATE processing_jobs SET user_id = ? WHERE user_id IS NULL OR user_id <= 0",
        (qihua_user_id,),
    )

    conn.execute(
        """
        UPDATE categories
        SET user_id = COALESCE(
            (
                SELECT p.user_id
                FROM papers p
                WHERE p.category_id = categories.id
                ORDER BY p.id ASC
                LIMIT 1
            ),
            (
                SELECT p2.user_id
                FROM paper_categories pc
                JOIN papers p2 ON p2.id = pc.paper_id
                WHERE pc.category_id = categories.id
                ORDER BY p2.id ASC
                LIMIT 1
            ),
            user_id,
            ?
        )
        """,
        (qihua_user_id,),
    )
    conn.execute(
        "UPDATE categories SET user_id = ? WHERE user_id IS NULL OR user_id <= 0",
        (qihua_user_id,),
    )

    conn.execute(
        """
        UPDATE conversations
        SET user_id = COALESCE(user_id, ?)
        WHERE user_id IS NULL OR user_id <= 0
        """,
        (qihua_user_id,),
    )

    conn.execute(
        """
        UPDATE chat_attachments
        SET user_id = COALESCE(
            (SELECT p.user_id FROM papers p WHERE p.id = chat_attachments.paper_id),
            (
                SELECT c.user_id
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE m.id = chat_attachments.message_id
                LIMIT 1
            ),
            user_id,
            ?
        )
        """,
        (qihua_user_id,),
    )
    conn.execute(
        "UPDATE chat_attachments SET user_id = ? WHERE user_id IS NULL OR user_id <= 0",
        (qihua_user_id,),
    )

    conn.execute(
        """
        UPDATE system_logs
        SET user_id = COALESCE(
            CASE
                WHEN entity_type = 'paper' THEN (
                    SELECT p.user_id FROM papers p WHERE p.id = system_logs.entity_id LIMIT 1
                )
                WHEN entity_type = 'category' THEN (
                    SELECT c.user_id FROM categories c WHERE c.id = system_logs.entity_id LIMIT 1
                )
                ELSE NULL
            END,
            user_id,
            ?
        )
        """,
        (qihua_user_id,),
    )
    conn.execute(
        "UPDATE system_logs SET user_id = ? WHERE user_id IS NULL OR user_id <= 0",
        (qihua_user_id,),
    )

    if bill_user_id is not None:
        legacy_guidance = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            ("classification_guidance",),
        ).fetchone()
        if legacy_guidance is not None and str(legacy_guidance["value"] or "").strip():
            conn.execute(
                """
                INSERT INTO user_settings (user_id, key, value, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, key) DO NOTHING
                """,
                (bill_user_id, "classification_guidance", str(legacy_guidance["value"])),
            )


def _resolve_db_path(db_path: Optional[str]) -> str:
    return db_path or DEFAULT_DB_PATH


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def connect_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = _resolve_db_path(db_path)
    _ensure_parent_dir(path)

    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    with connect_db(db_path) as conn:
        for stmt in TABLE_STATEMENTS:
            conn.execute(stmt)
        _migrate_user_scoped_columns(conn)
        for stmt in INDEX_STATEMENTS:
            conn.execute(stmt)
        _migrate_multi_category(conn)
        _migrate_user_scoped_data(conn)
        ensure_default_settings(conn)
        conn.commit()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()
