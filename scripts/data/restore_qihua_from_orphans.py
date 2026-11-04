#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import connect_db


DB_PATH = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
PDF_DIR = Path(os.getenv("APP_PDFS_DIR", "/var/www/data/pdfs"))
TEXT_DIR = Path(os.getenv("APP_TEXTS_DIR", "/var/www/data/texts"))
RECOVERY_CATEGORY_NAME = "恢复待整理"
QIHUA_USERNAME = "其华"


def safe(value) -> str:
    return str(value or "").strip()


def has_cn(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", safe(text)))


def compact(text: str, limit: int) -> str:
    return re.sub(r"\s+", " ", safe(text)).strip()[:limit]


def parse_block(text: str, start_marker: str, next_markers: List[str], limit: int = 3200) -> str:
    source = safe(text)
    if not source:
        return ""
    idx = source.find(start_marker)
    if idx < 0:
        return ""
    tail = source[idx + len(start_marker) :]
    end = len(tail)
    for marker in next_markers:
        m = tail.find(marker)
        if m >= 0 and m < end:
            end = m
    return compact(tail[:end], limit)


def first_cn_sentence(text: str, limit: int = 220) -> str:
    src = compact(text, 5000)
    if not src:
        return ""
    parts = re.split(r"(?<=[。！？])\s*", src)
    for part in parts:
        p = safe(part)
        if p and has_cn(p):
            return p[:limit]
    return src[:limit] if has_cn(src) else ""


def normalize_title_from_filename(pdf_path: Path) -> str:
    stem = safe(pdf_path.stem)
    if not stem:
        return "Recovered Paper"
    t = stem.replace("_", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:260]


def parse_authors(text: str) -> List[str]:
    line = parse_block(text, "Authors:", ["\nTitle:", "\nCategories:", "\nSummary", "\nAbstract"], limit=400)
    if not line:
        return []
    parts = [safe(x) for x in re.split(r"[,;|/]", line) if safe(x)]
    return parts[:12]


def parse_year(title: str, text: str) -> Optional[int]:
    matches = re.findall(r"\b(19\d{2}|20\d{2})\b", "{} {}".format(safe(title), safe(text)[:2000]))
    for value in matches:
        year = int(value)
        if 1900 <= year <= 2100:
            return year
    return None


def parse_from_text_cache(text_path: Path) -> Tuple[str, str, str, List[str], Optional[int]]:
    if not text_path.exists():
        return "", "", "", [], None
    content = text_path.read_text(encoding="utf-8", errors="ignore")
    summary_zh = parse_block(
        content,
        "Summary (ZH):",
        ["\nAbstract (ZH):", "\nAbstract (Original):", "\nTitle:", "\nAuthors:", "\nCategories:"],
        limit=600,
    )
    abstract_zh = parse_block(
        content,
        "Abstract (ZH):",
        ["\nAbstract (Original):", "\nTitle:", "\nAuthors:", "\nCategories:", "\nSummary (ZH):"],
        limit=3200,
    )
    abstract_original = parse_block(
        content,
        "Abstract (Original):",
        ["\nTitle:", "\nAuthors:", "\nCategories:", "\nSummary (ZH):", "\nAbstract (ZH):"],
        limit=3200,
    )

    if not abstract_original:
        # Fallback: keep a head excerpt from cached text.
        abstract_original = compact(content, 3200)
    if has_cn(abstract_original) and not abstract_zh:
        abstract_zh = abstract_original
    if not abstract_zh and has_cn(summary_zh):
        abstract_zh = summary_zh
    if not summary_zh:
        summary_zh = first_cn_sentence(abstract_zh)
    if not summary_zh:
        summary_zh = "该论文已从历史文件恢复，请查看正文并补充摘要。"
    if not abstract_zh:
        abstract_zh = summary_zh

    authors = parse_authors(content)
    year = parse_year("", content)
    return abstract_original, abstract_zh, summary_zh, authors, year


def main() -> None:
    with connect_db(DB_PATH) as db:
        user_row = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (QIHUA_USERNAME,),
        ).fetchone()
        if user_row is None:
            raise RuntimeError("user not found: {}".format(QIHUA_USERNAME))
        user_id = int(user_row["id"])

        cat_row = db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND name = ? LIMIT 1",
            (user_id, RECOVERY_CATEGORY_NAME),
        ).fetchone()
        if cat_row is None:
            cur = db.execute(
                "INSERT INTO categories (user_id, name, parent_id, order_index) VALUES (?, ?, NULL, 0)",
                (user_id, RECOVERY_CATEGORY_NAME),
            )
            category_id = int(cur.lastrowid)
        else:
            category_id = int(cat_row["id"])

        existing = {
            safe(r["file_path"])
            for r in db.execute("SELECT file_path FROM papers WHERE file_path IS NOT NULL").fetchall()
            if safe(r["file_path"])
        }

        pdf_files = sorted([p for p in PDF_DIR.glob("*.pdf") if safe(str(p)) not in existing], key=lambda x: x.name.lower())
        total = len(pdf_files)
        ok = 0
        for idx, pdf_path in enumerate(pdf_files, start=1):
            text_path = TEXT_DIR / (pdf_path.stem + ".txt")
            title = normalize_title_from_filename(pdf_path)
            ao, az, sm, authors, parsed_year = parse_from_text_cache(text_path)
            if not ao:
                ao = "Recovered from legacy file set. Original abstract unavailable."
            if not az:
                az = "该论文由历史文件恢复，建议查看正文后补充中文摘要。"
            if not sm:
                sm = "该论文由历史文件恢复，待进一步整理。"

            cur = db.execute(
                """
                INSERT INTO papers (
                    user_id, title, authors, year, publisher, doi,
                    abstract_original, abstract_zh, summary_one_line,
                    category_id, file_path, text_cache_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    title,
                    json.dumps(authors or [], ensure_ascii=False),
                    parsed_year,
                    "",
                    "",
                    compact(ao, 3200),
                    compact(az, 3200),
                    compact(sm, 600),
                    category_id,
                    str(pdf_path),
                    str(text_path) if text_path.exists() else None,
                ),
            )
            paper_id = int(cur.lastrowid)
            db.execute(
                "INSERT OR IGNORE INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
                (paper_id, category_id),
            )
            db.execute(
                """
                INSERT INTO processing_jobs (user_id, paper_id, status, error_msg)
                VALUES (?, ?, 'done', ?)
                """,
                (user_id, paper_id, "restored from orphan files"),
            )
            ok += 1
            if idx % 10 == 0 or idx == total:
                print("[{}/{}] restored {}".format(idx, total, pdf_path.name), flush=True)

        db.commit()
        print(
            "[DONE] total_orphans={} restored={} user_id={} category_id={}".format(
                total, ok, user_id, category_id
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
