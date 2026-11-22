"""Тесты CRUD мероприятий, записи и подтверждения участия."""

from tests.helpers import (
    auth_header,
    confirm_participant,
    create_event,
    future_iso,
    join_event,
    past_iso,
    register_user,
)


def test_create_event_requires_auth(client):
    res = client.post("/api/v1/events", json={"title": "Без токена"})
    assert res.status_code == 401


def test_create_event_success(client):
    registered = register_user(client)
    event_id = create_event(client, registered["tokens"]["accessToken"])

    detail = client.get(f"/api/v1/events/{event_id}")
    assert detail.status_code == 200
    event = detail.json()["event"]
    assert event["title"] == "Тестовый субботник"
    assert event["organizer"]["id"] == registered["user"]["id"]
    assert event["organizer"]["name"] == registered["user"]["name"]
    assert event["isFinished"] is False
    assert event["isOwner"] is False  # запрос без токена


def test_create_event_validates_data(client):
    registered = register_user(client)
    token = registered["tokens"]["accessToken"]

    res = client.post(
        "/api/v1/events",
        json={
            "title": "Тестовое мероприятие",
            "description": "Описание достаточно длинное.",
            "type": "dance_party",
            "location": "Парк",
            "startsAt": future_iso(),
        },
        headers=auth_header(token),
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"

    res = client.post(
        "/api/v1/events",
        json={
            "title": "Х",
            "description": "Описание достаточно длинное.",
            "type": "cleanup",
            "location": "Парк",
            "startsAt": future_iso(),
        },
        headers=auth_header(token),
    )
    assert res.status_code == 400

    res = client.post(
        "/api/v1/events",
        json={
            "title": "Тестовое мероприятие",
            "description": "Описание достаточно длинное.",
            "type": "cleanup",
            "location": "Парк",
            "startsAt": future_iso(10),
            "endsAt": future_iso(2),
        },
        headers=auth_header(token),
    )
    assert res.status_code == 400
    assert any(d["field"] == "endsAt" for d in res.json()["error"]["details"])


def test_list_events_filters_and_pagination(client):
    registered = register_user(client)
    token = registered["tokens"]["accessToken"]
    create_event(client, token, title="Субботник в парке", startsAt=future_iso(3))
    create_event(client, token, title="Посадка елей", type="tree_planting", startsAt=future_iso(10))
    create_event(client, token, title="Старый субботник", startsAt=past_iso())

    upcoming = client.get("/api/v1/events").json()
    assert upcoming["meta"]["total"] == 2
    assert [e["title"] for e in upcoming["items"]] == ["Субботник в парке", "Посадка елей"]

    past = client.get("/api/v1/events", params={"scope": "past"}).json()
    assert past["meta"]["total"] == 1
    assert past["items"][0]["title"] == "Старый субботник"

    filtered = client.get("/api/v1/events", params={"type": "tree_planting"}).json()
    assert filtered["meta"]["total"] == 1
    assert filtered["items"][0]["title"] == "Посадка елей"

    searched = client.get("/api/v1/events", params={"q": "ПАРКЕ"}).json()
    assert searched["meta"]["total"] == 1
    assert searched["items"][0]["title"] == "Субботник в парке"

    paged = client.get("/api/v1/events", params={"page": 1, "limit": 1}).json()
    assert len(paged["items"]) == 1
    assert paged["meta"]["totalPages"] == 2


def test_join_and_joined_flag(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])

    res = join_event(client, volunteer["tokens"]["accessToken"], event_id)
    assert res.status_code == 201

    detail = client.get(f"/api/v1/events/{event_id}", headers=auth_header(volunteer["tokens"]["accessToken"]))
    event = detail.json()["event"]
    assert event["joined"] is True
    assert event["participantsCount"] == 1
    assert event["participants"][0]["user"]["id"] == volunteer["user"]["id"]
    assert event["participants"][0]["status"] == "joined"


def test_join_duplicate_rejected(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])
    join_event(client, volunteer["tokens"]["accessToken"], event_id)

    res = join_event(client, volunteer["tokens"]["accessToken"], event_id)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALREADY_JOINED"


def test_join_own_event_rejected(client):
    organizer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])

    res = join_event(client, organizer["tokens"]["accessToken"], event_id)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "OWN_EVENT"


def test_join_respects_capacity(client):
    organizer = register_user(client)
    first = register_user(client)
    second = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"], capacity=1)
    join_event(client, first["tokens"]["accessToken"], event_id)

    res = join_event(client, second["tokens"]["accessToken"], event_id)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EVENT_FULL"


def test_join_finished_event_rejected(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"], startsAt=past_iso(2), endsAt=past_iso(1))

    res = join_event(client, volunteer["tokens"]["accessToken"], event_id)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EVENT_FINISHED"


def test_leave_event(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])
    join_event(client, volunteer["tokens"]["accessToken"], event_id)

    res = client.delete(f"/api/v1/events/{event_id}/join", headers=auth_header(volunteer["tokens"]["accessToken"]))
    assert res.status_code == 204

    again = client.delete(f"/api/v1/events/{event_id}/join", headers=auth_header(volunteer["tokens"]["accessToken"]))
    assert again.status_code == 404
    assert again.json()["error"]["code"] == "NOT_JOINED"


def test_confirm_awards_points(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"], pointsReward=25)
    join_event(client, volunteer["tokens"]["accessToken"], event_id)

    res = confirm_participant(client, organizer["tokens"]["accessToken"], event_id, volunteer["user"]["id"])
    assert res.status_code == 200
    body = res.json()
    assert body["pointsAwarded"] == 25
    assert body["participant"]["status"] == "confirmed"
    assert body["user"]["points"] == 25

    me = client.get("/api/v1/auth/me", headers=auth_header(volunteer["tokens"]["accessToken"]))
    assert me.json()["user"]["points"] == 25


def test_confirm_awards_once(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"], pointsReward=25)
    join_event(client, volunteer["tokens"]["accessToken"], event_id)
    confirm_participant(client, organizer["tokens"]["accessToken"], event_id, volunteer["user"]["id"])

    again = confirm_participant(client, organizer["tokens"]["accessToken"], event_id, volunteer["user"]["id"])
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "ALREADY_CONFIRMED"


def test_confirm_forbidden_for_outsider(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    outsider = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])
    join_event(client, volunteer["tokens"]["accessToken"], event_id)

    res = confirm_participant(client, outsider["tokens"]["accessToken"], event_id, volunteer["user"]["id"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_owner_can_update_and_delete(client):
    organizer = register_user(client)
    volunteer = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])
    join_event(client, volunteer["tokens"]["accessToken"], event_id)

    res = client.patch(
        f"/api/v1/events/{event_id}",
        json={
            "title": "Обновлённое название",
            "description": "Обновлённое описание мероприятия, достаточно длинное.",
            "type": "recycling",
            "location": "Новое место",
            "startsAt": future_iso(7),
            "capacity": 42,
            "pointsReward": 15,
        },
        headers=auth_header(organizer["tokens"]["accessToken"]),
    )
    assert res.status_code == 200

    detail = client.get(f"/api/v1/events/{event_id}").json()["event"]
    assert detail["title"] == "Обновлённое название"
    assert detail["capacity"] == 42

    deleted = client.delete(f"/api/v1/events/{event_id}", headers=auth_header(organizer["tokens"]["accessToken"]))
    assert deleted.status_code == 204

    after = client.get(f"/api/v1/events/{event_id}")
    assert after.status_code == 404


def test_outsider_cannot_modify(client):
    organizer = register_user(client)
    outsider = register_user(client)
    event_id = create_event(client, organizer["tokens"]["accessToken"])

    res = client.patch(
        f"/api/v1/events/{event_id}",
        json={
            "title": "Захват",
            "description": "Описание мероприятия для теста, достаточно длинное.",
            "type": "cleanup",
            "location": "Парк",
            "startsAt": future_iso(),
            "capacity": 10,
            "pointsReward": 20,
        },
        headers=auth_header(outsider["tokens"]["accessToken"]),
    )
    assert res.status_code == 403

    deleted = client.delete(f"/api/v1/events/{event_id}", headers=auth_header(outsider["tokens"]["accessToken"]))
    assert deleted.status_code == 403
