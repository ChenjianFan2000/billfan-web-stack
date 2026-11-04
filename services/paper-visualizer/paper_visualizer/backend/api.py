"""FastAPI JSON API for the paper visualizer.

Endpoints:
  GET  /api/health
  GET  /api/papers
  GET  /api/papers/{slug}
  GET  /api/tags
  POST /api/chat   (SSE stream)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from paper_visualizer.backend import prompts, schemas, vector_client

CONTENT_DIR = Path(__file__).resolve().parent / "content"
ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


def _chat_model() -> str:
    return os.environ.get("PAPER_VISUALIZER_CHAT_MODEL", "claude-sonnet-4-6")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_md(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def create_app() -> FastAPI:
    app = FastAPI(title="Paper Visualizer API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=schemas.HealthResponse)
    def health() -> schemas.HealthResponse:
        idx = CONTENT_DIR / "papers.json"
        if not idx.exists():
            return schemas.HealthResponse(status="not_ingested", papers_count=0)
        data = _load_json(idx)
        return schemas.HealthResponse(
            status="ok", papers_count=len(data.get("papers", []))
        )

    @app.get("/api/papers")
    def list_papers() -> dict:
        idx = CONTENT_DIR / "papers.json"
        if not idx.exists():
            return {"generated_at": "", "papers": []}
        return _load_json(idx)

    @app.get("/api/papers/{slug}")
    def paper_detail(slug: str) -> dict:
        meta_path = CONTENT_DIR / slug / "meta.json"
        if not meta_path.exists():
            raise HTTPException(status_code=404, detail=f"paper not found: {slug}")
        meta = _load_json(meta_path)
        return {
            "meta": meta,
            "content": {
                "zh": _load_md(CONTENT_DIR / slug / "zh.md"),
                "en": _load_md(CONTENT_DIR / slug / "en.md"),
            },
        }

    @app.get("/api/tags")
    def tags() -> dict:
        tags_path = CONTENT_DIR / "tags.json"
        if not tags_path.exists():
            return {"domains": {}, "math_tools": {}}
        return _load_json(tags_path)

    @app.post("/api/chat")
    def chat(req: schemas.ChatRequest) -> StreamingResponse:
        meta_path = CONTENT_DIR / req.paper_slug / "meta.json"
        if not meta_path.exists():
            raise HTTPException(
                status_code=404, detail=f"paper not found: {req.paper_slug}"
            )
        meta = _load_json(meta_path)

        # Prefer the bundled source tex (shipped with the repo), fall back to
        # the absolute/relative path recorded at ingest time (dev mode).
        bundled = CONTENT_DIR / req.paper_slug / "source.tex"
        tex_body = ""
        if bundled.exists():
            try:
                tex_body = bundled.read_text(encoding="utf-8", errors="replace")
            except OSError:
                tex_body = ""
        if not tex_body:
            tex_path = ROOT / meta["source"]["tex_path"]
            try:
                tex_body = tex_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                tex_body = ""
        if len(tex_body) > 60_000:
            tex_body = tex_body[:60_000] + "\n... [truncated]"

        theorems_fmt = "\n".join(
            f"- [{t['id']}]: {t['statement_tex'][:400]}"
            for t in meta.get("main_theorems", [])
        ) or "(none)"

        section_context = (
            f"\nThe student is currently reading section: {req.current_section}\n"
            if req.current_section
            else ""
        )

        system = (
            prompts.CHAT_SYSTEM_TEMPLATE.format(
                lang_name="Chinese (中文)" if req.lang == "zh" else "English",
                title=meta["title"].get("en", req.paper_slug),
                abstract=meta["abstract"]["tex"][:3000],
                theorems=theorems_fmt,
                section_context=section_context,
            )
            + f"\nFull paper source (truncated):\n{tex_body}"
        )

        messages: list[dict] = [{"role": "system", "content": system}]
        for h in req.history[-20:]:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": req.message})

        def event_stream() -> Iterator[bytes]:
            try:
                for token in vector_client.chat_stream(
                    model=_chat_model(),
                    messages=messages,
                    temperature=0.4,
                    max_tokens=4000,
                ):
                    payload = json.dumps({"text": token}, ensure_ascii=False)
                    yield f"event: token\ndata: {payload}\n\n".encode("utf-8")
                yield b"event: done\ndata: {}\n\n"
            except Exception as e:
                err = json.dumps({"message": str(e)}, ensure_ascii=False)
                yield f"event: error\ndata: {err}\n\n".encode("utf-8")

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # Serve bundled per-paper assets (source.pdf, source.tex) under /content/.
    app.mount(
        "/content",
        StaticFiles(directory=str(CONTENT_DIR)),
        name="content",
    )

    if FRONTEND_DIST.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIST), html=True),
            name="frontend",
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "paper_visualizer.backend.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
