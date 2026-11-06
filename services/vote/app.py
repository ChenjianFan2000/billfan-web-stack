"""旦口喜剧投票站：独立 FastAPI 服务，单进程 SSE 与 SQLite 持久化。"""

from __future__ import annotations

import asyncio
import math
import secrets
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt
from starlette.background import BackgroundTask

from .core import (
    ADMIN_SECONDS,
    SESSION_SECONDS,
    Config,
    DomainError,
    VoteStore,
    compact,
    now_ms,
)


TOKEN_COOKIE = "vote_token"
ADMIN_COOKIE = "vote_admin"
STATIC_DIR = Path(__file__).with_name("static")
MAX_BODY = 65536


class SessionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tokens: list[str] = Field(default_factory=list, max_length=8)
    fingerprint: str | None = Field(default=None, max_length=128)
    fingerprintVersion: str = Field(default="v1", max_length=20)
    fingerprintQualified: StrictBool = False
    identityHint: str | None = Field(default=None, max_length=100)
    recoveryCode: str | None = Field(default=None, max_length=200)


class VotePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voted: StrictBool
    epoch: StrictInt = Field(ge=0)
    requestId: str = Field(min_length=8, max_length=128)


class MessagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=200)
    requestId: str = Field(min_length=8, max_length=128)


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=1024)


class SafetyMiddleware:
    """限制实际请求体大小，拒绝跨站写入，并统一安全和缓存响应头。"""

    def __init__(self, app: Any, config: Config):
        self.app = app
        self.config = config

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        headers = {key.decode("latin1").lower(): value.decode("latin1") for key, value in scope["headers"]}

        async def secure_send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                output_headers = list(message.get("headers", []))
                extra = {
                    b"x-content-type-options": b"nosniff",
                    b"referrer-policy": b"no-referrer",
                    b"x-frame-options": b"DENY",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                    b"content-security-policy": b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
                }
                if path.startswith("/api/") or path.startswith("/admin"):
                    extra[b"cache-control"] = b"no-store"
                    extra[b"x-robots-tag"] = b"noindex, nofollow"
                elif path in {"/", "/players", "/index.html", "/players.html"} or path.endswith((".js", ".css")):
                    extra[b"cache-control"] = b"no-cache"
                output_headers = [(key, value) for key, value in output_headers if key.lower() not in extra]
                output_headers.extend(extra.items())
                message["headers"] = output_headers
            await send(message)

        async def reject(status: int, code: str, message: str) -> None:
            response = JSONResponse({"error": {"code": code, "message": message}}, status_code=status)
            await response(scope, receive, secure_send)

        write = scope["method"] in {"POST", "PUT", "PATCH", "DELETE"} and path.startswith("/api/")
        if write:
            origin = headers.get("origin", "").rstrip("/")
            if (origin and origin not in self.config.allowed_origins) or headers.get("sec-fetch-site") == "cross-site":
                await reject(403, "origin_forbidden", "请在本站页面内操作。")
                return
            if headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                await reject(415, "json_required", "请求必须使用 JSON 格式。")
                return
            try:
                declared_length = int(headers.get("content-length", "0"))
            except ValueError:
                await reject(400, "invalid_length", "请求长度无效。")
                return
            if declared_length > MAX_BODY or declared_length < 0:
                await reject(413, "body_too_large", "请求内容过大。")
                return
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > MAX_BODY:
                    await reject(413, "body_too_large", "请求内容过大。")
                    return
                if not message.get("more_body", False):
                    break
            delivered = False

            async def limited_receive() -> dict[str, Any]:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, limited_receive, secure_send)
            return
        await self.app(scope, receive, secure_send)


@dataclass
class Subscriber:
    id: str
    user_id: str
    admin: bool
    queue: asyncio.Queue[str | None]


class EventHub:
    def __init__(self, store: VoteStore):
        self.store = store
        self.clients: dict[str, Subscriber] = {}
        self.sequence = 0

    def frame(self, name: str, data: Any) -> str:
        self.sequence += 1
        return f"id: {self.store.stream_id}:{self.sequence}\nevent: {name}\ndata: {compact(data)}\n\n"

    def subscribe(self, user_id: str, admin: bool = False) -> Subscriber:
        if len(self.clients) >= self.store.config.max_connections:
            raise DomainError(503, "stream_capacity", "当前连接较多，正在尝试重新连接。", retryAfterMs=10000)
        own_count = sum(1 for client in self.clients.values() if client.user_id == user_id and client.admin == admin)
        if own_count >= 8:
            raise DomainError(429, "stream_limit", "同一身份打开的页面过多，请关闭部分页面。", retryAfterMs=10000)
        client = Subscriber(secrets.token_urlsafe(10), user_id, admin, asyncio.Queue(maxsize=16))
        self.clients[client.id] = client
        return client

    def unsubscribe(self, client_id: str) -> None:
        self.clients.pop(client_id, None)

    def publish(self, name: str, payload: Any, *, audience: str = "public", user_id: str | None = None) -> None:
        frame = self.frame(name, payload)
        for client in list(self.clients.values()):
            if audience == "public" and client.admin:
                continue
            if audience == "admin" and not client.admin:
                continue
            if user_id is not None and (client.user_id != user_id or client.admin):
                continue
            if client.queue.full():
                while not client.queue.empty():
                    client.queue.get_nowait()
                client.queue.put_nowait(self.frame("resync", {"reason": "slow_client"}))
                client.queue.put_nowait(None)
                self.unsubscribe(client.id)
            else:
                client.queue.put_nowait(frame)

    def shutdown(self) -> None:
        for client in list(self.clients.values()):
            while not client.queue.empty():
                client.queue.get_nowait()
            client.queue.put_nowait(self.frame("resync", {"reason": "server_restart"}))
            client.queue.put_nowait(None)
        self.clients.clear()

    def disconnect_admin(self, session_id: str) -> None:
        for client in list(self.clients.values()):
            if not client.admin or client.user_id != session_id:
                continue
            while not client.queue.empty():
                client.queue.get_nowait()
            client.queue.put_nowait(self.frame("resync", {"reason": "admin_logout"}))
            client.queue.put_nowait(None)
            self.unsubscribe(client.id)


class Runtime:
    def __init__(self, store: VoteStore):
        self.store = store
        self.hub = EventHub(store)
        self.pending_messages: list[dict[str, Any]] = []
        self.admin_dirty = False
        self.public_dirty = False

    async def pump(self) -> None:
        next_messages = time.monotonic() + 0.8
        next_counts = time.monotonic() + 3
        while True:
            await asyncio.sleep(0.2)
            current = time.monotonic()
            if current >= next_messages:
                if self.pending_messages:
                    self.hub.publish("messages", {"messages": self.pending_messages}, audience="public")
                    self.pending_messages = []
                next_messages = current + 0.8
            if current >= next_counts:
                if self.admin_dirty:
                    self.hub.publish("admin_state", self.store.state(admin=True), audience="admin")
                if self.public_dirty:
                    self.hub.publish("counts", self.store.public_counts(), audience="public")
                self.admin_dirty = False
                self.public_dirty = False
                next_counts = current + 3

    def after_vote(self, result: dict[str, Any]) -> None:
        self.hub.publish("me", result["me"], user_id=result["me"]["id"])
        if not result["replayed"]:
            self.admin_dirty = True
            if self.store.contestants[result["contestantId"]]["published"]:
                self.public_dirty = True

    def after_message(self, result: dict[str, Any]) -> None:
        if not result["replayed"]:
            self.pending_messages.append(result["message"])
            self.admin_dirty = True

    def after_admin(self, effects: dict[str, Any]) -> None:
        if not effects:
            return
        if "deletedId" in effects:
            message_id = effects["deletedId"]
            self.pending_messages = [item for item in self.pending_messages if item["id"] != message_id]
            self.hub.publish("message_deleted", {"id": message_id})
        if "message" in effects:
            self.hub.publish("messages", {"messages": [effects["message"]]})
        if "banUserId" in effects:
            user_id = effects["banUserId"]
            self.hub.publish("me", self.store.me(user_id), user_id=user_id)
        # 管理台同步优先；控制变更在事务提交后立即发出，不等待节流批次。
        self.hub.publish("admin_state", self.store.state(admin=True), audience="admin")
        self.admin_dirty = False
        self.hub.publish("state", self.store.state(), audience="public")
        self.public_dirty = False


def create_app(config: Config | None = None) -> FastAPI:
    active_config = config or Config.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        store = VoteStore(active_config)
        runtime = Runtime(store)
        application.state.vote = runtime
        application.state.store = store
        application.state.hub = runtime.hub
        task = asyncio.create_task(runtime.pump(), name="vote-sse-batches")
        try:
            yield
        finally:
            runtime.hub.shutdown()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            store.close()

    application = FastAPI(title="旦口喜剧投票服务", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    application.add_middleware(SafetyMiddleware, config=active_config)

    @application.exception_handler(DomainError)
    async def domain_error(_: Request, error: DomainError) -> JSONResponse:
        details = dict(error.extra)
        state = details.pop("state", None)
        content: dict[str, Any] = {"error": {"code": error.code, "message": error.message, **details}}
        if state is not None:
            content["state"] = state
        headers = {}
        if "retryAfterMs" in error.extra:
            headers["Retry-After"] = str(max(1, math.ceil(error.extra["retryAfterMs"] / 1000)))
        return JSONResponse(content, status_code=error.status, headers=headers)

    @application.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        # 不把管理员密码、token 或原始提交内容回显到错误响应。
        return JSONResponse({"error": {"code": "invalid_input", "message": "提交内容格式不正确，请刷新页面后重试。"}}, status_code=422)

    def runtime(request: Request) -> Runtime:
        return request.app.state.vote

    def viewer(request: Request) -> tuple[str, str]:
        authorization = request.headers.get("authorization", "")
        token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else request.cookies.get(TOKEN_COOKIE)
        user_id = runtime(request).store.authenticate(token)
        if user_id is None:
            raise DomainError(401, "session_required", "正在恢复观众身份，请重新连接。")
        return user_id, token

    def administrator(request: Request) -> tuple[str, str]:
        token = request.cookies.get(ADMIN_COOKIE)
        session_id = runtime(request).store.authenticate_admin(token)
        if session_id is None:
            raise DomainError(401, "admin_required", "管理凭证已失效，请使用管理链接重新进入。")
        return session_id, token

    @application.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "service": "dankou-vote", "version": 1}

    @application.post("/api/session")
    async def session(payload: SessionPayload, request: Request, response: Response) -> dict[str, Any]:
        result = runtime(request).store.establish_session(payload.model_dump(), request.cookies.get(TOKEN_COOKIE))
        response.set_cookie(TOKEN_COOKIE, result["token"], max_age=SESSION_SECONDS, httponly=True, secure=active_config.secure_cookie, samesite="lax", path="/")
        return result

    @application.get("/api/snapshot")
    async def snapshot(request: Request) -> dict[str, Any]:
        user_id, _ = viewer(request)
        return runtime(request).store.snapshot(user_id)

    @application.put("/api/votes/{contestant_id}")
    async def vote(contestant_id: str, payload: VotePayload, request: Request) -> dict[str, Any]:
        user_id, _ = viewer(request)
        current = runtime(request)
        result = current.store.vote(user_id, contestant_id, payload.model_dump())
        current.after_vote(result)
        return result

    @application.post("/api/messages")
    async def message(payload: MessagePayload, request: Request) -> dict[str, Any]:
        user_id, _ = viewer(request)
        current = runtime(request)
        result = current.store.send_message(user_id, payload.model_dump())
        current.after_message(result)
        return result

    def event_response(request: Request, user_id: str, token: str, *, admin: bool = False) -> StreamingResponse:
        current = runtime(request)
        client = current.hub.subscribe(user_id, admin=admin)

        async def stream():
            try:
                initial = current.store.state(admin=True) if admin else current.store.snapshot(user_id)
                yield "retry: 2000\n" + current.hub.frame("admin_state" if admin else "snapshot", initial)
                while True:
                    try:
                        frame = await asyncio.wait_for(client.queue.get(), timeout=25)
                    except asyncio.TimeoutError:
                        frame = current.hub.frame("heartbeat", {"serverTime": now_ms()})
                    if frame is None:
                        return
                    valid = current.store.authenticate_admin(token) if admin else current.store.authenticate(token)
                    if not valid:
                        yield current.hub.frame("resync", {"reason": "session_expired"})
                        return
                    yield frame
            finally:
                current.hub.unsubscribe(client.id)

        return StreamingResponse(
            stream(), media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
            background=BackgroundTask(current.hub.unsubscribe, client.id),
        )

    @application.get("/api/events")
    async def events(request: Request) -> StreamingResponse:
        user_id, token = viewer(request)
        return event_response(request, user_id, token)

    @application.post("/api/admin/session")
    async def admin_session(payload: LoginPayload, request: Request, response: Response) -> dict[str, Any]:
        current = runtime(request)
        address = request.client.host if request.client else "unknown"
        token = current.store.login_admin(payload.password, address)
        response.set_cookie(ADMIN_COOKIE, token, max_age=ADMIN_SECONDS, httponly=True, secure=active_config.secure_cookie, samesite="strict", path="/api/admin")
        return {"ok": True, "state": current.store.state(admin=True)}

    @application.post("/api/admin/logout")
    async def admin_logout(request: Request, response: Response) -> dict[str, bool]:
        session_id, token = administrator(request)
        current = runtime(request)
        current.store.revoke_admin(token)
        current.hub.disconnect_admin(session_id)
        response.delete_cookie(ADMIN_COOKIE, path="/api/admin", secure=active_config.secure_cookie, httponly=True, samesite="strict")
        return {"ok": True}

    @application.get("/api/admin/state")
    async def admin_state(request: Request) -> dict[str, Any]:
        administrator(request)
        return runtime(request).store.state(admin=True)

    @application.post("/api/admin/action")
    async def admin_action(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        session_id, _ = administrator(request)
        current = runtime(request)
        result, effects = current.store.admin_action(session_id, payload)
        current.after_admin(effects)
        return result

    @application.get("/api/admin/events")
    async def admin_events(request: Request) -> StreamingResponse:
        session_id, token = administrator(request)
        return event_response(request, session_id, token, admin=True)

    @application.get("/api/admin/export")
    async def admin_export(request: Request) -> Response:
        administrator(request)
        return Response(runtime(request).store.results_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="dankou-vote-results.csv"'})

    @application.get("/admin", include_in_schema=False)
    async def admin_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "admin.html")

    @application.get("/players", include_in_schema=False)
    async def players_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "players.html")

    application.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True, check_dir=False), name="vote-static")
    return application


app = create_app()
