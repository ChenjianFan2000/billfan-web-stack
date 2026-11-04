#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db


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


def normalize_space(text: str, limit: int = 3200) -> str:
    return re.sub(r"\s+", " ", safe(text)).strip()[:limit]


def has_cn(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", safe(text)))


def first_cn_sentence(text: str, limit: int = 220) -> str:
    src = normalize_space(text, 8000)
    if not src:
        return ""
    for part in re.split(r"(?<=[。！？])\s*", src):
        p = part.strip()
        if p and has_cn(p):
            return p[:limit]
    return src[:limit] if has_cn(src) else ""


def read_text(path: str) -> str:
    target = safe(path)
    if not target:
        return ""
    p = Path(target)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:260000]
    except Exception:
        return ""


def looks_bad_abstract(text: str, title: str) -> bool:
    s = normalize_space(text, 5000)
    if not s:
        return True
    if len(s) < 100:
        return True
    low = s.lower()
    bad_signals = [
        "英文摘要已提取",
        "未能自动提取到稳定摘要",
        "journal homepage",
        "springer finance editorial board",
        "table of contents",
    ]
    if any(marker in low for marker in bad_signals):
        return True
    # When extracted text is almost identical to title, it is not a real abstract.
    t = normalize_space(title, 260).lower()
    if t and low.startswith(t):
        return True
    # If there are almost no sentence boundaries, quality is usually poor.
    if s.count(".") + s.count(";") + s.count(":") < 2 and len(s) > 240:
        return True
    return False


def call_qwen_json(
    user_prompt: str,
    payload: Dict[str, Any],
    system_prompt: str,
    max_tokens: int,
    timeout: int,
    retries: int,
) -> Dict[str, Any]:
    messages = [
        pipeline._to_anthropic_message(
            "user",
            user_prompt + "\n\n" + json.dumps(payload, ensure_ascii=False),
        )
    ]
    raw = safe(
        pipeline._call_qwen_text(
            messages=messages,
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            timeout=timeout,
            retries=retries,
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


def extract_abstract_en(title: str, full_text: str, candidate: str) -> str:
    base = normalize_space(candidate, 3200)
    if base and not looks_bad_abstract(base, title):
        return base

    text_snippet = safe(full_text)[:18000]
    if not text_snippet:
        return base

    prompt = (
        "从给定论文文本中提取英文摘要。"
        "若存在明确 Abstract 段落，尽量提取原文摘要并清理断行；"
        "若不存在明确 Abstract，请生成 80-180 词英文概述。"
        "只输出 JSON：{\"abstract_en\":\"...\",\"source\":\"original|generated\"}。"
    )
    data = call_qwen_json(
        user_prompt=prompt,
        payload={"title": safe(title), "text": text_snippet, "candidate_abstract": base},
        system_prompt="You extract English academic abstracts and return strict JSON.",
        max_tokens=1000,
        timeout=120,
        retries=2,
    )
    extracted = normalize_space(data.get("abstract_en"), 3200)
    if extracted:
        return extracted
    return base


def translate_and_summarize(title: str, abstract_en: str) -> Dict[str, str]:
    prompt = (
        "将英文摘要翻译为准确、自然的简体中文，并给出一句话中文总结。"
        "仅输出 JSON：{\"abstract_zh\":\"...\",\"summary_zh\":\"...\"}。"
        "要求：summary_zh 为 20-70 字完整句子，不要模板化。"
    )
    data = call_qwen_json(
        user_prompt=prompt,
        payload={"title": safe(title), "abstract_en": normalize_space(abstract_en, 2600)},
        system_prompt="你是金融数学论文中文助手。仅返回 JSON。",
        max_tokens=1300,
        timeout=110,
        retries=3,
    )
    abstract_zh = normalize_space(data.get("abstract_zh"), 3200)
    summary_zh = normalize_space(data.get("summary_zh"), 500)

    if not has_cn(abstract_zh):
        abstract_zh = normalize_space(pipeline._translate_to_chinese_with_qwen(abstract_en), 3200)

    if not has_cn(summary_zh) or len(summary_zh) > 300:
        summary_zh = first_cn_sentence(abstract_zh, limit=220)

    if not has_cn(summary_zh):
        title_text = safe(title) or "该论文"
        summary_zh = f"{title_text}：请查看原文摘要获取核心内容。"

    if not has_cn(abstract_zh):
        abstract_zh = summary_zh

    return {"abstract_zh": abstract_zh, "summary_zh": summary_zh}


def main() -> None:
    load_env()
    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")

    with connect_db(db_path) as db:
        rows = db.execute(
            """
            SELECT id, title, file_path, text_cache_path, abstract_original, abstract_zh, summary_one_line
            FROM papers
            ORDER BY id ASC
            """
        ).fetchall()

        total = len(rows)
        ok = 0
        fail = 0
        improved = 0

        for idx, row in enumerate(rows, start=1):
            paper_id = int(row["id"])
            title = safe(row["title"])
            old_ao = normalize_space(row["abstract_original"], 3200)
            old_zh = normalize_space(row["abstract_zh"], 3200)
            old_sum = normalize_space(row["summary_one_line"], 500)

            text = read_text(row["text_cache_path"])
            if not text and safe(row["file_path"]):
                try:
                    text = safe(pipeline.extract_text_best_effort(safe(row["file_path"]))["text"])
                except Exception:
                    text = ""

            extracted = ""
            if text:
                extracted = normalize_space(
                    pipeline._normalize_extracted_text(pipeline._extract_abstract(text)),
                    3200,
                )

            candidate = old_ao or extracted
            if extracted and (not candidate or looks_bad_abstract(candidate, title)):
                candidate = extracted

            abstract_en = extract_abstract_en(title, text, candidate)
            if not abstract_en:
                abstract_en = old_ao
            if not abstract_en:
                fail += 1
                print(f"[ERR {idx}/{total}] paper_id={paper_id} no abstract", flush=True)
                continue

            zh_pair = translate_and_summarize(title, abstract_en)
            abstract_zh = normalize_space(zh_pair["abstract_zh"], 3200)
            summary_zh = normalize_space(zh_pair["summary_zh"], 500)

            if not has_cn(abstract_zh) and has_cn(old_zh):
                abstract_zh = old_zh
            if not has_cn(summary_zh) and has_cn(old_sum):
                summary_zh = old_sum

            try:
                db.execute(
                    """
                    UPDATE papers
                    SET abstract_original = ?, abstract_zh = ?, summary_one_line = ?
                    WHERE id = ?
                    """,
                    (abstract_en, abstract_zh, summary_zh, paper_id),
                )
                db.commit()
                ok += 1
                if old_sum != summary_zh or old_zh != abstract_zh or old_ao != abstract_en:
                    improved += 1
                print(f"[OK {idx}/{total}] paper_id={paper_id}", flush=True)
            except Exception as exc:
                db.rollback()
                fail += 1
                print(f"[ERR {idx}/{total}] paper_id={paper_id} {exc}", flush=True)

            time.sleep(0.1)

        rem_tpl = db.execute(
            """
            SELECT COUNT(*) c
            FROM papers
            WHERE abstract_zh LIKE '%英文摘要已提取%'
               OR summary_one_line LIKE '%英文摘要已提取%'
               OR abstract_zh LIKE '%未能自动提取到稳定摘要%'
               OR summary_one_line LIKE '%未能自动提取到稳定摘要%'
            """
        ).fetchone()["c"]
        zh_abs = db.execute("SELECT COUNT(*) c FROM papers WHERE abstract_zh GLOB '*[一-龥]*'").fetchone()["c"]
        zh_sum = db.execute("SELECT COUNT(*) c FROM papers WHERE summary_one_line GLOB '*[一-龥]*'").fetchone()["c"]

        print(
            f"[DONE] total={total} ok={ok} fail={fail} improved={improved} remain_template={rem_tpl} zh_abs={zh_abs} zh_sum={zh_sum}",
            flush=True,
        )


if __name__ == "__main__":
    main()
