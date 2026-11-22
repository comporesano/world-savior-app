"""Фикстуры тестов: отдельная in-memory БД на каждый тест, отключённые rate-limit'ы."""

import os

os.environ["RATE_LIMIT_ENABLED"] = "0"
os.environ.setdefault("JWT_SECRET", "test-secret-long-enough-for-hs256-algorithm")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db import Base, get_db
from src.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Без контекстного менеджера lifespan (создание таблиц в файловой БД) не запускается —
    # тесты работают только с in-memory БД и не трогают data/ecosavior.db
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()
    engine.dispose()
