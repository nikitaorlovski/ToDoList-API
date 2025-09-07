from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import UserOrm


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, user: UserOrm):
        self.session.add(user)
        await self.session.flush()
        await self.session.commit()
        return user

    async def users_list(self) -> list[UserOrm]:
        result = await self.session.execute(select(UserOrm))
        return list(result.scalars().all())

    async def get_by_email(self, email) -> UserOrm | None:
        result = await self.session.execute(
            select(UserOrm).where(UserOrm.email == email)
        )
        return result.scalars().first()
