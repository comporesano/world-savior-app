from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import LeaderboardOut, StatsOut
from ..services import event_service

router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardOut)
def leaderboard(limit: int = Query(default=20, ge=1, le=50), db: Session = Depends(get_db)):
    return event_service.get_leaderboard(db, limit)


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    return event_service.get_stats(db)
