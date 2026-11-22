from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_current_user
from ..levels import level_for_points, level_progress, rank_title
from ..limiter import limiter
from ..models import User
from ..schemas import LoginIn, LoginOut, MeOut, RefreshIn, RefreshOut, RegisterIn, RegisterOut
from ..services import auth_service

router = APIRouter()


@router.post("/register", response_model=RegisterOut, status_code=201)
@limiter.limit(settings.auth_rate_limit)
def register(request: Request, data: RegisterIn, db: Session = Depends(get_db)):
    return auth_service.register(db, data)


@router.post("/login", response_model=LoginOut)
@limiter.limit(settings.auth_rate_limit)
def login(request: Request, data: LoginIn, db: Session = Depends(get_db)):
    return auth_service.login(db, data)


@router.post("/refresh", response_model=RefreshOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    return auth_service.rotate_refresh(db, data.refreshToken)


@router.post("/logout", status_code=204)
def logout(data: RefreshIn, db: Session = Depends(get_db)):
    auth_service.revoke_refresh(db, data.refreshToken)
    return Response(status_code=204)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)):
    level = level_for_points(user.points)
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "points": user.points,
            "createdAt": user.created_at,
            "level": level,
            "rankTitle": rank_title(level),
        },
        "levelProgress": level_progress(user.points),
    }
