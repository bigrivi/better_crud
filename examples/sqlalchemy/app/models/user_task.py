from typing import Optional
from enum import Enum
from sqlalchemy_utils import ChoiceType
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from pydantic import BaseModel


class TaskStatusEnum(str, Enum):
    pending = "pending"
    inprogress = "inprogress"
    completed = "completed"


class UserTaskBase(BaseModel):
    description: str
    status: TaskStatusEnum | None = None


class UserTask(Base):
    __tablename__ = "user_task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    status: Mapped[TaskStatusEnum | None] = mapped_column(
        ChoiceType(TaskStatusEnum, impl=String(20))
    )
    description: Mapped[str] = mapped_column(String(200))


class UserTaskPublic(UserTaskBase):
    id: int


class UserTaskCreate(UserTaskBase):
    pass


class UserTaskUpdate(UserTaskBase):
    id: Optional[int] = None
