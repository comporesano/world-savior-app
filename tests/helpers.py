"""Вспомогательные функции для тестов."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

_counter = {"n": 0}


def future_iso(days: int = 5) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def past_iso(days: int = 5) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def register_user(
    client: TestClient,
    name: str | None = None,
    email: str | None = None,
    password: str = "password123",
) -> dict:
    _counter["n"] += 1
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": name or "Тест Пользователь",
            "email": email or f"user{_counter['n']}@test.dev",
            "password": password,
        },
    )
    assert res.status_code == 201, f"register failed: {res.status_code} {res.text}"
    return res.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_event(client: TestClient, token: str, **overrides) -> int:
    payload = {
        "title": "Тестовый субботник",
        "description": "Описание мероприятия для теста, достаточно длинное.",
        "type": "cleanup",
        "location": "Городской парк",
        "startsAt": future_iso(),
        "capacity": 10,
        "pointsReward": 20,
        **overrides,
    }
    res = client.post("/api/v1/events", json=payload, headers=auth_header(token))
    assert res.status_code == 201, f"create_event failed: {res.status_code} {res.text}"
    return res.json()["id"]


def join_event(client: TestClient, token: str, event_id: int):
    return client.post(f"/api/v1/events/{event_id}/join", headers=auth_header(token))


def confirm_participant(client: TestClient, token: str, event_id: int, user_id: int):
    return client.post(f"/api/v1/events/{event_id}/participants/{user_id}/confirm", headers=auth_header(token))
