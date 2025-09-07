from typing import Optional

from pydantic import BaseModel

from db.models.enums import TaskPriority, TaskStatus


class TaskSchema(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.NORMAL


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    author_id: int

    model_config = {"from_attributes": True}


class TaskOutPublic(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority

    model_config = {"from_attributes": True}


class PaginatedTasks(BaseModel):
    items: list[TaskOutPublic]
    page: int
    limit: int
    total: int
    pages: int
