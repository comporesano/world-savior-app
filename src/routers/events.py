from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user
from ..models import User
from ..schemas import ConfirmOut, EventDetailResponse, EventIdOut, EventIn, EventsPageOut, EventType
from ..services import event_service

router = APIRouter()


@router.get("", response_model=EventsPageOut)
def list_events(
    scope: Literal["upcoming", "past", "all"] = "upcoming",
    event_type: Optional[EventType] = Query(default=None, alias="type"),
    q: Optional[str] = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return event_service.list_events(
        db,
        event_type=event_type,
        q=q.strip() if q else None,
        scope=scope,
        page=page,
        limit=limit,
        user_id=user.id if user else None,
    )


@router.post("", response_model=EventIdOut, status_code=201)
def create_event(data: EventIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return event_service.create_event(db, user.id, data)


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(
    event_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return event_service.get_event(db, event_id, user.id if user else None)


@router.patch("/{event_id}", response_model=dict)
def update_event(
    event_id: int,
    data: EventIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event_service.update_event(db, event_id, user.id, data)
    return {"ok": True}


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event_service.delete_event(db, event_id, user.id)


@router.post("/{event_id}/join", response_model=dict, status_code=201)
def join_event(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event_service.join_event(db, event_id, user.id)
    return {"ok": True}


@router.delete("/{event_id}/join", status_code=204)
def leave_event(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event_service.leave_event(db, event_id, user.id)


@router.post("/{event_id}/participants/{user_id}/confirm", response_model=ConfirmOut)
def confirm_participant(
    event_id: int,
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return event_service.confirm_participant(db, event_id, user_id, user.id)
