from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, String, Column
from enum import Enum
from sqlalchemy_utils import ChoiceType


class TaskStatusEnum(str, Enum):
    pending = "pending"
    inprogress = "inprogress"
    completed = "completed"


class UserTaskBase(SQLModel):
    description: str
    status: TaskStatusEnum | None = Field(
        sa_column=Column(ChoiceType(TaskStatusEnum, impl=String(20))),
    )


class UserTask(UserTaskBase, table=True):
    __tablename__ = "user_task"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id"
    )


class UserTaskList(UserTaskBase):
    id: int

class UserTaskPublic(UserTaskBase):
    id: int
    user_id: Optional[int]

class UserTaskCreate(UserTaskBase):
    id: Optional[int] = None


class UserTaskCreateWithoutId(UserTaskBase):
    pass
