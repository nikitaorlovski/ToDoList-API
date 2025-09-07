from enum import StrEnum


class TaskStatus(StrEnum):
    NEW = "new"
    ACTIVE = "active"
    COMPLETED = "completed"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
