#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db


TEMPLATE_MARKERS = (
    "英文摘要已提取",
    "未能自动提取到稳定摘要",
    "暂未生成稳定中文总结",
)


def load_env(path: str = "/etc/qh-paper-assistant/app.env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")


def safe(text: Any) -> str:
    return str(text or "").strip()


def norm_space(text: Any, limit: int = 3200) -> str:
    return re.sub(r"\s+", " ", safe(text)).strip()[:limit]


def has_cn(text: Any) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", safe(text)))


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


def first_cn_sentence(text: str, limit: int = 220) -> str:
    src = norm_space(text, 5000)
    if not src:
        return ""
    parts = re.split(r"(?<=[。！？])\s*", src)
    for part in parts:
        p = part.strip()
        if p and has_cn(p):
            return p[:limit]
    return src[:limit] if has_cn(src) else ""


def has_template(text: str) -> bool:
    t = safe(text)
    return any(marker in t for marker in TEMPLATE_MARKERS)


def looks_bad_abstract(text: str, title: str) -> bool:
    src = norm_space(text, 5000)
    if not src or len(src) < 90:
        return True
    low = src.lower()
    if any(x in low for x in ("journal homepage", "springer finance editorial board", "contents lists available")):
        return True
    title_low = norm_space(title, 260).lower()
    if title_low and low.startswith(title_low):
        return True
    return False


def call_qwen_json(prompt: str, payload: Dict[str, Any], max_tokens: int = 1200, timeout: int = 120) -> Dict[str, Any]:
    messages = [
        pipeline._to_anthropic_message(
            "user",
            prompt + "\n\n" + json.dumps(payload, ensure_ascii=False),
        )
    ]
    raw = safe(
        pipeline._call_qwen_text(
            messages=messages,
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt="你是论文元数据修复助手。仅返回JSON。",
            max_tokens=max_tokens,
            temperature=0.1,
            timeout=timeout,
            retries=1,
        )
    )
    if not raw:
        return {}
    blob = pipeline._extract_json_blob(raw)
    if not blob:
        return {}
    try:
        parsed = json.loads(blob)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def prepare_abstract_en(row: Dict[str, Any]) -> str:
    title = safe(row["title"])
    abstract_en = norm_space(row["abstract_original"], 2600)
    text = read_text(row["text_cache_path"])

    if text:
        extracted = norm_space(pipeline._normalize_extracted_text(pipeline._extract_abstract(text)), 2600)
        if extracted and (not abstract_en or looks_bad_abstract(abstract_en, title)):
            abstract_en = extracted

    if abstract_en:
        return abstract_en

    if text:
        return norm_space(text, 1600)
    return norm_space(title, 300)


def translate_and_summarize(title: str, abstract_en: str) -> Dict[str, str]:
    prompt = (
        "将英文摘要翻译为准确自然的简体中文，并给一句话中文总结。"
        "只输出JSON：{\"abstract_zh\":\"...\",\"summary_zh\":\"...\"}。"
        "summary_zh必须是完整中文句子，不超过70字。"
    )
    payload = {"title": safe(title), "abstract_en": norm_space(abstract_en, 1400)}
    data = call_qwen_json(prompt, payload, max_tokens=1200, timeout=120)

    abstract_zh = norm_space(data.get("abstract_zh"), 3200)
    summary_zh = norm_space(data.get("summary_zh"), 500)

    if not has_cn(abstract_zh) or not has_cn(summary_zh):
        retry_payload = {"title": safe(title), "abstract_en": norm_space(abstract_en, 800)}
        retry_data = call_qwen_json(prompt, retry_payload, max_tokens=900, timeout=110)
        if not has_cn(abstract_zh):
            abstract_zh = norm_space(retry_data.get("abstract_zh"), 3200)
        if not has_cn(summary_zh):
            summary_zh = norm_space(retry_data.get("summary_zh"), 500)

    if not has_cn(summary_zh):
        summary_zh = first_cn_sentence(abstract_zh)
    if not has_cn(summary_zh):
        summary_zh = "{}：请查看原文摘要获取核心内容。".format(safe(title) or "该论文")
    if not has_cn(abstract_zh):
        abstract_zh = summary_zh

    return {"abstract_zh": abstract_zh[:3200], "summary_zh": summary_zh[:500]}


def needs_fix(row: Dict[str, Any]) -> bool:
    if has_template(row["abstract_zh"]) or has_template(row["summary_one_line"]):
        return True
    if not has_cn(row["summary_one_line"]) or len(safe(row["summary_one_line"])) < 6:
        return True
    if looks_bad_abstract(row["abstract_original"], row["title"]):
        return True
    return False


def worker(row: Dict[str, Any]) -> Dict[str, Any]:
    paper_id = int(row["id"])
    title = safe(row["title"])
    abstract_en = prepare_abstract_en(row)
    repaired = translate_and_summarize(title, abstract_en)
    return {
        "paper_id": paper_id,
        "abstract_original": norm_space(abstract_en, 3200),
        "abstract_zh": repaired["abstract_zh"],
        "summary_one_line": repaired["summary_zh"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh unstable Chinese abstract/summary fields.")
    parser.add_argument("--user-id", type=int, default=0, help="Only process papers for this user_id (0 means all users)")
    parser.add_argument("--max-workers", type=int, default=0, help="Override worker count; 0 uses env REPAIR_MAX_WORKERS")
    args = parser.parse_args()

    load_env()
    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
    max_workers = int(args.max_workers) if int(args.max_workers) > 0 else int(os.getenv("REPAIR_MAX_WORKERS", "2"))
    user_id = int(args.user_id)

    with connect_db(db_path) as db:
        if user_id > 0:
            rows = db.execute(
                """
                SELECT id, user_id, title, abstract_original, abstract_zh, summary_one_line, text_cache_path
                FROM papers
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, user_id, title, abstract_original, abstract_zh, summary_one_line, text_cache_path
                FROM papers
                ORDER BY id ASC
                """
            ).fetchall()

        targets = [row for row in rows if needs_fix(row)]
        total = len(targets)
        print(f"[INFO] user_id={user_id if user_id > 0 else 'all'} targets={total} / total_papers={len(rows)}", flush=True)
        if total == 0:
            return

        ok = 0
        fail = 0
        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            future_map = {executor.submit(worker, row): row for row in targets}
            for idx, fut in enumerate(as_completed(future_map), start=1):
                row = future_map[fut]
                paper_id = int(row["id"])
                try:
                    fixed = fut.result()
                    db.execute(
                        """
                        UPDATE papers
                        SET abstract_original = ?, abstract_zh = ?, summary_one_line = ?
                        WHERE id = ?
                        """,
                        (
                            fixed["abstract_original"],
                            fixed["abstract_zh"],
                            fixed["summary_one_line"],
                            fixed["paper_id"],
                        ),
                    )
                    db.commit()
                    ok += 1
                    print(f"[OK {idx}/{total}] paper_id={paper_id}", flush=True)
                except Exception as exc:
                    db.rollback()
                    fail += 1
                    print(f"[ERR {idx}/{total}] paper_id={paper_id} error={exc}", flush=True)

        rem = db.execute(
            """
            SELECT COUNT(*) c
            FROM papers
            WHERE abstract_zh LIKE '%英文摘要已提取%'
               OR summary_one_line LIKE '%英文摘要已提取%'
               OR abstract_zh LIKE '%未能自动提取到稳定摘要%'
               OR summary_one_line LIKE '%未能自动提取到稳定摘要%'
               OR abstract_zh LIKE '%暂未生成稳定中文总结%'
               OR summary_one_line LIKE '%暂未生成稳定中文总结%'
            """
        ).fetchone()["c"]
        zh_abs = db.execute("SELECT COUNT(*) c FROM papers WHERE abstract_zh GLOB '*[一-龥]*'").fetchone()["c"]
        zh_sum = db.execute("SELECT COUNT(*) c FROM papers WHERE summary_one_line GLOB '*[一-龥]*'").fetchone()["c"]
        print(
            f"[DONE] total={total} ok={ok} fail={fail} remain_template={rem} zh_abs={zh_abs} zh_sum={zh_sum}",
            flush=True,
        )


if __name__ == "__main__":
    main()
