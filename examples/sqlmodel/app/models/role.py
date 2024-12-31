from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from .user_role import UserRoleLink
if TYPE_CHECKING:
    from .user import User


class RoleBase(SQLModel):
    name: str
    description: str = Field(default=None)


class Role(RoleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(
        back_populates="roles", sa_relationship_kwargs={"viewonly": True}, link_model=UserRoleLink)


class RolePublic(RoleBase):
    id: Optional[int]


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    pass
