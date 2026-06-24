import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, register_payload: dict):
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]["tokens"]
    assert "refresh_token" in data["data"]["tokens"]
    assert "merchant" in data["data"]
    assert data["data"]["merchant"]["email"] == register_payload["email"]


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient, register_payload: dict):
    await client.post("/api/v1/auth/register", json=register_payload)
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_phone(client: AsyncClient, register_payload: dict):
    register_payload["phone"] = "0171234567"  # missing +880 prefix
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, register_payload: dict):
    await client.post("/api/v1/auth/register", json=register_payload)
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": register_payload["phone"], "password": register_payload["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]["tokens"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, register_payload: dict):
    await client.post("/api/v1/auth/register", json=register_payload)
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": register_payload["phone"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=register_payload)
    access_token = reg.json()["data"]["tokens"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == register_payload["email"]


@pytest.mark.asyncio
async def test_refresh_tokens(client: AsyncClient, register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=register_payload)
    refresh_token = reg.json()["data"]["tokens"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data

    # Verify invalid refresh token is rejected
    bad = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not.a.token"})
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=register_payload)
    tokens = reg.json()["data"]["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert logout.status_code == 200

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401
