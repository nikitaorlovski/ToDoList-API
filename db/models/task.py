from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from db.models.enums import TaskPriority, TaskStatus
from datetime import date

class TaskORM(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str | None]

    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status"),
        default=TaskStatus.NEW,
        server_default=TaskStatus.NEW.value,
        index=True,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, name="task_priority"),
        default=TaskPriority.NORMAL,
        server_default=TaskPriority.NORMAL.value,
        index=True,
        nullable=False,
    )
    term_date: Mapped[date] = mapped_column(Date, nullable=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped["UserOrm"] = relationship(back_populates="tasks")

    def __str__(self):
        return f"Задача {self.title}"
