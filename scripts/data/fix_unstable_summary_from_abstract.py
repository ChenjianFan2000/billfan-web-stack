#!/usr/bin/env python3
import argparse
import os
import re
import sys
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
    target = Path(path)
    if not target.exists():
        return
    for raw in target.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


def safe(value: Any) -> str:
    return str(value or "").strip()


def norm_space(text: Any, limit: int = 3200) -> str:
    return re.sub(r"\s+", " ", safe(text)).strip()[:limit]


def has_cn(text: Any) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", safe(text)))


def has_template(text: Any) -> bool:
    src = safe(text)
    return any(marker in src for marker in TEMPLATE_MARKERS)


def first_cn_sentence(text: str, limit: int = 180) -> str:
    src = norm_space(text, 8000)
    if not src:
        return ""
    for part in re.split(r"(?<=[。！？])\s*", src):
        candidate = part.strip()
        if candidate and has_cn(candidate):
            return candidate[:limit]
    return src[:limit] if has_cn(src) else ""


def read_text(path: Any, max_chars: int = 220000) -> str:
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


def looks_bad_abstract(text: Any, title: Any) -> bool:
    src = norm_space(text, 5000)
    if not src or len(src) < 90:
        return True
    low = src.lower()
    if any(x in low for x in ("journal homepage", "contents lists available", "table of contents")):
        return True
    title_low = norm_space(title, 260).lower()
    if title_low and low.startswith(title_low):
        return True
    if has_template(src):
        return True
    return False


def needs_fix(row: Dict[str, Any]) -> bool:
    summary = safe(row["summary_one_line"])
    if not summary or len(summary) < 8 or not has_cn(summary):
        return True
    if has_template(summary):
        return True
    if has_template(row["abstract_zh"]):
        return True
    return False


def choose_abstract_en(row: Dict[str, Any]) -> str:
    title = safe(row["title"])
    abstract_en = norm_space(row["abstract_original"], 3200)
    if abstract_en and not looks_bad_abstract(abstract_en, title):
        return abstract_en

    text = read_text(row["text_cache_path"])
    if text:
        extracted = norm_space(pipeline._normalize_extracted_text(pipeline._extract_abstract(text)), 3200)
        if extracted and not looks_bad_abstract(extracted, title):
            return extracted
        if extracted:
            return extracted

    if abstract_en:
        return abstract_en
    if text:
        return norm_space(text, 1800)
    return norm_space(title, 300)


def translate_abstract_zh(existing_zh: str, abstract_en: str, allow_llm: bool) -> str:
    if has_cn(existing_zh) and len(norm_space(existing_zh, 3200)) >= 40 and not has_template(existing_zh):
        return norm_space(existing_zh, 3200)

    translated = ""
    if allow_llm and abstract_en:
        try:
            translated = norm_space(pipeline._translate_to_chinese_with_qwen(abstract_en), 3200)
        except Exception:
            translated = ""
    if has_cn(translated):
        return translated

    if has_cn(existing_zh):
        return norm_space(existing_zh, 3200)
    return ""


def summarize_zh(title: str, abstract_zh: str, abstract_en: str, allow_llm: bool) -> str:
    from_zh = first_cn_sentence(abstract_zh, 180)
    if from_zh and not has_template(from_zh):
        return from_zh

    if allow_llm and abstract_en and safe(os.getenv("DASHSCOPE_API_KEY")):
        try:
            prompt = (
                "根据论文摘要生成一句中文总结，20-70字，完整句，尽量包含研究对象与主要发现。"
                "只输出中文总结。"
            )
            payload = {"title": safe(title), "abstract_en": norm_space(abstract_en, 1200)}
            msg = [
                pipeline._to_anthropic_message(
                    "user",
                    prompt + "\n\n" + __import__("json").dumps(payload, ensure_ascii=False),
                )
            ]
            out = norm_space(
                pipeline._call_qwen_text(
                    messages=msg,
                    model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
                    system_prompt="你是论文中文总结助手。",
                    max_tokens=600,
                    temperature=0.1,
                    timeout=65,
                    retries=1,
                ),
                500,
            )
            if has_cn(out) and not has_template(out):
                return out
        except Exception:
            pass

    title_text = safe(title)
    if has_cn(title_text):
        return f"本文围绕《{title_text[:48]}》展开研究，概述了研究对象、方法与主要结论。"
    return "本文基于原文摘要梳理了研究对象、方法与主要结论。"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix unstable Chinese summaries by prioritizing original abstracts.")
    parser.add_argument("--user-id", type=int, default=1, help="Target user id")
    parser.add_argument("--limit", type=int, default=0, help="Optional max papers to process")
    parser.add_argument("--disable-llm", action="store_true", help="Do not call remote LLM; use local fallback only")
    args = parser.parse_args()

    load_env()
    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
    user_id = int(args.user_id)
    limit = int(args.limit)
    allow_llm = not bool(args.disable_llm)

    with connect_db(db_path) as db:
        rows = db.execute(
            """
            SELECT id, user_id, title, abstract_original, abstract_zh, summary_one_line, text_cache_path
            FROM papers
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_id,),
        ).fetchall()
        targets = [row for row in rows if needs_fix(row)]
        if limit > 0:
            targets = targets[:limit]
        total = len(targets)
        print(f"[INFO] user_id={user_id} targets={total} total_papers={len(rows)}", flush=True)

        ok = 0
        fail = 0
        for idx, row in enumerate(targets, start=1):
            paper_id = int(row["id"])
            title = safe(row["title"])
            try:
                abstract_en = choose_abstract_en(row)
                abstract_zh = translate_abstract_zh(safe(row["abstract_zh"]), abstract_en, allow_llm=allow_llm)
                summary_zh = summarize_zh(title, abstract_zh, abstract_en, allow_llm=allow_llm)

                if not has_cn(summary_zh):
                    raise RuntimeError("summary_not_chinese")
                if not abstract_zh:
                    abstract_zh = summary_zh

                db.execute(
                    """
                    UPDATE papers
                    SET abstract_original = ?, abstract_zh = ?, summary_one_line = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (
                        norm_space(abstract_en, 3200),
                        norm_space(abstract_zh, 3200),
                        norm_space(summary_zh, 500),
                        paper_id,
                        user_id,
                    ),
                )
                db.commit()
                ok += 1
                print(f"[OK {idx}/{total}] paper_id={paper_id}", flush=True)
            except Exception as exc:
                db.rollback()
                fail += 1
                print(f"[ERR {idx}/{total}] paper_id={paper_id} error={exc}", flush=True)

        remain = db.execute(
            """
            SELECT COUNT(*) AS c
            FROM papers
            WHERE user_id = ?
              AND (
                summary_one_line IS NULL
                OR trim(summary_one_line) = ''
                OR summary_one_line NOT GLOB '*[一-龥]*'
                OR summary_one_line LIKE '%暂未生成稳定中文总结%'
                OR summary_one_line LIKE '%未能自动提取到稳定摘要%'
                OR summary_one_line LIKE '%英文摘要已提取%'
              )
            """,
            (user_id,),
        ).fetchone()["c"]
        print(f"[DONE] ok={ok} fail={fail} remain_unstable={int(remain)}", flush=True)


if __name__ == "__main__":
    main()
