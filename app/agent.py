import base64
import difflib
import json
import mimetypes
import os
import queue
import re
import shutil
import threading
import time
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
from app.settings_store import (
    CLASSIFICATION_GUIDANCE_KEY,
    DEFAULT_CLASSIFICATION_GUIDANCE,
    get_setting_value,
)
from app import dashscope_client, pipeline

router = APIRouter(prefix="/api/agent", tags=["agent"])

_DEFAULT_CONVERSATION_TITLE = "新对话"
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def _chat_files_dir() -> str:
    return os.getenv("APP_CHAT_FILES_DIR", "/var/www/data/chat_files")


def _guess_media_type(file_path: str, fallback: str = "application/octet-stream") -> str:
    guessed, _ = mimetypes.guess_type(file_path)
    return guessed or fallback


def _normalize_ext(filename: str, default_ext: str) -> str:
    ext = os.path.splitext((filename or "").strip())[1].lower()
    return ext or default_ext


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)


class ConversationUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class AgentChatRequest(BaseModel):
    content: str = Field(..., min_length=1)
    attachment_ids: Optional[List[int]] = None
    paper_ids: Optional[List[int]] = None


def _serialize_conversation(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "updated_at": row["updated_at"],
    }


def _conversation_exists(db, conversation_id: int, user_id: int) -> bool:
    row = db.execute(
        "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, int(user_id)),
    ).fetchone()
    return row is not None


def create_conversation_record(db, user_id: int = 1, title: Optional[str] = None) -> int:
    final_title = (title or "").strip() or _DEFAULT_CONVERSATION_TITLE
    cur = db.execute(
        "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
        (int(user_id), final_title),
    )
    db.commit()
    return cur.lastrowid


def append_message(
    db,
    conversation_id: int,
    role: str,
    content: Optional[str],
    attachments: Optional[List[int]] = None,
    user_id: int = 1,
) -> int:
    if role not in {"user", "assistant"}:
        raise ValueError("invalid role")

    if not _conversation_exists(db, conversation_id, user_id=user_id):
        raise ValueError("conversation not found")

    attachments_json = None
    if attachments is not None:
        attachments_json = json.dumps(attachments, ensure_ascii=False)

    cur = db.execute(
        "INSERT INTO messages (conversation_id, role, content, attachments) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, attachments_json),
    )

    _maybe_auto_title_on_first_user_message(db, conversation_id, role, content)

    db.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,),
    )
    db.commit()
    return cur.lastrowid


def _maybe_auto_title_on_first_user_message(db, conversation_id: int, role: str, content: Optional[str]) -> None:
    if role != "user":
        return

    conv = db.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    if conv is None:
        return

    current_title = (conv["title"] or "").strip()
    if current_title and current_title != _DEFAULT_CONVERSATION_TITLE:
        return

    count_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM messages WHERE conversation_id = ? AND role = 'user'",
        (conversation_id,),
    ).fetchone()
    if int(count_row["cnt"]) != 1:
        return

    auto_title = (content or "").strip()[:30]
    if not auto_title:
        return

    db.execute("UPDATE conversations SET title = ? WHERE id = ?", (auto_title, conversation_id))


@router.get("/conversations")
def list_conversations(_user=Depends(get_current_user), db=Depends(get_db)):
    rows = db.execute(
        "SELECT id, title, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
        (int(_user["id"]),),
    ).fetchall()
    return [_serialize_conversation(row) for row in rows]


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreateRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    conv_id = create_conversation_record(db, user_id=int(_user["id"]), title=payload.title)
    row = db.execute(
        "SELECT id, title, updated_at FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, int(_user["id"])),
    ).fetchone()
    return _serialize_conversation(row)


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, _user=Depends(get_current_user), db=Depends(get_db)):
    if not _conversation_exists(db, conversation_id, user_id=int(_user["id"])):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")

    rows = db.execute(
        """
        SELECT id, role, content, attachments, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (conversation_id,),
    ).fetchall()

    result = []
    for row in rows:
        attachments = []
        if row["attachments"]:
            try:
                parsed = json.loads(row["attachments"])
                if isinstance(parsed, list):
                    attachments = parsed
            except Exception:
                attachments = []

        result.append(
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "attachments": attachments,
                "created_at": row["created_at"],
            }
        )

    return result


@router.patch("/conversations/{conversation_id}")
def rename_conversation(
    conversation_id: int,
    payload: ConversationUpdateRequest,
    _user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not _conversation_exists(db, conversation_id, user_id=int(_user["id"])):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")

    new_title = payload.title.strip()
    if not new_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title cannot be blank")

    db.execute(
        "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (new_title, conversation_id, int(_user["id"])),
    )
    db.commit()

    row = db.execute(
        "SELECT id, title, updated_at FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, int(_user["id"])),
    ).fetchone()
    return _serialize_conversation(row)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, _user=Depends(get_current_user), db=Depends(get_db)):
    if not _conversation_exists(db, conversation_id, user_id=int(_user["id"])):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")

    db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, int(_user["id"])))
    db.commit()
    return {"ok": True}


def _is_image_file(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower()
    ext = _normalize_ext(file.filename or "", "")
    return content_type.startswith("image/") or ext in _IMAGE_EXTENSIONS


def _is_pdf_file(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower()
    ext = _normalize_ext(file.filename or "", "")
    return content_type == "application/pdf" or ext == ".pdf"


def _save_upload_file(file: UploadFile, target_path: str) -> None:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def _fetch_category_names(db, user_id: int) -> List[str]:
    rows = db.execute(
        "SELECT name FROM categories WHERE user_id = ? ORDER BY order_index ASC, id ASC",
        (int(user_id),),
    ).fetchall()
    return [row["name"] for row in rows]


def _process_chat_pdf_attachment(db, pdf_path: str, user_id: int) -> Dict[str, Any]:
    hints = pipeline.extract_pdf_metadata_hints(pdf_path)
    hints["_classification_guidance"] = get_setting_value(
        db,
        CLASSIFICATION_GUIDANCE_KEY,
        default=DEFAULT_CLASSIFICATION_GUIDANCE,
        user_id=int(user_id),
    )
    step1 = pipeline.extract_text_pymupdf(pdf_path)
    text = str(step1.get("text") or "").strip()

    if not step1.get("needs_ocr"):
        tables_md = pipeline.extract_tables_pdfplumber(pdf_path)
        if tables_md:
            text = (text + "\n\n" + tables_md).strip()
    else:
        ocr_text = pipeline.run_ocr_branch(pdf_path, pipeline.default_ocr_callable)
        if ocr_text:
            text = ocr_text

    categories = _fetch_category_names(db, user_id=int(user_id))
    processed = pipeline.llm_extract_metadata(
        text=text,
        hints=hints,
        categories=categories,
        llm_callable=pipeline.default_llm_callable,
    )
    return {"text_cache": text, "processed_data": processed}


@router.post("/attachments", status_code=status.HTTP_201_CREATED)
def upload_chat_attachment(
    file: UploadFile = File(...),
    _user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not _is_image_file(file) and not _is_pdf_file(file):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="only image/pdf is supported")

    is_image = _is_image_file(file)
    ext = _normalize_ext(file.filename or "", ".png" if is_image else ".pdf")
    file_id = uuid.uuid4().hex
    target_path = os.path.join(_chat_files_dir(), file_id + ext)
    _save_upload_file(file, target_path)

    if is_image:
        cur = db.execute(
            """
            INSERT INTO chat_attachments (user_id, message_id, type, file_path, text_cache, processed_data, paper_id)
            VALUES (?, NULL, ?, ?, NULL, NULL, NULL)
            """,
            (int(_user["id"]), "image", target_path),
        )
        attachment_id = cur.lastrowid
        db.commit()
        log_operation(
            db,
            operation="chat_file",
            entity_type="chat_attachment",
            entity_id=attachment_id,
            detail={"type": "image", "file_path": target_path},
            status="success",
            message="chat image attachment uploaded",
            user_id=int(_user["id"]),
        )
        return {"attachment_id": attachment_id, "type": "image", "file_path": target_path}

    try:
        try:
            processed = _process_chat_pdf_attachment(db, target_path, user_id=int(_user["id"]))
        except TypeError:
            processed = _process_chat_pdf_attachment(db, target_path)
    except Exception as exc:
        log_operation(
            db,
            operation="chat_file",
            entity_type="chat_attachment",
            entity_id=None,
            detail={"type": "pdf", "file_path": target_path, "error": str(exc)},
            status="error",
            message="chat pdf attachment processing failed",
            user_id=int(_user["id"]),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="pdf processing failed")

    cur = db.execute(
        """
        INSERT INTO chat_attachments (user_id, message_id, type, file_path, text_cache, processed_data, paper_id)
        VALUES (?, NULL, ?, ?, ?, ?, NULL)
        """,
        (
            int(_user["id"]),
            "pdf",
            target_path,
            processed["text_cache"],
            json.dumps(processed["processed_data"], ensure_ascii=False),
        ),
    )
    attachment_id = cur.lastrowid
    db.commit()

    log_operation(
        db,
        operation="chat_file",
        entity_type="chat_attachment",
        entity_id=attachment_id,
        detail={"type": "pdf", "file_path": target_path, "has_text": bool(processed["text_cache"])},
        status="success",
        message="chat pdf attachment processed",
        user_id=int(_user["id"]),
    )

    return {
        "attachment_id": attachment_id,
        "type": "pdf",
        "file_path": target_path,
        "processed_data": processed["processed_data"],
    }


# ----------------------
# M8b tool functions
# ----------------------

def _parse_authors(raw_authors: Optional[str]) -> List[str]:
    if not raw_authors:
        return []
    try:
        data = json.loads(raw_authors)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [str(item).strip() for item in data if str(item).strip()]


def tool_list_categories(db, user_id: int = 1) -> List[Dict[str, Any]]:
    rows = db.execute(
        "SELECT id, name, parent_id, order_index FROM categories WHERE user_id = ? ORDER BY order_index ASC, id ASC",
        (int(user_id),),
    ).fetchall()

    if not rows:
        return []

    counts = category_direct_paper_counts(db, user_id=int(user_id))

    nodes = {}
    for row in rows:
        nodes[row["id"]] = {
            "id": row["id"],
            "name": row["name"],
            "parent_id": row["parent_id"],
            "order_index": row["order_index"],
            "count": counts.get(row["id"], 0),
            "children": [],
        }

    roots = []
    for node in nodes.values():
        if node["parent_id"] is None:
            roots.append(node)
        elif node["parent_id"] in nodes:
            nodes[node["parent_id"]]["children"].append(node)

    def _sort(items):
        items.sort(key=lambda x: (x["order_index"], x["id"]))
        for item in items:
            _sort(item["children"])

    _sort(roots)
    return roots


def tool_list_papers(db, user_id: int = 1, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
    if category_id is None:
        rows = db.execute(
            """
            SELECT id, title, authors, year, publisher, category_id, summary_one_line
            FROM papers
            WHERE user_id = ?
              AND COALESCE(is_quarantined, 0) = 0
            ORDER BY id ASC
            """,
            (int(user_id),),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT id, title, authors, year, publisher, category_id, summary_one_line
            FROM papers
            WHERE EXISTS (
                SELECT 1 FROM paper_categories pc
                JOIN categories c ON c.id = pc.category_id
                WHERE pc.paper_id = papers.id AND pc.category_id = ? AND c.user_id = ?
            ) OR (
                category_id = ?
                AND user_id = ?
                AND COALESCE(is_quarantined, 0) = 0
                AND NOT EXISTS (SELECT 1 FROM paper_categories pc2 WHERE pc2.paper_id = papers.id)
            )
              AND user_id = ?
              AND COALESCE(is_quarantined, 0) = 0
            ORDER BY id ASC
            """,
            (category_id, int(user_id), category_id, int(user_id), int(user_id)),
        ).fetchall()

    category_map = fetch_paper_category_ids_map(db, [int(row["id"]) for row in rows], user_id=int(user_id))

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "authors": _parse_authors(row["authors"]),
            "year": row["year"],
            "publisher": row["publisher"],
            "category_ids": category_map.get(int(row["id"]), []),
            "category_id": (category_map.get(int(row["id"]), []) or [row["category_id"]])[0],
            "summary_one_line": row["summary_one_line"],
        }
        for row in rows
    ]


def _normalize_search_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _tokenize_search_query(query: str) -> List[str]:
    normalized = _normalize_search_text(query)
    if not normalized:
        return []
    tokens = [item.strip() for item in re.split(r"[\s,，;；|/]+", normalized) if item.strip()]
    return tokens


def _text_similarity(query: str, target: str) -> float:
    left = _normalize_search_text(query)
    right = _normalize_search_text(target)
    if not left or not right:
        return 0.0
    return difflib.SequenceMatcher(None, left, right).ratio()


def _collect_category_name_map(db, user_id: int = 1) -> Dict[int, str]:
    rows = db.execute(
        "SELECT id, name FROM categories WHERE user_id = ? ORDER BY id ASC",
        (int(user_id),),
    ).fetchall()
    return {int(row["id"]): str(row["name"] or "") for row in rows}


def _paper_match_score(
    row,
    query: str,
    title_query: str = "",
    author_query: str = "",
) -> Dict[str, Any]:
    title = str(row["title"] or "")
    authors = _parse_authors(row["authors"])
    authors_text = " ".join(authors)
    publisher = str(row["publisher"] or "")
    doi = str(row["doi"] or "")
    summary = str(row["summary_one_line"] or "")

    title_norm = _normalize_search_text(title)
    authors_norm = _normalize_search_text(authors_text)
    publisher_norm = _normalize_search_text(publisher)
    doi_norm = _normalize_search_text(doi)
    summary_norm = _normalize_search_text(summary)

    matched_fields: List[str] = []
    score = 0.0

    combined_query = " ".join(
        [item for item in [query, title_query, author_query] if _normalize_search_text(item)]
    ).strip()
    combined_norm = _normalize_search_text(combined_query)
    tokens = _tokenize_search_query(combined_query)

    if _normalize_search_text(title_query):
        title_ratio = _text_similarity(title_query, title)
        if _normalize_search_text(title_query) not in title_norm and title_ratio < 0.35:
            return {"score": 0.0, "matched_fields": []}

    if _normalize_search_text(author_query):
        author_ratio = _text_similarity(author_query, authors_text)
        if _normalize_search_text(author_query) not in authors_norm and author_ratio < 0.35:
            return {"score": 0.0, "matched_fields": []}

    if combined_norm:
        if combined_norm in title_norm:
            score += 150
            matched_fields.append("title")
        if combined_norm in authors_norm:
            score += 130
            matched_fields.append("authors")
        if combined_norm in doi_norm:
            score += 110
            matched_fields.append("doi")
        if combined_norm in publisher_norm:
            score += 70
            matched_fields.append("publisher")
        if combined_norm in summary_norm:
            score += 50
            matched_fields.append("summary")

    for token in tokens:
        if token in title_norm:
            score += 25
            if "title" not in matched_fields:
                matched_fields.append("title")
        if token in authors_norm:
            score += 22
            if "authors" not in matched_fields:
                matched_fields.append("authors")
        if token in doi_norm:
            score += 20
            if "doi" not in matched_fields:
                matched_fields.append("doi")
        if token in publisher_norm:
            score += 12
            if "publisher" not in matched_fields:
                matched_fields.append("publisher")
        if token in summary_norm:
            score += 8
            if "summary" not in matched_fields:
                matched_fields.append("summary")

    title_ratio = _text_similarity(combined_query, title) if combined_query else 0.0
    author_ratio = _text_similarity(combined_query, authors_text) if combined_query else 0.0
    if title_ratio >= 0.35:
        score += title_ratio * 70
        if "title" not in matched_fields:
            matched_fields.append("title")
    if author_ratio >= 0.35:
        score += author_ratio * 60
        if "authors" not in matched_fields:
            matched_fields.append("authors")

    if not combined_norm:
        score = 1.0

    return {"score": score, "matched_fields": matched_fields}


def tool_search_local_papers(
    db,
    query: str = "",
    max_results: int = 10,
    user_id: int = 1,
    title_query: str = "",
    author_query: str = "",
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(max_results), 50))
    rows = db.execute(
        """
        SELECT id, title, authors, year, publisher, doi, summary_one_line, category_id, text_cache_path, file_path
        FROM papers
        WHERE user_id = ?
          AND COALESCE(is_quarantined, 0) = 0
        ORDER BY id DESC
        """,
        (int(user_id),),
    ).fetchall()
    if not rows:
        return []

    category_map = fetch_paper_category_ids_map(db, [int(row["id"]) for row in rows], user_id=int(user_id))
    category_name_map = _collect_category_name_map(db, user_id=int(user_id))

    ranked: List[Dict[str, Any]] = []
    for row in rows:
        match_meta = _paper_match_score(
            row,
            query=query,
            title_query=title_query,
            author_query=author_query,
        )
        score = float(match_meta.get("score") or 0.0)
        if score <= 0:
            continue

        category_ids = category_map.get(int(row["id"]), [])
        primary_category_id = category_ids[0] if category_ids else row["category_id"]
        primary_category_name = category_name_map.get(int(primary_category_id), "") if primary_category_id else ""

        text_cache_path = str(row["text_cache_path"] or "")
        text_exists = bool(text_cache_path and os.path.exists(text_cache_path))

        ranked.append(
            {
                "id": int(row["id"]),
                "title": str(row["title"] or ""),
                "authors": _parse_authors(row["authors"]),
                "year": row["year"],
                "publisher": str(row["publisher"] or ""),
                "doi": str(row["doi"] or ""),
                "summary_one_line": str(row["summary_one_line"] or ""),
                "category_id": int(primary_category_id) if primary_category_id else None,
                "category_ids": category_ids,
                "category_name": primary_category_name,
                "score": round(score, 3),
                "matched_fields": match_meta.get("matched_fields") or [],
                "text_available": text_exists,
                "text_cache_path": text_cache_path,
                "file_path": str(row["file_path"] or ""),
            }
        )

    ranked.sort(key=lambda item: (-float(item["score"]), -int(item["id"])))
    return ranked[:limit]


def tool_inspect_library_metadata(
    db,
    user_id: int = 1,
    sample_limit: int = 20,
    pdfs_dir: Optional[str] = None,
    texts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    sample_limit = max(1, min(int(sample_limit), 100))
    pdfs_dir = pdfs_dir or os.getenv("APP_PDFS_DIR", "/var/www/data/pdfs")
    texts_dir = texts_dir or os.getenv("APP_TEXTS_DIR", "/var/www/data/texts")

    papers = db.execute(
        """
        SELECT id, title, authors, file_path, text_cache_path
        FROM papers
        WHERE user_id = ?
          AND COALESCE(is_quarantined, 0) = 0
        ORDER BY id ASC
        """,
        (int(user_id),),
    ).fetchall()
    categories_total = int(
        db.execute("SELECT COUNT(*) FROM categories WHERE user_id = ?", (int(user_id),)).fetchone()[0]
    )

    missing_pdf: List[int] = []
    missing_text: List[int] = []
    empty_title: List[int] = []
    empty_authors: List[int] = []
    invalid_text_path: List[int] = []
    referenced_pdfs: set = set()
    referenced_texts: set = set()

    for row in papers:
        paper_id = int(row["id"])
        title = str(row["title"] or "").strip()
        authors = _parse_authors(row["authors"])
        pdf_path = str(row["file_path"] or "").strip()
        text_path = str(row["text_cache_path"] or "").strip()

        if not title:
            empty_title.append(paper_id)
        if not authors:
            empty_authors.append(paper_id)

        if pdf_path:
            referenced_pdfs.add(os.path.abspath(pdf_path))
            if not os.path.exists(pdf_path):
                missing_pdf.append(paper_id)
        else:
            missing_pdf.append(paper_id)

        if text_path:
            referenced_texts.add(os.path.abspath(text_path))
            if not os.path.exists(text_path):
                missing_text.append(paper_id)
                invalid_text_path.append(paper_id)
        else:
            missing_text.append(paper_id)

    def _collect_files(root_dir: str, suffix: str) -> List[str]:
        if not root_dir or not os.path.isdir(root_dir):
            return []
        files: List[str] = []
        for current_root, _, names in os.walk(root_dir):
            for name in names:
                if name.lower().endswith(suffix):
                    files.append(os.path.abspath(os.path.join(current_root, name)))
        return files

    pdf_files = _collect_files(pdfs_dir, ".pdf")
    text_files = _collect_files(texts_dir, ".txt")

    global_rows = db.execute("SELECT file_path, text_cache_path FROM papers").fetchall()
    global_pdf_refs: set = set()
    global_text_refs: set = set()
    for row in global_rows:
        pdf_path = str(row["file_path"] or "").strip()
        text_path = str(row["text_cache_path"] or "").strip()
        if pdf_path:
            global_pdf_refs.add(os.path.abspath(pdf_path))
        if text_path:
            global_text_refs.add(os.path.abspath(text_path))

    orphan_pdfs = [path for path in pdf_files if path not in global_pdf_refs]
    orphan_texts = [path for path in text_files if path not in global_text_refs]

    return {
        "user_id": int(user_id),
        "papers_total": len(papers),
        "categories_total": categories_total,
        "pdf_dir": pdfs_dir,
        "texts_dir": texts_dir,
        "pdf_files_total": len(pdf_files),
        "text_files_total": len(text_files),
        "missing_pdf_count": len(missing_pdf),
        "missing_text_count": len(missing_text),
        "empty_title_count": len(empty_title),
        "empty_authors_count": len(empty_authors),
        "orphan_pdf_count": len(orphan_pdfs),
        "orphan_text_count": len(orphan_texts),
        "sample_missing_pdf_paper_ids": missing_pdf[:sample_limit],
        "sample_missing_text_paper_ids": missing_text[:sample_limit],
        "sample_empty_title_paper_ids": empty_title[:sample_limit],
        "sample_empty_authors_paper_ids": empty_authors[:sample_limit],
        "sample_orphan_pdf_files": orphan_pdfs[:sample_limit],
        "sample_orphan_text_files": orphan_texts[:sample_limit],
        "sample_invalid_text_path_paper_ids": invalid_text_path[:sample_limit],
    }


def tool_move_paper(db, paper_id: int, target_category_id: int, user_id: int = 1) -> Dict[str, Any]:
    paper = db.execute(
        "SELECT id FROM papers WHERE id = ? AND user_id = ? AND COALESCE(is_quarantined, 0) = 0",
        (paper_id, int(user_id)),
    ).fetchone()
    if paper is None:
        raise ValueError("paper not found")

    category = db.execute(
        "SELECT id FROM categories WHERE id = ? AND user_id = ?",
        (target_category_id, int(user_id)),
    ).fetchone()
    if category is None:
        raise ValueError("target category not found")

    set_paper_categories(db, paper_id, [target_category_id])
    db.commit()
    log_operation(
        db,
        operation="paper_edit",
        entity_type="paper",
        entity_id=paper_id,
        detail={"action": "move", "target_category_id": target_category_id},
        status="success",
        message="paper moved by agent",
        user_id=int(user_id),
    )
    return {"paper_id": paper_id, "category_id": target_category_id, "category_ids": [target_category_id]}


def tool_update_paper_info(db, paper_id: int, fields: Dict[str, Any], user_id: int = 1) -> Dict[str, Any]:
    if not isinstance(fields, dict) or not fields:
        raise ValueError("fields must be non-empty dict")

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

    for key in fields.keys():
        if key not in allowed_fields:
            raise ValueError("invalid field")

    category_ids_to_set: Optional[List[int]] = None
    if "category_ids" in fields:
        try:
            category_ids_to_set = normalize_category_ids(fields["category_ids"] or [])
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
    elif "category_id" in fields:
        if fields["category_id"] is None:
            category_ids_to_set = []
        else:
            try:
                category_ids_to_set = normalize_category_ids([fields["category_id"]])
            except ValueError as exc:
                raise ValueError(str(exc)) from exc

    if category_ids_to_set is not None:
        missing = missing_category_ids(db, category_ids_to_set, user_id=int(user_id))
        if missing:
            raise ValueError("category not found")

    if "authors" in fields:
        if not isinstance(fields["authors"], list):
            raise ValueError("authors must be list")
        fields["authors"] = json.dumps(fields["authors"], ensure_ascii=False)

    fields = dict(fields)
    fields.pop("category_ids", None)
    fields.pop("category_id", None)

    if fields:
        set_clause = ", ".join(["{} = ?".format(key) for key in fields.keys()])
        params = list(fields.values()) + [paper_id, int(user_id)]
        db.execute("UPDATE papers SET {} WHERE id = ? AND user_id = ?".format(set_clause), params)
    if category_ids_to_set is not None:
        set_paper_categories(db, paper_id, category_ids_to_set)
    db.commit()
    log_operation(
        db,
        operation="paper_edit",
        entity_type="paper",
        entity_id=paper_id,
        detail={
            "action": "update",
            "fields": list(fields.keys()) + (["category_ids"] if category_ids_to_set is not None else []),
            "source": "agent_tool",
        },
        status="success",
        message="paper updated by agent",
        user_id=int(user_id),
    )

    row = db.execute(
        "SELECT id, title, authors, year, publisher, category_id FROM papers WHERE id = ? AND user_id = ? AND COALESCE(is_quarantined, 0) = 0",
        (paper_id, int(user_id)),
    ).fetchone()
    if row is None:
        raise ValueError("paper not found")

    category_ids = fetch_paper_category_ids(db, paper_id, user_id=int(user_id))
    return {
        "id": row["id"],
        "title": row["title"],
        "authors": _parse_authors(row["authors"]),
        "year": row["year"],
        "publisher": row["publisher"],
        "category_id": category_ids[0] if category_ids else row["category_id"],
        "category_ids": category_ids,
    }


def tool_create_category(db, name: str, parent_id: Optional[int] = None, user_id: int = 1) -> Dict[str, Any]:
    final_name = (name or "").strip()
    if not final_name:
        raise ValueError("name cannot be blank")

    if parent_id is not None:
        parent = db.execute(
            "SELECT id, parent_id FROM categories WHERE id = ? AND user_id = ?",
            (parent_id, int(user_id)),
        ).fetchone()
        if parent is None:
            raise ValueError("parent not found")
        if parent["parent_id"] is not None:
            raise ValueError("only one-level nesting is allowed")

    cur = db.execute(
        "INSERT INTO categories (user_id, name, parent_id, order_index) VALUES (?, ?, ?, 0)",
        (int(user_id), final_name, parent_id),
    )
    db.commit()
    log_operation(
        db,
        operation="category_edit",
        entity_type="category",
        entity_id=cur.lastrowid,
        detail={"action": "create", "name": final_name, "parent_id": parent_id, "source": "agent_tool"},
        status="success",
        message="category created by agent",
        user_id=int(user_id),
    )
    return {"id": cur.lastrowid, "name": final_name, "parent_id": parent_id}


def tool_rename_category(db, category_id: int, new_name: str, user_id: int = 1) -> Dict[str, Any]:
    final_name = (new_name or "").strip()
    if not final_name:
        raise ValueError("new_name cannot be blank")

    row = db.execute(
        "SELECT id FROM categories WHERE id = ? AND user_id = ?",
        (category_id, int(user_id)),
    ).fetchone()
    if row is None:
        raise ValueError("category not found")

    db.execute(
        "UPDATE categories SET name = ? WHERE id = ? AND user_id = ?",
        (final_name, category_id, int(user_id)),
    )
    db.commit()
    log_operation(
        db,
        operation="category_edit",
        entity_type="category",
        entity_id=category_id,
        detail={"action": "rename", "name": final_name, "source": "agent_tool"},
        status="success",
        message="category renamed by agent",
        user_id=int(user_id),
    )
    return {"id": category_id, "name": final_name}


def _http_get_text(url: str) -> str:
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _clean_text(text: str) -> str:
    return " ".join((text or "").split())


def tool_search_arxiv(query: str, max_results: int = 5, http_get=None) -> List[Dict[str, Any]]:
    http_get = http_get or _http_get_text
    max_results = max(1, min(int(max_results), 20))

    encoded_query = urllib.parse.quote_plus(query)
    url = "http://export.arxiv.org/api/query?search_query=all:{}&start=0&max_results={}".format(
        encoded_query,
        max_results,
    )
    raw_xml = http_get(url)

    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw_xml)
    entries = root.findall("a:entry", ns)

    results = []
    for entry in entries:
        title = _clean_text(entry.findtext("a:title", default="", namespaces=ns))
        summary = _clean_text(entry.findtext("a:summary", default="", namespaces=ns))
        entry_id = _clean_text(entry.findtext("a:id", default="", namespaces=ns))
        published = _clean_text(entry.findtext("a:published", default="", namespaces=ns))

        authors = []
        for node in entry.findall("a:author", ns):
            name = _clean_text(node.findtext("a:name", default="", namespaces=ns))
            if name:
                authors.append(name)

        pdf_url = ""
        for link in entry.findall("a:link", ns):
            link_type = (link.attrib.get("type") or "").lower()
            link_title = (link.attrib.get("title") or "").lower()
            href = link.attrib.get("href") or ""
            if link_type == "application/pdf" or link_title == "pdf":
                pdf_url = href
                break

        results.append(
            {
                "id": entry_id,
                "title": title,
                "summary": summary,
                "published": published,
                "authors": authors,
                "pdf_url": pdf_url,
            }
        )

    return results[:max_results]


def _http_post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    return json.loads(body)


def _extract_mcp_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if not isinstance(result, dict):
        return ""
    content = result.get("content")
    if isinstance(content, list):
        chunks = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
        if chunks:
            return "\n".join(chunks)
    text = result.get("text")
    if isinstance(text, str):
        return text
    return ""


def _mcp_call_tool(server_url: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": "agent-tool-call",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    req = urllib.request.Request(
        url=server_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    data = json.loads(body)
    if isinstance(data, dict) and "result" in data:
        return data.get("result")
    return data


def tool_exa_search(
    query: str,
    max_results: int = 5,
    http_post=None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    http_post = http_post or _http_post_json
    api_key = api_key or os.getenv("EXA_API_KEY", "")

    max_results = max(1, min(int(max_results), 20))

    mcp_url = (os.getenv("EXA_MCP_URL", "https://mcp.exa.ai/mcp") or "").strip()
    if mcp_url:
        try:
            mcp_result = _mcp_call_tool(
                mcp_url,
                os.getenv("EXA_MCP_TOOL_NAME", "web_search_exa"),
                {"query": query, "numResults": max_results},
            )
            text = _extract_mcp_text(mcp_result)
            if text:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        results = parsed.get("results")
                        if isinstance(results, list):
                            return [
                                {
                                    "title": str(item.get("title") or ""),
                                    "url": str(item.get("url") or ""),
                                    "text": str(item.get("text") or ""),
                                    "published_date": str(item.get("publishedDate") or ""),
                                }
                                for item in results[:max_results]
                                if isinstance(item, dict)
                            ]
                except Exception:
                    pass
        except Exception:
            pass

    if not api_key:
        return []

    payload = {"query": query, "numResults": max_results}
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    try:
        data = http_post("https://api.exa.ai/search", headers, payload)
    except Exception:
        return []

    results = []
    for item in data.get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "text": item.get("text", ""),
                "published_date": item.get("publishedDate", ""),
            }
        )
    return results


def tool_paper_search(
    query: str,
    max_results: int = 5,
    http_get=None,
) -> List[Dict[str, Any]]:
    max_results = max(1, min(int(max_results), 20))
    mcp_url = (os.getenv("PAPER_SEARCH_MCP_URL", "") or "").strip()
    tool_name = (os.getenv("PAPER_SEARCH_MCP_TOOL_NAME", "search_papers") or "search_papers").strip()

    if mcp_url:
        try:
            mcp_result = _mcp_call_tool(mcp_url, tool_name, {"query": query, "max_results": max_results})
            text = _extract_mcp_text(mcp_result)
            if text:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return parsed[:max_results]
                    if isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
                        return parsed["results"][:max_results]
                except Exception:
                    return [{"title": "paper_search", "summary": text[:2000]}]
        except Exception:
            pass

    http_get = http_get or _http_get_text
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/search"
        "?query={}&limit={}&fields=title,year,authors,url,abstract,venue"
    ).format(urllib.parse.quote_plus(query), max_results)
    try:
        body = http_get(url)
        data = json.loads(body)
    except Exception:
        return []

    out = []
    for item in data.get("data", [])[:max_results]:
        if not isinstance(item, dict):
            continue
        authors = []
        for author in item.get("authors", []) or []:
            if isinstance(author, dict):
                name = str(author.get("name") or "").strip()
                if name:
                    authors.append(name)
        out.append(
            {
                "title": str(item.get("title") or ""),
                "year": item.get("year"),
                "authors": authors,
                "url": str(item.get("url") or ""),
                "summary": str(item.get("abstract") or ""),
                "publisher": str(item.get("venue") or ""),
            }
        )
    return out


def tool_get_paper_fulltext(
    db,
    paper_ids: Optional[List[int]] = None,
    query: str = "",
    title_query: str = "",
    author_query: str = "",
    max_papers: int = 8,
    texts_dir: Optional[str] = None,
    max_chars: int = 12000,
    user_id: int = 1,
) -> List[Dict[str, Any]]:
    texts_dir = texts_dir or os.getenv("APP_TEXTS_DIR", "/var/www/data/texts")
    max_chars = max(500, min(int(max_chars), 120000))
    max_papers = max(1, min(int(max_papers), 20))

    selected_ids: List[int] = []
    if isinstance(paper_ids, list):
        seen = set()
        for paper_id in paper_ids:
            try:
                parsed = int(paper_id)
            except Exception:
                continue
            if parsed <= 0 or parsed in seen:
                continue
            seen.add(parsed)
            selected_ids.append(parsed)

    if not selected_ids and (_normalize_search_text(query) or _normalize_search_text(title_query) or _normalize_search_text(author_query)):
        hits = tool_search_local_papers(
            db,
            query=str(query or ""),
            title_query=str(title_query or ""),
            author_query=str(author_query or ""),
            user_id=int(user_id),
            max_results=max_papers,
        )
        selected_ids = [int(item["id"]) for item in hits]

    if not selected_ids:
        return []

    result = []
    for paper_id in selected_ids[:max_papers]:
        row = db.execute(
            "SELECT id, title, abstract_original, text_cache_path, file_path FROM papers WHERE id = ? AND user_id = ? AND COALESCE(is_quarantined, 0) = 0",
            (paper_id, int(user_id)),
        ).fetchone()
        if row is None:
            continue

        text = ""
        text_path = row["text_cache_path"]
        if text_path and os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif texts_dir:
            fallback = os.path.join(texts_dir, "{}.txt".format(paper_id))
            if os.path.exists(fallback):
                with open(fallback, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

        if not text:
            text = row["abstract_original"] or ""

        if len(text) > max_chars:
            text = text[:max_chars]

        result.append(
            {
                "paper_id": row["id"],
                "title": row["title"],
                "text": text,
                "text_cache_path": str(row["text_cache_path"] or ""),
                "file_path": str(row["file_path"] or ""),
            }
        )

    return result


def tool_get_system_logs(
    db,
    user_id: int = 1,
    operation: Optional[str] = None,
    last_n: int = 20,
    entity_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    filters = ["user_id = ?"]
    params = [int(user_id)]

    if operation:
        filters.append("operation = ?")
        params.append(operation)

    if entity_id is not None:
        filters.append("entity_id = ?")
        params.append(entity_id)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    limit = max(1, min(int(last_n), 200))
    rows = db.execute(
        """
        SELECT id, operation, entity_type, entity_id, detail, status, message, created_at
        FROM system_logs
        {}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """.format(where_clause),
        tuple(params + [limit]),
    ).fetchall()

    result = []
    for row in rows:
        detail_obj = {}
        if row["detail"]:
            try:
                parsed = json.loads(row["detail"])
                if isinstance(parsed, dict):
                    detail_obj = parsed
            except Exception:
                detail_obj = {}

        result.append(
            {
                "id": row["id"],
                "operation": row["operation"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "detail": detail_obj,
                "status": row["status"],
                "message": row["message"],
                "created_at": row["created_at"],
            }
        )

    return result


def _resolve_category_id_by_name(db, user_id: int = 1, category_name: str = "") -> Optional[int]:
    if not category_name:
        return None
    row = db.execute(
        "SELECT id FROM categories WHERE user_id = ? AND name = ? ORDER BY id ASC LIMIT 1",
        (int(user_id), category_name),
    ).fetchone()
    if row is None:
        return None
    return row["id"]


def _resolve_category_ids_by_names(db, user_id: int = 1, names: List[str] = None) -> List[int]:
    names = names or []
    resolved: List[int] = []
    for name in names:
        category_id = _resolve_category_id_by_name(db, int(user_id), str(name or "").strip())
        if category_id is None:
            continue
        category_id_int = int(category_id)
        if category_id_int in resolved:
            continue
        resolved.append(category_id_int)
    return resolved


def tool_add_chat_pdf_to_library(
    db,
    attachment_id: int,
    category_id: Optional[int] = None,
    pdfs_dir: str = "/var/www/data/pdfs",
    texts_dir: str = "/var/www/data/texts",
    user_id: int = 1,
) -> Dict[str, Any]:
    row = db.execute(
        """
        SELECT id, type, file_path, text_cache, processed_data, paper_id
        FROM chat_attachments
        WHERE id = ? AND user_id = ?
        """,
        (attachment_id, int(user_id)),
    ).fetchone()

    if row is None:
        raise ValueError("attachment not found")
    if row["type"] != "pdf":
        raise ValueError("attachment type must be pdf")

    if row["paper_id"] is not None:
        return {"paper_id": row["paper_id"], "already_exists": True}

    source_pdf = row["file_path"]
    if not source_pdf or not os.path.exists(source_pdf):
        raise ValueError("attachment file missing")

    processed = {}
    if row["processed_data"]:
        try:
            parsed = json.loads(row["processed_data"])
            if isinstance(parsed, dict):
                processed = parsed
        except Exception:
            processed = {}

    if category_id is not None:
        c_row = db.execute(
            "SELECT id FROM categories WHERE id = ? AND user_id = ?",
            (category_id, int(user_id)),
        ).fetchone()
        if c_row is None:
            raise ValueError("category not found")
        category_ids = [int(category_id)]
    else:
        rec_names = processed.get("recommended_categories")
        if isinstance(rec_names, list):
            names = [str(name or "").strip() for name in rec_names if str(name or "").strip()]
        else:
            names = []
        if not names:
            single = str(processed.get("recommended_category") or "").strip()
            if single:
                names = [single]
        category_ids = _resolve_category_ids_by_names(db, int(user_id), names)

    os.makedirs(pdfs_dir, exist_ok=True)
    os.makedirs(texts_dir, exist_ok=True)

    ext = os.path.splitext(source_pdf)[1] or ".pdf"
    file_token = uuid.uuid4().hex
    target_pdf = os.path.join(pdfs_dir, file_token + ext)
    target_text = os.path.join(texts_dir, file_token + ".txt")

    shutil.copy2(source_pdf, target_pdf)

    text_content = row["text_cache"] or ""
    if not text_content:
        text_content = str(processed.get("text_cache") or "")

    text_cache_path = None
    if text_content:
        with open(target_text, "w", encoding="utf-8") as f:
            f.write(text_content)
        text_cache_path = target_text

    authors = processed.get("authors") if isinstance(processed.get("authors"), list) else []

    cur = db.execute(
        """
        INSERT INTO papers (
            user_id, title, authors, year, publisher, doi,
            abstract_original, abstract_zh, summary_one_line,
            category_id, file_path, text_cache_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(user_id),
            str(processed.get("title") or ""),
            json.dumps(authors, ensure_ascii=False),
            processed.get("year"),
            str(processed.get("publisher") or ""),
            str(processed.get("doi") or ""),
            str(processed.get("abstract_original") or ""),
            str(processed.get("abstract_zh") or ""),
            str(processed.get("summary_one_line") or ""),
            category_ids[0] if category_ids else None,
            target_pdf,
            text_cache_path,
        ),
    )
    new_paper_id = cur.lastrowid
    set_paper_categories(db, new_paper_id, category_ids)

    db.execute(
        "UPDATE chat_attachments SET paper_id = ? WHERE id = ? AND user_id = ?",
        (new_paper_id, attachment_id, int(user_id)),
    )
    db.commit()
    log_operation(
        db,
        operation="chat_file",
        entity_type="chat_attachment",
        entity_id=attachment_id,
        detail={"action": "add_to_library", "paper_id": new_paper_id},
        status="success",
        message="chat pdf added to library",
        user_id=int(user_id),
    )

    return {
        "paper_id": new_paper_id,
        "file_path": target_pdf,
        "text_cache_path": text_cache_path,
        "category_id": category_ids[0] if category_ids else None,
        "category_ids": category_ids,
    }


def _tool_schemas() -> List[Dict[str, Any]]:
    return [
        {
            "name": "list_categories",
            "description": "列出所有分类树与论文计数。",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "list_papers",
            "description": "列出论文，可按分类筛选。",
            "input_schema": {
                "type": "object",
                "properties": {"category_id": {"type": "integer"}},
            },
        },
        {
            "name": "search_local_papers",
            "description": "在当前用户论文库中按标题/作者等字段做模糊检索，并返回候选论文及文本可用性。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "title_query": {"type": "string"},
                    "author_query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
            },
        },
        {
            "name": "inspect_library_metadata",
            "description": "检查数据库与论文目录/文本目录的一致性、缺失文件与孤儿文件等元数据健康度。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sample_limit": {"type": "integer"},
                },
            },
        },
        {
            "name": "move_paper",
            "description": "移动论文到指定分类。",
            "input_schema": {
                "type": "object",
                "required": ["paper_id", "target_category_id"],
                "properties": {
                    "paper_id": {"type": "integer"},
                    "target_category_id": {"type": "integer"},
                },
            },
        },
        {
            "name": "update_paper_info",
            "description": "更新论文元数据字段。",
            "input_schema": {
                "type": "object",
                "required": ["paper_id", "fields"],
                "properties": {
                    "paper_id": {"type": "integer"},
                    "fields": {"type": "object"},
                },
            },
        },
        {
            "name": "create_category",
            "description": "创建新分类。",
            "input_schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "parent_id": {"type": "integer"},
                },
            },
        },
        {
            "name": "rename_category",
            "description": "重命名分类。",
            "input_schema": {
                "type": "object",
                "required": ["category_id", "new_name"],
                "properties": {
                    "category_id": {"type": "integer"},
                    "new_name": {"type": "string"},
                },
            },
        },
        {
            "name": "search_arxiv",
            "description": "按关键词在 arXiv 搜索论文。",
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
            },
        },
        {
            "name": "exa_search",
            "description": "使用 Exa 进行语义网络搜索。",
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
            },
        },
        {
            "name": "paper_search",
            "description": "通过 paper_search MCP（或语义学术检索回退）获取候选新论文。",
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
            },
        },
        {
            "name": "get_paper_fulltext",
            "description": "读取论文正文/缓存文本；可传 paper_ids，或用 query/title_query/author_query 先模糊检索再读取。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "paper_ids": {"type": "array", "items": {"type": "integer"}},
                    "query": {"type": "string"},
                    "title_query": {"type": "string"},
                    "author_query": {"type": "string"},
                    "max_papers": {"type": "integer"},
                    "max_chars": {"type": "integer"},
                },
            },
        },
        {
            "name": "get_system_logs",
            "description": "查询系统操作日志。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "last_n": {"type": "integer"},
                    "entity_id": {"type": "integer"},
                },
            },
        },
        {
            "name": "add_chat_pdf_to_library",
            "description": "把聊天中上传的 PDF 正式加入论文库。",
            "input_schema": {
                "type": "object",
                "required": ["attachment_id"],
                "properties": {
                    "attachment_id": {"type": "integer"},
                    "category_id": {"type": "integer"},
                },
            },
        },
    ]


def _parse_tool_arguments(raw_args: Any) -> Dict[str, Any]:
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        try:
            parsed = json.loads(raw_args)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _run_tool_call(db, user_id: int, name: str, args: Dict[str, Any]) -> Any:
    if name == "list_categories":
        return tool_list_categories(db, user_id=int(user_id))
    if name == "list_papers":
        return tool_list_papers(db, user_id=int(user_id), category_id=args.get("category_id"))
    if name == "search_local_papers":
        return tool_search_local_papers(
            db,
            user_id=int(user_id),
            query=str(args.get("query") or ""),
            title_query=str(args.get("title_query") or ""),
            author_query=str(args.get("author_query") or ""),
            max_results=int(args.get("max_results", 10)),
        )
    if name == "inspect_library_metadata":
        return tool_inspect_library_metadata(
            db,
            user_id=int(user_id),
            sample_limit=int(args.get("sample_limit", 20)),
        )
    if name == "move_paper":
        return tool_move_paper(
            db,
            user_id=int(user_id),
            paper_id=int(args.get("paper_id")),
            target_category_id=int(args.get("target_category_id")),
        )
    if name == "update_paper_info":
        return tool_update_paper_info(
            db,
            user_id=int(user_id),
            paper_id=int(args.get("paper_id")),
            fields=args.get("fields") or {},
        )
    if name == "create_category":
        return tool_create_category(
            db,
            user_id=int(user_id),
            name=str(args.get("name") or ""),
            parent_id=args.get("parent_id"),
        )
    if name == "rename_category":
        return tool_rename_category(
            db,
            user_id=int(user_id),
            category_id=int(args.get("category_id")),
            new_name=str(args.get("new_name") or ""),
        )
    if name == "search_arxiv":
        return tool_search_arxiv(
            query=str(args.get("query") or ""),
            max_results=int(args.get("max_results", 5)),
        )
    if name == "exa_search":
        return tool_exa_search(
            query=str(args.get("query") or ""),
            max_results=int(args.get("max_results", 5)),
        )
    if name == "paper_search":
        return tool_paper_search(
            query=str(args.get("query") or ""),
            max_results=int(args.get("max_results", 5)),
        )
    if name == "get_paper_fulltext":
        return tool_get_paper_fulltext(
            db,
            user_id=int(user_id),
            paper_ids=args.get("paper_ids") or [],
            query=str(args.get("query") or ""),
            title_query=str(args.get("title_query") or ""),
            author_query=str(args.get("author_query") or ""),
            max_papers=int(args.get("max_papers", 8)),
            max_chars=int(args.get("max_chars", 12000)),
        )
    if name == "get_system_logs":
        return tool_get_system_logs(
            db,
            user_id=int(user_id),
            operation=args.get("operation"),
            last_n=int(args.get("last_n", 20)),
            entity_id=args.get("entity_id"),
        )
    if name == "add_chat_pdf_to_library":
        return tool_add_chat_pdf_to_library(
            db,
            user_id=int(user_id),
            attachment_id=int(args.get("attachment_id")),
            category_id=args.get("category_id"),
        )
    raise ValueError("unknown tool")


def _build_context_from_attachments(db, user_id: int, attachment_ids: List[int]) -> Dict[str, Any]:
    if not attachment_ids:
        return {"images": [], "pdf_notes": []}

    images = []
    pdf_notes = []
    for aid in attachment_ids:
        row = db.execute(
            """
            SELECT id, type, file_path, text_cache, processed_data
            FROM chat_attachments
            WHERE id = ? AND user_id = ?
            """,
            (aid, int(user_id)),
        ).fetchone()
        if row is None:
            continue

        if row["type"] == "image":
            path = row["file_path"]
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("ascii")
                images.append(
                    {
                        "attachment_id": row["id"],
                        "base64": encoded,
                        "media_type": _guess_media_type(path, fallback="image/png"),
                    }
                )
        elif row["type"] == "pdf":
            note = (row["text_cache"] or "").strip()
            if not note and row["processed_data"]:
                try:
                    processed = json.loads(row["processed_data"])
                    if isinstance(processed, dict):
                        note = str(
                            processed.get("abstract_original")
                            or processed.get("summary_one_line")
                            or ""
                        ).strip()
                except Exception:
                    note = ""
            if note:
                pdf_notes.append({"attachment_id": row["id"], "text": note[:6000]})

    return {"images": images, "pdf_notes": pdf_notes}


def _build_context_from_papers(
    db,
    user_id: int,
    paper_ids: List[int],
    max_chars_per_paper: int = 9000,
) -> List[Dict[str, Any]]:
    if not paper_ids:
        return []

    sanitized: List[int] = []
    seen = set()
    for paper_id in paper_ids:
        try:
            parsed = int(paper_id)
        except Exception:
            continue
        if parsed <= 0 or parsed in seen:
            continue
        seen.add(parsed)
        sanitized.append(parsed)

    if not sanitized:
        return []

    return tool_get_paper_fulltext(
        db,
        user_id=int(user_id),
        paper_ids=sanitized,
        max_chars=max_chars_per_paper,
    )


def _load_conversation_history(db, conversation_id: int, user_id: int) -> List[Dict[str, Any]]:
    if not _conversation_exists(db, conversation_id, user_id=int(user_id)):
        return []
    rows = db.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (conversation_id,),
    ).fetchall()
    return [{"role": row["role"], "content": row["content"] or ""} for row in rows]


def _default_invoke_chat_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    messages = payload.get("messages") or []
    last_user = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user = str(msg.get("content") or "")
            break
    return {"content": "我已收到：{}".format(last_user[:200])}


def _convert_history_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    converted = []
    for msg in messages:
        role = str(msg.get("role") or "").strip().lower()
        text = str(msg.get("content") or "")
        if role not in {"user", "assistant", "tool"}:
            continue

        if role == "tool":
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "[TOOL RESULT:{}]\n{}".format(msg.get("name") or "tool", text),
                        }
                    ],
                }
            )
        else:
            converted.append({"role": role, "content": [{"type": "text", "text": text}]})
    return converted


def _append_images_to_last_user(messages: List[Dict[str, Any]], images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not images:
        return messages

    out = list(messages)
    user_index = None
    for idx in range(len(out) - 1, -1, -1):
        if out[idx].get("role") == "user":
            user_index = idx
            break
    if user_index is None:
        out.append({"role": "user", "content": []})
        user_index = len(out) - 1

    content = out[user_index].get("content")
    if not isinstance(content, list):
        content = [{"type": "text", "text": str(out[user_index].get("content") or "")}]

    for img in images:
        encoded = img.get("base64")
        if not isinstance(encoded, str) or not encoded.strip():
            continue
        media_type = str(img.get("media_type") or "image/png")
        content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": encoded},
            }
        )

    out[user_index]["content"] = content
    return out


def _invoke_chat_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    api_key = (os.getenv("DASHSCOPE_API_KEY", "") or "").strip()
    if not api_key:
        return _default_invoke_chat_model(payload)

    history = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    images = payload.get("images") if isinstance(payload.get("images"), list) else []
    tools = payload.get("tools") if isinstance(payload.get("tools"), list) else []

    messages = _convert_history_messages(history)
    messages = _append_images_to_last_user(messages, images)

    response = dashscope_client.call_messages(
        messages=messages,
        model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
        system_prompt=(
            "你是论文管理助手。可以使用工具完成分类管理、论文修改、日志查询、搜索与入库。"
            "当用户想按标题/作者模糊找库内论文或检查库文件健康时，应优先使用 search_local_papers、inspect_library_metadata、get_paper_fulltext。"
            "当需要调用工具时请发起 tool_use；否则直接给中文结论。"
        ),
        tools=tools,
        max_tokens=1600,
        temperature=0.2,
    )
    if not response:
        return _default_invoke_chat_model(payload)

    tool_calls = dashscope_client.extract_tool_calls(response)
    if tool_calls:
        return {"tool_calls": tool_calls}

    text = dashscope_client.extract_text(response)
    if text:
        return {"content": text}

    return _default_invoke_chat_model(payload)


def _run_chat_loop(
    db,
    user_id: int,
    history_messages: List[Dict[str, Any]],
    attachment_context: Dict[str, Any],
    max_rounds: int = 4,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    messages = list(history_messages)

    if attachment_context.get("pdf_notes"):
        appendix = []
        for item in attachment_context["pdf_notes"]:
            appendix.append("[PDF_ATTACHMENT:{}]\n{}".format(item["attachment_id"], item["text"]))
        if messages and messages[-1].get("role") == "user":
            messages[-1]["content"] = "{}\n\n{}".format(messages[-1].get("content", ""), "\n\n".join(appendix))

    payload = {
        "messages": messages,
        "tools": _tool_schemas(),
        "images": attachment_context.get("images") or [],
    }

    tool_events = []
    final_text = ""

    for _ in range(max_rounds):
        model_out = _invoke_chat_model(payload) or {}
        if not isinstance(model_out, dict):
            final_text = str(model_out)
            break

        tool_calls = model_out.get("tool_calls")
        if tool_calls and isinstance(tool_calls, list):
            for call in tool_calls:
                name = str(call.get("name") or "").strip()
                args = _parse_tool_arguments(call.get("arguments"))
                if not name:
                    continue
                start_event = {"type": "tool_call", "name": name, "status": "start"}
                if on_event is not None:
                    try:
                        on_event(start_event)
                    except Exception:
                        pass
                started_at = time.time()
                try:
                    result = _run_tool_call(db, int(user_id), name, args)
                    event = {
                        "type": "tool_call",
                        "name": name,
                        "status": "success",
                        "duration_ms": int((time.time() - started_at) * 1000),
                    }
                    log_operation(
                        db,
                        operation="agent_action",
                        entity_type="tool_call",
                        entity_id=None,
                        detail={"tool": name, "args": args, "ok": True},
                        status="success",
                        message="agent tool call success",
                        user_id=int(user_id),
                    )
                    payload["messages"].append(
                        {
                            "role": "tool",
                            "name": name,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                except Exception as exc:
                    err = "tool error: {}".format(str(exc))
                    event = {
                        "type": "tool_call",
                        "name": name,
                        "status": "error",
                        "error": err,
                        "duration_ms": int((time.time() - started_at) * 1000),
                    }
                    log_operation(
                        db,
                        operation="agent_action",
                        entity_type="tool_call",
                        entity_id=None,
                        detail={"tool": name, "args": args, "ok": False, "error": str(exc)},
                        status="error",
                        message="agent tool call failed",
                        user_id=int(user_id),
                    )
                    payload["messages"].append(
                        {
                            "role": "tool",
                            "name": name,
                            "content": json.dumps({"error": err}, ensure_ascii=False),
                        }
                    )
                tool_events.append(event)
                if on_event is not None:
                    try:
                        on_event(event)
                    except Exception:
                        pass
            continue

        final_text = str(model_out.get("content") or "").strip()
        break

    if not final_text:
        final_text = "我暂时没有生成有效回复，请重试。"

    return {"content": final_text, "tool_events": tool_events}


def _sse_event(event: Dict[str, Any]) -> str:
    return "data: {}\n\n".format(json.dumps(event, ensure_ascii=False))


@router.post("/conversations/{conversation_id}/chat")
def chat_in_conversation(
    conversation_id: int,
    payload: AgentChatRequest,
    _user=Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = int(_user["id"])
    if not _conversation_exists(db, conversation_id, user_id=user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")

    attachment_ids = payload.attachment_ids or []
    paper_ids = payload.paper_ids or []
    append_message(
        db,
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=payload.content,
        attachments=attachment_ids if attachment_ids else None,
    )

    def _event_iter():
        try:
            yield _sse_event({"type": "status", "status": "已接收问题，准备上下文..."})
            history = _load_conversation_history(db, conversation_id, user_id=user_id)
            attachment_context = _build_context_from_attachments(db, user_id=user_id, attachment_ids=attachment_ids)
            paper_context = _build_context_from_papers(db, user_id=user_id, paper_ids=paper_ids)
            if paper_ids:
                if paper_context:
                    yield _sse_event({"type": "status", "status": "已关联论文正文，正在组织上下文..."})
                else:
                    yield _sse_event({"type": "status", "status": "未找到论文正文，将按已有信息回答。"})

            if paper_context and history and history[-1].get("role") == "user":
                paper_blocks: List[str] = []
                for item in paper_context:
                    title = str(item.get("title") or "未命名论文")
                    text = str(item.get("text") or "").strip()
                    if not text:
                        continue
                    paper_blocks.append(
                        "[LIBRARY_PAPER:{}:{}]\n{}".format(
                            item.get("paper_id"),
                            title,
                            text,
                        )
                    )
                if paper_blocks:
                    history[-1]["content"] = "{}\n\n{}".format(
                        history[-1].get("content", ""),
                        "\n\n".join(paper_blocks),
                    )
            yield _sse_event({"type": "status", "status": "上下文已就绪，正在调用模型..."})

            events_queue = queue.Queue()
            worker_state: Dict[str, Any] = {"result": None, "error": None}

            def _emit_tool_event(event: Dict[str, Any]) -> None:
                events_queue.put(event)

            def _worker() -> None:
                try:
                    worker_state["result"] = _run_chat_loop(
                        db,
                        user_id,
                        history,
                        attachment_context,
                        on_event=_emit_tool_event,
                    )
                except Exception as exc:  # pragma: no cover - safety net
                    worker_state["error"] = exc
                finally:
                    events_queue.put({"type": "__worker_done__"})

            worker = threading.Thread(target=_worker, daemon=True)
            worker.start()

            emitted_tool_events = 0
            last_heartbeat_at = time.time()
            heartbeat_interval = 2.5

            while True:
                wait_timeout = max(0.2, heartbeat_interval - (time.time() - last_heartbeat_at))
                try:
                    event = events_queue.get(timeout=wait_timeout)
                except queue.Empty:
                    now = time.time()
                    if now - last_heartbeat_at >= heartbeat_interval:
                        yield _sse_event({"type": "status", "status": "模型仍在思考，请稍候..."})
                        last_heartbeat_at = now
                    continue

                if event.get("type") == "__worker_done__":
                    break

                if event.get("type") == "tool_call":
                    emitted_tool_events += 1
                yield _sse_event(event)
                last_heartbeat_at = time.time()

            worker.join()

            if worker_state["error"] is not None:
                raise worker_state["error"]

            chat_result = worker_state["result"] or {"content": "", "tool_events": []}
            assistant_text = chat_result["content"]

            if emitted_tool_events == 0:
                for event in chat_result["tool_events"]:
                    yield _sse_event(event)

            yield _sse_event({"type": "status", "status": "模型生成完成，正在整理回复..."})

            append_message(
                db,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=assistant_text,
                attachments=None,
            )

            for i in range(0, len(assistant_text), 120):
                yield _sse_event({"type": "chunk", "content": assistant_text[i : i + 120]})

            yield _sse_event({"type": "done", "content": assistant_text})
        except Exception as exc:
            yield _sse_event({"type": "error", "error": str(exc)})

    return StreamingResponse(_event_iter(), media_type="text/event-stream")
