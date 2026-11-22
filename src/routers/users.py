from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import UserProfileOut
from ..services import event_service

router = APIRouter()


@router.get("/{user_id}", response_model=UserProfileOut)
def user_profile(user_id: int, db: Session = Depends(get_db)):
    return event_service.get_user_profile(db, user_id)
