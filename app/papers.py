import json
import os
import sqlite3
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.auth import get_current_user
from app.db import get_db
from app.logger import log_operation
from app.paper_categories import (
    category_direct_paper_counts,
    fetch_paper_category_ids,
    fetch_paper_category_ids_map,
    missing_category_ids,
    normalize_category_ids,
    set_paper_categories,
)

router = APIRouter(prefix="/api", tags=["papers"])


class PaperUpdateRequest(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    publisher: Optional[str] = None
    doi: Optional[str] = None
    abstract_original: Optional[str] = None
    abstract_zh: Optional[str] = None
    summary_one_line: Optional[str] = None
    category_id: Optional[int] = None
    category_ids: Optional[List[int]] = None
    file_path: Optional[str] = None
    text_cache_path: Optional[str] = None
    is_quarantined: Optional[int] = None
    quarantine_reason: Optional[str] = None


def _parse_authors(authors_raw: Optional[str]) -> List[str]:
    if not authors_raw:
        return []
    try:
        data = json.loads(authors_raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


def _serialize_paper(row, category_ids: List[int], include_paths: bool = True) -> Dict[str, Any]:
    primary_category_id = category_ids[0] if category_ids else row["category_id"]
    paper = {
        "id": row["id"],
        "title": row["title"],
        "authors": _parse_authors(row["authors"]),
        "year": row["year"],
        "publisher": row["publisher"],
        "doi": row["doi"],
        "abstract_original": row["abstract_original"],
        "abstract_zh": row["abstract_zh"],
        "summary_one_line": row["summary_one_line"],
        "category_id": primary_category_id,
        "category_ids": category_ids,
        "created_at": row["created_at"],
    }
    if include_paths:
        paper["file_path"] = row["file_path"]
        paper["text_cache_path"] = row["text_cache_path"]
    return paper


def _get_paper(db, paper_id: int, user_id: int):
    return db.execute(
        """
        SELECT id, title, authors, year, publisher, doi,
               abstract_original, abstract_zh, summary_one_line,
               category_id, file_path, text_cache_path, created_at, user_id,
               is_quarantined, quarantine_reason
        FROM papers
        WHERE id = ? AND user_id = ?
        """,
        (paper_id, int(user_id)),
    ).fetchone()


def _ensure_categories_exist(db, category_ids: List[int], user_id: int) -> None:
    missing = missing_category_ids(db, category_ids, user_id=user_id)
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")


def _safe_pdf_filename(title: str, fallback: str) -> str:
    name = (title or "").strip()
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = fallback
    if not name.lower().endswith(".pdf"):
        name = "{}.pdf".format(name)
    return name[:160]


@router.get("/papers")
def list_papers(
    category_id: Optional[int] = Query(default=None),
    _user=Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = int(_user["id"])
    if category_id is None:
        rows = db.execute(
            """
            SELECT id, title, authors, year, publisher, doi,
                   abstract_original, abstract_zh, summary_one_line,
                   category_id, file_path, text_cache_path, created_at
            FROM papers
            WHERE user_id = ?
              AND COALESCE(is_quarantined, 0) = 0
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT p.id, p.title, p.authors, p.year, p.publisher, p.doi,
                   p.abstract_original, p.abstract_zh, p.summary_one_line,
                   p.category_id, p.file_path, p.text_cache_path, p.created_at
            FROM papers p
            WHERE p.user_id = ?
              AND COALESCE(p.is_quarantined, 0) = 0
              AND EXISTS (SELECT 1 FROM categories c WHERE c.id = ? AND c.user_id = ?)
              AND (
                EXISTS (
                    SELECT 1 FROM paper_categories pc
                    JOIN categories cx ON cx.id = pc.category_id
                    WHERE pc.paper_id = p.id
                      AND pc.category_id = ?
                      AND cx.user_id = ?
                )
                OR (
                    p.category_id = ?
                    AND NOT EXISTS (SELECT 1 FROM paper_categories pc2 WHERE pc2.paper_id = p.id)
                )
              )
            ORDER BY p.created_at DESC, p.id DESC
            """,
            (user_id, category_id, user_id, category_id, user_id, category_id),
        ).fetchall()

    paper_ids = [int(row["id"]) for row in rows]
    category_map = fetch_paper_category_ids_map(db, paper_ids, user_id=user_id)
    return [_serialize_paper(row, category_map.get(int(row["id"]), [])) for row in rows]


@router.get("/papers/{paper_id}")
def get_paper_detail(paper_id: int, _user=Depends(get_current_user), db=Depends(get_db)):
    row = _get_paper(db, paper_id, user_id=int(_user["id"]))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper not found")
    return _serialize_paper(row, fetch_paper_category_ids(db, paper_id, user_id=int(_user["id"])))


@router.get("/papers/{paper_id}/file")
def get_paper_file(
    paper_id: int,
    mode: str = Query(default="preview"),
    _user=Depends(get_current_user),
    db=Depends(get_db),
):
    row = _get_paper(db, paper_id, user_id=int(_user["id"]))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper not found")

    file_path = (row["file_path"] or "").strip()
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper file not found")

    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"preview", "download"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid mode")

    fallback_name = "paper_{}".format(paper_id)
    filename = _safe_pdf_filename(row["title"] or "", fallback=fallback_name)
    disposition = "inline" if normalized_mode == "preview" else "attachment"
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type=disposition,
    )


@router.put("/papers/{paper_id}")
def update_paper(paper_id: int, payload: PaperUpdateRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    user_id = int(_user["id"])
    row = _get_paper(db, paper_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper not found")

    update_data = payload.dict(exclude_unset=True)
    if not update_data:
        return _serialize_paper(row, fetch_paper_category_ids(db, paper_id, user_id=user_id))

    allowed_fields = {
        "title",
        "authors",
        "year",
        "publisher",
        "doi",
        "abstract_original",
        "abstract_zh",
        "summary_one_line",
        "category_id",
        "category_ids",
        "file_path",
        "text_cache_path",
    }

    invalid_keys = [k for k in update_data.keys() if k not in allowed_fields]
    if invalid_keys:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid update fields")

    category_ids_to_set: Optional[List[int]] = None
    if "category_ids" in payload.__fields_set__:
        try:
            category_ids_to_set = normalize_category_ids(payload.category_ids or [])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    elif "category_id" in payload.__fields_set__:
        if payload.category_id is None:
            category_ids_to_set = []
        else:
            try:
                category_ids_to_set = normalize_category_ids([payload.category_id])
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if category_ids_to_set is not None:
        _ensure_categories_exist(db, category_ids_to_set, user_id=user_id)

    update_data.pop("category_ids", None)
    update_data.pop("category_id", None)

    if "authors" in update_data:
        update_data["authors"] = json.dumps(update_data["authors"], ensure_ascii=False)

    if update_data:
        set_clause = ", ".join(f"{field} = ?" for field in update_data.keys())
        params = list(update_data.values()) + [paper_id, user_id]
        db.execute(f"UPDATE papers SET {set_clause} WHERE id = ? AND user_id = ?", params)

    if category_ids_to_set is not None:
        set_paper_categories(db, paper_id, category_ids_to_set)

    db.commit()
    changed_fields = list(update_data.keys())
    if category_ids_to_set is not None:
        changed_fields.append("category_ids")

    log_operation(
        db,
        operation="paper_edit",
        entity_type="paper",
        entity_id=paper_id,
        detail={"action": "update", "fields": changed_fields},
        status="success",
        message="paper updated",
        user_id=user_id,
    )

    updated = _get_paper(db, paper_id, user_id=user_id)
    return _serialize_paper(updated, fetch_paper_category_ids(db, paper_id, user_id=user_id))


@router.delete("/papers/{paper_id}")
def delete_paper(paper_id: int, _user=Depends(get_current_user), db=Depends(get_db)):
    user_id = int(_user["id"])
    row = _get_paper(db, paper_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper not found")

    file_paths = [row["file_path"], row["text_cache_path"]]

    try:
        db.execute("DELETE FROM processing_jobs WHERE paper_id = ? AND user_id = ?", (paper_id, user_id))
        db.execute("UPDATE chat_attachments SET paper_id = NULL WHERE paper_id = ? AND user_id = ?", (paper_id, user_id))
        db.execute("DELETE FROM papers WHERE id = ? AND user_id = ?", (paper_id, user_id))
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="paper cannot be deleted because dependent records still reference it",
        ) from exc

    log_operation(
        db,
        operation="paper_edit",
        entity_type="paper",
        entity_id=paper_id,
        detail={"action": "delete", "file_paths": [p for p in file_paths if p]},
        status="success",
        message="paper deleted",
        user_id=user_id,
    )

    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    return {"ok": True}


@router.get("/stats")
def get_stats(_user=Depends(get_current_user), db=Depends(get_db)):
    user_id = int(_user["id"])
    total_row = db.execute(
        "SELECT COUNT(*) AS total FROM papers WHERE user_id = ? AND COALESCE(is_quarantined, 0) = 0",
        (user_id,),
    ).fetchone()
    category_rows = db.execute(
        """
        SELECT id, name
        FROM categories
        WHERE user_id = ?
        ORDER BY order_index ASC, id ASC
        """,
        (user_id,),
    ).fetchall()
    counts = category_direct_paper_counts(db, user_id=user_id)

    return {
        "total": int(total_row["total"]),
        "categories": [
            {"id": row["id"], "name": row["name"], "count": int(counts.get(int(row["id"]), 0))}
            for row in category_rows
        ],
    }


@router.get("/papers-quarantine")
def list_quarantined_papers(_user=Depends(get_current_user), db=Depends(get_db)):
    user_id = int(_user["id"])
    rows = db.execute(
        """
        SELECT p.id,
               p.title,
               p.file_path,
               p.text_cache_path,
               p.created_at,
               p.quarantine_reason,
               (
                 SELECT j.id
                 FROM processing_jobs j
                 WHERE j.paper_id = p.id AND j.user_id = p.user_id
                 ORDER BY j.id DESC
                 LIMIT 1
               ) AS latest_job_id,
               (
                 SELECT j.status
                 FROM processing_jobs j
                 WHERE j.paper_id = p.id AND j.user_id = p.user_id
                 ORDER BY j.id DESC
                 LIMIT 1
               ) AS latest_job_status,
               (
                 SELECT j.error_msg
                 FROM processing_jobs j
                 WHERE j.paper_id = p.id AND j.user_id = p.user_id
                 ORDER BY j.id DESC
                 LIMIT 1
               ) AS latest_job_error
        FROM papers p
        WHERE p.user_id = ?
          AND COALESCE(p.is_quarantined, 0) = 1
        ORDER BY p.created_at DESC, p.id DESC
        """,
        (user_id,),
    ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "title": row["title"] or "",
            "file_path": row["file_path"] or "",
            "text_cache_path": row["text_cache_path"] or "",
            "created_at": row["created_at"],
            "quarantine_reason": row["quarantine_reason"] or "",
            "latest_job_id": int(row["latest_job_id"]) if row["latest_job_id"] is not None else None,
            "latest_job_status": row["latest_job_status"] or "",
            "latest_job_error": row["latest_job_error"] or "",
        }
        for row in rows
    ]
