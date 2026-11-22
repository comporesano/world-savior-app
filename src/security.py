"""Хеширование паролей и работа с JWT (access + refresh с ротацией)."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def now_iso() -> str:
    """Текущее время UTC в виде ISO-строки без суффикса таймзоны."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="milliseconds")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """Возвращает (token, jti). jti связывает токен с записью в БД для ротации."""
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": jti,
            "iat": now,
            "exp": now + timedelta(days=settings.refresh_token_ttl_days),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )
    return token, jti


def decode_token(token: str) -> dict:
    """Декодирует JWT; при невалидности бросает jwt.PyJWTError."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
