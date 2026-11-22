"""Модели SQLAlchemy.

Важное решение: все даты хранятся строками ISO 8601 в UTC (без суффикса 'Z').
Это даёт корректное лексикографическое сравнение/сортировку в SQLite
и избавляет от классических проблем с таймзонами в SQLite.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

EVENT_TYPES = ("cleanup", "tree_planting", "recycling", "eco_lecture", "water_cleanup")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str] = mapped_column(Text, default="")
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(40))

    events: Mapped[list["Event"]] = relationship(
        back_populates="organizer", cascade="all, delete-orphan", passive_deletes=True
    )
    participations: Mapped[list["Participant"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    jti: Mapped[str] = mapped_column(String(36))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[str] = mapped_column(String(40))
    revoked_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("type IN ('cleanup','tree_planting','recycling','eco_lecture','water_cleanup')", name="ck_events_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20))
    location: Mapped[str] = mapped_column(String(160))
    starts_at: Mapped[str] = mapped_column(String(40), index=True)
    ends_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=0)  # 0 = без ограничения
    points_reward: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[str] = mapped_column(String(40))

    organizer: Mapped["User"] = relationship(back_populates="events")
    participants: Mapped[list["Participant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", passive_deletes=True
    )


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_participant_event_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(10), default="joined")  # joined | confirmed
    joined_at: Mapped[str] = mapped_column(String(40))

    event: Mapped["Event"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participations")
