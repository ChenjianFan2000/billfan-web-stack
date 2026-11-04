#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db

TEMPLATE_MARKERS = (
    "英文摘要已提取",
    "未能自动提取到稳定摘要",
    "暂未生成稳定中文总结",
    "本文基于原文摘要梳理了研究对象、方法与主要结论。",
)

GENERIC_SUMMARY_PATTERNS = (
    r"^本文基于原文摘要",
    r"^该研究围绕核心问题展开分析",
    r"^本文聚焦相关研究主题",
    r"请查看原文摘要",
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


def norm_space(value: Any, limit: int = 3200) -> str:
    return re.sub(r"\s+", " ", safe(value)).strip()[:limit]


def has_cn(value: Any) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", safe(value)))


def has_template(value: Any) -> bool:
    src = safe(value)
    if any(marker in src for marker in TEMPLATE_MARKERS):
        return True
    return any(re.search(pattern, src) for pattern in GENERIC_SUMMARY_PATTERNS)


def looks_bad_abstract_en(text: str, title: str) -> bool:
    src = norm_space(text, 5000)
    if not src:
        return True
    min_len = 45 if has_cn(src) else 60
    if len(src) < min_len:
        return True
    low = src.lower()
    if any(x in low for x in ("journal homepage", "contents lists available", "table of contents")):
        return True
    if "copyright" in low and low.find("copyright") < 120:
        return True
    if has_template(src):
        return True
    if low.startswith("doi:") or low.startswith("http"):
        return True
    title_low = norm_space(title, 260).lower()
    if title_low and low.startswith(title_low) and len(src) < 180:
        return True
    alpha = len(re.findall(r"[A-Za-z]", src))
    if alpha < 25 and not has_cn(src):
        return True
    return False


def valid_abstract_zh(text: str) -> bool:
    src = norm_space(text, 3200)
    if not src or len(src) < 30:
        return False
    if not has_cn(src):
        return False
    if has_template(src):
        return False
    return True


def valid_summary_zh(text: str) -> bool:
    src = norm_space(text, 500)
    if not src or len(src) < 12 or len(src) > 180:
        return False
    if not has_cn(src):
        return False
    if has_template(src):
        return False
    return True


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


def compact_abstract_excerpt(text: str) -> str:
    src = safe(text)
    if not src:
        return ""
    low = src.lower()
    idx = low.find("abstract")
    if idx >= 0:
        start = max(0, idx - 800)
        end = min(len(src), idx + 6000)
        return src[start:end]
    return src[:7000]


def call_qwen_json(
    user_prompt: str,
    payload: Dict[str, Any],
    system_prompt: str,
    max_tokens: int,
    timeout: int,
    retries: int,
) -> Dict[str, Any]:
    effective_timeout = max(20, min(int(timeout), 45))
    for _ in range(max(1, retries)):
        raw = safe(
            pipeline._call_qwen_text(
                messages=[
                    pipeline._to_anthropic_message(
                        "user",
                        user_prompt + "\n\n" + json.dumps(payload, ensure_ascii=False),
                    )
                ],
                model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=0.1,
                timeout=effective_timeout,
                retries=1,
            )
        )
        if not raw:
            continue
        blob = pipeline._extract_json_blob(raw)
        if not blob:
            continue
        try:
            parsed = json.loads(blob)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return {}


def extract_abstract_en_strict(title: str, text: str, existing_abstract: str) -> str:
    candidate = norm_space(existing_abstract, 3200)
    if candidate and not looks_bad_abstract_en(candidate, title):
        return candidate

    extracted = norm_space(pipeline._normalize_extracted_text(pipeline._extract_abstract(text)), 3200)
    if extracted and not looks_bad_abstract_en(extracted, title):
        candidate = extracted

    excerpt = compact_abstract_excerpt(text)
    prompt = (
        "你是学术论文信息抽取助手。请从给定论文文本中抽取英文摘要。"
        "若文本中存在 Abstract 段，优先原样提取并清理断行；若没有，生成忠实的英文摘要（120-260词）。"
        "只返回JSON：{\"abstract_en\":\"...\"}。"
    )
    payload = {
        "title": safe(title),
        "candidate_abstract_en": candidate,
        "paper_text_excerpt": excerpt,
    }
    data = call_qwen_json(
        user_prompt=prompt,
        payload=payload,
        system_prompt="You extract English abstracts and return strict JSON.",
        max_tokens=1200,
        timeout=45,
        retries=2,
    )
    abstract_en = norm_space(data.get("abstract_en"), 3200)
    if abstract_en and not looks_bad_abstract_en(abstract_en, title):
        return abstract_en
    if candidate and not looks_bad_abstract_en(candidate, title):
        return candidate
    return abstract_en


def translate_abstract_zh_strict(title: str, abstract_en: str) -> str:
    if has_cn(abstract_en):
        return norm_space(abstract_en, 3200)
    direct = norm_space(
        pipeline._call_qwen_text(
            messages=[
                pipeline._to_anthropic_message(
                    "user",
                    "请把以下英文摘要翻译成自然准确的简体中文，只输出译文：\n\n" + norm_space(abstract_en, 1400),
                )
            ],
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt="你是学术翻译助手。",
            max_tokens=1600,
            temperature=0.05,
            timeout=28,
            retries=1,
        ),
        3200,
    )
    if valid_abstract_zh(direct):
        return direct
    prompt = (
        "将以下英文摘要准确翻译为简体中文，保持学术语义，术语一致。"
        "只返回JSON：{\"abstract_zh\":\"...\"}。"
    )
    payload = {"title": safe(title), "abstract_en": norm_space(abstract_en, 1200)}
    data = call_qwen_json(
        user_prompt=prompt,
        payload=payload,
        system_prompt="你是学术翻译助手，只返回 JSON。",
        max_tokens=1200,
        timeout=30,
        retries=1,
    )
    return norm_space(data.get("abstract_zh"), 3200)


def summarize_zh_strict(title: str, abstract_en: str, abstract_zh: str) -> str:
    out = norm_space(
        pipeline._call_qwen_text(
            messages=[
                pipeline._to_anthropic_message(
                    "user",
                    "请给出一句中文总结（20-70字，完整句，不要模板）：\n\n标题：{}\n摘要：{}".format(
                        safe(title), norm_space(abstract_zh or abstract_en, 1400)
                    ),
                )
            ],
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt="你是论文中文总结助手。",
            max_tokens=320,
            temperature=0.1,
            timeout=24,
            retries=1,
        ),
        500,
    )
    if valid_summary_zh(out):
        return out
    prompt = (
        "基于论文摘要生成一句中文总结（20-70字）。"
        "要求：包含研究对象或方法与主要结论之一；必须是完整中文句子；禁止模板话术。"
        "只返回JSON：{\"summary_zh\":\"...\"}。"
    )
    payload = {
        "title": safe(title),
        "abstract_zh": norm_space(abstract_zh, 800),
        "abstract_en": norm_space(abstract_en, 800),
    }
    data = call_qwen_json(
        user_prompt=prompt,
        payload=payload,
        system_prompt="你是论文中文总结助手，只返回 JSON。",
        max_tokens=260,
        timeout=28,
        retries=1,
    )
    summary = norm_space(data.get("summary_zh"), 500)
    if valid_summary_zh(summary):
        return summary
    return out


def paper_needs_repair(row: Dict[str, Any]) -> bool:
    if looks_bad_abstract_en(row["abstract_original"], row["title"]):
        return True
    if not valid_abstract_zh(row["abstract_zh"]):
        return True
    if not valid_summary_zh(row["summary_one_line"]):
        return True
    return False


def repair_one(row: Dict[str, Any], max_attempts: int) -> Tuple[bool, str, Dict[str, str]]:
    title = safe(row["title"])
    paper_id = int(row["id"])
    text = read_text(row["text_cache_path"])
    existing_en = norm_space(row["abstract_original"], 3200)
    last_err = ""

    for attempt in range(1, max(1, max_attempts) + 1):
        print("  [TRY {}] paper_id={}".format(attempt, paper_id), flush=True)
        abstract_en = extract_abstract_en_strict(title, text, existing_en)
        if looks_bad_abstract_en(abstract_en, title):
            last_err = "bad_abstract_en"
            print("  [RETRY] paper_id={} reason={}".format(paper_id, last_err), flush=True)
            time.sleep(min(3, attempt))
            continue

        abstract_zh = translate_abstract_zh_strict(title, abstract_en)
        if not valid_abstract_zh(abstract_zh):
            last_err = "bad_abstract_zh"
            print("  [RETRY] paper_id={} reason={}".format(paper_id, last_err), flush=True)
            time.sleep(min(3, attempt))
            continue

        summary_zh = summarize_zh_strict(title, abstract_en, abstract_zh)
        if not valid_summary_zh(summary_zh):
            last_err = "bad_summary_zh"
            print("  [RETRY] paper_id={} reason={}".format(paper_id, last_err), flush=True)
            time.sleep(min(3, attempt))
            continue

        return True, "", {
            "abstract_original": norm_space(abstract_en, 3200),
            "abstract_zh": norm_space(abstract_zh, 3200),
            "summary_one_line": norm_space(summary_zh, 500),
        }

    return False, last_err or "unknown", {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Strict LLM repair for abstract extraction/translation/summary.")
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
    max_attempts = max(1, int(args.max_attempts))

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
        targets = [row for row in rows if paper_needs_repair(row)]
        selected_ids = {int(x) for x in re.findall(r"\d+", safe(args.paper_ids))}
        if selected_ids:
            targets = [row for row in targets if int(row["id"]) in selected_ids]
        if int(args.limit) > 0:
            targets = targets[: int(args.limit)]

        print("[INFO] user_id={} targets={} total={}".format(user_id, len(targets), len(rows)), flush=True)
        ok = 0
        fail = 0
        failed_ids: List[int] = []

        for idx, row in enumerate(targets, start=1):
            paper_id = int(row["id"])
            print("[RUN {}/{}] paper_id={} title={}".format(idx, len(targets), paper_id, safe(row["title"])[:90]), flush=True)
            success, err, payload = repair_one(row, max_attempts=max_attempts)
            if not success:
                fail += 1
                failed_ids.append(paper_id)
                print("[ERR {}/{}] paper_id={} reason={}".format(idx, len(targets), paper_id, err), flush=True)
                continue

            db.execute(
                """
                UPDATE papers
                SET abstract_original = ?, abstract_zh = ?, summary_one_line = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    payload["abstract_original"],
                    payload["abstract_zh"],
                    payload["summary_one_line"],
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
              AND (
                abstract_original IS NULL OR trim(abstract_original) = ''
                OR abstract_zh IS NULL OR trim(abstract_zh) = '' OR abstract_zh NOT GLOB '*[一-龥]*'
                OR summary_one_line IS NULL OR trim(summary_one_line) = '' OR summary_one_line NOT GLOB '*[一-龥]*'
                OR summary_one_line LIKE '%暂未生成稳定中文总结%'
                OR summary_one_line LIKE '%未能自动提取到稳定摘要%'
                OR summary_one_line LIKE '%英文摘要已提取%'
                OR summary_one_line = '本文基于原文摘要梳理了研究对象、方法与主要结论。'
              )
            """,
            (user_id,),
        ).fetchone()["c"]
        print(
            "[DONE] ok={} fail={} remain_unstable={} failed_ids={}".format(
                ok, fail, int(remain), ",".join([str(x) for x in failed_ids])
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
