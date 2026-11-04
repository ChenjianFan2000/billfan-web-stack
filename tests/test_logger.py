import json

import pytest

from app.db import connect_db, init_db
from app.logger import log_operation


def test_log_writes_to_db(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        log_id = log_operation(
            db=db,
            operation="upload",
            entity_type="paper",
            entity_id=1,
            detail={"file": "a.pdf"},
            status="success",
            message="上传完成",
        )

    with connect_db(str(db_path)) as db:
        row = db.execute("SELECT * FROM system_logs WHERE id = ?", (log_id,)).fetchone()

    assert row is not None
    assert row["operation"] == "upload"
    assert row["status"] == "success"


def test_log_detail_is_valid_json(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        log_id = log_operation(
            db=db,
            operation="export",
            entity_type="export_job",
            entity_id=None,
            detail={"count": 5},
            status="success",
            message="导出成功",
        )

    with connect_db(str(db_path)) as db:
        row = db.execute("SELECT detail FROM system_logs WHERE id = ?", (log_id,)).fetchone()

    detail = json.loads(row["detail"])
    assert detail["count"] == 5


def test_invalid_operation_raises(tmp_path):
    db_path = tmp_path / "db.sqlite"
    init_db(str(db_path))

    with connect_db(str(db_path)) as db:
        with pytest.raises(ValueError):
            log_operation(
                db=db,
                operation="invalid_op",
                entity_type="paper",
                entity_id=1,
                detail={"x": 1},
                status="success",
                message="x",
            )
