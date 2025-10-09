import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import (create_access_token, get_current_auth_user,
                      get_current_auth_user_for_refresh, rate_limiter)
from db.database import get_session
from db.models.task import TaskORM
from db.models.user import UserOrm
from db.schemas.task import (PaginatedTasks, TaskOut, TaskOutPublic,
                             TaskSchema, TaskUpdate)
from db.schemas.token import Token
from repositories.task_repository import TaskRepository

http_bearer = HTTPBearer(auto_error=False)
router = APIRouter(tags=["Tasks"], dependencies=[Depends(http_bearer)], prefix="/api")


async def get_task_repo(session: AsyncSession = Depends(get_session)) -> TaskRepository:
    return TaskRepository(session)


async def get_owned_task(
    task_id: Annotated[int, Path(ge=1)],
    user: UserOrm = Depends(get_current_auth_user),
    repo: TaskRepository = Depends(get_task_repo),
):
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not your task")
    return task


@router.post(
    "/refresh",
    response_model=Token,
    response_model_exclude_none=True,
    dependencies=[Depends(rate_limiter)],
)
async def refreshed(user: UserOrm = Depends(get_current_auth_user_for_refresh)):
    access = await create_access_token(user)
    return Token(access_token=access, token_type="Bearer")


@router.post(
    "/todos",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude={"author_id"},
    dependencies=[Depends(rate_limiter)],
)
async def create_todo(
    task: TaskSchema,
    user: UserOrm = Depends(get_current_auth_user),
    repo: TaskRepository = Depends(get_task_repo),
) -> TaskORM:
    new_task = TaskORM(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        term_date=task.term_date,
        author_id=user.id,
    )
    created = await repo.create_new_task(new_task)
    return created


@router.put(
    "/todos/{task_id}",
    response_model=TaskOut,
    response_model_exclude={"author_id"},
    dependencies=[Depends(rate_limiter)],
)
async def update_todo(
    task_update: TaskUpdate,
    task: TaskORM = Depends(get_owned_task),
    repo: TaskRepository = Depends(get_task_repo),
) -> TaskORM:
    fields = {}
    if task_update.title is not None:
        fields["title"] = task_update.title
    if task_update.description is not None:
        fields["description"] = task_update.description
    if task_update.status is not None:
        fields["status"] = task_update.status
    if task_update.priority is not None:
        fields["priority"] = task_update.priority
    if task_update.term_date is not None:
        fields["term_date"] = task_update.term_date
    return await repo.update_task(task, **fields)


@router.delete(
    "/todos/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limiter)],
)
async def delete_todo(
    task: TaskORM = Depends(get_owned_task),
    repo: TaskRepository = Depends(get_task_repo),
):
    await repo.delete_task(task)
    return


@router.get("/todos/{page}/{limit}", response_model=PaginatedTasks)
async def get_tasks_from_page(
    user: UserOrm = Depends(get_current_auth_user),
    page: int = Path(ge=1),
    limit: int = Path(ge=1, le=100),
    repo: TaskRepository = Depends(get_task_repo),
):
    items, total = await repo.get_by_pages(user_id=user.id, page=page, limit=limit)
    pages = max(1, math.ceil(total / limit)) if total else 1
    if page > 1 and not items:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Страница за доступным диапазоном"
        )
    public_items = [TaskOutPublic.model_validate(it) for it in items]
    return PaginatedTasks(
        items=public_items, page=page, limit=limit, total=total, pages=pages
    )
