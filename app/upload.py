import asyncio
import inspect
import os
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.auth import get_current_user
from app.db import get_db
from app.logger import log_operation
from app import pipeline

router = APIRouter(prefix="/api", tags=["upload"])


def _pdf_dir() -> str:
    return os.getenv("APP_PDFS_DIR", "/var/www/data/pdfs")


def _db_path() -> str:
    return os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")


def _is_pdf_file(file: UploadFile) -> bool:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    return filename.endswith(".pdf") or content_type == "application/pdf"


def _save_upload_file(file: UploadFile, target_path: str) -> None:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def _run_pipeline_job(db_path: str, paper_id: int, job_id: int, pdf_path: str, user_id: int) -> None:
    try:
        try:
            result = pipeline.process_pdf_job(
                db_path=db_path,
                paper_id=paper_id,
                job_id=job_id,
                pdf_path=pdf_path,
                user_id=int(user_id),
            )
        except TypeError:
            # Backward-compatible for patched/mocked callables in tests.
            result = pipeline.process_pdf_job(
                db_path=db_path,
                paper_id=paper_id,
                job_id=job_id,
                pdf_path=pdf_path,
            )

        if inspect.isawaitable(result):
            asyncio.run(result)
    except Exception as exc:  # pragma: no cover - safety net
        from app.db import connect_db

        with connect_db(db_path) as db:
            db.execute(
                "UPDATE processing_jobs SET status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                ("error", str(exc), job_id, int(user_id)),
            )
            db.commit()


@router.post("/upload")
def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not _is_pdf_file(file):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="only PDF is supported")

    file_id = str(uuid.uuid4())
    saved_path = os.path.join(_pdf_dir(), f"{file_id}.pdf")
    _save_upload_file(file, saved_path)

    cur = db.execute(
        "INSERT INTO papers (user_id, file_path) VALUES (?, ?)",
        (int(_user["id"]), saved_path),
    )
    paper_id = cur.lastrowid

    job_cur = db.execute(
        "INSERT INTO processing_jobs (user_id, paper_id, status) VALUES (?, ?, 'pending')",
        (int(_user["id"]), paper_id),
    )
    job_id = job_cur.lastrowid
    db.commit()
    log_operation(
        db,
        operation="upload",
        entity_type="paper",
        entity_id=paper_id,
        detail={"action": "start", "job_id": job_id, "file_path": saved_path},
        status="in_progress",
        message="upload job created",
        user_id=int(_user["id"]),
    )

    background_tasks.add_task(_run_pipeline_job, _db_path(), paper_id, job_id, saved_path, int(_user["id"]))

    return {"job_id": job_id, "paper_id": paper_id}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, _user=Depends(get_current_user), db=Depends(get_db)):
    row = db.execute(
        "SELECT id, status, error_msg FROM processing_jobs WHERE id = ? AND user_id = ?",
        (job_id, int(_user["id"])),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")

    payload = {"job_id": row["id"], "status": row["status"]}
    if row["error_msg"]:
        payload["error_msg"] = row["error_msg"]
    return payload
