"""FastAPI-зависимости: получение текущего пользователя из Bearer-токена."""

from typing import Optional

import jwt as pyjwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .db import get_db
from .errors import ApiError
from .models import User
from .security import decode_token


def _parse_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[len("Bearer ") :]


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _parse_bearer(authorization)
    if token is None:
        raise ApiError(401, "UNAUTHORIZED", "Требуется авторизация")
    try:
        payload = decode_token(token)
    except pyjwt.PyJWTError:
        raise ApiError(401, "UNAUTHORIZED", "Недействительный или просроченный токен") from None

    user = db.get(User, int(payload["sub"])) if payload.get("sub") else None
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "Пользователь не найден")
    return user


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Для публичных эндпоинтов: валидный токен → пользователь, иначе None."""
    token = _parse_bearer(authorization)
    if token is None:
        return None
    try:
        payload = decode_token(token)
        return db.get(User, int(payload["sub"])) if payload.get("sub") else None
    except (pyjwt.PyJWTError, ValueError):
        return None
