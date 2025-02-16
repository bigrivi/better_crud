from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, String, Column
from app.models.user import User, UserPublic


class PostBase(SQLModel):
    title: str
    description: Optional[str] = None


class Post(PostBase, table=True):
    __tablename__ = "post"
    id: Optional[int] = Field(default=None, primary_key=True)
    creater_user_id: Optional[int] = Field(
        default=None, foreign_key="user.id"
    )
    modifier_user_id: Optional[int] = Field(
        default=None, foreign_key="user.id"
    )

    creater_user: User = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload", "foreign_keys": "[Post.creater_user_id]"})

    modifier_user: User = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload", "foreign_keys": "[Post.modifier_user_id]"})


class PostPublic(PostBase):
    id: int
    creater_user: Optional[UserPublic] = None
    modifiier_user: Optional[UserPublic] = None


class PostCreate(PostBase):
    creater_user_id: int


class PostUpdate(PostBase):
    modifiier_user_id: int
