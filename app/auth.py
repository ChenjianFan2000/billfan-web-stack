import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE_NAME = "access_token"
_HASH_PREFIX = "pbkdf2_sha256"
_HASH_ITERATIONS = 200000
_DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "其华")
_DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "jclcgs")
_JWT_SECRET = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_DEV_ONLY")
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "720"))


class LoginRequest(BaseModel):
    username: str
    password: str


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def _password_hash(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _HASH_ITERATIONS,
    ).hex()
    return f"{_HASH_PREFIX}${_HASH_ITERATIONS}${salt}${digest}"


def _verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        prefix, rounds, salt, digest = stored_hash.split("$", 3)
        if prefix != _HASH_PREFIX:
            return False
        iterations = int(rounds)
    except (TypeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual, digest)


def _jwt_encode(payload: Dict) -> str:
    header = {"alg": _JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        _JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _jwt_decode(token: str) -> Dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("token format invalid") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(
        _JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_b64)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ValueError("token signature invalid")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if int(datetime.utcnow().timestamp()) >= exp:
        raise ValueError("token expired")

    return payload


def create_access_token(user_id: int, username: str, expires_delta: Optional[timedelta] = None) -> str:
    ttl = expires_delta or timedelta(hours=_JWT_EXPIRE_HOURS)
    payload = {
        "uid": user_id,
        "sub": username,
        "exp": int((datetime.utcnow() + ttl).timestamp()),
    }
    return _jwt_encode(payload)


def _seed_default_user(db) -> None:
    row = db.execute("SELECT id FROM users WHERE username = ?", (_DEFAULT_USERNAME,)).fetchone()
    if row is not None:
        return

    password_hash = _password_hash(_DEFAULT_PASSWORD)
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (_DEFAULT_USERNAME, password_hash),
    )
    db.commit()


def get_current_user(request: Request, db=Depends(get_db)) -> Dict:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")

    try:
        payload = _jwt_decode(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

    user_id = payload.get("uid")
    username = payload.get("sub")
    if not user_id or not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token payload")

    row = db.execute(
        "SELECT id, username FROM users WHERE id = ? AND username = ?",
        (user_id, username),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")

    return {"id": row["id"], "username": row["username"]}


@router.get("/users")
def list_users(db=Depends(get_db)):
    _seed_default_user(db)
    rows = db.execute("SELECT username FROM users ORDER BY id ASC").fetchall()
    return [{"username": row["username"]} for row in rows]


@router.post("/login")
def login(payload: LoginRequest, response: Response, db=Depends(get_db)):
    _seed_default_user(db)

    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (payload.username,),
    ).fetchone()

    if row is None or not _verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )

    token = create_access_token(user_id=row["id"], username=row["username"])
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=_JWT_EXPIRE_HOURS * 3600,
        path="/",
    )
    return {"ok": True, "username": row["username"]}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user
