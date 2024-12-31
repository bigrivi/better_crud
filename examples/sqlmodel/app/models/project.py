from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from .user_project import UserProjectLink
if TYPE_CHECKING:
    from .user import User
    from .company import Company


class ProjectBase(SQLModel):
    name: str | None = None
    description: str | None = Field(default=None)
    company_id: Optional[int] = Field(
        default=None, foreign_key="company.id"
    )
    is_active: Optional[bool] = Field(default=True)


class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(
        back_populates="projects", sa_relationship_kwargs={"viewonly": True}, link_model=UserProjectLink)
    company: "Company" = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})


class ProjectPublic(ProjectBase):
    id: Optional[int]


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass
