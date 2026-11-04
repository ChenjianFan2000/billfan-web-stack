#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
from typing import Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db, init_db


KEEP_JOB_ID_START = 53
KEEP_JOB_ID_END = 134


def load_env_file(path: str) -> None:
    target = Path(path)
    if not target.exists():
        return
    for raw in target.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


def contains_cn(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _safe(text) -> str:
    return str(text or "").strip()


def _read_text(path: str) -> str:
    p = _safe(path)
    if not p or not os.path.exists(p):
        return ""
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(200000)
    except Exception:
        return ""


def _normalize_abstract(text: str) -> str:
    extracted = pipeline._extract_abstract(text)
    normalized = pipeline._normalize_extracted_text(extracted)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:3200]


def _first_cn_sentence(text: str, limit: int = 220) -> str:
    src = _safe(text)
    if not src:
        return ""
    parts = re.split(r"(?<=[。！？])\s*", src)
    for part in parts:
        p = part.strip()
        if contains_cn(p):
            return p[:limit]
    return src[:limit] if contains_cn(src) else ""


def _llm_translate_and_summarize(title: str, abstract_en: str, category: str) -> Tuple[str, str]:
    prompt = (
        "你将收到论文标题、英文摘要和分类。请只输出JSON："
        '{"abstract_zh":"...","summary_zh":"..."}。'
        "要求：abstract_zh为准确中文翻译；summary_zh为2-4句中文总结，包含研究对象、方法、主要结论。"
        "禁止输出JSON以外内容。"
    )
    payload = {
        "title": _safe(title),
        "category": _safe(category),
        "abstract_en": _safe(abstract_en),
    }
    msg = [pipeline._to_anthropic_message("user", prompt + "\n\n" + json.dumps(payload, ensure_ascii=False))]
    raw = _safe(
        pipeline._call_qwen_text(
            messages=msg,
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt="你是金融数学论文中文化助手。",
            max_tokens=1400,
            temperature=0.1,
            timeout=22,
            retries=1,
        )
    )
    blob = pipeline._extract_json_blob(raw)
    if not blob:
        return "", ""
    try:
        data = json.loads(blob)
    except Exception:
        return "", ""
    if not isinstance(data, dict):
        return "", ""

    abstract_zh = _safe(data.get("abstract_zh"))[:3200]
    summary_zh = _safe(data.get("summary_zh"))[:600]
    if not contains_cn(abstract_zh):
        abstract_zh = ""
    if not contains_cn(summary_zh):
        summary_zh = ""
    return abstract_zh, summary_zh


def _category_name(db, paper_id: int) -> str:
    row = db.execute(
        """
        SELECT c.name
        FROM papers p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.id = ?
        """,
        (paper_id,),
    ).fetchone()
    return _safe(row["name"]) if row else ""


def main() -> None:
    load_env_file("/etc/qh-paper-assistant/app.env")
    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
    init_db(db_path)

    with connect_db(db_path) as db:
        keep_ids: Set[int] = {
            int(r["paper_id"])
            for r in db.execute(
                """
                SELECT DISTINCT paper_id
                FROM processing_jobs
                WHERE id BETWEEN ? AND ?
                  AND paper_id IS NOT NULL
                """,
                (KEEP_JOB_ID_START, KEEP_JOB_ID_END),
            ).fetchall()
        }
        if not keep_ids:
            raise RuntimeError("No imported paper ids found")

        keep_sorted = sorted(keep_ids)
        keep_placeholders = ",".join(["?"] * len(keep_sorted))

        remove_ids = [
            int(r["id"])
            for r in db.execute(
                f"SELECT id FROM papers WHERE id NOT IN ({keep_placeholders})",
                tuple(keep_sorted),
            ).fetchall()
        ]
        if remove_ids:
            ph = ",".join(["?"] * len(remove_ids))
            db.execute(f"DELETE FROM processing_jobs WHERE paper_id IN ({ph})", tuple(remove_ids))
            db.execute(f"DELETE FROM papers WHERE id IN ({ph})", tuple(remove_ids))
            db.commit()
            print(f"[CLEAN] removed non-zip papers: {len(remove_ids)}", flush=True)

        db.execute(
            """
            UPDATE processing_jobs
            SET status='error', error_msg='stale processing job marked during repair', updated_at=CURRENT_TIMESTAMP
            WHERE status='processing'
            """
        )
        db.commit()

        rows = db.execute(
            f"""
            SELECT id, title, file_path, text_cache_path, abstract_original, abstract_zh, summary_one_line
            FROM papers
            WHERE id IN ({keep_placeholders})
            ORDER BY id ASC
            """,
            tuple(keep_sorted),
        ).fetchall()

        ok = 0
        fail = 0
        skip = 0

        for idx, row in enumerate(rows, start=1):
            paper_id = int(row["id"])
            title = _safe(row["title"])
            existing_zh = _safe(row["abstract_zh"])
            existing_sum = _safe(row["summary_one_line"])
            if contains_cn(existing_zh) and contains_cn(existing_sum) and len(existing_sum) <= 600:
                skip += 1
                print(f"[SKIP {idx}/{len(rows)}] paper_id={paper_id} already-chinese", flush=True)
                continue

            text = _read_text(_safe(row["text_cache_path"]))
            if not text:
                text = _safe(row["abstract_original"])
            if not text and _safe(row["file_path"]):
                try:
                    text = _safe(pipeline.extract_text_best_effort(_safe(row["file_path"]))["text"])
                except Exception:
                    text = ""

            if not text:
                fail += 1
                print(f"[ERR {idx}/{len(rows)}] paper_id={paper_id} no text", flush=True)
                continue

            try:
                abstract_en = _normalize_abstract(text)
                if not abstract_en:
                    abstract_en = _safe(row["abstract_original"])[:3200]

                category_name = _category_name(db, paper_id)
                abstract_zh, summary_zh = _llm_translate_and_summarize(title, abstract_en, category_name)

                if not summary_zh:
                    summary_zh = _first_cn_sentence(abstract_zh)
                if not summary_zh:
                    summary_zh = _safe(pipeline._fallback_summary_zh(abstract_zh, abstract_en, title))[:600]
                if not abstract_zh:
                    abstract_zh = summary_zh

                db.execute(
                    """
                    UPDATE papers
                    SET abstract_original = ?,
                        abstract_zh = ?,
                        summary_one_line = ?
                    WHERE id = ?
                    """,
                    (abstract_en, abstract_zh[:3200], summary_zh[:600], paper_id),
                )
                db.commit()
                ok += 1
                print(f"[OK {idx}/{len(rows)}] paper_id={paper_id}", flush=True)
            except Exception as exc:
                db.rollback()
                fail += 1
                print(f"[ERR {idx}/{len(rows)}] paper_id={paper_id} error={exc}", flush=True)

        check = db.execute(
            f"SELECT abstract_zh, summary_one_line FROM papers WHERE id IN ({keep_placeholders})",
            tuple(keep_sorted),
        ).fetchall()
        zh_abs = sum(1 for r in check if contains_cn(_safe(r["abstract_zh"])))
        zh_sum = sum(1 for r in check if contains_cn(_safe(r["summary_one_line"])))
        print(
            f"[DONE] papers={len(check)} ok={ok} skip={skip} fail={fail} zh_abstract={zh_abs} zh_summary={zh_sum}",
            flush=True,
        )


if __name__ == "__main__":
    main()
