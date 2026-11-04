import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import dashscope_client

router = APIRouter(prefix="/api/aimath", tags=["aimath"])

_BASE_DIR = Path("/var/www")
_CONTENT_DIR = _BASE_DIR / "services" / "paper-visualizer" / "paper_visualizer" / "backend" / "content"
_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")

_CHAT_SYSTEM_TEMPLATE = """You are a mathematical tutor helping a graduate student
understand a research paper in computational finance. The student has a solid
background in measure-theoretic probability and stochastic calculus but is new
to this specific paper.

Answer in {lang_name}. Keep math in LaTeX ($..$ or $$..$$). When referencing
the proof, cite specific theorem, lemma, or section numbers. Never invent
references. If the student asks about a part of the paper you don't have
context for, say so. Keep answers focused; one question at a time.

PAPER: {title}

ABSTRACT: {abstract}

MAIN THEOREMS (statements):
{theorems}

{section_context}
"""


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_md(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _normalize_slug(slug: str) -> str:
    value = (slug or "").strip()
    if not _SLUG_RE.match(value):
        raise HTTPException(status_code=404, detail="paper not found")
    return value


def _index_payload() -> Dict[str, Any]:
    path = _CONTENT_DIR / "papers.json"
    if not path.exists():
        return {"generated_at": "", "papers": []}
    return _load_json(path)


def _tags_payload() -> Dict[str, Any]:
    path = _CONTENT_DIR / "tags.json"
    if not path.exists():
        return {"domains": {}, "math_tools": {}}
    return _load_json(path)


def _paper_meta(slug: str) -> Dict[str, Any]:
    safe_slug = _normalize_slug(slug)
    path = _CONTENT_DIR / safe_slug / "meta.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="paper not found: {}".format(safe_slug))
    return _load_json(path)


def _paper_detail(slug: str) -> Dict[str, Any]:
    safe_slug = _normalize_slug(slug)
    meta = _paper_meta(safe_slug)
    return {
        "meta": meta,
        "content": {
            "zh": _load_md(_CONTENT_DIR / safe_slug / "zh.md"),
            "en": _load_md(_CONTENT_DIR / safe_slug / "en.md"),
        },
    }


def _chat_models() -> List[str]:
    candidates = [
        (os.getenv("AIMATH_MODEL", "") or "").strip(),
        (os.getenv("QWEN_MODEL", "") or "").strip(),
        (os.getenv("AIMATH_FALLBACK_MODEL", "") or "").strip(),
        "qwen3.5-plus",
    ]
    models: List[str] = []
    seen = set()
    for item in candidates:
        if not item or item in seen:
            continue
        models.append(item)
        seen.add(item)
    return models


def _chat_model() -> str:
    return _chat_models()[0]


def _chat_key_ready() -> bool:
    return bool((os.getenv("DASHSCOPE_API_KEY", "") or "").strip())


def _paper_tex(slug: str) -> str:
    tex_path = _CONTENT_DIR / _normalize_slug(slug) / "source.tex"
    if not tex_path.exists():
        return ""
    try:
        text = tex_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if len(text) > 60000:
        text = text[:60000] + "\n... [truncated]"
    return text


def _theorems_text(meta: Dict[str, Any]) -> str:
    parts: List[str] = []
    for theorem in meta.get("main_theorems", []) or []:
        if not isinstance(theorem, dict):
            continue
        theorem_id = str(theorem.get("id") or "").strip()
        statement_tex = str(theorem.get("statement_tex") or "").strip()
        if not theorem_id or not statement_tex:
            continue
        parts.append("- [{}]: {}".format(theorem_id, statement_tex[:400]))
    return "\n".join(parts) or "(none)"


def _lang_name(lang: str) -> str:
    return "Chinese (中文)" if lang == "zh" else "English"


class AimathChatMessage(BaseModel):
    role: str = Field(..., min_length=1, max_length=20)
    content: str = Field(..., min_length=1, max_length=4000)


class AimathChatRequest(BaseModel):
    paper_slug: str = Field(..., min_length=1, max_length=80)
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[AimathChatMessage] = Field(default_factory=list)
    lang: str = Field(default="zh", regex="^(zh|en)$")
    current_section: Optional[str] = Field(default=None, max_length=240)


@router.get("/health")
def aimath_health() -> Dict[str, Any]:
    papers = _index_payload().get("papers", [])
    return {"status": "ok", "papers_count": len(papers)}


@router.get("/papers")
def aimath_papers() -> Dict[str, Any]:
    return _index_payload()


@router.get("/papers/{slug}")
def aimath_paper_detail(slug: str) -> Dict[str, Any]:
    return _paper_detail(slug)


@router.get("/tags")
def aimath_tags() -> Dict[str, Any]:
    return _tags_payload()


def _chat_event_stream(payload: AimathChatRequest) -> Iterator[bytes]:
    detail = _paper_detail(payload.paper_slug)
    meta = detail["meta"]
    tex_body = _paper_tex(payload.paper_slug)
    section_context = ""
    if payload.current_section:
        section_context = "The student is currently reading section: {}".format(payload.current_section)

    system_prompt = _CHAT_SYSTEM_TEMPLATE.format(
        lang_name=_lang_name(payload.lang),
        title=(meta.get("title") or {}).get("en") or payload.paper_slug,
        abstract=((meta.get("abstract") or {}).get("tex") or "")[:3000],
        theorems=_theorems_text(meta),
        section_context=section_context,
    )
    if tex_body:
        system_prompt = "{}\nFull paper source (truncated):\n{}".format(system_prompt, tex_body)

    history_messages: List[Dict[str, Any]] = []
    for item in payload.history[-20:]:
        role = (item.role or "").strip().lower()
        if role not in {"user", "assistant"}:
            continue
        history_messages.append({"role": role, "content": item.content})
    history_messages.append({"role": "user", "content": payload.message})

    if not _chat_key_ready():
        err = json.dumps({"message": "LLM API key is not configured (DASHSCOPE_API_KEY missing)"}, ensure_ascii=False)
        yield "event: error\ndata: {}\n\n".format(err).encode("utf-8")
        return

    try:
        attempted_models: List[str] = []
        text = ""
        for model in _chat_models():
            attempted_models.append(model)
            response = dashscope_client.call_messages(
                messages=history_messages,
                model=model,
                system_prompt=system_prompt,
                max_tokens=2200,
                temperature=0.35,
                timeout=120,
            )
            if not response:
                continue
            text = dashscope_client.extract_text(response).strip()
            if text:
                break

        if not text:
            err = json.dumps(
                {
                    "message": "chat upstream returned empty response for configured models: {}".format(
                        ", ".join(attempted_models)
                    )
                },
                ensure_ascii=False,
            )
            yield "event: error\ndata: {}\n\n".format(err).encode("utf-8")
            return

        chunk_size = 120
        for i in range(0, len(text), chunk_size):
            part = text[i : i + chunk_size]
            payload_text = json.dumps({"text": part}, ensure_ascii=False)
            yield "event: token\ndata: {}\n\n".format(payload_text).encode("utf-8")
        yield b"event: done\ndata: {}\n\n"
    except Exception as exc:
        err = json.dumps({"message": str(exc)}, ensure_ascii=False)
        yield "event: error\ndata: {}\n\n".format(err).encode("utf-8")


@router.post("/chat")
def aimath_chat(payload: AimathChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _chat_event_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
