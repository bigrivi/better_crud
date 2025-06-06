from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, collate
from datetime import datetime

from .user_profile import UserProfile, UserProfileList, UserProfileCreate
from .company import Company, CompanyPublic
from .user_role import UserRoleLink
from .user_project import UserProjectLink
from .user_zone import UserZoneLink
from .zone import Zone
from .role import Role, RolePublic
from .project import Project, ProjectPublic
from .user_task import UserTask, UserTaskList, UserTaskCreate
from .staff import Staff, StaffPublic, StaffCreate


class UserBase(SQLModel):
    email: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = None
    hashed_password: str
    profile_id: Optional[int] = Field(
        default=None, foreign_key="user_profile.id")
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    profile: UserProfile = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    tasks: List[UserTask] = Relationship(
        sa_relationship_kwargs={"uselist": True,
                                "order_by": "UserTask.id.asc()",
                                "cascade": "all, delete-orphan",
                                "lazy": "noload"})
    staff: Staff = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    company: Company = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    roles: List["Role"] = Relationship(back_populates="users", sa_relationship_kwargs={
                                       "lazy": "noload"}, link_model=UserRoleLink)
    projects: List["Project"] = Relationship(back_populates="users", sa_relationship_kwargs={
        "lazy": "noload"}, link_model=UserProjectLink)
    zone: Optional[Zone] = Relationship(
        sa_relationship_kwargs={
            "lazy": "noload", "uselist": False},
        link_model=UserZoneLink
    )
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class UserPublic(UserBase):
    id: int
    user_name: Optional[str] = None
    profile: Optional[UserProfileList] = None
    roles: List[RolePublic] = None
    projects: List[ProjectPublic] = None
    company: Optional[CompanyPublic] = None
    profile_id: Optional[int] = Field(
        default=None, foreign_key="user_profile.id")
    tasks: List[UserTaskList] = None
    company_id: Optional[int] = None
    staff: Optional[StaffPublic] = None


class UserCreate(UserBase):
    user_name: str
    password: str
    profile: Optional[UserProfileCreate] = None
    roles: Optional[List[int]] = None
    tasks: Optional[List[UserTaskCreate]] = None
    staff: Optional[StaffCreate] = None
    company_id: Optional[int] = None
    projects: Optional[List[int]] = None
    zone:Optional[int] = None


class UserCreateWithRolesDict(UserBase):
    user_name: str
    password: str
    profile: Optional[UserProfileCreate] = None
    roles: Optional[List[dict]] = None
    tasks: Optional[List[UserTaskCreate]] = None
    staff: Optional[StaffCreate] = None
    company_id: Optional[int] = None
    projects: Optional[List[int]] = None



class UserUpdate(UserBase):
    password: Optional[str] = None
    profile: Optional[UserProfileCreate] = None
    roles: List[int] = None
    tasks: Optional[List[UserTaskCreate]] = None
    staff: Optional[StaffCreate] = None
    company_id: Optional[int] = None
    projects: Optional[List[int]] = None
