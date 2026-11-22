"""Тесты рейтинга, статистики, публичного профиля и истории участия."""

from tests.helpers import auth_header, confirm_participant, create_event, join_event, register_user


def test_leaderboard_orders_by_points(client):
    organizer = register_user(client)
    first = register_user(client)
    second = register_user(client)

    e1 = create_event(client, organizer["tokens"]["accessToken"], pointsReward=10)
    e2 = create_event(client, organizer["tokens"]["accessToken"], pointsReward=20)
    join_event(client, first["tokens"]["accessToken"], e1)
    join_event(client, first["tokens"]["accessToken"], e2)
    join_event(client, second["tokens"]["accessToken"], e1)

    confirm_participant(client, organizer["tokens"]["accessToken"], e1, first["user"]["id"])
    confirm_participant(client, organizer["tokens"]["accessToken"], e2, first["user"]["id"])
    confirm_participant(client, organizer["tokens"]["accessToken"], e1, second["user"]["id"])

    items = client.get("/api/v1/leaderboard").json()["items"]
    assert len(items) == 3
    assert items[0]["rank"] == 1
    assert items[0]["user"]["id"] == first["user"]["id"]
    assert items[0]["user"]["points"] == 30
    assert items[0]["confirmedCount"] == 2
    assert items[0]["rankTitle"] == "Новичок"
    assert items[1]["user"]["id"] == second["user"]["id"]
    assert items[1]["user"]["points"] == 10
    assert items[2]["user"]["id"] == organizer["user"]["id"]


def test_leaderboard_limit(client):
    organizer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])
    for _ in range(2):
        u = register_user(client)
        join_event(client, u["tokens"]["accessToken"], event_id)

    items = client.get("/api/v1/leaderboard", params={"limit": 1}).json()["items"]
    assert len(items) == 1


def test_stats_counts(client):
    organizer = register_user(client)
    volunteer = register_user(client)

    create_event(client, organizer["tokens"]["accessToken"])
    create_event(client, organizer["tokens"]["accessToken"], type="recycling")
    e3 = create_event(client, organizer["tokens"]["accessToken"], pointsReward=15)
    join_event(client, volunteer["tokens"]["accessToken"], e3)
    confirm_participant(client, organizer["tokens"]["accessToken"], e3, volunteer["user"]["id"])

    stats = client.get("/api/v1/stats").json()
    assert stats["users"] == 2
    assert stats["events"] == 3
    assert stats["upcomingEvents"] == 3
    assert stats["participants"] == 1
    assert stats["pointsAwarded"] == 15
    assert stats["eventsByType"]["cleanup"] == 2
    assert stats["eventsByType"]["recycling"] == 1
    assert stats["eventsByType"]["tree_planting"] == 0


def test_public_profile(client):
    registered = register_user(client, name="Публичная Персона")
    res = client.get(f"/api/v1/users/{registered['user']['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["name"] == "Публичная Персона"
    assert "email" not in body["user"]
    assert body["level"] == 1
    assert body["stats"] == {"confirmedCount": 0, "organizedCount": 0}


def test_public_profile_404(client):
    res = client.get("/api/v1/users/999")
    assert res.status_code == 404


def test_my_events_history(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"], title="Моя история")
    join_event(client, volunteer["tokens"]["accessToken"], event_id)

    res = client.get("/api/v1/me/events", headers=auth_header(volunteer["tokens"]["accessToken"]))
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "joined"
    assert items[0]["event"]["title"] == "Моя история"


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
