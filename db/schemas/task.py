from typing import Optional

from pydantic import BaseModel, field_validator

from db.models.enums import TaskPriority, TaskStatus
from datetime import date

class TaskSchema(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.NORMAL
    term_date: Optional[date] = None

    @field_validator('term_date', mode='before')
    def parse_date(cls, v):
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    class Config:
        json_encoders = {
            date: lambda v: v.strftime('%Y-%m-%d')  # Сериализуем в строку в формате 'YYYY-MM-DD'
        }

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    term_date: Optional[date] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    author_id: int
    term_date: Optional[date]
    model_config = {"from_attributes": True}


class TaskOutPublic(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    term_date: Optional[date]
    model_config = {"from_attributes": True}


class PaginatedTasks(BaseModel):
    items: list[TaskOutPublic]
    page: int
    limit: int
    total: int
    pages: int
