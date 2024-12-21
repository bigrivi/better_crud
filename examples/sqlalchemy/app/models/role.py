from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from pydantic import BaseModel
from .user_role import UserRoleLink
if TYPE_CHECKING:
    from .user import User


class Role(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    users: Mapped[List['User']] = relationship(
        lazy="noload", secondary=UserRoleLink, back_populates='roles'
    )


class RoleBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RolePublic(RoleBase):
    id: int


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    pass
