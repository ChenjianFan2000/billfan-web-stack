#!/usr/bin/env python3
import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db
from app.settings_store import (
    CLASSIFICATION_GUIDANCE_KEY,
    DEFAULT_CLASSIFICATION_GUIDANCE,
    get_setting_value,
)


def safe(value: Any) -> str:
    return str(value or "").strip()


def load_env(path: str = "/etc/qh-paper-assistant/app.env") -> None:
    target = Path(path)
    if not target.exists():
        return
    for raw in target.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


def read_text(path: str, max_chars: int = 220000) -> str:
    target = safe(path)
    if not target:
        return ""
    p = Path(target)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


def needs_repair(row: Dict[str, Any]) -> bool:
    title = safe(row["title"])
    abs_en = safe(row["abstract_original"])
    abs_zh = safe(row["abstract_zh"])
    summary = safe(row["summary_one_line"])
    if pipeline._looks_bad_abstract_original(abs_en, title):
        return True
    if not pipeline._valid_abstract_zh_text(abs_zh):
        return True
    if not pipeline._valid_summary_zh_text(summary):
        return True
    return False


def build_hints(row: Dict[str, Any], classification_guidance: str) -> Dict[str, Any]:
    hints: Dict[str, Any] = {
        "title": safe(row["title"]),
        "_classification_guidance": safe(classification_guidance),
    }
    try:
        authors = row["authors"]
        if isinstance(authors, str) and authors.strip().startswith("["):
            import json

            parsed = json.loads(authors)
            if isinstance(parsed, list) and parsed:
                hints["authors"] = [safe(x) for x in parsed if safe(x)]
    except Exception:
        pass
    year_raw = row["year"]
    if isinstance(year_raw, int):
        hints["year"] = year_raw
    return hints


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair abstract/translation/summary by re-running main pipeline LLM flow.")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--paper-ids", type=str, default="")
    args = parser.parse_args()

    load_env()
    if not safe(os.getenv("DASHSCOPE_API_KEY", "")):
        raise RuntimeError("DASHSCOPE_API_KEY not configured")

    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
    user_id = int(args.user_id)
    selected_ids = {int(x) for x in re.findall(r"\d+", safe(args.paper_ids))}
    max_attempts = max(1, int(args.max_attempts))

    with connect_db(db_path) as db:
        rows = db.execute(
            """
            SELECT id, user_id, title, authors, year, abstract_original, abstract_zh, summary_one_line, text_cache_path
            FROM papers
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_id,),
        ).fetchall()

        targets = [row for row in rows if needs_repair(row)]
        if selected_ids:
            targets = [row for row in targets if int(row["id"]) in selected_ids]
        if int(args.limit) > 0:
            targets = targets[: int(args.limit)]

        # Repair task only needs abstract extraction/translation/summary; skip category LLM calls for stability.
        categories: List[str] = []
        guidance = get_setting_value(
            db,
            CLASSIFICATION_GUIDANCE_KEY,
            default=DEFAULT_CLASSIFICATION_GUIDANCE,
            user_id=user_id,
        )

        print("[INFO] user_id={} targets={} total={}".format(user_id, len(targets), len(rows)), flush=True)
        ok = 0
        fail = 0
        failed_ids: List[int] = []

        for idx, row in enumerate(targets, start=1):
            paper_id = int(row["id"])
            print("[RUN {}/{}] paper_id={} title={}".format(idx, len(targets), paper_id, safe(row["title"])[:90]), flush=True)
            text = read_text(row["text_cache_path"])
            if not text:
                fail += 1
                failed_ids.append(paper_id)
                print("[ERR {}/{}] paper_id={} reason=missing_text_cache".format(idx, len(targets), paper_id), flush=True)
                continue

            payload = {}
            last_reason = "unknown"
            for attempt in range(1, max_attempts + 1):
                print("  [TRY {}] paper_id={}".format(attempt, paper_id), flush=True)
                hints = build_hints(row, guidance)
                result = pipeline.llm_extract_metadata(
                    text=text,
                    hints=hints,
                    categories=categories,
                    llm_callable=pipeline.default_llm_callable,
                )
                if not pipeline._looks_bad_abstract_original(safe(result.get("abstract_original")), safe(result.get("title"))):
                    if pipeline._valid_abstract_zh_text(safe(result.get("abstract_zh"))):
                        if pipeline._valid_summary_zh_text(safe(result.get("summary_one_line"))):
                            payload = result
                            break
                        last_reason = "bad_summary_zh"
                    else:
                        last_reason = "bad_abstract_zh"
                else:
                    last_reason = "bad_abstract_original"

                print("  [RETRY] paper_id={} reason={}".format(paper_id, last_reason), flush=True)
                time.sleep(min(3, attempt))

            if not payload:
                fail += 1
                failed_ids.append(paper_id)
                print("[ERR {}/{}] paper_id={} reason={}".format(idx, len(targets), paper_id, last_reason), flush=True)
                continue

            db.execute(
                """
                UPDATE papers
                SET title = ?, abstract_original = ?, abstract_zh = ?, summary_one_line = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    safe(payload.get("title")) or safe(row["title"]),
                    safe(payload.get("abstract_original")),
                    safe(payload.get("abstract_zh")),
                    safe(payload.get("summary_one_line")),
                    paper_id,
                    user_id,
                ),
            )
            db.commit()
            ok += 1
            print("[OK {}/{}] paper_id={}".format(idx, len(targets), paper_id), flush=True)

        remain = db.execute(
            """
            SELECT COUNT(*) AS c
            FROM papers
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()["c"]
        print(
            "[DONE] ok={} fail={} total_after={} failed_ids={}".format(
                ok, fail, int(remain), ",".join([str(x) for x in failed_ids])
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
