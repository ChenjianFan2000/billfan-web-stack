from typing import Dict, Optional

CLASSIFICATION_GUIDANCE_KEY = "classification_guidance"
DEFAULT_CLASSIFICATION_GUIDANCE = ""

DEFAULT_SETTINGS: Dict[str, str] = {
    CLASSIFICATION_GUIDANCE_KEY: DEFAULT_CLASSIFICATION_GUIDANCE,
}


def ensure_default_settings(db, user_id: Optional[int] = None) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        if user_id is None:
            db.execute(
                "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            continue
        db.execute(
            """
            INSERT INTO user_settings (user_id, key, value, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, key) DO NOTHING
            """,
            (int(user_id), key, value),
        )


def get_setting_value(db, key: str, default: str = "", user_id: Optional[int] = None) -> str:
    if user_id is not None:
        row = db.execute(
            "SELECT value FROM user_settings WHERE user_id = ? AND key = ?",
            (int(user_id), key),
        ).fetchone()
        if row is not None:
            return str(row["value"] or "")

    row = db.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    if row is not None:
        return str(row["value"] or "")
    return default


def upsert_setting_value(db, key: str, value: str, user_id: Optional[int] = None) -> None:
    if user_id is None:
        db.execute(
            """
            INSERT INTO app_settings (key, value, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        return

    db.execute(
        """
        INSERT INTO user_settings (user_id, key, value, created_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (int(user_id), key, value),
    )
