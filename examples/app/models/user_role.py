from typing import Optional,List
from sqlmodel import Field, SQLModel,Relationship

class UserRoleLink(SQLModel, table=True):
    __tablename__ = "user_role"
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    role_id: Optional[int] = Field(
        default=None, foreign_key="role.id", primary_key=True
    )