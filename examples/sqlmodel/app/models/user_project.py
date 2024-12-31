from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class UserProjectLink(SQLModel, table=True):
    __tablename__ = "user_project"
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    project_id: Optional[int] = Field(
        default=None, foreign_key="project.id", primary_key=True
    )
