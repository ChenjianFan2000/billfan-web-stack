import base64
import concurrent.futures
import io
import json
import os
import random
import re
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.db import connect_db
from app import dashscope_client
from app.paper_categories import set_paper_categories
from app.settings_store import (
    CLASSIFICATION_GUIDANCE_KEY,
    DEFAULT_CLASSIFICATION_GUIDANCE,
    get_setting_value,
)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _looks_like_bad_title(title: str) -> bool:
    value = _safe_text(title)
    if not value:
        return True

    low = value.lower()
    if "indirectobject(" in low or low == "datastream":
        return True
    if re.fullmatch(r"[A-Z]{2,}\d{5,}.*", value):
        return True
    if "\\\\" in value or value.startswith(("C:\\", "/")):
        return True
    if low.endswith((".doc", ".docx", ".wpd")):
        return True
    if value.count("..") >= 1:
        return True
    return False


def extract_pdf_metadata_hints(pdf_path: str, reader_factory: Optional[Callable] = None) -> Dict[str, Any]:
    reader_factory = reader_factory or _default_pdf_reader_factory
    if reader_factory is None:
        return {}

    try:
        reader = reader_factory(pdf_path)
        metadata = getattr(reader, "metadata", None) or {}
    except Exception:
        return {}

    title = _safe_text(metadata.get("/Title"))
    author_raw = _safe_text(metadata.get("/Author"))
    subject = _safe_text(metadata.get("/Subject"))
    creator = _safe_text(metadata.get("/Creator"))

    hints = {}
    if title:
        hints["title"] = title
    if author_raw:
        authors = [a.strip() for a in re.split(r"[,;]", author_raw) if a.strip()]
        hints["authors"] = authors if authors else [author_raw]
    if subject:
        hints["subject"] = subject
    if creator:
        hints["creator"] = creator
    return hints


def _default_pdf_reader_factory(_pdf_path: str):
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None
    return PdfReader(_pdf_path)


def extract_filename_hints(pdf_path: str) -> Dict[str, Any]:
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    if not stem:
        return {}

    tokens = [tok for tok in re.split(r"[_\-\s]+", stem) if tok]
    year_idx = -1
    for idx, token in enumerate(tokens):
        if re.fullmatch(r"(19|20)\d{2}", token):
            year_idx = idx
            break

    hints: Dict[str, Any] = {}
    if year_idx > 0:
        hints["year"] = int(tokens[year_idx])

        author_tokens = tokens[:year_idx]
        authors = _parse_authors_from_filename_tokens(author_tokens)
        if authors:
            hints["authors"] = authors

        title_tokens = tokens[year_idx + 1 :]
        if title_tokens:
            hints["title"] = " ".join(title_tokens).replace("Et Al", "et al").strip()
    else:
        # uuid-like names should not become title hints.
        if not re.fullmatch(r"[0-9a-fA-F-]{24,}", stem):
            hints["title"] = stem.replace("_", " ").strip()

    return hints


def _parse_authors_from_filename_tokens(tokens: List[str]) -> List[str]:
    cleaned = [t for t in tokens if t and t.lower() not in {"et", "al"}]
    if not cleaned:
        return []

    if len(cleaned) <= 4:
        return [token.strip() for token in cleaned if token.strip()]

    # Chinese and transliterated names are often stored as pairs in the sample set.
    if len(cleaned) % 2 == 0 and len(cleaned) <= 10:
        pairs = []
        for idx in range(0, len(cleaned), 2):
            pairs.append((cleaned[idx] + " " + cleaned[idx + 1]).strip())
        return [p for p in pairs if p]

    return [token.strip() for token in cleaned if token.strip()]


def _estimate_garbled_ratio(text: str) -> float:
    if not text:
        return 1.0

    total = len(text)
    weird = 0
    for ch in text:
        if ch == "\ufffd":
            weird += 1
            continue
        o = ord(ch)
        if o < 32 and ch not in "\n\r\t":
            weird += 1
            continue
        if 0xE000 <= o <= 0xF8FF:  # private-use chars
            weird += 1
    return weird / float(total)


def _has_dashscope_key() -> bool:
    return bool(_safe_text(os.getenv("DASHSCOPE_API_KEY", "")))


_TEMPLATE_FALLBACK_MARKERS = (
    "英文摘要已提取",
    "未能自动提取到稳定摘要",
    "暂未生成稳定中文总结",
    "本文基于原文摘要梳理了研究对象、方法与主要结论。",
    "请查看原文摘要获取核心内容",
    "核心内容和研究结论已归入",
    "便于后续快速检索与对比阅读",
)


def _contains_template_fallback(text: str) -> bool:
    value = _safe_text(text)
    if not value:
        return False
    return any(marker in value for marker in _TEMPLATE_FALLBACK_MARKERS)


def _looks_bad_abstract_original(text: str, title: str = "") -> bool:
    value = re.sub(r"\s+", " ", _safe_text(text)).strip()
    if not value:
        return True
    min_len = 45 if _contains_chinese(value) else 60
    if len(value) < min_len:
        return True
    if _contains_template_fallback(value):
        return True
    low = value.lower()
    noisy_markers = ("journal homepage", "contents lists available", "table of contents")
    if any(marker in low for marker in noisy_markers):
        return True
    if "copyright" in low and low.find("copyright") < 120:
        return True
    title_norm = re.sub(r"\s+", " ", _safe_text(title)).strip().lower()
    if title_norm and low.startswith(title_norm) and len(value) < 180:
        return True
    alpha_chars = len(re.findall(r"[A-Za-z]", value))
    if alpha_chars < 25 and not _contains_chinese(value):
        return True
    return False


def _valid_abstract_zh_text(text: str) -> bool:
    value = re.sub(r"\s+", " ", _safe_text(text)).strip()
    if not value or len(value) < 60:
        return False
    if not _contains_chinese(value):
        return False
    if _contains_template_fallback(value):
        return False
    return True


def _valid_summary_zh_text(text: str) -> bool:
    value = re.sub(r"\s+", " ", _safe_text(text)).strip()
    if not value or len(value) < 12 or len(value) > 220:
        return False
    if not _contains_chinese(value):
        return False
    if _contains_template_fallback(value):
        return False
    return True


def _contains_coded_artifacts(text: str) -> bool:
    return bool(re.search(r"(?:/C\d{1,3}){3,}", _safe_text(text)))


def _contains_joined_word_artifacts(text: str) -> bool:
    source = _safe_text(text)
    if not source or _contains_chinese(source):
        return False

    letters = len(re.findall(r"[A-Za-z]", source))
    if letters < 800:
        return False
    spaces = source.count(" ")
    long_runs = len(re.findall(r"[A-Za-z]{18,}", source))
    space_ratio = spaces / float(max(letters, 1))
    return (space_ratio < 0.12 and long_runs >= 8) or long_runs >= 40


def _decode_coded_artifacts(text: str) -> str:
    source = _safe_text(text)
    if not source:
        return ""

    pattern = re.compile(r"(?:/C\d{1,3}){3,}")

    def _decode_segment(match) -> str:
        codes = re.findall(r"/C(\d{1,3})", match.group(0))
        chars: List[str] = []
        for code in codes:
            try:
                value = int(code)
            except Exception:
                continue
            if value < 0 or value > 1114111:
                continue
            try:
                chars.append(chr(value))
            except Exception:
                continue
        return "".join(chars) if chars else match.group(0)

    return pattern.sub(_decode_segment, source)


def _normalize_extracted_text(text: str) -> str:
    value = _decode_coded_artifacts(text)
    if not value:
        return ""

    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _normalize_title_for_duplicate_check(title: str) -> str:
    value = _safe_text(title)
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()


def _normalize_text_for_duplicate_check(text: str, max_chars: int = 90000) -> str:
    value = _safe_text(text)
    if not value:
        return ""
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"\s+", "", value).casefold()
    if len(value) > max_chars:
        half = max_chars // 2
        value = value[:half] + value[-half:]
    return value


def _char_ngrams(text: str, n: int = 5) -> Set[str]:
    source = _safe_text(text)
    if not source:
        return set()
    if len(source) <= n:
        return {source}
    return {source[i : i + n] for i in range(len(source) - n + 1)}


def _jaccard_similarity(left: Set[str], right: Set[str]) -> float:
    if not left or not right:
        return 0.0
    inter = len(left.intersection(right))
    if inter == 0:
        return 0.0
    union = len(left) + len(right) - inter
    if union <= 0:
        return 0.0
    return inter / float(union)


def _read_text_cache(path: str, max_chars: int = 180000) -> str:
    target = _safe_text(path)
    if not target or not os.path.exists(target):
        return ""
    try:
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def _safe_remove_file(path: Optional[str]) -> None:
    target = _safe_text(path)
    if not target or not os.path.exists(target):
        return
    try:
        os.remove(target)
    except OSError:
        pass


def _get_duplicate_text_similarity_threshold() -> float:
    default = 0.86
    raw = _safe_text(os.getenv("PAPER_DUPLICATE_TEXT_SIM_THRESHOLD", ""))
    if not raw:
        return default
    try:
        parsed = float(raw)
    except ValueError:
        return default
    return max(0.5, min(0.99, parsed))


def _get_duplicate_text_min_chars() -> int:
    default = 1200
    raw = _safe_text(os.getenv("PAPER_DUPLICATE_TEXT_MIN_CHARS", ""))
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(200, min(20000, parsed))


def _split_for_llm(text: str, chunk_size: int = 7000) -> List[str]:
    source = _safe_text(text)
    if not source:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for line in source.splitlines(keepends=True):
        if current_len + len(line) > chunk_size and current:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("".join(current))
    return chunks


def _call_qwen_text(
    messages: List[Dict[str, Any]],
    model: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: int,
    retries: int = 4,
) -> str:
    timeout_cap_raw = _safe_text(os.getenv("QWEN_TIMEOUT_CAP", "45"))
    retry_cap_raw = _safe_text(os.getenv("QWEN_RETRY_CAP", "2"))
    try:
        timeout_cap = max(12, int(timeout_cap_raw))
    except ValueError:
        timeout_cap = 45
    try:
        retry_cap = max(1, int(retry_cap_raw))
    except ValueError:
        retry_cap = 2

    effective_timeout = min(max(8, int(timeout)), timeout_cap)
    effective_retries = min(max(1, int(retries)), retry_cap)

    for attempt in range(effective_retries):
        response = dashscope_client.call_messages(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=effective_timeout,
        )
        text = _safe_text(dashscope_client.extract_text(response))
        if text:
            return text
        if attempt < effective_retries - 1:
            sleep_seconds = min(6.0, (1.4 ** attempt) + random.random())
            time.sleep(sleep_seconds)
    return ""


def _qwen_quality_check_text(text: str, hints: Dict[str, Any]) -> Dict[str, Any]:
    if not _has_dashscope_key() or not _safe_text(text):
        return {"needs_ocr": False}

    snippet = _safe_text(text)
    raw_max_chars = _safe_text(os.getenv("QWEN_QUALITY_SNIPPET_MAX_CHARS", "24000"))
    try:
        max_chars = int(raw_max_chars)
    except ValueError:
        max_chars = 24000
    max_chars = max(6000, max_chars)
    if len(snippet) > max_chars:
        slice_len = max_chars // 3
        mid = len(snippet) // 2
        mid_start = max(0, mid - (slice_len // 2))
        mid_end = min(len(snippet), mid_start + slice_len)
        snippet = "\n...\n".join(
            [
                snippet[:slice_len],
                snippet[mid_start:mid_end],
                snippet[-slice_len:],
            ]
        )
    prompt = (
        "You judge PDF text extraction quality.\n"
        "Return STRICT JSON only with keys: needs_ocr(boolean), reason(string).\n"
        "Set needs_ocr=true only if text is mostly unreadable or heavily corrupted.\n"
        "Corruption examples: repeated encoding artifacts like /C67/C111, severe mojibake, or mostly broken tokens."
    )
    content = {
        "hints": hints,
        "text_snippet": snippet,
    }
    messages = [_to_anthropic_message("user", prompt + "\n\n" + json.dumps(content, ensure_ascii=False))]
    raw = _call_qwen_text(
        messages=messages,
        model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
        system_prompt="Return JSON only.",
        max_tokens=260,
        temperature=0,
        timeout=60,
        retries=3,
    )
    blob = _extract_json_blob(raw)
    if not blob:
        return {"needs_ocr": False}
    try:
        parsed = json.loads(blob)
    except Exception:
        return {"needs_ocr": False}
    if not isinstance(parsed, dict):
        return {"needs_ocr": False}
    return {"needs_ocr": bool(parsed.get("needs_ocr")), "reason": _safe_text(parsed.get("reason"))}


def _qwen_clean_text(text: str, hints: Dict[str, Any]) -> str:
    source = _safe_text(text)
    if not source or not _has_dashscope_key():
        return source

    def _env_int(name: str, default: int, minimum: int) -> int:
        raw_value = _safe_text(os.getenv(name, ""))
        if not raw_value:
            return max(minimum, default)
        try:
            parsed = int(raw_value)
        except ValueError:
            return max(minimum, default)
        return max(minimum, parsed)

    chunks = _split_for_llm(source, chunk_size=7000)
    if not chunks:
        return source

    chunk_count = len(chunks)
    if chunk_count >= 16:
        per_chunk_timeout = _env_int("QWEN_CLEAN_TIMEOUT_LONG", default=18, minimum=12)
        per_chunk_retries = _env_int("QWEN_CLEAN_RETRIES_LONG", default=1, minimum=1)
    elif chunk_count >= 10:
        per_chunk_timeout = _env_int("QWEN_CLEAN_TIMEOUT_MEDIUM", default=26, minimum=15)
        per_chunk_retries = _env_int("QWEN_CLEAN_RETRIES_MEDIUM", default=1, minimum=1)
    else:
        per_chunk_timeout = _env_int("QWEN_CLEAN_TIMEOUT_SHORT", default=35, minimum=20)
        per_chunk_retries = _env_int("QWEN_CLEAN_RETRIES_SHORT", default=2, minimum=1)

    cleaned: List[str] = []
    def _clean_one_chunk(idx: int, chunk: str) -> str:
        prompt = (
            "You are repairing noisy PDF text extraction.\n"
            "Tasks:\n"
            "1) Decode artifacts like /C67/C111 into readable characters.\n"
            "2) Fix obvious broken words and punctuation.\n"
            "3) Insert missing spaces in concatenated English words when needed.\n"
            "4) Preserve original meaning and paragraph structure; DO NOT summarize.\n"
            "Return plain text only."
        )
        payload = {
            "hints": hints,
            "chunk_index": idx + 1,
            "chunk_total": len(chunks),
            "text_chunk": chunk,
        }
        messages = [_to_anthropic_message("user", prompt + "\n\n" + json.dumps(payload, ensure_ascii=False))]
        out = _call_qwen_text(
            messages=messages,
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt="Return plain corrected text, no markdown.",
            max_tokens=3500,
            temperature=0,
            timeout=per_chunk_timeout,
            retries=per_chunk_retries,
        )
        # Guardrail: if model output is too short, keep original chunk to avoid accidental summarization.
        if len(out) < max(120, int(len(chunk) * 0.35)):
            return chunk
        return out

    max_workers = _env_int("QWEN_CLEAN_MAX_WORKERS", default=3, minimum=1)
    max_workers = min(max_workers, chunk_count)
    if max_workers <= 1 or chunk_count <= 1:
        for idx, chunk in enumerate(chunks):
            cleaned.append(_clean_one_chunk(idx, chunk))
    else:
        ordered: Dict[int, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(_clean_one_chunk, idx, chunk): idx
                for idx, chunk in enumerate(chunks)
            }
            for future in concurrent.futures.as_completed(future_map):
                idx = future_map[future]
                try:
                    ordered[idx] = future.result()
                except Exception:
                    ordered[idx] = chunks[idx]
        cleaned = [ordered.get(idx, chunks[idx]) for idx in range(chunk_count)]

    merged = "\n".join(cleaned).strip()
    return _normalize_extracted_text(merged) if merged else source


def _prepare_text_with_qwen_guardrail(text: str, hints: Dict[str, Any]) -> Tuple[str, bool]:
    normalized = _normalize_extracted_text(text)
    if not normalized:
        return "", True

    garbled_ratio = _estimate_garbled_ratio(normalized)
    has_joined_words = _contains_joined_word_artifacts(normalized)
    coded_artifacts = _contains_coded_artifacts(normalized)
    needs_ocr = len(normalized) < 200 or garbled_ratio >= 0.12 or coded_artifacts
    suspicious = needs_ocr or has_joined_words

    if coded_artifacts or garbled_ratio >= 0.08 or has_joined_words:
        normalized = _qwen_clean_text(normalized, hints)
        garbled_ratio = _estimate_garbled_ratio(normalized)
        has_joined_words = _contains_joined_word_artifacts(normalized)
        coded_artifacts = _contains_coded_artifacts(normalized)

    if suspicious:
        quality = _qwen_quality_check_text(normalized, hints)
        if quality.get("needs_ocr"):
            needs_ocr = True

    # Final local safety check.
    if len(normalized) >= 200 and garbled_ratio < 0.12 and not coded_artifacts:
        needs_ocr = False
    return normalized, needs_ocr


def extract_text_pymupdf(pdf_path: str, fitz_module=None, max_pages: Optional[int] = 30) -> Dict[str, Any]:
    fitz_module = fitz_module or _load_fitz()
    if fitz_module is None:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    try:
        with fitz_module.open(pdf_path) as doc:
            parts = []
            for idx, page in enumerate(doc):
                if max_pages is not None and idx >= max_pages:
                    break
                page_text = page.get_text("text")
                if page_text:
                    parts.append(page_text)
    except Exception:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    text = "\n".join(parts).strip()
    garbled_ratio = _estimate_garbled_ratio(text)
    needs_ocr = len(text) <= 200 or garbled_ratio >= 0.10
    return {
        "text": text,
        "needs_ocr": needs_ocr,
        "garbled_ratio": garbled_ratio,
    }


def extract_text_pypdf(
    pdf_path: str, reader_factory: Optional[Callable] = None, max_pages: Optional[int] = 30
) -> Dict[str, Any]:
    reader_factory = reader_factory or _default_pdf_reader_factory
    if reader_factory is None:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    try:
        reader = reader_factory(pdf_path)
        parts = []
        for idx, page in enumerate(reader.pages):
            if max_pages is not None and idx >= max_pages:
                break
            page_text = _safe_text(page.extract_text() if hasattr(page, "extract_text") else "")
            if page_text:
                parts.append(page_text)
    except Exception:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    text = "\n".join(parts).strip()
    garbled_ratio = _estimate_garbled_ratio(text)
    return {
        "text": text,
        "needs_ocr": len(text) <= 200 or garbled_ratio >= 0.10,
        "garbled_ratio": garbled_ratio,
    }


def _load_pdfium():
    try:
        import pypdfium2 as pdfium  # type: ignore

        return pdfium
    except Exception:
        return None


def extract_text_pdfium(pdf_path: str, pdfium_module=None, max_pages: Optional[int] = 30) -> Dict[str, Any]:
    pdfium_module = pdfium_module or _load_pdfium()
    if pdfium_module is None:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    try:
        doc = pdfium_module.PdfDocument(pdf_path)
    except Exception:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    parts: List[str] = []
    try:
        for idx, page in enumerate(doc):
            if max_pages is not None and idx >= max_pages:
                break
            try:
                textpage = page.get_textpage()
                page_text = _safe_text(textpage.get_text_bounded() if hasattr(textpage, "get_text_bounded") else "")
            except Exception:
                page_text = ""
            if page_text:
                parts.append(page_text)
    except Exception:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    text = "\n".join(parts).strip()
    garbled_ratio = _estimate_garbled_ratio(text)
    return {
        "text": text,
        "needs_ocr": len(text) <= 200 or garbled_ratio >= 0.10,
        "garbled_ratio": garbled_ratio,
    }


def _load_fitz():
    try:
        import fitz  # type: ignore

        return fitz
    except Exception:
        return None


def _table_to_markdown(table: List[List[Any]]) -> str:
    if not table:
        return ""

    normalized = []
    for row in table:
        normalized.append([_safe_text(cell) for cell in row])

    if not normalized:
        return ""

    header = normalized[0]
    body = normalized[1:] if len(normalized) > 1 else []

    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def extract_tables_pdfplumber(
    pdf_path: str,
    pdfplumber_module=None,
    max_pages: Optional[int] = 8,
    max_tables: Optional[int] = 16,
) -> str:
    pdfplumber_module = pdfplumber_module or _load_pdfplumber()
    if pdfplumber_module is None:
        return ""

    blocks = []
    try:
        with pdfplumber_module.open(pdf_path) as pdf:
            table_count = 0
            for idx, page in enumerate(pdf.pages):
                if max_pages is not None and idx >= max_pages:
                    break
                tables = page.extract_tables() or []
                for table in tables:
                    if max_tables is not None and table_count >= max_tables:
                        break
                    md = _table_to_markdown(table)
                    if md:
                        blocks.append(md)
                        table_count += 1
                if max_tables is not None and table_count >= max_tables:
                    break
    except Exception:
        return ""

    return "\n\n".join(blocks).strip()


def _load_pdfplumber():
    try:
        import pdfplumber  # type: ignore

        return pdfplumber
    except Exception:
        return None


def extract_text_pdfplumber(
    pdf_path: str, pdfplumber_module=None, max_pages: Optional[int] = 20
) -> Dict[str, Any]:
    pdfplumber_module = pdfplumber_module or _load_pdfplumber()
    if pdfplumber_module is None:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    parts = []
    try:
        with pdfplumber_module.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                if max_pages is not None and idx >= max_pages:
                    break
                page_text = _safe_text(page.extract_text() if hasattr(page, "extract_text") else "")
                if page_text:
                    parts.append(page_text)
    except Exception:
        return {"text": "", "needs_ocr": True, "garbled_ratio": 1.0}

    text = "\n".join(parts).strip()
    garbled_ratio = _estimate_garbled_ratio(text)
    return {
        "text": text,
        "needs_ocr": len(text) <= 200 or garbled_ratio >= 0.10,
        "garbled_ratio": garbled_ratio,
    }


def _text_quality_score(text: str) -> float:
    value = _safe_text(text)
    if not value:
        return -1.0

    garbled = _estimate_garbled_ratio(value)
    # Prioritize longer and cleaner text while preventing huge-length bias.
    return min(len(value), 12000) * (1.0 - min(garbled, 0.9))


def extract_text_best_effort(pdf_path: str) -> Dict[str, Any]:
    primary = extract_text_pymupdf(pdf_path)
    primary_text = _safe_text(primary.get("text"))
    if len(primary_text) >= 1800 and float(primary.get("garbled_ratio") or 1.0) < 0.08:
        return {
            "text": primary_text,
            "needs_ocr": bool(primary.get("needs_ocr")),
            "garbled_ratio": float(primary.get("garbled_ratio") or 1.0),
            "engine": "pymupdf",
        }

    candidates: List[Tuple[str, Dict[str, Any]]] = [
        ("pymupdf", primary),
        ("pypdf", extract_text_pypdf(pdf_path)),
        ("pdfium", extract_text_pdfium(pdf_path)),
        ("pdfplumber", extract_text_pdfplumber(pdf_path)),
    ]

    best_engine = "pymupdf"
    best = candidates[0][1]
    best_score = _text_quality_score(_safe_text(best.get("text")))

    for engine, result in candidates[1:]:
        score = _text_quality_score(_safe_text(result.get("text")))
        if score > best_score:
            best_engine = engine
            best = result
            best_score = score

    selected_text = _safe_text(best.get("text"))
    return {
        "text": selected_text,
        "needs_ocr": bool(best.get("needs_ocr")),
        "garbled_ratio": float(best.get("garbled_ratio") or 1.0),
        "engine": best_engine,
    }


def run_ocr_branch(
    pdf_path: str,
    ocr_callable: Callable[[bytes, int], str],
    fitz_module=None,
    max_pages: Optional[int] = None,
) -> str:
    fitz_module = fitz_module or _load_fitz()
    texts: List[str] = []

    if fitz_module is not None:
        try:
            with fitz_module.open(pdf_path) as doc:
                for idx, page in enumerate(doc):
                    if max_pages is not None and idx >= max_pages:
                        break
                    pix = page.get_pixmap(dpi=150)
                    png_bytes = pix.tobytes("png")
                    page_text = ocr_callable(png_bytes, idx + 1)
                    texts.append(_safe_text(page_text))
            return "\n".join([t for t in texts if t]).strip()
        except Exception:
            texts = []

    pdfium_module = _load_pdfium()
    if pdfium_module is None:
        return ""

    try:
        doc = pdfium_module.PdfDocument(pdf_path)
    except Exception:
        return ""

    try:
        for idx, page in enumerate(doc):
            if max_pages is not None and idx >= max_pages:
                break
            try:
                bitmap = page.render(scale=150 / 72.0)
                image = bitmap.to_pil()
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                png_bytes = buf.getvalue()
            except Exception:
                continue
            page_text = ocr_callable(png_bytes, idx + 1)
            texts.append(_safe_text(page_text))
    except Exception:
        return ""

    return "\n".join([t for t in texts if t]).strip()


def _extract_json_blob(raw_text: str) -> Optional[str]:
    if not raw_text:
        return None

    text = raw_text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None


def _match_category_name(categories: List[str], candidate: str) -> Optional[str]:
    chosen = _safe_text(candidate)
    if not chosen:
        return None
    if chosen in categories:
        return chosen

    normalized = re.sub(r"\s+", "", chosen).lower()
    if not normalized:
        return None

    for category in categories:
        cat_norm = re.sub(r"\s+", "", category).lower()
        if normalized == cat_norm:
            return category
    for category in categories:
        cat_norm = re.sub(r"\s+", "", category).lower()
        if normalized in cat_norm or cat_norm in normalized:
            return category
    return None


def _normalize_recommended_categories(raw_value: Any, categories: List[str], max_count: int = 3) -> List[str]:
    if not categories:
        return []

    candidates: List[str] = []
    if isinstance(raw_value, list):
        candidates = [_safe_text(item) for item in raw_value]
    elif isinstance(raw_value, str):
        text = _safe_text(raw_value)
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                candidates = [_safe_text(item) for item in parsed]
        if not candidates and text:
            parts = [p.strip() for p in re.split(r"[,，/|；;\n]+", text) if p.strip()]
            candidates = parts if parts else [text]

    out: List[str] = []
    seen = set()
    for candidate in candidates:
        matched = _match_category_name(categories, candidate)
        if not matched or matched in seen:
            continue
        seen.add(matched)
        out.append(matched)
        if len(out) >= max_count:
            break
    return out


def _recommend_categories_with_llm(
    categories: List[str],
    title: str,
    text: str,
    max_count: int = 3,
    classification_guidance: str = "",
) -> List[str]:
    if not categories:
        return []
    if not _has_dashscope_key():
        return categories[:1]

    prompt = (
        "从给定候选分类中，选择最适合该论文的1-3项分类（按相关性降序）。\n"
        "如果提供了classification_guidance，必须优先遵守该规则。\n"
        "仅返回JSON数组，数组元素必须是候选分类名。"
    )
    payload = {
        "title": _safe_text(title),
        "text_content": _safe_text(text),
        "categories": categories,
        "max_count": max_count,
        "classification_guidance": _safe_text(classification_guidance),
    }
    messages = [_to_anthropic_message("user", prompt + "\n\n" + json.dumps(payload, ensure_ascii=False))]
    chosen = _call_qwen_text(
        messages=messages,
        model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
        system_prompt="你是论文分类助手。",
        max_tokens=240,
        temperature=0,
        timeout=60,
        retries=3,
    )
    normalized = _normalize_recommended_categories(chosen, categories, max_count=max_count)
    if normalized:
        return normalized
    return categories[:1]


def _normalize_llm_result(
    data: Dict[str, Any],
    categories: List[str],
    classification_guidance: str = "",
) -> Dict[str, Any]:
    recommended_categories = _normalize_recommended_categories(
        data.get("recommended_categories"),
        categories,
    )
    if not recommended_categories:
        recommended_categories = _normalize_recommended_categories(
            data.get("recommended_category"),
            categories,
        )

    authors = data.get("authors")
    if not isinstance(authors, list):
        authors = []

    year_raw = data.get("year")
    try:
        year = int(year_raw) if year_raw is not None else None
    except Exception:
        year = None

    title = _safe_text(data.get("title"))
    abstract_original = _safe_text(data.get("abstract_original"))
    summary = _safe_text(data.get("summary_one_line"))
    if not recommended_categories and categories:
        recommended_categories = _recommend_categories_with_llm(
            categories,
            title,
            abstract_original + "\n" + summary,
            classification_guidance=classification_guidance,
        )

    recommended = recommended_categories[0] if recommended_categories else ""

    return {
        "title": title,
        "authors": [str(a).strip() for a in authors if str(a).strip()],
        "year": year,
        "publisher": _safe_text(data.get("publisher")),
        "doi": _safe_text(data.get("doi")),
        "abstract_original": abstract_original,
        "abstract_zh": _safe_text(data.get("abstract_zh")),
        "summary_one_line": summary,
        "recommended_categories": recommended_categories,
        "recommended_category": recommended,
    }


def llm_extract_metadata(
    text: str,
    hints: Dict[str, Any],
    categories: List[str],
    llm_callable: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> Dict[str, Any]:
    classification_guidance = _safe_text(hints.get("_classification_guidance"))

    def _finalize(data: Dict[str, Any]) -> Dict[str, Any]:
        base = _normalize_llm_result(data, categories, classification_guidance=classification_guidance)
        return _postprocess_metadata_result(
            base,
            text,
            hints,
            categories,
            classification_guidance=classification_guidance,
        )

    if llm_callable is None:
        return _finalize(
            _fallback_extract(text, hints, categories, classification_guidance=classification_guidance)
        )

    payload = {
        "text": text,
        "hints": hints,
        "categories": categories,
    }
    focused_text = _build_metadata_text_for_llm(text)
    if focused_text and focused_text != text:
        payload["text"] = focused_text

    raw_retry_env = _safe_text(os.getenv("LLM_METADATA_RETRIES", "3"))
    try:
        max_attempts = max(1, min(5, int(raw_retry_env)))
    except ValueError:
        max_attempts = 3

    for attempt in range(max_attempts):
        raw = llm_callable(payload)
        if isinstance(raw, dict):
            return _finalize(raw)

        blob = _extract_json_blob(_safe_text(raw))
        if blob:
            try:
                parsed = json.loads(blob)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                return _finalize(parsed)

        if attempt < max_attempts - 1:
            retry_hints = dict(hints)
            retry_hints["_retry_note"] = "Previous output was not valid JSON; return strict JSON only."
            payload = {
                "text": focused_text or text,
                "hints": retry_hints,
                "categories": categories,
            }
            time.sleep(min(3.0, 1.0 + attempt))

    return _finalize(
        _fallback_extract(text, hints, categories, classification_guidance=classification_guidance)
    )


def _extract_year(text: str) -> Optional[int]:
    matches = re.findall(r"\b(19\d{2}|20\d{2})\b", text)
    for value in matches:
        year = int(value)
        if 1900 <= year <= 2100:
            return year
    return None


def _extract_doi(text: str) -> str:
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", text)
    return _safe_text(match.group(0)) if match else ""


def _extract_abstract(text: str) -> str:
    source = _safe_text(text)
    if not source:
        return ""

    patterns = [
        re.compile(
            r"(?is)\babstract\b[\s:：-]*(.+?)(?:\n\s*(?:keywords?|index terms?|jel classification|introduction|1[\.\s]+introduction)\b)",
        ),
        re.compile(
            r"(?is)\babstract\b[\s:：-]*(.+?)(?:\n\s*(?:\d+\s*[\.、)]\s*[A-Za-z].{0,30}\n))",
        ),
    ]
    for pattern in patterns:
        match = pattern.search(source)
        if match:
            abstract = _safe_text(match.group(1))
            if abstract:
                return abstract[:8000]

    # Fall back to a short head excerpt instead of dumping full body text.
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    if not lines:
        return ""
    joined = " ".join(lines[:40]).strip()
    return joined[:2000]


def _compact_abstract_excerpt(text: str, max_chars: int = 14000) -> str:
    source = _safe_text(text)
    if not source:
        return ""
    low = source.lower()
    idx = low.find("abstract")
    if idx >= 0:
        start = max(0, idx - 1200)
        end = min(len(source), idx + max_chars)
        return source[start:end]
    idx_cn = source.find("摘要")
    if idx_cn >= 0:
        start = max(0, idx_cn - 1000)
        end = min(len(source), idx_cn + max_chars)
        return source[start:end]
    return source[:max_chars]


def _build_metadata_text_for_llm(text: str, max_chars: int = 52000) -> str:
    source = _safe_text(text)
    if not source:
        return ""
    if len(source) <= max_chars:
        return source

    sections: List[str] = []
    head = source[:12000]
    if head:
        sections.append(head)

    abstract_window = _compact_abstract_excerpt(source, max_chars=18000)
    if abstract_window:
        sections.append(abstract_window)

    lower = source.lower()
    for marker in ("conclusion", "conclusions", "discussion", "summary", "结论"):
        idx = lower.find(marker)
        if idx >= 0:
            start = max(0, idx - 1000)
            end = min(len(source), idx + 9000)
            sections.append(source[start:end])
            break

    tail = source[-12000:]
    if tail:
        sections.append(tail)

    deduped: List[str] = []
    seen = set()
    for segment in sections:
        cleaned = _safe_text(segment)
        if not cleaned:
            continue
        key = re.sub(r"\s+", "", cleaned[:800]).casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)

    merged = "\n\n---\n\n".join(deduped).strip()
    if len(merged) <= max_chars:
        return merged

    keep_head = merged[: max_chars // 2]
    keep_tail = merged[-(max_chars // 2) :]
    return (keep_head + "\n\n---\n\n" + keep_tail).strip()


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", _safe_text(text)))


def _translate_to_chinese_with_qwen(text: str) -> str:
    source = _safe_text(text)
    if not source:
        return ""
    if _contains_chinese(source):
        return source
    if not _has_dashscope_key():
        return ""

    # Bound input length and use smaller chunks to keep translation calls stable.
    source = source[:3200]
    chunks = _split_for_llm(source, chunk_size=1800)
    if not chunks:
        return ""

    translated_chunks: List[str] = []
    for idx, chunk in enumerate(chunks):
        prompt = (
            "Translate the text to accurate Simplified Chinese.\n"
            "Keep academic meaning precise, preserve proper nouns and key terms.\n"
            "Return Chinese text only, no explanation."
        )
        payload = {
            "chunk_index": idx + 1,
            "chunk_total": len(chunks),
            "source_text": chunk,
        }
        messages = [_to_anthropic_message("user", prompt + "\n\n" + json.dumps(payload, ensure_ascii=False))]
        out = _call_qwen_text(
            messages=messages,
            model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
            system_prompt="You are an academic translator.",
            max_tokens=1800,
            temperature=0.05,
            timeout=35,
            retries=1,
        )
        if out:
            translated_chunks.append(out)
        else:
            translated_chunks.append("")

    merged = "\n".join([_safe_text(chunk) for chunk in translated_chunks if _safe_text(chunk)]).strip()
    return merged


def _extract_abstract_with_qwen(title: str, text: str, candidate_abstract: str = "") -> str:
    if not _has_dashscope_key():
        return ""
    excerpt = _compact_abstract_excerpt(text, max_chars=18000)
    payload = {
        "title": _safe_text(title),
        "candidate_abstract_en": _safe_text(candidate_abstract),
        "paper_text_excerpt": excerpt,
    }
    prompt = (
        "You extract abstract text from an academic paper excerpt.\n"
        "Priority: if an explicit Abstract section exists, preserve its source language content.\n"
        "If missing, synthesize a faithful abstract-like paragraph from the excerpt (120-260 words).\n"
        "Return STRICT JSON only: {\"abstract_en\":\"...\"}."
    )
    messages = [_to_anthropic_message("user", prompt + "\n\n" + json.dumps(payload, ensure_ascii=False))]
    raw = _call_qwen_text(
        messages=messages,
        model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
        system_prompt="You are a strict academic abstract extractor. Return JSON only.",
        max_tokens=1400,
        temperature=0.05,
        timeout=55,
        retries=2,
    )
    blob = _extract_json_blob(raw)
    if not blob:
        return ""
    try:
        parsed = json.loads(blob)
    except Exception:
        return ""
    if not isinstance(parsed, dict):
        return ""
    return _safe_text(parsed.get("abstract_en"))


def _summary_from_chinese_text(text: str, max_len: int = 220) -> str:
    value = re.sub(r"\s+", " ", _safe_text(text)).strip()
    if not value:
        return ""
    sentence = re.split(r"(?<=[。！？])\s*", value, maxsplit=1)[0].strip()
    if sentence:
        return sentence[:max_len]
    return value[:max_len]


def _fallback_summary_zh(abstract_zh: str, abstract_original: str, title: str) -> str:
    zh = _summary_from_chinese_text(abstract_zh, max_len=220)
    if _valid_summary_zh_text(zh):
        return zh
    source = _summary_from_chinese_text(abstract_original, max_len=220)
    if _valid_summary_zh_text(source):
        return source
    return ""


def _generate_summary_zh_with_qwen(title: str, abstract_text: str, category: str) -> str:
    if not _has_dashscope_key():
        return ""

    source = _safe_text(abstract_text)
    if not source:
        return ""

    prompt = (
        "请基于摘要生成一句中文总结。\n"
        "要求：20-90字，完整句；包含研究对象/方法或核心贡献之一；禁止模板化套话。"
    )
    payload = {
        "title": _safe_text(title),
        "category": _safe_text(category),
        "abstract_or_text": source,
    }
    messages = [_to_anthropic_message("user", prompt + "\n\n" + json.dumps(payload, ensure_ascii=False))]
    summary = _call_qwen_text(
        messages=messages,
        model=os.getenv("QWEN_MODEL", "qwen3.5-plus"),
        system_prompt="你是学术内容通俗化助手。",
        max_tokens=420,
        temperature=0.1,
        timeout=40,
        retries=2,
    )
    sentence = _summary_from_chinese_text(summary, max_len=220)
    if not _valid_summary_zh_text(sentence):
        return ""
    return sentence


def _postprocess_metadata_result(
    result: Dict[str, Any],
    text: str,
    hints: Dict[str, Any],
    categories: List[str],
    classification_guidance: str = "",
) -> Dict[str, Any]:
    def _looks_like_metadata_dump(value: str) -> bool:
        txt = _safe_text(value)
        if not txt:
            return False
        low = txt.lower()
        markers = [
            "title:",
            "summary (zh):",
            "abstract (zh):",
            "abstract (original):",
            "categories:",
            "category:",
        ]
        return any(marker in low for marker in markers)

    def _normalize_summary_line(value: str, limit: int = 220) -> str:
        src = re.sub(r"\s+", " ", _safe_text(value)).strip()
        if not src:
            return ""
        sentence = re.split(r"(?<=[。！？])\s*", src, maxsplit=1)[0].strip()
        if sentence:
            return sentence[:limit]
        return src[:limit]

    merged = dict(result)
    title = _safe_text(merged.get("title"))
    if _looks_like_bad_title(title):
        candidate = _safe_text(hints.get("_filename_title")) or _safe_text(hints.get("title"))
        if candidate:
            merged["title"] = candidate
            title = candidate

    if not title:
        merged["title"] = _guess_title_from_text(text) or _safe_text(hints.get("_filename_title"))
        title = _safe_text(merged.get("title"))

    abstract_original = _safe_text(merged.get("abstract_original"))
    if not abstract_original or _contains_template_fallback(abstract_original):
        abstract_original = _extract_abstract(text)
    abstract_original = _normalize_extracted_text(abstract_original)
    if _looks_like_metadata_dump(abstract_original) or _contains_template_fallback(abstract_original):
        abstract_original = ""
    if _contains_coded_artifacts(abstract_original):
        abstract_original = _qwen_clean_text(abstract_original, hints)

    text_is_metadata_dump = _looks_like_metadata_dump(_safe_text(text[:1800]))
    if _looks_bad_abstract_original(abstract_original, title):
        abstract_from_text = _normalize_extracted_text(_extract_abstract(text))
        if abstract_from_text and not _looks_bad_abstract_original(abstract_from_text, title):
            abstract_original = abstract_from_text

    if _looks_bad_abstract_original(abstract_original, title) and len(_safe_text(text)) >= 600 and not text_is_metadata_dump:
        llm_abstract = _normalize_extracted_text(_extract_abstract_with_qwen(title, text, abstract_original))
        if llm_abstract and not _looks_bad_abstract_original(llm_abstract, title):
            abstract_original = llm_abstract

    # Guardrail: abstract_original should stay in source language when title is non-Chinese.
    if _contains_chinese(abstract_original) and not _contains_chinese(title):
        abstract_from_text = _normalize_extracted_text(_extract_abstract(text))
        if abstract_from_text and not _contains_chinese(abstract_from_text):
            abstract_original = abstract_from_text
    merged["abstract_original"] = abstract_original

    recommended_categories = _normalize_recommended_categories(
        merged.get("recommended_categories"),
        categories,
    )
    if not recommended_categories:
        recommended_categories = _normalize_recommended_categories(
            merged.get("recommended_category"),
            categories,
        )
    if not recommended_categories and categories:
        recommended_categories = _recommend_categories_with_llm(
            categories,
            title,
            abstract_original or text,
            classification_guidance=classification_guidance,
        )
    merged["recommended_categories"] = recommended_categories
    merged["recommended_category"] = recommended_categories[0] if recommended_categories else ""
    recommended = merged["recommended_category"]

    abstract_zh = _safe_text(merged.get("abstract_zh"))
    if not _valid_abstract_zh_text(abstract_zh):
        abstract_zh = _translate_to_chinese_with_qwen(abstract_original)
        if not _valid_abstract_zh_text(abstract_zh) and _contains_chinese(abstract_original):
            abstract_zh = abstract_original
        merged["abstract_zh"] = abstract_zh
    if abstract_zh and (not _contains_chinese(abstract_zh) or _contains_template_fallback(abstract_zh)):
        retried = _translate_to_chinese_with_qwen(abstract_original)
        if _valid_abstract_zh_text(retried):
            abstract_zh = retried
            merged["abstract_zh"] = abstract_zh

    summary = _safe_text(merged.get("summary_one_line"))
    if not _valid_summary_zh_text(summary):
        summary_source = _safe_text(abstract_zh) or abstract_original or text
        summary = _generate_summary_zh_with_qwen(title, summary_source, recommended)
    if not _valid_summary_zh_text(summary):
        summary = _fallback_summary_zh(abstract_zh, abstract_original, title)
    merged["summary_one_line"] = _normalize_summary_line(summary, limit=220)

    final_summary = _safe_text(merged.get("summary_one_line"))
    if not _valid_summary_zh_text(final_summary):
        final_summary = _summary_from_chinese_text(abstract_zh, max_len=220)
        merged["summary_one_line"] = final_summary if _valid_summary_zh_text(final_summary) else ""

    final_zh = _safe_text(merged.get("abstract_zh"))
    if not _valid_abstract_zh_text(final_zh) and _contains_chinese(abstract_original):
        merged["abstract_zh"] = abstract_original

    return _normalize_llm_result(
        merged,
        categories,
        classification_guidance=classification_guidance,
    )


def _guess_title_from_text(text: str) -> str:
    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines()[:40]]
    for line in lines:
        if not line:
            continue
        if len(line) < 12 or len(line) > 260:
            continue
        low = line.lower()
        if low.startswith(("http", "doi", "arxiv", "keywords", "abstract", "received", "accepted")):
            continue
        if re.fullmatch(r"[\d\W_]+", line):
            continue
        return line
    return _safe_text(lines[0] if lines else "")


def _guess_summary(text: str, fallback_title: str) -> str:
    source = _safe_text(text)
    if not source:
        return _safe_text(fallback_title[:160])
    first_sentence = re.split(r"(?<=[\.\!\?。！？])\s+", source, maxsplit=1)[0]
    first_sentence = _safe_text(first_sentence)
    if first_sentence:
        return first_sentence[:200]
    return source[:200]


def _guess_authors_from_text(text: str, title: str) -> List[str]:
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title_low = title.lower()
    for line in lines[:20]:
        low = line.lower()
        if title_low and low == title_low:
            continue
        if len(line) > 140:
            continue
        if re.search(r"\b(university|department|journal|abstract|keywords?)\b", low):
            continue
        if "," in line:
            parts = [item.strip() for item in line.split(",") if item.strip()]
            if 1 <= len(parts) <= 8:
                return parts
    return []


def _fallback_extract(
    text: str,
    hints: Dict[str, Any],
    categories: List[str],
    classification_guidance: str = "",
) -> Dict[str, Any]:
    title = _safe_text(hints.get("title"))
    filename_title = _safe_text(hints.get("_filename_title"))
    if _looks_like_bad_title(title):
        title = filename_title
    authors = hints.get("authors") if isinstance(hints.get("authors"), list) else []
    if not title:
        title = _guess_title_from_text(text)
    if _looks_like_bad_title(title) and filename_title:
        title = filename_title
    if not authors:
        authors = _guess_authors_from_text(text, title)

    if not title:
        first_line = _safe_text(text.splitlines()[0] if text else "")
        title = first_line[:200]

    year = hints.get("year") if isinstance(hints.get("year"), int) else None
    if year is None:
        year = _extract_year(_safe_text(text[:4000]))

    abstract = _extract_abstract(text)
    summary = _guess_summary(abstract or text, title)
    doi = _extract_doi(_safe_text(text[:8000]))
    publisher = _safe_text(hints.get("subject") or hints.get("creator"))
    recommended_categories = _recommend_categories_with_llm(
        categories,
        title,
        abstract or text,
        classification_guidance=classification_guidance,
    )
    recommended = recommended_categories[0] if recommended_categories else ""

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "publisher": publisher,
        "doi": doi,
        "abstract_original": abstract,
        "abstract_zh": "",
        "summary_one_line": summary,
        "recommended_categories": recommended_categories,
        "recommended_category": recommended,
    }


def _compose_readable_text_from_metadata(result: Dict[str, Any], hints: Dict[str, Any]) -> str:
    title = _safe_text(result.get("title") or hints.get("title") or hints.get("_filename_title"))
    authors = result.get("authors") if isinstance(result.get("authors"), list) else []
    year = result.get("year")
    recommended_categories = result.get("recommended_categories")
    if not isinstance(recommended_categories, list):
        recommended_categories = []
    category = _safe_text(result.get("recommended_category"))
    if not category and recommended_categories:
        category = _safe_text(recommended_categories[0])
    abstract_original = _safe_text(result.get("abstract_original"))
    abstract_zh = _safe_text(result.get("abstract_zh"))
    summary = _safe_text(result.get("summary_one_line"))

    lines = []
    if title:
        lines.append("Title: {}".format(title))
    if authors:
        lines.append("Authors: {}".format(", ".join([_safe_text(a) for a in authors if _safe_text(a)])))
    if year:
        lines.append("Year: {}".format(year))
    if recommended_categories:
        joined = ", ".join([_safe_text(item) for item in recommended_categories if _safe_text(item)])
        if joined:
            lines.append("Categories: {}".format(joined))
    elif category:
        lines.append("Category: {}".format(category))
    if summary:
        lines.append("")
        lines.append("Summary (ZH):")
        lines.append(summary)
    if abstract_zh:
        lines.append("")
        lines.append("Abstract (ZH):")
        lines.append(abstract_zh)
    if abstract_original:
        lines.append("")
        lines.append("Abstract (Original):")
        lines.append(abstract_original)

    return "\n".join(lines).strip()


def write_pipeline_result(
    db,
    paper_id: int,
    job_id: int,
    result_dict: Dict[str, Any],
    user_id: Optional[int] = None,
    text_cache_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
) -> None:
    rec_names = result_dict.get("recommended_categories")
    if isinstance(rec_names, list):
        requested_names = [_safe_text(name) for name in rec_names if _safe_text(name)]
    else:
        requested_names = []
    if not requested_names:
        single = _safe_text(result_dict.get("recommended_category"))
        if single:
            requested_names = [single]

    category_ids: List[int] = []
    for name in requested_names:
        if user_id is None:
            category_row = db.execute(
                "SELECT id FROM categories WHERE name = ? ORDER BY id ASC LIMIT 1",
                (name,),
            ).fetchone()
        else:
            category_row = db.execute(
                "SELECT id FROM categories WHERE user_id = ? AND name = ? ORDER BY id ASC LIMIT 1",
                (int(user_id), name),
            ).fetchone()
        if category_row is None:
            continue
        category_id = int(category_row["id"])
        if category_id not in category_ids:
            category_ids.append(category_id)
    primary_category_id = category_ids[0] if category_ids else None

    db.execute(
        """
        UPDATE papers
        SET title = ?, authors = ?, year = ?, publisher = ?, doi = ?,
            abstract_original = ?, abstract_zh = ?, summary_one_line = ?,
            category_id = ?,
            is_quarantined = 0,
            quarantine_reason = NULL,
            file_path = COALESCE(?, file_path),
            text_cache_path = COALESCE(?, text_cache_path)
        WHERE id = ?
        """,
        (
            _safe_text(result_dict.get("title")),
            json.dumps(result_dict.get("authors") or [], ensure_ascii=False),
            result_dict.get("year"),
            _safe_text(result_dict.get("publisher")),
            _safe_text(result_dict.get("doi")),
            _safe_text(result_dict.get("abstract_original")),
            _safe_text(result_dict.get("abstract_zh")),
            _safe_text(result_dict.get("summary_one_line")),
            primary_category_id,
            pdf_path,
            text_cache_path,
            paper_id,
        ),
    )
    set_paper_categories(db, paper_id, category_ids)

    if user_id is None:
        db.execute(
            "UPDATE processing_jobs SET status = ?, error_msg = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("done", job_id),
        )
    else:
        db.execute(
            "UPDATE processing_jobs SET status = ?, error_msg = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            ("done", job_id, int(user_id)),
        )

    if user_id is None:
        db.execute(
            """
            INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "upload",
                "paper",
                paper_id,
                json.dumps({"job_id": job_id, "result": "pipeline_done"}, ensure_ascii=False),
                "success",
                "upload pipeline completed",
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO system_logs (user_id, operation, entity_type, entity_id, detail, status, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                "upload",
                "paper",
                paper_id,
                json.dumps({"job_id": job_id, "result": "pipeline_done"}, ensure_ascii=False),
                "success",
                "upload pipeline completed",
            ),
        )
    db.commit()


def _find_duplicate_paper(
    db,
    current_paper_id: int,
    title: str,
    full_text: str,
    user_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    if user_id is None:
        rows = db.execute(
            """
            SELECT id, title, text_cache_path, abstract_original
            FROM papers
            WHERE id <> ?
            ORDER BY id ASC
            """,
            (current_paper_id,),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT id, title, text_cache_path, abstract_original
            FROM papers
            WHERE id <> ? AND user_id = ?
            ORDER BY id ASC
            """,
            (current_paper_id, int(user_id)),
        ).fetchall()
    if not rows:
        return None

    normalized_title = _normalize_title_for_duplicate_check(title)
    if normalized_title:
        for row in rows:
            if _normalize_title_for_duplicate_check(row["title"]) == normalized_title:
                return {"paper_id": row["id"], "reason": "title_exact", "similarity": 1.0}

    normalized_current_text = _normalize_text_for_duplicate_check(full_text)
    min_chars = _get_duplicate_text_min_chars()
    if len(normalized_current_text) < min_chars:
        return None

    current_ngrams = _char_ngrams(normalized_current_text, n=5)
    if not current_ngrams:
        return None

    threshold = _get_duplicate_text_similarity_threshold()
    best_match: Optional[Dict[str, Any]] = None

    for row in rows:
        existing_text = _read_text_cache(row["text_cache_path"])
        if not existing_text:
            existing_text = _safe_text(row["abstract_original"])
        normalized_existing_text = _normalize_text_for_duplicate_check(existing_text)
        if len(normalized_existing_text) < min_chars:
            continue

        similarity = _jaccard_similarity(current_ngrams, _char_ngrams(normalized_existing_text, n=5))
        if similarity >= threshold and (best_match is None or similarity > float(best_match["similarity"])):
            best_match = {
                "paper_id": row["id"],
                "reason": "text_similarity",
                "similarity": similarity,
            }

    return best_match


def _mark_duplicate_and_skip(
    db,
    paper_id: int,
    job_id: int,
    duplicate_info: Dict[str, Any],
    pdf_path: Optional[str],
    text_cache_path: Optional[str],
    user_id: Optional[int] = None,
) -> None:
    duplicate_paper_id = int(duplicate_info["paper_id"])
    reason = _safe_text(duplicate_info.get("reason")) or "unknown"
    similarity = duplicate_info.get("similarity")
    message = "重复论文，已跳过（已存在 #{}）".format(duplicate_paper_id)
    detail: Dict[str, Any] = {
        "job_id": job_id,
        "result": "duplicate_skipped",
        "duplicate_paper_id": duplicate_paper_id,
        "reason": reason,
    }
    if isinstance(similarity, (int, float)):
        detail["similarity"] = round(float(similarity), 4)

    if user_id is None:
        db.execute(
            """
            UPDATE processing_jobs
            SET paper_id = ?, status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (duplicate_paper_id, "skipped", message, job_id),
        )
        db.execute(
            """
            UPDATE processing_jobs
            SET paper_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE paper_id = ? AND paper_id <> ?
            """,
            (duplicate_paper_id, paper_id, duplicate_paper_id),
        )
        db.execute(
            """
            UPDATE chat_attachments
            SET paper_id = ?
            WHERE paper_id = ? AND paper_id <> ?
            """,
            (duplicate_paper_id, paper_id, duplicate_paper_id),
        )
        db.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        db.execute(
            """
            INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "upload",
                "paper",
                duplicate_paper_id,
                json.dumps(detail, ensure_ascii=False),
                "success",
                "upload skipped duplicate paper",
            ),
        )
    else:
        db.execute(
            """
            UPDATE processing_jobs
            SET paper_id = ?, status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (duplicate_paper_id, "skipped", message, job_id, int(user_id)),
        )
        db.execute(
            """
            UPDATE processing_jobs
            SET paper_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE paper_id = ? AND user_id = ? AND paper_id <> ?
            """,
            (duplicate_paper_id, paper_id, int(user_id), duplicate_paper_id),
        )
        db.execute(
            """
            UPDATE chat_attachments
            SET paper_id = ?
            WHERE paper_id = ? AND user_id = ? AND paper_id <> ?
            """,
            (duplicate_paper_id, paper_id, int(user_id), duplicate_paper_id),
        )
        db.execute("DELETE FROM papers WHERE id = ? AND user_id = ?", (paper_id, int(user_id)))
        db.execute(
            """
            INSERT INTO system_logs (user_id, operation, entity_type, entity_id, detail, status, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                "upload",
                "paper",
                duplicate_paper_id,
                json.dumps(detail, ensure_ascii=False),
                "success",
                "upload skipped duplicate paper",
            ),
        )
    db.commit()
    _safe_remove_file(pdf_path)
    _safe_remove_file(text_cache_path)


def _fetch_category_names(db, user_id: Optional[int] = None) -> List[str]:
    if user_id is None:
        rows = db.execute("SELECT name FROM categories ORDER BY order_index ASC, id ASC").fetchall()
    else:
        rows = db.execute(
            "SELECT name FROM categories WHERE user_id = ? ORDER BY order_index ASC, id ASC",
            (int(user_id),),
        ).fetchall()
    return [row["name"] for row in rows]


def _to_anthropic_message(role: str, text: str) -> Dict[str, Any]:
    return {"role": role, "content": [{"type": "text", "text": text}]}


def default_ocr_callable(image_bytes: bytes, page_no: int) -> str:
    if not _safe_text(os.getenv("DASHSCOPE_API_KEY", "")):
        return ""

    encoded = base64.b64encode(image_bytes).decode("ascii")
    user_text = (
        "You are an OCR engine.\n"
        "Read the page image and output plain text only.\n"
        "Keep formulas and table text as-is when possible.\n"
        "Page: {}\n".format(page_no)
    )
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": encoded,
                    },
                },
            ],
        }
    ]

    model = os.getenv("QWEN_VL_MODEL", "qwen-vl-plus")
    for attempt in range(4):
        response = dashscope_client.call_messages(
            messages=messages,
            model=model,
            system_prompt="Return OCR text only.",
            max_tokens=2048,
            temperature=0,
            timeout=90,
        )
        text = _safe_text(dashscope_client.extract_text(response))
        if text:
            return text
        if attempt < 3:
            time.sleep(min(6.0, (1.6 ** attempt) + random.random()))
    return ""


def default_llm_callable(payload: Dict[str, Any]) -> str:
    text = _safe_text(payload.get("text"))
    hints = payload.get("hints") if isinstance(payload.get("hints"), dict) else {}
    categories = payload.get("categories") if isinstance(payload.get("categories"), list) else []
    classification_guidance = _safe_text(hints.get("_classification_guidance"))
    focused_text = _build_metadata_text_for_llm(text)

    instruction = (
        "You are processing extracted PDF text for an academic paper database.\n"
        "Return STRICT JSON only with fields:\n"
        "title, authors, year, publisher, doi, abstract_original, abstract_zh, summary_one_line, recommended_categories.\n"
        "Rules:\n"
        "1) Repair obvious extraction artifacts if present (e.g., /C67/C111 style encoding noise).\n"
        "2) authors must be a JSON array of names.\n"
        "3) year must be integer or null.\n"
        "4) abstract_original: prioritize the original Abstract section in source language; if missing, generate a faithful abstract-like synthesis.\n"
        "5) abstract_zh: accurate Chinese translation of abstract_original.\n"
        "6) summary_one_line: readable Chinese summary in one sentence (20-90 Chinese chars preferred), including object/method or key contribution.\n"
        "7) recommended_categories must be a JSON array with 1-3 items chosen from provided categories.\n"
        "8) If classification_guidance is provided, strictly follow it for category selection.\n"
        "9) Never output placeholder or template statements."
    )
    public_hints = dict(hints)
    public_hints.pop("_classification_guidance", None)
    public_hints.pop("_filename_title", None)
    user_content = {
        "hints": public_hints,
        "categories": categories,
        "classification_guidance": classification_guidance,
        "paper_text": focused_text,
        "full_text_length": len(text),
    }

    messages = [
        _to_anthropic_message("user", instruction + "\n\n" + json.dumps(user_content, ensure_ascii=False))
    ]
    model = os.getenv("QWEN_MODEL", "qwen3.5-plus")
    response = dashscope_client.call_messages(
        messages=messages,
        model=model,
        system_prompt="You are a precise academic paper information extractor and text cleaner.",
        max_tokens=3600,
        temperature=0.05,
        timeout=90,
    )
    return dashscope_client.extract_text(response)


def process_pdf_job(
    db_path: str,
    paper_id: int,
    job_id: int,
    pdf_path: str,
    user_id: Optional[int] = None,
    ocr_callable: Optional[Callable[[bytes, int], str]] = None,
    llm_callable: Optional[Callable[[Dict[str, Any]], Any]] = None,
    texts_dir: Optional[str] = None,
) -> None:
    texts_dir = texts_dir or os.getenv("APP_TEXTS_DIR", "/var/www/data/texts")
    os.makedirs(texts_dir, exist_ok=True)
    use_default_ocr = ocr_callable is None
    if ocr_callable is None:
        ocr_callable = default_ocr_callable
    if llm_callable is None:
        llm_callable = default_llm_callable

    with connect_db(db_path) as db:
        try:
            if user_id is None:
                db.execute(
                    "UPDATE processing_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    ("processing", job_id),
                )
            else:
                db.execute(
                    "UPDATE processing_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                    ("processing", job_id, int(user_id)),
                )
            db.commit()

            hints = extract_pdf_metadata_hints(pdf_path)
            filename_hints = extract_filename_hints(pdf_path)
            filename_title = _safe_text(filename_hints.get("title"))
            if filename_title:
                hints["_filename_title"] = filename_title
            for key, value in filename_hints.items():
                if key == "authors":
                    if not hints.get("authors"):
                        hints["authors"] = value
                elif key == "title":
                    if not _safe_text(hints.get("title")) or _looks_like_bad_title(_safe_text(hints.get("title"))):
                        hints["title"] = value
                elif not hints.get(key):
                    hints[key] = value
            hints["_classification_guidance"] = get_setting_value(
                db,
                CLASSIFICATION_GUIDANCE_KEY,
                default=DEFAULT_CLASSIFICATION_GUIDANCE,
                user_id=user_id,
            )

            step1 = extract_text_best_effort(pdf_path)
            raw_text = _safe_text(step1.get("text"))
            text, qwen_suggests_ocr = _prepare_text_with_qwen_guardrail(raw_text, hints)

            if text:
                tables_md = extract_tables_pdfplumber(pdf_path)
                if tables_md:
                    merged = (text + "\n\n" + tables_md).strip()
                    text, _ = _prepare_text_with_qwen_guardrail(merged, hints)

            needs_ocr = bool(step1.get("needs_ocr")) or qwen_suggests_ocr or not text
            if needs_ocr:
                can_ocr = True
                if (
                    use_default_ocr
                    and ocr_callable is default_ocr_callable
                    and getattr(ocr_callable, "__name__", "") == "default_ocr_callable"
                    and not _safe_text(os.getenv("DASHSCOPE_API_KEY", ""))
                ):
                    can_ocr = False
                ocr_text = run_ocr_branch(pdf_path, ocr_callable, max_pages=20) if can_ocr else ""
                ocr_text, _ = _prepare_text_with_qwen_guardrail(ocr_text, hints)
                if _text_quality_score(ocr_text) > _text_quality_score(text):
                    text = ocr_text
            if not _safe_text(text):
                raise RuntimeError("No readable text extracted from PDF (native parse + OCR both failed).")

            categories = _fetch_category_names(db, user_id=user_id)
            result = llm_extract_metadata(text=text, hints=hints, categories=categories, llm_callable=llm_callable)
            if not _safe_text(text):
                synthesized = _compose_readable_text_from_metadata(result, hints)
                if synthesized:
                    text = synthesized
            text_cache_path = os.path.join(
                texts_dir,
                os.path.splitext(os.path.basename(pdf_path))[0] + ".txt",
            )

            duplicate_info = _find_duplicate_paper(
                db,
                current_paper_id=paper_id,
                title=_safe_text(result.get("title")),
                full_text=text,
                user_id=user_id,
            )
            if duplicate_info is not None:
                _mark_duplicate_and_skip(
                    db,
                    paper_id=paper_id,
                    job_id=job_id,
                    duplicate_info=duplicate_info,
                    pdf_path=pdf_path,
                    text_cache_path=text_cache_path,
                    user_id=user_id,
                )
                return

            with open(text_cache_path, "w", encoding="utf-8") as f:
                f.write(text)
            write_pipeline_result(
                db,
                paper_id=paper_id,
                job_id=job_id,
                result_dict=result,
                user_id=user_id,
                text_cache_path=text_cache_path,
                pdf_path=pdf_path,
            )
        except Exception as exc:
            quarantine_reason = str(exc)
            filename_title = _safe_text(os.path.splitext(os.path.basename(pdf_path))[0])
            if user_id is None:
                db.execute(
                    """
                    UPDATE papers
                    SET is_quarantined = 1,
                        quarantine_reason = ?,
                        title = CASE WHEN title IS NULL OR trim(title) = '' THEN ? ELSE title END
                    WHERE id = ?
                    """,
                    (quarantine_reason, filename_title, paper_id),
                )
            else:
                db.execute(
                    """
                    UPDATE papers
                    SET is_quarantined = 1,
                        quarantine_reason = ?,
                        title = CASE WHEN title IS NULL OR trim(title) = '' THEN ? ELSE title END
                    WHERE id = ? AND user_id = ?
                    """,
                    (quarantine_reason, filename_title, paper_id, int(user_id)),
                )
            if user_id is None:
                db.execute(
                    "UPDATE processing_jobs SET status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    ("error", str(exc), job_id),
                )
                db.execute(
                    """
                    INSERT INTO system_logs (operation, entity_type, entity_id, detail, status, message)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "upload",
                        "paper",
                        paper_id,
                        json.dumps({"job_id": job_id, "error": str(exc)}, ensure_ascii=False),
                        "error",
                        "upload pipeline failed",
                    ),
                )
            else:
                db.execute(
                    "UPDATE processing_jobs SET status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                    ("error", str(exc), job_id, int(user_id)),
                )
                db.execute(
                    """
                    INSERT INTO system_logs (user_id, operation, entity_type, entity_id, detail, status, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(user_id),
                        "upload",
                        "paper",
                        paper_id,
                        json.dumps({"job_id": job_id, "error": str(exc)}, ensure_ascii=False),
                        "error",
                        "upload pipeline failed",
                    ),
                )
            db.commit()
            raise
