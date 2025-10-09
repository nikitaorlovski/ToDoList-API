import pytest

from api.auth import create_refresh_token


@pytest.mark.asyncio
async def test_refresh_token(authorized_client, test_db_session):
    client, user = authorized_client
    refresh_token = await create_refresh_token(user)
    client.cookies.clear()

    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = await client.post("/api/refresh", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(authorized_client, test_db_session):
    client, user = authorized_client

    response = await client.post("/api/refresh")
    assert response.status_code == 401, response.text
    assert (
        "Неправильный тип токена: 'access' когда ожидался 'refresh'"
        == response.json()["detail"]
    )
