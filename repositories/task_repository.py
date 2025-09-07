from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.task import TaskORM


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_new_task(self, task: TaskORM) -> TaskORM:
        self.session.add(task)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update_task(self, task: TaskORM, **fields):
        for k, v in fields.items():
            setattr(task, k, v)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: int) -> TaskORM | None:
        res = await self.session.execute(select(TaskORM).where(TaskORM.id == task_id))
        return res.scalar_one_or_none()

    async def delete_task(self, task: TaskORM) -> None:
        await self.session.delete(task)
        await self.session.commit()

    async def get_by_pages(
        self, user_id: int, page: int, limit: int
    ) -> tuple[list[TaskORM], int]:
        offset = (page - 1) * limit
        items_stmt = (
            select(TaskORM)
            .where(TaskORM.author_id == user_id)
            .order_by(TaskORM.id.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(items_stmt)
        items = res.scalars().all()
        total_stmt = select(func.count()).select_from(
            select(TaskORM.id).where(TaskORM.author_id == user_id).subquery()
        )
        total_res = await self.session.execute(total_stmt)
        total: int = total_res.scalar_one()
        return items, total
