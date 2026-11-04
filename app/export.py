import io
import json
import os
import re
import textwrap
import uuid
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.auth import get_current_user
from app.db import get_db
from app.logger import log_operation
from app.paper_categories import fetch_paper_category_ids_map

router = APIRouter(prefix="/api/export", tags=["export"])

_DEFAULT_EXPORT_DIR = os.getenv("EXPORTS_DIR", "/var/www/data/exports")
_UNCATEGORIZED_NAME = "未分类"


class ExportPdfsRequest(BaseModel):
    category_ids: Optional[List[int]] = None


class ExportTextsRequest(BaseModel):
    category_ids: Optional[List[int]] = None


class ExportReferencesRequest(BaseModel):
    format: str = "apa"
    output: str = "text"
    category_ids: Optional[List[int]] = None


def _ensure_export_dir() -> str:
    os.makedirs(_DEFAULT_EXPORT_DIR, exist_ok=True)
    return _DEFAULT_EXPORT_DIR


def _sanitize_name(name: str, fallback: str) -> str:
    value = (name or "").strip()
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        value = fallback
    return value[:120]


def _build_file_name(prefix: str, ext: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    token = uuid.uuid4().hex[:8]
    return "{}_{}_{}.{}".format(prefix, ts, token, ext)


def _fetch_papers(db, category_ids: Optional[Sequence[int]], user_id: int) -> List[Dict[str, Any]]:
    params: List[Any] = []
    where = "WHERE p.user_id = ? AND COALESCE(p.is_quarantined, 0) = 0"
    params.append(int(user_id))

    if category_ids:
        normalized_category_ids = [int(cid) for cid in category_ids]
        placeholders = ",".join(["?"] * len(normalized_category_ids))
        where += """
        AND (
            EXISTS (
            SELECT 1 FROM paper_categories pc
            JOIN categories c0 ON c0.id = pc.category_id
            WHERE pc.paper_id = p.id
              AND c0.user_id = ?
              AND pc.category_id IN ({ph})
        ) OR (
            p.category_id IN ({ph})
            AND EXISTS (SELECT 1 FROM categories c1 WHERE c1.id = p.category_id AND c1.user_id = ?)
            AND NOT EXISTS (SELECT 1 FROM paper_categories pc2 WHERE pc2.paper_id = p.id)
        ))
        """.format(ph=placeholders)
        params.append(int(user_id))
        params.extend(normalized_category_ids)
        params.extend(normalized_category_ids)
        params.append(int(user_id))

    rows = db.execute(
        """
        SELECT
            p.id,
            p.title,
            p.authors,
            p.year,
            p.publisher,
            p.doi,
            p.file_path,
            p.category_id
        FROM papers p
        {}
        ORDER BY p.id ASC
        """.format(where),
        tuple(params),
    ).fetchall()

    paper_ids = [int(row["id"]) for row in rows]
    paper_category_map = fetch_paper_category_ids_map(db, paper_ids, user_id=user_id)
    all_category_ids = sorted(
        {
            int(cid)
            for paper_category_ids in paper_category_map.values()
            for cid in paper_category_ids
        }
    )
    all_category_ids.extend(
        [
            int(row["category_id"])
            for row in rows
            if row["category_id"] is not None and int(row["category_id"]) not in all_category_ids
        ]
    )
    if all_category_ids:
        c_placeholders = ",".join(["?"] * len(all_category_ids))
        category_rows = db.execute(
            "SELECT id, name FROM categories WHERE user_id = ? AND id IN ({})".format(c_placeholders),
            tuple([int(user_id)] + all_category_ids),
        ).fetchall()
    else:
        category_rows = []
    category_name_map = {int(row["id"]): row["name"] for row in category_rows}

    result = []
    for row in rows:
        authors: List[str] = []
        if row["authors"]:
            try:
                parsed = json.loads(row["authors"])
                if isinstance(parsed, list):
                    authors = [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                authors = []

        paper_categories = paper_category_map.get(int(row["id"]), [])
        primary_category_id = paper_categories[0] if paper_categories else row["category_id"]
        category_name = category_name_map.get(int(primary_category_id), _UNCATEGORIZED_NAME) if primary_category_id is not None else _UNCATEGORIZED_NAME

        result.append(
            {
                "id": row["id"],
                "title": row["title"] or "",
                "authors": authors,
                "year": row["year"],
                "publisher": row["publisher"] or "",
                "doi": row["doi"] or "",
                "file_path": row["file_path"] or "",
                "category_name": category_name,
                "category_ids": paper_categories,
            }
        )
    return result


def _unique_arc_name(base_dir: str, base_name: str, used: set) -> str:
    stem, ext = os.path.splitext(base_name)
    candidate = os.path.join(base_dir, base_name)
    i = 1
    while candidate in used:
        candidate = os.path.join(base_dir, "{}_{}{}".format(stem, i, ext))
        i += 1
    used.add(candidate)
    return candidate


def _build_text_payload_for_paper(db, paper: Dict[str, Any]) -> str:
    paper_id = int(paper["id"])
    row = db.execute(
        """
        SELECT text_cache_path, abstract_original, abstract_zh, summary_one_line
        FROM papers
        WHERE id = ?
        """,
        (paper_id,),
    ).fetchone()
    if row is None:
        return ""

    text_cache_path = str(row["text_cache_path"] or "").strip()
    if text_cache_path and os.path.exists(text_cache_path):
        try:
            with open(text_cache_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
            if text:
                return text
        except Exception:
            pass

    parts: List[str] = []
    title = str(paper.get("title") or "").strip()
    if title:
        parts.append("Title: {}".format(title))
    authors = paper.get("authors") or []
    if isinstance(authors, list) and authors:
        parts.append("Authors: {}".format(", ".join([str(a).strip() for a in authors if str(a).strip()])))
    if paper.get("year"):
        parts.append("Year: {}".format(paper["year"]))
    if paper.get("publisher"):
        parts.append("Publisher: {}".format(str(paper["publisher"]).strip()))
    if paper.get("doi"):
        parts.append("DOI: {}".format(str(paper["doi"]).strip()))
    if paper.get("category_name"):
        parts.append("Category: {}".format(str(paper["category_name"]).strip()))

    summary = str(row["summary_one_line"] or "").strip()
    abstract_zh = str(row["abstract_zh"] or "").strip()
    abstract_original = str(row["abstract_original"] or "").strip()
    if summary:
        parts.append("")
        parts.append("Summary (ZH):")
        parts.append(summary)
    if abstract_zh:
        parts.append("")
        parts.append("Abstract (ZH):")
        parts.append(abstract_zh)
    if abstract_original:
        parts.append("")
        parts.append("Abstract (Original):")
        parts.append(abstract_original)
    return "\n".join(parts).strip()


def _format_apa_line(paper: Dict[str, Any]) -> str:
    authors = ", ".join(paper["authors"]) if paper["authors"] else "Unknown author"
    year = str(paper["year"]) if paper["year"] else "n.d."
    title = paper["title"] or "Untitled"
    publisher = paper["publisher"]
    doi = paper["doi"]

    line = "{} ({}). {}.".format(authors, year, title)
    if publisher:
        line += " {}.".format(publisher)
    if doi:
        if doi.startswith("http://") or doi.startswith("https://"):
            line += " {}".format(doi)
        else:
            line += " https://doi.org/{}".format(doi)
    return line.strip()


def _format_bibtex_entry(paper: Dict[str, Any]) -> str:
    key = "paper{}".format(paper["id"])
    title = (paper["title"] or "Untitled").replace("{", "\\{").replace("}", "\\}")
    author = " and ".join(paper["authors"]) if paper["authors"] else "Unknown"
    year = str(paper["year"] or "")
    journal = (paper["publisher"] or "").replace("{", "\\{").replace("}", "\\}")
    doi = paper["doi"] or ""

    lines = [
        "@article{{{},".format(key),
        "  title={{ {} }},".format(title),
        "  author={{ {} }},".format(author),
        "  year={{ {} }},".format(year),
        "  journal={{ {} }},".format(journal),
        "  doi={{ {} }}".format(doi),
        "}",
    ]
    return "\n".join(lines)


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_text_pdf(content: str) -> bytes:
    wrapped_lines: List[str] = []
    for src in (content or "").splitlines() or [""]:
        chunks = textwrap.wrap(src, width=90) or [""]
        wrapped_lines.extend(chunks)

    stream_lines = ["BT", "/F1 10 Tf", "72 800 Td"]
    for line in wrapped_lines[:120]:
        stream_lines.append("({}) Tj".format(_escape_pdf_text(line)))
        stream_lines.append("0 -12 Td")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects: List[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        b"",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    objects[3] = (
        b"4 0 obj\n<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream\nendobj\n"
    )

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = [0]
    for obj in objects:
        offsets.append(out.tell())
        out.write(obj)

    xref_pos = out.tell()
    out.write("xref\n0 {}\n".format(len(objects) + 1).encode("ascii"))
    out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.write("{:010d} 00000 n \n".format(off).encode("ascii"))

    out.write("trailer\n<< /Size {} /Root 1 0 R >>\n".format(len(objects) + 1).encode("ascii"))
    out.write("startxref\n{}\n%%EOF\n".format(xref_pos).encode("ascii"))
    return out.getvalue()


@router.post("/pdfs", status_code=status.HTTP_201_CREATED)
def export_pdfs(payload: ExportPdfsRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    papers = _fetch_papers(db, payload.category_ids, user_id=int(_user["id"]))

    export_dir = _ensure_export_dir()
    filename = _build_file_name("papers", "zip")
    export_path = os.path.join(export_dir, filename)

    added = 0
    used_names = set()
    with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for paper in papers:
            file_path = paper["file_path"]
            if not file_path or not os.path.exists(file_path):
                continue

            category_name = _sanitize_name(paper["category_name"], _UNCATEGORIZED_NAME)
            paper_name = _sanitize_name(paper["title"], "paper_{}".format(paper["id"]))
            arc_name = _unique_arc_name(category_name, paper_name + ".pdf", used_names)
            zf.write(file_path, arc_name)
            added += 1

    log_operation(
        db,
        operation="export",
        entity_type="export_job",
        entity_id=None,
        detail={
            "kind": "pdfs",
            "category_ids": payload.category_ids or [],
            "count": added,
            "file": filename,
        },
        status="success",
        message="exported pdf archive",
        user_id=int(_user["id"]),
    )

    return {
        "download_url": "/api/export/downloads/{}".format(filename),
        "file_path": export_path,
        "count": added,
    }


@router.post("/texts", status_code=status.HTTP_201_CREATED)
def export_texts(payload: ExportTextsRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    papers = _fetch_papers(db, payload.category_ids, user_id=int(_user["id"]))

    export_dir = _ensure_export_dir()
    filename = _build_file_name("texts", "zip")
    export_path = os.path.join(export_dir, filename)

    added = 0
    used_names = set()
    with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for paper in papers:
            payload_text = _build_text_payload_for_paper(db, paper)
            if not payload_text:
                continue

            category_name = _sanitize_name(paper["category_name"], _UNCATEGORIZED_NAME)
            paper_name = _sanitize_name(paper["title"], "paper_{}".format(paper["id"]))
            arc_name = _unique_arc_name(category_name, paper_name + ".txt", used_names)
            zf.writestr(arc_name, payload_text.encode("utf-8", errors="ignore"))
            added += 1

    log_operation(
        db,
        operation="export",
        entity_type="export_job",
        entity_id=None,
        detail={
            "kind": "texts",
            "category_ids": payload.category_ids or [],
            "count": added,
            "file": filename,
        },
        status="success",
        message="exported text archive",
        user_id=int(_user["id"]),
    )

    return {
        "download_url": "/api/export/downloads/{}".format(filename),
        "file_path": export_path,
        "count": added,
    }


@router.post("/references")
def export_references(payload: ExportReferencesRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    fmt = (payload.format or "").strip().lower()
    output = (payload.output or "text").strip().lower()
    if fmt not in {"apa", "bibtex"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid format")
    if output not in {"text", "pdf"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid output")

    papers = _fetch_papers(db, payload.category_ids, user_id=int(_user["id"]))

    if fmt == "apa":
        lines = [_format_apa_line(p) for p in papers]
        text = "\n".join(lines)
    else:
        entries = [_format_bibtex_entry(p) for p in papers]
        text = "\n\n".join(entries)

    detail = {
        "kind": "references",
        "format": fmt,
        "output": output,
        "category_ids": payload.category_ids or [],
        "count": len(papers),
    }

    if output == "text":
        log_operation(
            db,
            operation="export",
            entity_type="export_job",
            entity_id=None,
            detail=detail,
            status="success",
            message="exported reference text",
            user_id=int(_user["id"]),
        )
        return {"format": fmt, "output": "text", "content": text}

    export_dir = _ensure_export_dir()
    filename = _build_file_name("references", "pdf")
    export_path = os.path.join(export_dir, filename)
    pdf_bytes = _build_simple_text_pdf(text)

    with open(export_path, "wb") as f:
        f.write(pdf_bytes)

    detail["file"] = filename
    log_operation(
        db,
        operation="export",
        entity_type="export_job",
        entity_id=None,
        detail=detail,
        status="success",
        message="exported reference pdf",
        user_id=int(_user["id"]),
    )

    return {
        "format": fmt,
        "output": "pdf",
        "download_url": "/api/export/downloads/{}".format(filename),
        "file_path": export_path,
    }


@router.get("/downloads/{filename}")
def download_export_file(filename: str, _user=Depends(get_current_user)):
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid filename")

    path = os.path.join(_ensure_export_dir(), safe_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")

    return FileResponse(path, filename=safe_name)
