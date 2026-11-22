from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import ParticipationsOut, UpdateMeIn
from ..services import event_service

router = APIRouter()


@router.patch("", response_model=dict)
def update_me(data: UpdateMeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name is not None:
        user.name = data.name
    if data.bio is not None:
        user.bio = data.bio
    db.commit()
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "points": user.points,
            "createdAt": user.created_at,
        }
    }


@router.get("/events", response_model=ParticipationsOut)
def my_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return event_service.list_user_participations(db, user.id)
