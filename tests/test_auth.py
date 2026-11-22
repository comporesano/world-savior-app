"""Тесты регистрации, входа, ротации refresh-токенов и профиля."""

from tests.helpers import auth_header, register_user


def test_register_creates_user_and_tokens(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Мария Иванова", "email": "maria@test.dev", "password": "password123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["name"] == "Мария Иванова"
    assert body["user"]["email"] == "maria@test.dev"
    assert body["user"]["points"] == 0
    assert "password" not in body["user"] and "password_hash" not in body["user"]
    assert body["tokens"]["accessToken"]
    assert body["tokens"]["refreshToken"]


def test_register_rejects_duplicate_email(client):
    register_user(client, email="dup@test.dev")
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Другой Пользователь", "email": "dup@test.dev", "password": "password123"},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMAIL_TAKEN"


def test_register_validates_input(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "not-an-email", "password": "short"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    fields = [d["field"] for d in res.json()["error"]["details"]]
    assert "name" in fields
    assert "email" in fields
    assert "password" in fields


def test_login_success(client):
    register_user(client, email="login@test.dev")
    res = client.post("/api/v1/auth/login", json={"email": "login@test.dev", "password": "password123"})
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "login@test.dev"
    assert res.json()["tokens"]["accessToken"]


def test_login_wrong_password(client):
    register_user(client, email="login@test.dev")
    res = client.post("/api/v1/auth/login", json={"email": "login@test.dev", "password": "wrong-password"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_returns_profile(client):
    registered = register_user(client)
    res = client.get("/api/v1/auth/me", headers=auth_header(registered["tokens"]["accessToken"]))
    assert res.status_code == 200
    assert res.json()["user"]["email"] == registered["user"]["email"]
    assert res.json()["user"]["level"] == 1
    assert res.json()["levelProgress"]["progress"] == 0


def test_me_requires_auth(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_rejects_fake_token(client):
    res = client.get("/api/v1/auth/me", headers=auth_header("fake.token.value"))
    assert res.status_code == 401


def test_refresh_rotates_tokens(client):
    registered = register_user(client)
    first = client.post("/api/v1/auth/refresh", json={"refreshToken": registered["tokens"]["refreshToken"]})
    assert first.status_code == 200
    assert first.json()["tokens"]["refreshToken"] != registered["tokens"]["refreshToken"]

    second = client.post("/api/v1/auth/refresh", json={"refreshToken": first.json()["tokens"]["refreshToken"]})
    assert second.status_code == 200


def test_refresh_detects_reuse_and_revokes_all(client):
    registered = register_user(client)
    rotated = client.post("/api/v1/auth/refresh", json={"refreshToken": registered["tokens"]["refreshToken"]})
    assert rotated.status_code == 200

    reused = client.post("/api/v1/auth/refresh", json={"refreshToken": registered["tokens"]["refreshToken"]})
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "TOKEN_REUSE_DETECTED"

    after = client.post("/api/v1/auth/refresh", json={"refreshToken": rotated.json()["tokens"]["refreshToken"]})
    assert after.status_code == 401


def test_logout_revokes_refresh_token(client):
    registered = register_user(client)
    logout = client.post("/api/v1/auth/logout", json={"refreshToken": registered["tokens"]["refreshToken"]})
    assert logout.status_code == 204

    refresh = client.post("/api/v1/auth/refresh", json={"refreshToken": registered["tokens"]["refreshToken"]})
    assert refresh.status_code == 401


def test_patch_me_updates_profile(client):
    registered = register_user(client)
    res = client.patch(
        "/api/v1/me",
        json={"name": "Новое Имя", "bio": "Новое био"},
        headers=auth_header(registered["tokens"]["accessToken"]),
    )
    assert res.status_code == 200
    assert res.json()["user"]["name"] == "Новое Имя"
    assert res.json()["user"]["bio"] == "Новое био"


def test_patch_me_requires_auth(client):
    res = client.patch("/api/v1/me", json={"name": "Хакер"})
    assert res.status_code == 401
