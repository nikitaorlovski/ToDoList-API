from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.auth import rate_limiter
from core.security import hash_password
from db.models.enums import TaskStatus, TaskPriority
from db.models.task import TaskORM
from db.models.user import UserOrm
from main import app
from db.database import Base, get_session

test_db_url = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(test_db_url)
TestSessionLocal = async_sessionmaker(bind=test_engine,expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def test_db_session():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def clear_tables(test_db_session):

    tables = reversed(Base.metadata.sorted_tables)

    await test_db_session.execute(text("PRAGMA foreign_keys=OFF"))

    for table in tables:
        await test_db_session.execute(text(f"DELETE FROM {table.name};"))

    await test_db_session.execute(text("PRAGMA foreign_keys=ON"))
    await test_db_session.commit()

@pytest_asyncio.fixture
async def client(test_db_session):
    async def override_get_session():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[rate_limiter] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
def user_factory(test_db_session):
    async def _create_user(
            name="TestUser",
            email="test@example.com",
            password="123456",
            is_admin=False,
            session=None,
    ):
        user = UserOrm(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            is_admin=is_admin,
        )
        db = session or test_db_session
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    return _create_user

@pytest_asyncio.fixture
async def authorized_client(client, user_factory):

    user = await user_factory(email="authuser@example.com", password="authpass123")

    response = await client.post(
        "/api/login",
        data={"email": user.email, "password": "authpass123"},
    )
    assert response.status_code == 200, response.text

    access_token = response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {access_token}"})

    return client, user

@pytest_asyncio.fixture
async def create_task_for_user(test_db_session):
    async def _create_task(user, **kwargs):
        task = TaskORM(
            title=kwargs.get("title", "Test task"),
            description=kwargs.get("description", "desc"),
            status=kwargs.get("status", TaskStatus.NEW),
            priority=kwargs.get("priority", TaskPriority.NORMAL),
            term_date=kwargs.get("term_date", date.today()),
            author_id=user.id
        )
        test_db_session.add(task)
        await test_db_session.commit()
        await test_db_session.refresh(task)
        return task
    return _create_task
