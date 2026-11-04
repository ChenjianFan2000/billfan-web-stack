import json
from typing import Any, Dict, Optional

ALLOWED_OPERATIONS = {
    "upload",
    "export",
    "category_edit",
    "paper_edit",
    "agent_action",
    "chat_file",
}

ALLOWED_STATUSES = {"success", "error", "in_progress"}


def log_operation(
    db,
    operation: str,
    entity_type: Optional[str],
    entity_id: Optional[int],
    detail: Dict[str, Any],
    status: str,
    message: str,
    user_id: Optional[int] = None,
) -> int:
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError("invalid operation")
    if status not in ALLOWED_STATUSES:
        raise ValueError("invalid status")
    if not isinstance(detail, dict):
        raise ValueError("detail must be a dict")

    if user_id is None:
        cur = db.execute(
            """
            INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                operation,
                entity_type,
                entity_id,
                json.dumps(detail, ensure_ascii=False),
                status,
                message,
            ),
        )
    else:
        cur = db.execute(
            """
            INSERT INTO system_logs (user_id, operation, entity_type, entity_id, detail, status, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                operation,
                entity_type,
                entity_id,
                json.dumps(detail, ensure_ascii=False),
                status,
                message,
            ),
        )
    db.commit()
    return cur.lastrowid
