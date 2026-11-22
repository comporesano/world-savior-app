"""Подключение к БД: engine, фабрика сессий, зависимость get_db для FastAPI."""

import sqlite3
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


@event.listens_for(Engine, "connect")
def _register_sqlite_functions(dbapi_conn, _connection_record):
    """Встроенный lower() в SQLite не работает для кириллицы — регистрируем свой."""
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.create_function("lower_utf8", 1, lambda s: s.lower() if s else s)


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    if url.startswith("sqlite"):
        # Для файловых БД гарантируем существование каталога data/
        if ":///" in url:
            db_path = url.split(":///", 1)[-1]
            if db_path and db_path != ":memory:" and not db_path.startswith("file:"):
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
