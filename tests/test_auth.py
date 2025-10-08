import pytest

from db.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_valid_registration(client):
    user = UserCreate(name="killchik",email="orlovski15555@gmail.com",password="123456")
    response = await client.post("/api/registration",json=user.model_dump())
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.parametrize("name,email,password",
                         [
                             pytest.param("killchik","orlovski15555","123456",id="invalid email"),
                             pytest.param("killchiks","orlovski155556@gmail.com","1234",id="invalid password"),
                             pytest.param("killchik","orlovski@gmail.com","123456",id="duplicate email")

                         ])
@pytest.mark.asyncio
async def test_invalid_registration(client,name,email,password,user_factory):
    user_in_db = await user_factory(email="orlovski@gmail.com")
    invalid_user = {
        "name": name,
        "email": email,
        "password": password,
    }
    response = await client.post("/api/registration",json=invalid_user)
    assert response.status_code in (422,409), response.text

@pytest.mark.asyncio
async def test_authorization(client, user_factory):
    user = await user_factory(email="orlovski@gmail.com",password="testpass123")
    response = await client.post(
        "/api/login",
        data={
            "email": user.email,
            "password": "testpass123"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.parametrize("email,password",
                         [
                             pytest.param("orlovski15555@gmail.com","123456",id="invalid auth-email"),
                             pytest.param("orlovski@gmail.com","1234567",id="invalid auth-password"),

                         ])
@pytest.mark.asyncio
async def test_authorization_invalid(client, user_factory,email,password):
    user = await user_factory(email="orlovski@gmail.com", password="testpass123")
    response = await client.post(
        "/api/login",
        data={
            "email": email,
            "password": password
        }
    )
    assert response.status_code == 401, response.text