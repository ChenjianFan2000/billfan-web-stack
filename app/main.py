import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.aimath import router as aimath_router
from app.agent import router as agent_router
from app.auth import router as auth_router
from app.categories import router as categories_router
from app.db import init_db
from app.export import router as export_router
from app.papers import router as papers_router
from app.settings import router as settings_router
from app.upload import router as upload_router

_AIMATH_ORIGINS = [
    "https://aimath.billfan.cn",
    "http://aimath.billfan.cn",
]


def _cors_origins():
    raw = os.getenv("CORS_ORIGINS", "")
    if not raw:
        return ["*"]
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    for origin in _AIMATH_ORIGINS:
        if origin not in origins:
            origins.append(origin)
    return origins


def _aimath_host(request: Request) -> bool:
    host = (request.headers.get("host", "") or "").split(":", 1)[0].strip().lower()
    return host == "aimath.billfan.cn"


def _rewrite_aimath_api_path(path: str) -> str:
    if path == "/api/health":
        return "/api/aimath/health"
    if path == "/api/papers":
        return "/api/aimath/papers"
    if path == "/api/tags":
        return "/api/aimath/tags"
    if path == "/api/chat":
        return "/api/aimath/chat"
    if path.startswith("/api/papers/"):
        return "/api/aimath" + path[len("/api") :]
    return ""


def create_app() -> FastAPI:
    app = FastAPI(title="其华的论文管理小助手", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _aimath_api_dispatch(request: Request, call_next):
        if _aimath_host(request):
            current_path = request.scope.get("path", "") or ""
            new_path = _rewrite_aimath_api_path(current_path)
            if new_path:
                request.scope["path"] = new_path
                request.scope["raw_path"] = new_path.encode("utf-8")
        return await call_next(request)

    app.include_router(aimath_router)
    app.include_router(auth_router)
    app.include_router(categories_router)
    app.include_router(papers_router)
    app.include_router(upload_router)
    app.include_router(agent_router)
    app.include_router(export_router)
    app.include_router(settings_router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
