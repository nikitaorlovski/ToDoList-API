from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class UserOrm(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[bytes]
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    tasks: Mapped[list["TaskORM"]] = relationship(
        back_populates="author", cascade="all, delete-orphan", lazy="selectin"
    )

    def __str__(self):
        return f"Пользователь {self.name}"