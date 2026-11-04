#!/usr/bin/env python3
import argparse
import signal
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db, init_db
from app.settings_store import CLASSIFICATION_GUIDANCE_KEY, ensure_default_settings, upsert_setting_value

TARGET_CATEGORIES = [
    "价值共创理论（核心理论库）",
    "文博出版与博物馆研究（核心领域库）",
    "出版业变革研究（行业背景库）",
    "众筹、平台与社群经济（实证支撑库）",
    "中国文化政策与产业情境（本土化背景库）",
]
RECOVERY_CATEGORY_NAME = "恢复待整理"
DEFAULT_USERNAME = "其华"

GUIDANCE = (
    "请仅在以下五类中推荐1-3个分类，可多选："
    "价值共创理论（核心理论库）、文博出版与博物馆研究（核心领域库）、"
    "出版业变革研究（行业背景库）、众筹、平台与社群经济（实证支撑库）、"
    "中国文化政策与产业情境（本土化背景库）。"
    "优先根据论文研究问题、方法与语境综合判断；若同时具备理论与应用价值，应同时标注多个分类。"
)


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def _read_text(path_value: object) -> str:
    path = _safe_text(path_value)
    if not path:
        return ""
    try:
        p = Path(path)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return ""


@contextmanager
def _time_limit(seconds: int):
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(_signum, _frame):
        raise TimeoutError("llm timeout")

    prev_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(int(seconds))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prev_handler)


def _upsert_target_categories(db, user_id: int, names: List[str]) -> List[int]:
    category_ids: List[int] = []
    for idx, name in enumerate(names):
        row = db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND name = ? ORDER BY id ASC LIMIT 1",
            (int(user_id), name),
        ).fetchone()
        if row is None:
            cur = db.execute(
                "INSERT INTO categories (user_id, name, parent_id, order_index) VALUES (?, ?, NULL, ?)",
                (int(user_id), name, int(idx)),
            )
            category_ids.append(int(cur.lastrowid))
            continue
        cat_id = int(row["id"])
        db.execute(
            "UPDATE categories SET parent_id = NULL, order_index = ? WHERE id = ? AND user_id = ?",
            (int(idx), cat_id, int(user_id)),
        )
        category_ids.append(cat_id)
    return category_ids


def _normalize_filename_hints(hints: Dict[str, object], filename_hints: Dict[str, object]) -> Dict[str, object]:
    merged = dict(hints or {})
    filename_title = _safe_text(filename_hints.get("title"))
    if filename_title:
        merged["_filename_title"] = filename_title
    for key, value in (filename_hints or {}).items():
        if key == "authors":
            if not merged.get("authors"):
                merged["authors"] = value
        elif key == "title":
            current_title = _safe_text(merged.get("title"))
            if (not current_title) or pipeline._looks_like_bad_title(current_title):
                merged["title"] = value
        elif not merged.get(key):
            merged[key] = value
    return merged


def _ensure_text_for_classification(pdf_path: str, text_cache_path: str) -> Tuple[str, Optional[str]]:
    cached = _read_text(text_cache_path)
    if cached:
        return cached, _safe_text(text_cache_path) or None

    pdf = _safe_text(pdf_path)
    if not pdf:
        return "", None

    extracted = pipeline.extract_text_best_effort(pdf)
    text = _safe_text(extracted.get("text"))
    if not text:
        return "", None

    texts_dir = Path(os.getenv("APP_TEXTS_DIR", "/var/www/data/texts"))
    texts_dir.mkdir(parents=True, exist_ok=True)
    out_path = texts_dir / (Path(pdf).stem + ".txt")
    out_path.write_text(text, encoding="utf-8")
    return text, str(out_path)


def _reclassify_one_paper(
    db,
    user_id: int,
    paper_row,
    categories: List[str],
    guidance: str,
    use_llm: bool,
    llm_timeout_seconds: int,
) -> Tuple[bool, str]:
    paper_id = int(paper_row["id"])
    title = _safe_text(paper_row["title"])
    pdf_path = _safe_text(paper_row["file_path"])
    text_cache_path = _safe_text(paper_row["text_cache_path"])

    hints: Dict[str, object] = {}
    if pdf_path:
        try:
            hints = pipeline.extract_pdf_metadata_hints(pdf_path)
        except Exception:
            hints = {}
        try:
            filename_hints = pipeline.extract_filename_hints(pdf_path)
        except Exception:
            filename_hints = {}
        hints = _normalize_filename_hints(hints, filename_hints)
    hints["_classification_guidance"] = guidance

    text, resolved_text_cache_path = _ensure_text_for_classification(pdf_path, text_cache_path)
    if not text:
        text = title

    cur = db.execute(
        "INSERT INTO processing_jobs (user_id, paper_id, status, error_msg) VALUES (?, ?, ?, ?)",
        (int(user_id), int(paper_id), "processing", "qihua reclassification"),
    )
    job_id = int(cur.lastrowid)
    db.commit()

    try:
        llm_callable = pipeline.default_llm_callable if use_llm else None
        try:
            with _time_limit(int(llm_timeout_seconds)):
                result = pipeline.llm_extract_metadata(text=text, hints=hints, categories=categories, llm_callable=llm_callable)
        except Exception:
            result = pipeline.llm_extract_metadata(text=text, hints=hints, categories=categories, llm_callable=None)

        rec = result.get("recommended_categories")
        if not isinstance(rec, list) or not rec:
            result["recommended_categories"] = [categories[0]]
            result["recommended_category"] = categories[0]

        pipeline.write_pipeline_result(
            db=db,
            paper_id=paper_id,
            job_id=job_id,
            result_dict=result,
            user_id=int(user_id),
            text_cache_path=resolved_text_cache_path or text_cache_path or None,
            pdf_path=pdf_path or None,
        )
        return True, ""
    except Exception as exc:
        db.execute(
            "UPDATE processing_jobs SET status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            ("error", str(exc), int(job_id), int(user_id)),
        )
        db.commit()
        return False, str(exc)


def _cleanup_categories(db, user_id: int, keep_category_ids: List[int]) -> None:
    placeholders = ",".join(["?"] * len(keep_category_ids))
    args = [int(user_id)] + [int(item) for item in keep_category_ids]
    rows = db.execute(
        f"SELECT id FROM categories WHERE user_id = ? AND id NOT IN ({placeholders})",
        tuple(args),
    ).fetchall()
    remove_ids = [int(row["id"]) for row in rows]
    if remove_ids:
        p2 = ",".join(["?"] * len(remove_ids))
        db.execute(
            f"DELETE FROM paper_categories WHERE category_id IN ({p2})",
            tuple(remove_ids),
        )
        db.execute(
            f"UPDATE papers SET category_id = NULL WHERE user_id = ? AND category_id IN ({p2})",
            tuple([int(user_id)] + remove_ids),
        )
        db.execute(
            f"DELETE FROM categories WHERE user_id = ? AND id IN ({p2})",
            tuple([int(user_id)] + remove_ids),
        )

    default_category_id = int(keep_category_ids[0])
    no_cat_rows = db.execute(
        """
        SELECT p.id
        FROM papers p
        WHERE p.user_id = ?
          AND NOT EXISTS (SELECT 1 FROM paper_categories pc WHERE pc.paper_id = p.id)
        ORDER BY p.id ASC
        """,
        (int(user_id),),
    ).fetchall()
    for row in no_cat_rows:
        paper_id = int(row["id"])
        db.execute(
            "INSERT OR IGNORE INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
            (paper_id, default_category_id),
        )
        db.execute(
            "UPDATE papers SET category_id = ? WHERE id = ? AND user_id = ?",
            (default_category_id, paper_id, int(user_id)),
        )

    db.execute(
        """
        UPDATE papers
        SET category_id = (
            SELECT pc.category_id
            FROM paper_categories pc
            JOIN categories c ON c.id = pc.category_id
            WHERE pc.paper_id = papers.id AND c.user_id = ?
            ORDER BY pc.rowid ASC
            LIMIT 1
        )
        WHERE user_id = ?
        """,
        (int(user_id), int(user_id)),
    )
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reclassify Qihua papers into new categories using standard pipeline classification.")
    parser.add_argument("--db-path", default=os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite"))
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--limit", type=int, default=0, help="Optional: only process first N papers (0 = all)")
    parser.add_argument("--min-paper-id", type=int, default=0, help="Optional: only process papers with id >= this value")
    parser.add_argument("--only-unfinished", action="store_true", help="Only process papers still linked to 恢复待整理")
    parser.add_argument("--llm-timeout", type=int, default=180, help="Per-paper LLM timeout in seconds before fallback")
    args = parser.parse_args()

    init_db(args.db_path)
    use_llm = bool(_safe_text(os.getenv("DASHSCOPE_API_KEY", "")))
    processed = 0
    success = 0
    failed = 0

    with connect_db(args.db_path) as db:
        user_row = db.execute("SELECT id FROM users WHERE username = ?", (_safe_text(args.username),)).fetchone()
        if user_row is None:
            raise RuntimeError(f"user not found: {args.username}")
        user_id = int(user_row["id"])

        ensure_default_settings(db, user_id=user_id)
        upsert_setting_value(db, CLASSIFICATION_GUIDANCE_KEY, GUIDANCE, user_id=user_id)
        target_category_ids = _upsert_target_categories(db, user_id=user_id, names=TARGET_CATEGORIES)
        db.execute(
            """
            UPDATE processing_jobs
            SET status = 'error', error_msg = 'interrupted reclassification'
            WHERE user_id = ? AND status = 'processing' AND error_msg = 'qihua reclassification'
            """,
            (int(user_id),),
        )
        db.commit()

        recovery_row = db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND name = ? ORDER BY id ASC LIMIT 1",
            (int(user_id), RECOVERY_CATEGORY_NAME),
        ).fetchone()
        recovery_id = int(recovery_row["id"]) if recovery_row is not None else None

        where_parts = ["p.user_id = ?"]
        params: List[object] = [int(user_id)]
        if int(args.min_paper_id) > 0:
            where_parts.append("p.id >= ?")
            params.append(int(args.min_paper_id))
        if bool(args.only_unfinished) and recovery_id is not None:
            where_parts.append(
                """
                (
                    p.category_id = ?
                    OR EXISTS (
                        SELECT 1 FROM paper_categories pc
                        WHERE pc.paper_id = p.id AND pc.category_id = ?
                    )
                )
                """
            )
            params.extend([int(recovery_id), int(recovery_id)])

        papers = db.execute(
            f"""
            SELECT p.id, p.title, p.file_path, p.text_cache_path
            FROM papers p
            WHERE {' AND '.join(where_parts)}
            ORDER BY p.id ASC
            """,
            tuple(params),
        ).fetchall()
        if args.limit > 0:
            papers = papers[: int(args.limit)]

        total = len(papers)
        print(f"[INFO] user={args.username} user_id={user_id} papers={total} llm={'on' if use_llm else 'off'}", flush=True)
        for idx, row in enumerate(papers, start=1):
            ok, err = _reclassify_one_paper(
                db=db,
                user_id=user_id,
                paper_row=row,
                categories=TARGET_CATEGORIES,
                guidance=GUIDANCE,
                use_llm=use_llm,
                llm_timeout_seconds=int(args.llm_timeout),
            )
            processed += 1
            if ok:
                success += 1
                print(f"[{idx}/{total}] OK paper_id={int(row['id'])}", flush=True)
            else:
                failed += 1
                print(f"[{idx}/{total}] ERR paper_id={int(row['id'])} err={err}", flush=True)

        _cleanup_categories(db, user_id=user_id, keep_category_ids=target_category_ids)

        summary_rows = db.execute(
            """
            SELECT c.name, COUNT(*) AS cnt
            FROM paper_categories pc
            JOIN papers p ON p.id = pc.paper_id
            JOIN categories c ON c.id = pc.category_id
            WHERE p.user_id = ? AND c.user_id = ?
            GROUP BY c.id, c.name
            ORDER BY c.order_index ASC, c.id ASC
            """,
            (int(user_id), int(user_id)),
        ).fetchall()
        print("[SUMMARY] category counts:", flush=True)
        for item in summary_rows:
            print(f"  - {item['name']}: {int(item['cnt'])}", flush=True)

        recovery = db.execute(
            "SELECT COUNT(*) AS cnt FROM categories WHERE user_id = ? AND name = ?",
            (int(user_id), RECOVERY_CATEGORY_NAME),
        ).fetchone()
        print(
            f"[DONE] processed={processed} success={success} failed={failed} recovery_category_remaining={int(recovery['cnt'])}",
            flush=True,
        )


if __name__ == "__main__":
    main()
