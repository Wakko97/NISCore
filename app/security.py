from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json

from fastapi import Depends, Header, HTTPException

from app.config import settings


@dataclass(frozen=True)
class AuthContext:
    username: str
    role: str


def _b64(data: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _ub64(data: str) -> bytes:
    import base64

    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def issue_token(username: str, role: str, ttl_minutes: int = 60) -> str:
    if not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="jwt secret not configured")
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "role": role,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    h = _b64(json.dumps(header, separators=(",", ":")).encode())
    p = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(settings.jwt_secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"


def decode_token(token: str) -> AuthContext:
    try:
        h, p, s = token.split(".")
        expected = _b64(hmac.new(settings.jwt_secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(s, expected):
            raise HTTPException(status_code=401, detail="invalid token signature")
        payload = json.loads(_ub64(p))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(status_code=401, detail="token expired")
        return AuthContext(username=payload["sub"], role=payload["role"])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc


def require_auth(authorization: str | None = Header(default=None)) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    return decode_token(token)


def require_role(*roles: str):
    def _dep(ctx: AuthContext = Depends(require_auth)) -> AuthContext:
        if ctx.role not in roles:
            raise HTTPException(status_code=403, detail="insufficient role")
        return ctx

    return _dep
