"""Бизнес-логика мероприятий: список, CRUD, запись, подтверждение, рейтинг, статистика."""

from typing import Optional

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.orm import Session, joinedload

from ..errors import ApiError
from ..levels import level_for_points, level_progress, rank_title
from ..models import Event, Participant, User
from ..schemas import EVENT_TYPES, EventIn, EventType
from ..security import now_iso


def _finished(event: Event, now: str) -> bool:
    end = event.ends_at if event.ends_at is not None else event.starts_at
    return end <= now


def _upcoming_cond(now: str):
    return or_(
        and_(Event.ends_at.is_(None), Event.starts_at >= now),
        and_(Event.ends_at.is_not(None), Event.ends_at >= now),
    )


def _counts_subqueries():
    participants_count = (
        select(func.count(Participant.id))
        .where(Participant.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
    )
    confirmed_count = (
        select(func.count(Participant.id))
        .where(Participant.event_id == Event.id, Participant.status == "confirmed")
        .correlate(Event)
        .scalar_subquery()
    )
    return participants_count, confirmed_count


def _event_item(event: Event, organizer_name: str, participants_count: int, confirmed_count: int, joined: bool) -> dict:
    return {
        "id": event.id,
        "organizerId": event.organizer_id,
        "organizerName": organizer_name,
        "title": event.title,
        "description": event.description,
        "type": event.type,
        "location": event.location,
        "startsAt": event.starts_at,
        "endsAt": event.ends_at,
        "capacity": event.capacity,
        "pointsReward": event.points_reward,
        "participantsCount": participants_count,
        "confirmedCount": confirmed_count,
        "joined": joined,
    }


def list_events(
    db: Session,
    *,
    event_type: Optional[EventType],
    q: Optional[str],
    scope: str,
    page: int,
    limit: int,
    user_id: Optional[int],
) -> dict:
    now = now_iso()
    conds = []
    if event_type:
        conds.append(Event.type == event_type)
    if q:
        like = f"%{q.lower()}%"
        conds.append(or_(func.lower_utf8(Event.title).like(like), func.lower_utf8(Event.location).like(like)))
    if scope == "upcoming":
        conds.append(_upcoming_cond(now))
    elif scope == "past":
        conds.append(not_(_upcoming_cond(now)))

    total = db.execute(select(func.count()).select_from(Event).where(*conds)).scalar_one()
    total_pages = max(1, (total + limit - 1) // limit)

    participants_count, confirmed_count = _counts_subqueries()
    stmt = (
        select(
            Event,
            User.name.label("organizer_name"),
            participants_count.label("participants_count"),
            confirmed_count.label("confirmed_count"),
        )
        .join(User, User.id == Event.organizer_id)
        .where(*conds)
        .order_by(Event.starts_at.desc() if scope == "past" else Event.starts_at.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = db.execute(stmt).all()

    joined_ids: set[int] = set()
    if user_id and rows:
        ids = [row[0].id for row in rows]
        joined_ids = set(
            db.execute(
                select(Participant.event_id).where(Participant.user_id == user_id, Participant.event_id.in_(ids))
            ).scalars()
        )

    items = [
        _event_item(event, organizer_name, pc, cc, event.id in joined_ids)
        for event, organizer_name, pc, cc in rows
    ]
    return {"items": items, "meta": {"page": page, "limit": limit, "total": total, "totalPages": total_pages}}


def _public_user(user: User) -> dict:
    return {"id": user.id, "name": user.name, "bio": user.bio, "points": user.points, "createdAt": user.created_at}


def get_event(db: Session, event_id: int, user_id: Optional[int]) -> dict:
    event = db.execute(select(Event).where(Event.id == event_id)).scalar_one_or_none()
    if event is None:
        raise ApiError(404, "NOT_FOUND", "Мероприятие не найдено")

    participants = db.execute(
        select(Participant)
        .options(joinedload(Participant.user))
        .where(Participant.event_id == event_id)
        .order_by(Participant.joined_at)
    ).scalars().all()

    joined = False
    if user_id is not None:
        joined = (
            db.execute(select(Participant.id).where(Participant.event_id == event_id, Participant.user_id == user_id)).first()
            is not None
        )

    organizer = event.organizer
    level = level_for_points(organizer.points)

    return {
        "event": {
            **_event_item(
                event,
                organizer.name,
                len(participants),
                sum(1 for p in participants if p.status == "confirmed"),
                joined,
            ),
            "organizer": {**_public_user(organizer), "level": level, "rankTitle": rank_title(level)},
            "participants": [
                {"user": _public_user(p.user), "status": p.status, "joinedAt": p.joined_at} for p in participants
            ],
            "isFinished": _finished(event, now_iso()),
            "isFull": event.capacity > 0 and len(participants) >= event.capacity,
            "isOwner": user_id == event.organizer_id,
        }
    }


def create_event(db: Session, organizer_id: int, data: EventIn) -> dict:
    event = Event(
        organizer_id=organizer_id,
        title=data.title,
        description=data.description,
        type=data.type,
        location=data.location,
        starts_at=data.startsAt,
        ends_at=data.endsAt,
        capacity=data.capacity,
        points_reward=data.pointsReward,
        created_at=now_iso(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id}


def _get_owned_event(db: Session, event_id: int, organizer_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise ApiError(404, "NOT_FOUND", "Мероприятие не найдено")
    if event.organizer_id != organizer_id:
        raise ApiError(403, "FORBIDDEN", "Изменить мероприятие может только организатор")
    return event


def update_event(db: Session, event_id: int, organizer_id: int, data: EventIn) -> None:
    event = _get_owned_event(db, event_id, organizer_id)
    event.title = data.title
    event.description = data.description
    event.type = data.type
    event.location = data.location
    event.starts_at = data.startsAt
    event.ends_at = data.endsAt
    event.capacity = data.capacity
    event.points_reward = data.pointsReward
    db.commit()


def delete_event(db: Session, event_id: int, organizer_id: int) -> None:
    event = _get_owned_event(db, event_id, organizer_id)
    db.delete(event)
    db.commit()


def join_event(db: Session, event_id: int, user_id: int) -> None:
    event = db.get(Event, event_id)
    if event is None:
        raise ApiError(404, "NOT_FOUND", "Мероприятие не найдено")
    if event.organizer_id == user_id:
        raise ApiError(409, "OWN_EVENT", "Нельзя записаться на собственное мероприятие")
    if _finished(event, now_iso()):
        raise ApiError(409, "EVENT_FINISHED", "Мероприятие уже завершилось")

    existing = db.execute(
        select(Participant.id).where(Participant.event_id == event_id, Participant.user_id == user_id)
    ).first()
    if existing:
        raise ApiError(409, "ALREADY_JOINED", "Вы уже записаны на это мероприятие")

    if event.capacity > 0:
        count = db.execute(select(func.count()).select_from(Participant).where(Participant.event_id == event_id)).scalar_one()
        if count >= event.capacity:
            raise ApiError(409, "EVENT_FULL", "Все места на мероприятие уже заняты")

    db.add(Participant(event_id=event_id, user_id=user_id, joined_at=now_iso()))
    db.commit()


def leave_event(db: Session, event_id: int, user_id: int) -> None:
    event = db.get(Event, event_id)
    if event is None:
        raise ApiError(404, "NOT_FOUND", "Мероприятие не найдено")
    if _finished(event, now_iso()):
        raise ApiError(409, "EVENT_FINISHED", "Нельзя отменить запись после завершения мероприятия")

    result = db.execute(
        select(Participant).where(Participant.event_id == event_id, Participant.user_id == user_id)
    ).scalar_one_or_none()
    if result is None:
        raise ApiError(404, "NOT_JOINED", "Вы не записаны на это мероприятие")
    db.delete(result)
    db.commit()


def confirm_participant(db: Session, event_id: int, participant_user_id: int, organizer_id: int) -> dict:
    """Подтверждение участия: участник получает баллы мероприятия (ровно один раз)."""
    event = _get_owned_event(db, event_id, organizer_id)

    participant = db.execute(
        select(Participant).where(Participant.event_id == event_id, Participant.user_id == participant_user_id)
    ).scalar_one_or_none()
    if participant is None:
        raise ApiError(404, "PARTICIPANT_NOT_FOUND", "Пользователь не записан на это мероприятие")
    if participant.status == "confirmed":
        raise ApiError(409, "ALREADY_CONFIRMED", "Участие уже подтверждено")

    participant.status = "confirmed"
    user = db.get(User, participant_user_id)
    user.points += event.points_reward
    db.commit()

    level = level_for_points(user.points)
    return {
        "participant": {"userId": participant_user_id, "status": "confirmed"},
        "pointsAwarded": event.points_reward,
        "user": {**_public_user(user), "level": level, "rankTitle": rank_title(level), "levelProgress": level_progress(user.points)},
    }


def list_user_participations(db: Session, user_id: int) -> dict:
    rows = db.execute(
        select(Participant, Event, User.name)
        .join(Event, Event.id == Participant.event_id)
        .join(User, User.id == Event.organizer_id)
        .where(Participant.user_id == user_id)
        .order_by(Event.starts_at.desc())
    ).all()

    items = []
    for participation, event, organizer_name in rows:
        items.append(
            {
                "status": participation.status,
                "joinedAt": participation.joined_at,
                "event": {
                    "id": event.id,
                    "title": event.title,
                    "type": event.type,
                    "location": event.location,
                    "startsAt": event.starts_at,
                    "endsAt": event.ends_at,
                    "pointsReward": event.points_reward,
                    "organizerName": organizer_name,
                },
            }
        )
    return {"items": items}


def get_leaderboard(db: Session, limit: int) -> dict:
    confirmed_count = (
        select(func.count(Participant.id))
        .where(Participant.user_id == User.id, Participant.status == "confirmed")
        .correlate(User)
        .scalar_subquery()
    )
    rows = db.execute(
        select(User, confirmed_count.label("confirmed_count"))
        .order_by(User.points.desc(), User.id.asc())
        .limit(limit)
    ).all()

    items = []
    for rank, (user, count) in enumerate(rows, start=1):
        level = level_for_points(user.points)
        items.append(
            {
                "rank": rank,
                "user": {"id": user.id, "name": user.name, "points": user.points},
                "level": level,
                "rankTitle": rank_title(level),
                "confirmedCount": count,
            }
        )
    return {"items": items}


def get_stats(db: Session) -> dict:
    now = now_iso()
    users = db.execute(select(func.count()).select_from(User)).scalar_one()
    events = db.execute(select(func.count()).select_from(Event)).scalar_one()
    upcoming = db.execute(select(func.count()).select_from(Event).where(_upcoming_cond(now))).scalar_one()
    participants = db.execute(
        select(func.count(func.distinct(Participant.user_id))).where(Participant.status == "confirmed")
    ).scalar_one()
    points_awarded = db.execute(select(func.coalesce(func.sum(User.points), 0))).scalar_one()
    by_type = dict(
        db.execute(select(Event.type, func.count()).group_by(Event.type)).all()
    )

    return {
        "users": users,
        "events": events,
        "upcomingEvents": upcoming,
        "participants": participants,
        "pointsAwarded": points_awarded,
        "eventsByType": {t: by_type.get(t, 0) for t in EVENT_TYPES},
    }


def get_user_profile(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise ApiError(404, "NOT_FOUND", "Пользователь не найден")

    confirmed = db.execute(
        select(func.count()).select_from(Participant).where(Participant.user_id == user_id, Participant.status == "confirmed")
    ).scalar_one()
    organized = db.execute(select(func.count()).select_from(Event).where(Event.organizer_id == user_id)).scalar_one()
    level = level_for_points(user.points)

    return {
        "user": _public_user(user),
        "level": level,
        "rankTitle": rank_title(level),
        "levelProgress": level_progress(user.points),
        "stats": {"confirmedCount": confirmed, "organizedCount": organized},
    }
