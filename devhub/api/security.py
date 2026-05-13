"""Şifre hash + JWT primitive'leri."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from ..config import get_settings


def hash_password(password: str) -> str:
    """Bcrypt ile şifreyi hashle. Bcrypt 72 byte sınırı için truncate (utf-8)."""
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    pw_bytes = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except ValueError:
        return False


def _now() -> datetime:
    return datetime.now(tz=UTC)


def create_access_token(user_id: int) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """Yeni bir refresh JWT üret. (token, jti, expires_at) döner."""
    settings = get_settings()
    jti = str(uuid.uuid4())
    expires_at = _now() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": int(_now().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    """JWT'yi doğrula ve payload'ı dön. Geçersizse jwt.PyJWTError fırlatır."""
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected token type '{expected_type}'")
    return payload
