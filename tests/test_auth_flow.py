import pytest


@pytest.mark.asyncio
async def test_register_login_logout_sessions(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "pass1234"},
        headers={"User-Agent": "pytest"},
    )
    assert r.status_code == 201
    body = r.json()
    assert "access" in body and "refresh" in body

    access = body["access"]
    refresh = body["refresh"]

    r = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 200
    sessions = r.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1

    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "pass1234"},
        headers={"User-Agent": "pytest"},
    )
    assert r.status_code == 200
    body2 = r.json()
    assert "access" in body2 and "refresh" in body2

    r = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh": body2["refresh"]},
        headers={"User-Agent": "pytest"},
    )
    assert r.status_code == 200
    body3 = r.json()
    assert "access" in body3 and "refresh" in body3

    r = await client.post("/api/v1/auth/logout", json={"refresh": body3["refresh"]})
    assert r.status_code == 204

    r = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh": body3["refresh"]},
        headers={"User-Agent": "pytest"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    r1 = await client.post(
        "/api/v1/auth/register",
        json={"name": "Bob", "email": "dup@example.com", "password": "pass1234"},
    )
    assert r1.status_code == 201

    r2 = await client.post(
        "/api/v1/auth/register",
        json={"name": "Bob2", "email": "dup@example.com", "password": "pass1234"},
    )
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "nope@example.com", "password": "wrong"},
    )
    assert r.status_code == 401
