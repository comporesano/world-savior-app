"""Pydantic-схемы (валидация входных данных и сериализация ответов).

Даты: на входе принимаются ISO 8601 строки (с 'Z' или смещением),
внутри хранятся как UTC без суффикса, на выходе всегда с 'Z'.
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator

EventType = Literal["cleanup", "tree_planting", "recycling", "eco_lecture", "water_cleanup"]
EVENT_TYPES: tuple[EventType, ...] = ("cleanup", "tree_planting", "recycling", "eco_lecture", "water_cleanup")


def parse_iso(value: str) -> str:
    """ISO 8601 (с таймзоной или без) → UTC-строка без суффикса таймзоны."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Дата должна быть в формате ISO 8601") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat(timespec="milliseconds")


def emit_iso(value: str) -> str:
    return value if value.endswith(("Z", "+00:00")) else f"{value}Z"


# ---------- Пользователи и токены ----------


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()


class TokenPair(BaseModel):
    accessToken: str
    refreshToken: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    bio: str
    points: int
    createdAt: str

    @field_serializer("createdAt")
    def emit_created(self, v: str) -> str:
        return emit_iso(v)


class PublicUserOut(BaseModel):
    id: int
    name: str
    bio: str
    points: int
    createdAt: str

    @field_serializer("createdAt")
    def emit_created(self, v: str) -> str:
        return emit_iso(v)


class MeUserOut(UserOut):
    level: int
    rankTitle: str


class LevelProgressOut(BaseModel):
    level: int
    current: int
    nextLevelAt: int
    progress: float


class RegisterOut(BaseModel):
    user: UserOut
    tokens: TokenPair


class LoginOut(RegisterOut):
    pass


class RefreshIn(BaseModel):
    refreshToken: str = Field(min_length=10)


class RefreshOut(BaseModel):
    tokens: TokenPair


class UpdateMeIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=60)
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name", "bio")
    @classmethod
    def strip(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else v


class MeOut(BaseModel):
    user: MeUserOut
    levelProgress: LevelProgressOut


# ---------- Мероприятия ----------


class EventIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=3000)
    type: EventType
    location: str = Field(min_length=2, max_length=160)
    startsAt: str
    endsAt: Optional[str] = None
    capacity: int = Field(default=0, ge=0, le=10_000)
    pointsReward: int = Field(default=10, ge=0, le=1000)

    @field_validator("title", "description", "location")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    @field_validator("startsAt")
    @classmethod
    def parse_starts(cls, v: str) -> str:
        return parse_iso(v)

    @field_validator("endsAt")
    @classmethod
    def parse_ends(cls, v: Optional[str], info) -> Optional[str]:
        parsed = parse_iso(v) if v else None
        starts = info.data.get("startsAt")
        if parsed is not None and starts is not None and parsed <= starts:
            # ValueError внутри field_validator даёт локацию ('endsAt',) в деталях ошибки
            raise ValueError("Дата окончания должна быть позже даты начала")
        return parsed


class EventItemOut(BaseModel):
    id: int
    organizerId: int
    organizerName: str
    title: str
    description: str
    type: EventType
    location: str
    startsAt: str
    endsAt: Optional[str] = None
    capacity: int
    pointsReward: int
    participantsCount: int
    confirmedCount: int
    joined: bool = False

    @field_serializer("startsAt", "endsAt")
    def emit_dates(self, v: Optional[str]) -> Optional[str]:
        return emit_iso(v) if v else v


class OrganizerOut(PublicUserOut):
    level: int
    rankTitle: str


class ParticipantOut(BaseModel):
    user: PublicUserOut
    status: Literal["joined", "confirmed"]
    joinedAt: str

    @field_serializer("joinedAt")
    def emit_joined(self, v: str) -> str:
        return emit_iso(v)


class EventDetailOut(EventItemOut):
    organizer: Optional[OrganizerOut] = None
    participants: list[ParticipantOut] = []
    isFinished: bool = False
    isFull: bool = False
    isOwner: bool = False


class EventDetailResponse(BaseModel):
    event: EventDetailOut


class EventIdOut(BaseModel):
    id: int


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int


class EventsPageOut(BaseModel):
    items: list[EventItemOut]
    meta: PageMeta


class ParticipationOut(BaseModel):
    status: Literal["joined", "confirmed"]
    joinedAt: str
    event: dict

    @field_serializer("joinedAt")
    def emit_joined(self, v: str) -> str:
        return emit_iso(v)


class ParticipationsOut(BaseModel):
    items: list[ParticipationOut]


class ConfirmOut(BaseModel):
    participant: dict
    pointsAwarded: int
    user: dict


# ---------- Рейтинг и статистика ----------


class LeaderboardUserOut(BaseModel):
    id: int
    name: str
    points: int


class LeaderboardEntryOut(BaseModel):
    rank: int
    user: LeaderboardUserOut
    level: int
    rankTitle: str
    confirmedCount: int


class LeaderboardOut(BaseModel):
    items: list[LeaderboardEntryOut]


class StatsOut(BaseModel):
    users: int
    events: int
    upcomingEvents: int
    participants: int
    pointsAwarded: int
    eventsByType: dict[str, int]


class UserProfileOut(BaseModel):
    user: PublicUserOut
    level: int
    rankTitle: str
    levelProgress: LevelProgressOut
    stats: dict
