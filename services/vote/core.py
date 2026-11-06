"""持久化与领域规则；所有计票判断都在同一 SQLite 事务中完成。"""

from __future__ import annotations

import csv
import fcntl
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{8,128}$")
SESSION_SECONDS = 400 * 24 * 60 * 60
ADMIN_SECONDS = 12 * 60 * 60
MAX_CONTESTANTS = 200
MAX_MESSAGE_LENGTH = 80


def now_ms() -> int:
    return int(time.time() * 1000)


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class Config:
    db_path: str
    admin_password: str
    secret_key: str
    secure_cookie: bool = True
    allowed_origins: tuple[str, ...] = ("https://vote.billfan.cn",)
    fingerprint_recovery: bool = True
    vote_interval_ms: int = 800
    message_interval_ms: int = 5000
    title: str = "旦口喜剧大赛"
    max_connections: int = 5000

    @classmethod
    def from_env(cls) -> "Config":
        def enabled(key: str, default: str = "true") -> bool:
            return os.getenv(key, default).lower() in {"1", "true", "yes", "on"}

        return cls(
            db_path=os.getenv("VOTE_DB_PATH", "data/vote.sqlite3"),
            admin_password=os.getenv("VOTE_ADMIN_PASSWORD", ""),
            secret_key=os.getenv("VOTE_SECRET_KEY", ""),
            secure_cookie=enabled("VOTE_COOKIE_SECURE"),
            allowed_origins=tuple(
                origin.strip().rstrip("/")
                for origin in os.getenv("VOTE_ALLOWED_ORIGINS", "https://vote.billfan.cn").split(",")
                if origin.strip()
            ),
            fingerprint_recovery=enabled("VOTE_FINGERPRINT_RECOVERY"),
            vote_interval_ms=max(100, int(os.getenv("VOTE_VOTE_INTERVAL_MS", "800"))),
            message_interval_ms=max(1000, int(os.getenv("VOTE_MESSAGE_INTERVAL_MS", "5000"))),
            title=os.getenv("VOTE_EVENT_TITLE", "旦口喜剧大赛")[:80],
            max_connections=max(16, int(os.getenv("VOTE_MAX_CONNECTIONS", "5000"))),
        )

    def validate(self) -> None:
        if len(self.admin_password) < 16:
            raise RuntimeError("VOTE_ADMIN_PASSWORD 必须至少 16 字符，不能使用空密码。")
        if len(self.secret_key) < 32:
            raise RuntimeError("VOTE_SECRET_KEY 必须至少 32 字符，并持久保存在服务器环境配置中。")
        if not self.allowed_origins:
            raise RuntimeError("VOTE_ALLOWED_ORIGINS 不能为空。")


class DomainError(Exception):
    def __init__(self, status: int, code: str, message: str, **extra: Any):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra


class RateLimits:
    """按用户而非观众共享的出口 IP 限速。"""

    def __init__(self) -> None:
        self.last: OrderedDict[tuple[str, str], float] = OrderedDict()
        self.login_failures: dict[str, list[float]] = {}
        self.message_times: list[float] = []

    def check(self, kind: str, key: str, interval_ms: int) -> None:
        current = time.monotonic()
        previous = self.last.get((kind, key), 0)
        remaining = interval_ms - (current - previous) * 1000
        if remaining > 0:
            raise DomainError(429, "rate_limited", "操作有点快，请稍后再试。", retryAfterMs=int(remaining) + 1)

    def mark(self, kind: str, key: str) -> None:
        item = (kind, key)
        self.last[item] = time.monotonic()
        self.last.move_to_end(item)
        while len(self.last) > 100000:
            self.last.popitem(last=False)

    def check_message_load(self) -> None:
        current = time.monotonic()
        self.message_times = [stamp for stamp in self.message_times if current - stamp < 1]
        if len(self.message_times) >= 40:
            raise DomainError(429, "rate_limited", "现场弹幕较多，请稍后再发。", retryAfterMs=1200)

    def check_login(self, address: str) -> None:
        current = time.monotonic()
        recent = [stamp for stamp in self.login_failures.get(address, []) if current - stamp < 60]
        self.login_failures[address] = recent
        if len(recent) >= 8:
            raise DomainError(429, "rate_limited", "密码尝试次数较多，请一分钟后再试。", retryAfterMs=60000)

    def failed_login(self, address: str) -> None:
        self.login_failures.setdefault(address, []).append(time.monotonic())
        if len(self.login_failures) > 10000:
            current = time.monotonic()
            self.login_failures = {
                key: values for key, values in self.login_failures.items()
                if values and current - values[-1] < 60
            }


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, created_at INTEGER NOT NULL, last_seen_at INTEGER NOT NULL,
    banned_until INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 0,
    fingerprint TEXT, fingerprint_version TEXT
);
CREATE INDEX IF NOT EXISTS users_fingerprint ON users(fingerprint, fingerprint_version);
CREATE TABLE IF NOT EXISTS tokens (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS tokens_user ON tokens(user_id);
CREATE TABLE IF NOT EXISTS admin_sessions (
    token_hash TEXT PRIMARY KEY, session_id TEXT NOT NULL UNIQUE,
    expires_at INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS contestants (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, group_name TEXT NOT NULL,
    sort_order INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'upcoming'
        CHECK(status IN ('upcoming','performing','performed')),
    voting TEXT NOT NULL DEFAULT 'pending' CHECK(voting IN ('pending','open','locked')),
    epoch INTEGER NOT NULL DEFAULT 0, published INTEGER NOT NULL DEFAULT 0,
    raw_votes INTEGER NOT NULL DEFAULT 0 CHECK(raw_votes >= 0),
    adjustment_total INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS votes (
    user_id TEXT NOT NULL REFERENCES users(id),
    contestant_id TEXT NOT NULL REFERENCES contestants(id),
    selected INTEGER NOT NULL CHECK(selected IN (0,1)), updated_at INTEGER NOT NULL,
    PRIMARY KEY(user_id, contestant_id)
);
CREATE INDEX IF NOT EXISTS votes_contestant ON votes(contestant_id, selected);
CREATE TABLE IF NOT EXISTS adjustments (
    id TEXT PRIMARY KEY, contestant_id TEXT NOT NULL REFERENCES contestants(id),
    delta INTEGER NOT NULL, reason TEXT NOT NULL, public INTEGER NOT NULL,
    created_at INTEGER NOT NULL, admin_session TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS adjustments_contestant ON adjustments(contestant_id);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id), text TEXT NOT NULL,
    highlight INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL,
    deleted_at INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS messages_recent ON messages(created_at DESC);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
    admin_session TEXT NOT NULL, detail TEXT NOT NULL, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS request_dedupe (
    scope TEXT NOT NULL, request_id TEXT NOT NULL, payload_hash TEXT NOT NULL,
    result TEXT NOT NULL, created_at INTEGER NOT NULL,
    PRIMARY KEY(scope,request_id)
);
CREATE INDEX IF NOT EXISTS request_dedupe_age ON request_dedupe(created_at);
"""


class VoteStore:
    def __init__(self, config: Config):
        config.validate()
        self.config = config
        self.stream_id = secrets.token_urlsafe(12)
        self.lock = threading.RLock()
        self.limits = RateLimits()
        self.auth_cache: OrderedDict[str, tuple[str, int]] = OrderedDict()
        self.user_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._public_cached: dict[str, Any] | None = None
        self._admin_cached: dict[str, Any] | None = None
        db_path = Path(config.db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.process_lock = open(str(db_path) + ".lock", "a+")
        try:
            fcntl.flock(self.process_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.process_lock.close()
            raise RuntimeError("投票数据库已被其他进程使用；此服务必须使用单 worker。") from None
        try:
            self.db = sqlite3.connect(str(db_path), isolation_level=None, check_same_thread=False, timeout=5)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA busy_timeout=5000")
            self.db.executescript(SCHEMA)
            with self.transaction():
                for key, value in (("revision", 0), ("current_id", None), ("title", config.title)):
                    self.db.execute("INSERT OR IGNORE INTO meta(key,value) VALUES (?,?)", (key, compact(value)))
                self.db.execute("DELETE FROM tokens WHERE expires_at < ?", (now_ms(),))
                self.db.execute("DELETE FROM admin_sessions WHERE expires_at < ?", (now_ms(),))
                self.db.execute("DELETE FROM request_dedupe WHERE created_at < ?", (now_ms() - 7 * 86400000,))
            self.reload()
        except Exception:
            if hasattr(self, "db"):
                self.db.close()
            fcntl.flock(self.process_lock, fcntl.LOCK_UN)
            self.process_lock.close()
            raise

    def close(self) -> None:
        with self.lock:
            self.db.close()
            fcntl.flock(self.process_lock, fcntl.LOCK_UN)
            self.process_lock.close()

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield
                self.db.execute("COMMIT")
            except BaseException:
                self.db.execute("ROLLBACK")
                raise

    def reload(self) -> None:
        self.meta = {row["key"]: json.loads(row["value"]) for row in self.db.execute("SELECT * FROM meta")}
        self.contestants = {row["id"]: dict(row) for row in self.db.execute("SELECT * FROM contestants ORDER BY sort_order,created_at,id")}
        self.adjustments = [dict(row) for row in self.db.execute("SELECT * FROM adjustments ORDER BY created_at,id")]
        self.messages = [dict(row) for row in self.db.execute("SELECT * FROM messages ORDER BY created_at DESC,rowid DESC LIMIT 160")]
        self.audit = [dict(row) for row in self.db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")]
        self.invalidate()

    def invalidate(self, public: bool = True) -> None:
        if public:
            self._public_cached = None
        self._admin_cached = None

    @staticmethod
    def public_message(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "text": row["text"], "highlight": bool(row["highlight"]), "createdAt": row["created_at"]}

    def _contestant_view(self, row: dict[str, Any], admin: bool) -> dict[str, Any]:
        visible = admin or bool(row["published"])
        adjustments = []
        if visible:
            for item in self.adjustments:
                if item["contestant_id"] != row["id"] or (not admin and not item["public"]):
                    continue
                view = {"id": item["id"], "delta": item["delta"], "reason": item["reason"], "createdAt": item["created_at"]}
                if admin:
                    view["public"] = bool(item["public"])
                adjustments.append(view)
        result = {
            "id": row["id"], "name": row["name"], "group": row["group_name"],
            "order": row["sort_order"], "status": row["status"], "voting": row["voting"],
            "epoch": row["epoch"], "published": bool(row["published"]),
            "votes": max(0, row["raw_votes"] + row["adjustment_total"]) if visible else None,
            "adjustments": adjustments,
        }
        if admin:
            result.update(rawVotes=row["raw_votes"], adjustmentTotal=row["adjustment_total"])
        return result

    def state(self, admin: bool = False) -> dict[str, Any]:
        cached = self._admin_cached if admin else self._public_cached
        if cached is None:
            visible_messages = self.messages if admin else [row for row in self.messages if not row["deleted_at"]][:60]
            messages = []
            for row in reversed(visible_messages):
                message = self.public_message(row)
                if admin:
                    message.update(userId=row["user_id"], deleted=bool(row["deleted_at"]))
                messages.append(message)
            cached = {
                "revision": self.meta["revision"], "streamId": self.stream_id,
                "title": self.meta["title"], "currentId": self.meta["current_id"],
                "contestants": [self._contestant_view(row, admin) for row in self.contestants.values()],
                "messages": messages,
                "limits": {"voteMs": self.config.vote_interval_ms, "messageMs": self.config.message_interval_ms, "maxMessageLength": MAX_MESSAGE_LENGTH},
            }
            if admin:
                cached["audit"] = [{"id": row["id"], "action": row["action"], "detail": json.loads(row["detail"]), "createdAt": row["created_at"]} for row in self.audit]
                self._admin_cached = cached
            else:
                self._public_cached = cached
        return {**cached, "serverTime": now_ms()}

    def me(self, user_id: str) -> dict[str, Any]:
        cached = self.user_cache.get(user_id)
        if cached is None:
            row = self.db.execute("SELECT id,banned_until,version FROM users WHERE id=?", (user_id,)).fetchone()
            if row is None:
                raise DomainError(401, "session_required", "观众身份已失效，请重新连接。")
            votes = [row[0] for row in self.db.execute("SELECT contestant_id FROM votes WHERE user_id=? AND selected=1 ORDER BY contestant_id", (user_id,))]
            cached = {"id": user_id, "votes": votes, "bannedUntil": row["banned_until"], "version": row["version"]}
            self.user_cache[user_id] = cached
        self.user_cache.move_to_end(user_id)
        while len(self.user_cache) > 30000:
            self.user_cache.popitem(last=False)
        return {**cached, "votes": list(cached["votes"])}

    def snapshot(self, user_id: str) -> dict[str, Any]:
        return {**self.state(), "me": self.me(user_id)}

    def public_counts(self) -> dict[str, Any]:
        """已公布计数的紧凑增量，不携带弹幕、个人状态或隐藏调整。"""
        return {
            "revision": self.meta["revision"], "streamId": self.stream_id, "serverTime": now_ms(),
            "counts": [
                {"id": row["id"], "votes": max(0, row["raw_votes"] + row["adjustment_total"])}
                for row in self.contestants.values() if row["published"]
            ],
        }

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("ascii")).hexdigest()

    def authenticate(self, token: str | None) -> str | None:
        if not token or not TOKEN_RE.fullmatch(token):
            return None
        hashed = self.token_hash(token)
        cached = self.auth_cache.get(hashed)
        if cached is not None:
            if cached[1] > now_ms():
                self.auth_cache.move_to_end(hashed)
                return cached[0]
            self.auth_cache.pop(hashed, None)
            return None
        row = self.db.execute("SELECT user_id,expires_at FROM tokens WHERE token_hash=?", (hashed,)).fetchone()
        if row and row["expires_at"] > now_ms():
            self.auth_cache[hashed] = (row["user_id"], row["expires_at"])
            while len(self.auth_cache) > 50000:
                self.auth_cache.popitem(last=False)
            return row["user_id"]
        return None

    def establish_session(self, payload: dict[str, Any], cookie_token: str | None) -> dict[str, Any]:
        tokens = payload.get("tokens") or []
        recovery = payload.get("recoveryCode")
        fingerprint = payload.get("fingerprint")
        identity_hint = payload.get("identityHint")
        qualified = payload.get("fingerprintQualified") is True
        version = payload.get("fingerprintVersion", "v1")
        valid_fingerprint = qualified and version == "v1" and isinstance(fingerprint, str) and bool(FINGERPRINT_RE.fullmatch(fingerprint))
        # 原始指纹不落盘；加服务器专用 HMAC，不能跨站关联指纹数据。
        fingerprint_hash = hmac.new(self.config.secret_key.encode(), fingerprint.encode(), hashlib.sha256).hexdigest() if valid_fingerprint else None
        candidates = ([recovery] if recovery else []) + tokens + ([cookie_token] if cookie_token else [])
        user_id = None
        token = None
        restored = "new"
        with self.transaction():
            if recovery and not self.authenticate(recovery):
                raise DomainError(401, "invalid_recovery", "恢复链接无效或已过期，请使用原浏览器进入。")
            for candidate in candidates:
                match = self.authenticate(candidate)
                if match:
                    user_id, token = match, candidate
                    restored = "recovery" if recovery == candidate else "token"
                    break
            # 同型号手机可能具有完全相同的指纹。只有本机独立冗余保存的随机
            # 身份提示和指纹同时匹配，才能恢复；绝不能凭裸指纹合并新观众。
            if not user_id and fingerprint_hash and identity_hint and self.config.fingerprint_recovery:
                rows = self.db.execute(
                    "SELECT id FROM users WHERE id=? AND fingerprint=? AND fingerprint_version=? AND last_seen_at>? LIMIT 2",
                    (identity_hint, fingerprint_hash, version, now_ms() - 30 * 86400000),
                ).fetchall()
                if len(rows) == 1:
                    user_id = rows[0]["id"]
                    restored = "fingerprint"
            if user_id is None:
                user_id = "u_" + secrets.token_urlsafe(12)
                self.db.execute(
                    "INSERT INTO users(id,created_at,last_seen_at,fingerprint,fingerprint_version) VALUES (?,?,?,?,?)",
                    (user_id, now_ms(), now_ms(), fingerprint_hash, version if fingerprint_hash else None),
                )
            else:
                if fingerprint_hash:
                    self.db.execute("UPDATE users SET last_seen_at=?,fingerprint=?,fingerprint_version=? WHERE id=?", (now_ms(), fingerprint_hash, version, user_id))
                else:
                    self.db.execute("UPDATE users SET last_seen_at=? WHERE id=?", (now_ms(), user_id))
            if token is None:
                token = secrets.token_urlsafe(32)
                self.db.execute("INSERT INTO tokens(token_hash,user_id,created_at,expires_at) VALUES (?,?,?,?)", (self.token_hash(token), user_id, now_ms(), now_ms() + SESSION_SECONDS * 1000))
        return {"token": token, "userId": user_id, "recoveryCode": token, "restored": restored, "snapshot": self.snapshot(user_id)}

    def _dedupe(self, scope: str, request_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(request_id, str) or not REQUEST_ID_RE.fullmatch(request_id):
            raise DomainError(422, "invalid_request_id", "requestId 格式不正确。")
        hashed = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        row = self.db.execute("SELECT payload_hash,result FROM request_dedupe WHERE scope=? AND request_id=?", (scope, request_id)).fetchone()
        if row:
            if not hmac.compare_digest(row["payload_hash"], hashed):
                raise DomainError(409, "request_id_conflict", "相同请求编号不能用于不同操作。")
            return json.loads(row["result"])
        return None

    def _record_request(self, scope: str, request_id: str, payload: dict[str, Any], result: dict[str, Any]) -> None:
        hashed = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.db.execute("INSERT INTO request_dedupe(scope,request_id,payload_hash,result,created_at) VALUES (?,?,?,?,?)", (scope, request_id, hashed, compact(result), now_ms()))

    def vote(self, user_id: str, contestant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        request_id = payload["requestId"]
        normalized = {"contestantId": contestant_id, "voted": payload["voted"], "epoch": payload["epoch"]}
        scope = "vote:" + user_id
        replayed = False
        with self.transaction():
            prior = self._dedupe(scope, request_id, normalized)
            if prior is not None:
                replayed = True
            else:
                # 不依赖网页、缓存或点击时刻；取事务内行状态裁决锁票。
                row = self.db.execute("SELECT voting,epoch FROM contestants WHERE id=?", (contestant_id,)).fetchone()
                if row is None:
                    raise DomainError(404, "contestant_not_found", "这位选手不存在。")
                if row["voting"] != "open":
                    raise DomainError(409, "vote_locked", "该选手尚未开票或已经锁票。", state=self.state())
                if row["epoch"] != payload["epoch"]:
                    raise DomainError(409, "stale_epoch", "开票状态已变化，请刷新后重试。", state=self.state())
                previous = self.db.execute("SELECT selected FROM votes WHERE user_id=? AND contestant_id=?", (user_id, contestant_id)).fetchone()
                old_value = bool(previous["selected"]) if previous else False
                if old_value != payload["voted"]:
                    self.limits.check("vote", user_id, self.config.vote_interval_ms)
                    self.db.execute(
                        "INSERT INTO votes(user_id,contestant_id,selected,updated_at) VALUES (?,?,?,?) "
                        "ON CONFLICT(user_id,contestant_id) DO UPDATE SET selected=excluded.selected,updated_at=excluded.updated_at",
                        (user_id, contestant_id, int(payload["voted"]), now_ms()),
                    )
                    delta = 1 if payload["voted"] else -1
                    self.db.execute("UPDATE contestants SET raw_votes=raw_votes+? WHERE id=?", (delta, contestant_id))
                    self.db.execute("UPDATE users SET version=version+1 WHERE id=?", (user_id,))
                self._record_request(scope, request_id, normalized, {"contestantId": contestant_id})
        if not replayed and old_value != payload["voted"]:
            self.limits.mark("vote", user_id)
            self.contestants[contestant_id]["raw_votes"] += 1 if payload["voted"] else -1
            self.user_cache.pop(user_id, None)
            self.invalidate(public=bool(self.contestants[contestant_id]["published"]))
        me = self.me(user_id)
        return {"voted": contestant_id in me["votes"], "contestantId": contestant_id, "me": me, "revision": self.meta["revision"], "replayed": replayed}

    @staticmethod
    def clean_text(value: Any, maximum: int, label: str, allow_empty: bool = False) -> str:
        if not isinstance(value, str):
            raise DomainError(422, "invalid_input", f"{label}格式不正确。")
        cleaned = " ".join(value.split())
        if (not cleaned and not allow_empty) or len(cleaned) > maximum:
            raise DomainError(422, "invalid_input", f"{label}需为 1 至 {maximum} 个字符。")
        if any(ord(char) < 32 or 0x202A <= ord(char) <= 0x202E or 0x2066 <= ord(char) <= 0x2069 for char in cleaned):
            raise DomainError(422, "invalid_input", f"{label}包含不支持的控制字符。")
        return cleaned

    def _insert_message(self, text: str, user_id: str | None, highlight: bool) -> dict[str, Any]:
        row = {"id": "m_" + secrets.token_urlsafe(10), "user_id": user_id, "text": text, "highlight": int(highlight), "created_at": now_ms(), "deleted_at": 0}
        self.db.execute("INSERT INTO messages(id,user_id,text,highlight,created_at) VALUES (?,?,?,?,?)", (row["id"], user_id, text, int(highlight), row["created_at"]))
        return row

    def send_message(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        text = self.clean_text(payload["text"], MAX_MESSAGE_LENGTH, "弹幕")
        scope = "message:" + user_id
        normalized = {"text": text}
        with self.transaction():
            previous = self._dedupe(scope, payload["requestId"], normalized)
            if previous is not None:
                return {**previous, "replayed": True}
            user = self.db.execute("SELECT banned_until FROM users WHERE id=?", (user_id,)).fetchone()
            if user["banned_until"] > now_ms():
                raise DomainError(403, "message_banned", "你暂时不能发送弹幕。", bannedUntil=user["banned_until"])
            self.limits.check("message", user_id, self.config.message_interval_ms)
            self.limits.check_message_load()
            row = self._insert_message(text, user_id, False)
            result = {"message": self.public_message(row)}
            self._record_request(scope, payload["requestId"], normalized, result)
        self.limits.mark("message", user_id)
        self.limits.message_times.append(time.monotonic())
        self.messages.insert(0, row)
        self.messages = self.messages[:160]
        self.invalidate()
        return {**result, "replayed": False}

    def sign_admin(self) -> str:
        session = secrets.token_urlsafe(12)
        expires = int(time.time()) + ADMIN_SECONDS
        body = f"{session}.{expires}"
        signature = hmac.new(self.config.secret_key.encode(), body.encode(), hashlib.sha256).hexdigest()
        token = f"{body}.{signature}"
        with self.transaction():
            self.db.execute("INSERT INTO admin_sessions(token_hash,session_id,expires_at) VALUES (?,?,?)", (self.token_hash(token), session, expires * 1000))
        return token

    def authenticate_admin(self, token: str | None) -> str | None:
        if not token or len(token) > 200:
            return None
        parts = token.split(".")
        if len(parts) != 3 or not parts[1].isdigit() or len(parts[2]) != 64:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_-]{16}", parts[0]):
            return None
        expiry = int(parts[1])
        if expiry <= int(time.time()) or expiry > int(time.time()) + ADMIN_SECONDS + 60:
            return None
        expected = hmac.new(self.config.secret_key.encode(), ".".join(parts[:2]).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, parts[2]):
            return None
        row = self.db.execute("SELECT session_id FROM admin_sessions WHERE token_hash=? AND revoked=0 AND expires_at>?", (self.token_hash(token), now_ms())).fetchone()
        return row["session_id"] if row else None

    def revoke_admin(self, token: str) -> None:
        with self.transaction():
            self.db.execute("UPDATE admin_sessions SET revoked=1 WHERE token_hash=?", (self.token_hash(token),))

    def login_admin(self, password: str, address: str) -> str:
        self.limits.check_login(address)
        if not hmac.compare_digest(password.encode(), self.config.admin_password.encode()):
            self.limits.failed_login(address)
            raise DomainError(401, "invalid_password", "管理密码不正确。")
        return self.sign_admin()

    def _require_contestant(self, contestant_id: Any) -> dict[str, Any]:
        if not isinstance(contestant_id, str) or contestant_id not in self.contestants:
            raise DomainError(404, "contestant_not_found", "这位选手不存在。")
        return self.contestants[contestant_id]

    @staticmethod
    def require_int(value: Any, minimum: int, maximum: int, label: str) -> int:
        if type(value) is not int or not minimum <= value <= maximum:
            raise DomainError(422, "invalid_input", f"{label}需在 {minimum} 至 {maximum} 之间。")
        return value

    def _set_meta(self, key: str, value: Any) -> None:
        self.db.execute("UPDATE meta SET value=? WHERE key=?", (compact(value), key))

    def _upsert_contestant(self, value: Any) -> str:
        if not isinstance(value, dict):
            raise DomainError(422, "invalid_input", "选手信息格式不正确。")
        name = self.clean_text(value.get("name"), 60, "选手名称")
        group = self.clean_text(value.get("group", ""), 40, "组别", allow_empty=True)
        existing_id = value.get("id")
        if existing_id is not None:
            existing = self._require_contestant(existing_id)
            order = self.require_int(value.get("order", existing["sort_order"]), 0, 100000, "顺序")
            self.db.execute("UPDATE contestants SET name=?,group_name=?,sort_order=? WHERE id=?", (name, group, order, existing_id))
            return existing_id
        count = self.db.execute("SELECT COUNT(*) FROM contestants").fetchone()[0]
        if count >= MAX_CONTESTANTS:
            raise DomainError(422, "contestant_limit", "最多支持 200 位选手。")
        last_order = self.db.execute("SELECT COALESCE(MAX(sort_order),-1)+1 FROM contestants").fetchone()[0]
        order = self.require_int(value.get("order", last_order), 0, 100000, "顺序")
        contestant_id = "c_" + secrets.token_urlsafe(9)
        self.db.execute("INSERT INTO contestants(id,name,group_name,sort_order,created_at) VALUES (?,?,?,?,?)", (contestant_id, name, group, order, now_ms()))
        return contestant_id

    def admin_action(self, admin_session: str, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        action = payload.get("action")
        request_id = payload.get("requestId", "")
        expected = payload.get("expectedRevision")
        base_keys = {"action", "expectedRevision", "requestId"}
        fields = {
            "upsert_contestant": {"contestant"}, "import_contestants": {"contestants"},
            "remove_contestant": {"contestantId"}, "select": {"contestantId", "lockPrevious"},
            "open": {"contestantId"}, "lock": {"contestantId"}, "lock_all": set(),
            "set_status": {"contestantId", "status"}, "publish": {"contestantIds", "visible"},
            "adjust": {"contestantId", "delta", "reason", "public"},
            "message": {"text", "highlight"}, "delete_message": {"messageId"},
            "ban": {"userId", "seconds"}, "settings": {"title"},
        }
        if not isinstance(action, str) or action not in fields:
            raise DomainError(422, "invalid_action", "不支持此管理操作。")
        if set(payload) - base_keys - fields[action]:
            raise DomainError(422, "invalid_input", "管理操作包含不支持的字段。")
        effects: dict[str, Any] = {"action": action}
        normalized = {key: value for key, value in payload.items() if key != "requestId"}
        with self.transaction():
            previous = self._dedupe("admin", request_id, normalized)
            if previous is not None:
                return {"ok": True, "state": self.state(admin=True), "replayed": True}, {}
            revision = json.loads(self.db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0])
            if type(expected) is not int or expected != revision:
                raise DomainError(409, "revision_conflict", "另一位管理员已更新状态，请检查最新信息后重试。", state=self.state(admin=True))
            detail = {key: value for key, value in payload.items() if key not in base_keys}
            if action == "upsert_contestant":
                effects["contestantId"] = self._upsert_contestant(payload.get("contestant"))
                detail["id"] = effects["contestantId"]
            elif action == "import_contestants":
                values = payload.get("contestants")
                if not isinstance(values, list) or not 1 <= len(values) <= MAX_CONTESTANTS:
                    raise DomainError(422, "invalid_input", "请提供 1 至 200 位选手。")
                for value in values:
                    if isinstance(value, dict) and value.get("id") is not None:
                        raise DomainError(422, "invalid_input", "批量导入仅追加新选手，不能携带 id。")
                    self._upsert_contestant(value)
                detail = {"count": len(values)}
            elif action == "remove_contestant":
                row = self._require_contestant(payload.get("contestantId"))
                has_votes = self.db.execute("SELECT 1 FROM votes WHERE contestant_id=? LIMIT 1", (row["id"],)).fetchone()
                has_adjustments = self.db.execute("SELECT 1 FROM adjustments WHERE contestant_id=? LIMIT 1", (row["id"],)).fetchone()
                if row["id"] == self.meta["current_id"] or has_votes or has_adjustments:
                    raise DomainError(409, "contestant_in_use", "当前选手或已有投票/调整记录的选手不能删除。")
                self.db.execute("DELETE FROM contestants WHERE id=?", (row["id"],))
            elif action == "select":
                row = self._require_contestant(payload.get("contestantId"))
                previous_id = self.meta["current_id"]
                if "lockPrevious" in payload and type(payload["lockPrevious"]) is not bool:
                    raise DomainError(422, "invalid_input", "lockPrevious 必须是布尔值。")
                if previous_id and previous_id != row["id"]:
                    self.db.execute("UPDATE contestants SET status='performed' WHERE id=?", (previous_id,))
                    if payload.get("lockPrevious", False):
                        self.db.execute("UPDATE contestants SET voting='locked',epoch=epoch+1 WHERE id=? AND voting!='locked'", (previous_id,))
                self.db.execute("UPDATE contestants SET status='performing' WHERE id=?", (row["id"],))
                self._set_meta("current_id", row["id"])
            elif action in {"open", "lock"}:
                row = self._require_contestant(payload.get("contestantId"))
                target = "open" if action == "open" else "locked"
                if row["voting"] != target:
                    self.db.execute("UPDATE contestants SET voting=?,epoch=epoch+1 WHERE id=?", (target, row["id"]))
            elif action == "lock_all":
                self.db.execute("UPDATE contestants SET voting='locked',epoch=epoch+1 WHERE voting='open'")
            elif action == "set_status":
                row = self._require_contestant(payload.get("contestantId"))
                status = payload.get("status")
                if not isinstance(status, str) or status not in {"upcoming", "performing", "performed"}:
                    raise DomainError(422, "invalid_input", "选手状态不正确。")
                if status == "performing" and row["id"] != self.meta["current_id"]:
                    raise DomainError(409, "select_required", "请使用切换选手操作设置当前选手。")
                if row["id"] == self.meta["current_id"] and status != "performing":
                    self._set_meta("current_id", None)
                self.db.execute("UPDATE contestants SET status=? WHERE id=?", (status, row["id"]))
            elif action == "publish":
                ids = payload.get("contestantIds")
                visible = payload.get("visible")
                if not isinstance(ids, list) or not 1 <= len(ids) <= MAX_CONTESTANTS or type(visible) is not bool:
                    raise DomainError(422, "invalid_input", "请选择选手并指定是否公布票数。")
                for contestant_id in ids:
                    self._require_contestant(contestant_id)
                    self.db.execute("UPDATE contestants SET published=? WHERE id=?", (int(visible), contestant_id))
            elif action == "adjust":
                row = self._require_contestant(payload.get("contestantId"))
                delta = self.require_int(payload.get("delta"), -1000000, 1000000, "调整票数")
                if delta == 0:
                    raise DomainError(422, "invalid_input", "调整票数不能为零。")
                public = payload.get("public")
                if type(public) is not bool:
                    raise DomainError(422, "invalid_input", "请指定是否公开调整原因。")
                reason = self.clean_text(payload.get("reason", ""), 200, "调整原因", allow_empty=not public)
                if delta < 0 and row["raw_votes"] + row["adjustment_total"] + delta < 0:
                    raise DomainError(422, "negative_total", "调整后票数不能小于零。")
                adjustment_id = "a_" + secrets.token_urlsafe(10)
                self.db.execute("INSERT INTO adjustments(id,contestant_id,delta,reason,public,created_at,admin_session) VALUES (?,?,?,?,?,?,?)", (adjustment_id, row["id"], delta, reason, int(public), now_ms(), admin_session))
                self.db.execute("UPDATE contestants SET adjustment_total=adjustment_total+? WHERE id=?", (delta, row["id"]))
                detail.update(reason=reason, adjustmentId=adjustment_id)
            elif action == "message":
                text = self.clean_text(payload.get("text"), MAX_MESSAGE_LENGTH, "弹幕")
                highlight = payload.get("highlight", True)
                if type(highlight) is not bool:
                    raise DomainError(422, "invalid_input", "highlight 必须是布尔值。")
                message = self._insert_message(text, None, highlight)
                effects["message"] = self.public_message(message)
                detail["messageId"] = message["id"]
            elif action == "delete_message":
                message_id = payload.get("messageId")
                if not isinstance(message_id, str):
                    raise DomainError(422, "invalid_input", "弹幕编号不正确。")
                row = self.db.execute("SELECT id FROM messages WHERE id=?", (message_id,)).fetchone()
                if row is None:
                    raise DomainError(404, "message_not_found", "这条弹幕不存在。")
                self.db.execute("UPDATE messages SET deleted_at=? WHERE id=?", (now_ms(), message_id))
                effects["deletedId"] = message_id
            elif action == "ban":
                user_id = payload.get("userId")
                seconds = self.require_int(payload.get("seconds"), 0, 7 * 86400, "禁言秒数")
                if not isinstance(user_id, str) or not self.db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
                    raise DomainError(404, "user_not_found", "这位观众不存在。")
                until = now_ms() + seconds * 1000 if seconds else 0
                self.db.execute("UPDATE users SET banned_until=?,version=version+1 WHERE id=?", (until, user_id))
                effects["banUserId"] = user_id
                detail["bannedUntil"] = until
            elif action == "settings":
                title = self.clean_text(payload.get("title"), 80, "活动名称")
                self._set_meta("title", title)
            self._set_meta("revision", revision + 1)
            self.db.execute("INSERT INTO audit(action,admin_session,detail,created_at) VALUES (?,?,?,?)", (action, admin_session, compact(detail), now_ms()))
            self._record_request("admin", request_id, normalized, {"ok": True})
        if "banUserId" in effects:
            self.user_cache.pop(effects["banUserId"], None)
        self.reload()
        return {"ok": True, "state": self.state(admin=True), "replayed": False}, effects

    def results_csv(self) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["顺序", "选手", "组别", "演出状态", "开票状态", "已公布", "原始票数", "调整合计", "显示总票数"])
        # 防止选手名称在电子表格中被当作公式执行。
        def cell(value: str) -> str:
            return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
        for row in self.contestants.values():
            writer.writerow([row["sort_order"] + 1, cell(row["name"]), cell(row["group_name"]), row["status"], row["voting"], "是" if row["published"] else "否", row["raw_votes"], row["adjustment_total"], max(0, row["raw_votes"] + row["adjustment_total"])])
        return "\ufeff" + output.getvalue()
