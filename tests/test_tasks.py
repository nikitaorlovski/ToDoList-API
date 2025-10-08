import pytest
from starlette.requests import Request

from api.auth import get_token_from_cookie, auth_header
from db.models.enums import TaskStatus, TaskPriority
from db.schemas.task import TaskSchema
from tests.conftest import create_task_for_user


@pytest.mark.asyncio
async def test_create_todo_unauth(client):
    task = TaskSchema(title="Hellow",
            description=None,
            status=TaskStatus.NEW,
            priority=TaskPriority.NORMAL)
    response = await client.post("/api/todos",json=task.model_dump())
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_todo_authorized(authorized_client):
    client, user = authorized_client
    task = TaskSchema(title="Hellow",
            description=None,
            status=TaskStatus.NEW,
            priority=TaskPriority.NORMAL,
            term_date=None)
    response = await client.post("/api/todos",json=task.model_dump())
    assert response.status_code == 201


@pytest.mark.parametrize("title,description,status,priority,term_date",
                         [
                             pytest.param("","description","new","normal","2024-10-10",id="invalid title"),
                             pytest.param("title","description","status","normal","2024-10-10",id="invalid status"),
                             pytest.param("title","description","new","priority","2024-10-10",id="invalid priority"),
                             pytest.param("title","description","new","normal","date",id="invalid date"),


                         ])
@pytest.mark.asyncio
async def test_create_todo_authorized_invalid(authorized_client,title,description,status,priority,term_date):
    client, user = authorized_client
    task = {"title":title,
            "description":description,
            "status":status,
            "priority":priority,
            "term_date":term_date}
    response = await client.post("/api/todos",json=task)
    assert response.status_code == 422, response.text

@pytest.mark.asyncio
async def test_update_todo_unauthorized(client):
    response = await client.put("/api/todos/1", json={"title": "Updated"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_todo_invalid_author(authorized_client,user_factory,create_task_for_user):
    client, user = authorized_client
    other_user = await user_factory(email="other@example.com")
    task = await create_task_for_user(other_user, title="Hellow")

    response = await client.put(f"/api/todos/{task.id}", json={"title": "Updated"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_todo_not_found_task(authorized_client):
    client, user = authorized_client

    response = await client.put(f"/api/todos/9999", json={"title": "Updated"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_todo_not_write_id(authorized_client):
    client, user = authorized_client

    response = await client.put(f"/api/todos/", json={"title": "Updated"})
    assert response.status_code == 307

@pytest.mark.asyncio
async def test_update_todo_id_not_int(authorized_client):
    client, user = authorized_client

    response = await client.put(f"/api/todos/d", json={"title": "Updated"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_todo_valid(authorized_client,create_task_for_user):
    client, user = authorized_client
    task = await create_task_for_user(user, title="Hellow")

    response = await client.delete(f"/api/todos/{task.id}")
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_delete_todo_invalid_author(authorized_client,user_factory,create_task_for_user):
    client, user = authorized_client
    other_user = await user_factory(email="other@example.com")
    task = await create_task_for_user(other_user, title="Hellow")

    response = await client.delete(f"/api/todos/{task.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_todo_not_found(authorized_client):
    client, user = authorized_client
    response = await client.delete(f"/api/todos/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_todo_not_int(authorized_client):
    client, user = authorized_client
    response = await client.delete(f"/api/todos/d")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_todo_unauth(client):

    response = await client.delete(f"/api/todos/4")
    assert response.status_code == 401

@pytest.mark.parametrize("page,limit",
                         [
                             pytest.param("1","5"),

                         ])
@pytest.mark.asyncio
async def test_get_tasks_from_page_valid(authorized_client,page,limit,create_task_for_user):
    client, user = authorized_client
    task = await create_task_for_user(user, title="Hellow")
    response = await client.get(f"/api/todos/{page}/{limit}")
    data = response.json()
    assert data["total"] >= 1
    assert isinstance(data["items"], list)
    assert all("title" in item for item in data["items"])
    assert "items" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data
    assert "pages" in data

@pytest.mark.asyncio
async def test_get_tasks_from_page_not_found(authorized_client,create_task_for_user):
    client, user = authorized_client
    task = await create_task_for_user(user, title="Hellow")
    response = await client.get("/api/todos/2/5")
    assert response.status_code == 404


@pytest.mark.parametrize("page,limit",
                         [
                             pytest.param("0","5"),
                             pytest.param("1","120"),

                         ])
@pytest.mark.asyncio
async def test_get_tasks_from_page_invalid(authorized_client,page,limit):
    client, user = authorized_client
    response = await client.get(f"/api/todos/{page}/{limit}")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_tasks_from_page_unauth(client):
    response = await client.get("/api/todos/1/5")
    assert response.status_code == 401

def test_auth_header():
    assert auth_header(None) == {}
    assert auth_header("abc") == {"Authorization": "abc"}

def test_get_token_from_cookie():
    request = Request(scope={"type": "http"})
    request._cookies = {"access_token": "testtoken"}
    assert get_token_from_cookie(request) == "testtoken"


