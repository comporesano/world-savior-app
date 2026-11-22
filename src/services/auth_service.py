"""Регистрация, вход, ротация refresh-токенов."""

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..errors import ApiError
from ..models import RefreshToken, User
from ..schemas import LoginIn, RegisterIn, TokenPair
from ..security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    now_iso,
    sha256,
    verify_password,
)


def _iso_in_days(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).replace(tzinfo=None).isoformat(timespec="milliseconds")


def issue_tokens(db: Session, user: User) -> TokenPair:
    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            token_hash=sha256(refresh_token),
            expires_at=_iso_in_days(settings.refresh_token_ttl_days),
        )
    )
    db.commit()
    return TokenPair(accessToken=access_token, refreshToken=refresh_token)


def register(db: Session, data: RegisterIn) -> dict:
    existing = db.execute(select(User.id).where(User.email == data.email)).first()
    if existing:
        raise ApiError(409, "EMAIL_TAKEN", "Пользователь с таким email уже зарегистрирован")

    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), created_at=now_iso())
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"user": _user_out(user), "tokens": issue_tokens(db, user)}


def login(db: Session, data: LoginIn) -> dict:
    user = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "Неверный email или пароль")
    return {"user": _user_out(user), "tokens": issue_tokens(db, user)}


def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "bio": user.bio,
        "points": user.points,
        "createdAt": user.created_at,
    }


def rotate_refresh(db: Session, raw_token: str) -> dict:
    """Ротация refresh-токена. Повторное использование отозванного токена
    трактуется как компрометация — отзываются все сессии пользователя."""
    try:
        payload = decode_token(raw_token)
    except pyjwt.PyJWTError:
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Недействительный refresh-токен") from None

    if payload.get("type") != "refresh" or not payload.get("jti"):
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Недействительный refresh-токен")

    row = db.execute(select(RefreshToken).where(RefreshToken.token_hash == sha256(raw_token))).scalar_one_or_none()
    if row is None:
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Токен не найден")

    if row.revoked_at is not None:
        for other in db.execute(
            select(RefreshToken).where(RefreshToken.user_id == row.user_id, RefreshToken.revoked_at.is_(None))
        ).scalars():
            other.revoked_at = now_iso()
        db.commit()
        raise ApiError(401, "TOKEN_REUSE_DETECTED", "Обнаружено повторное использование токена, все сессии отозваны")

    if row.expires_at <= now_iso():
        raise ApiError(401, "EXPIRED_REFRESH_TOKEN", "Срок действия refresh-токена истёк")

    row.revoked_at = now_iso()
    user = db.get(User, row.user_id)
    if user is None:
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Пользователь не найден")
    tokens = issue_tokens(db, user)
    return {"tokens": tokens}


def revoke_refresh(db: Session, raw_token: str) -> None:
    """Выход из аккаунта: отзыв конкретного refresh-токена."""
    try:
        payload = decode_token(raw_token)
    except pyjwt.PyJWTError:
        return
    if payload.get("type") != "refresh" or not payload.get("jti"):
        return
    row = db.execute(select(RefreshToken).where(RefreshToken.token_hash == sha256(raw_token))).scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = now_iso()
        db.commit()
