from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    "sqlite+aiosqlite:///tasks.db",
    echo=False,
)

new_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # ← без ()


async def get_session() -> AsyncSession:
    async with new_session() as session:
        yield session
