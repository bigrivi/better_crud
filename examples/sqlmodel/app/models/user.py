from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from datetime import datetime
from .user_profile import UserProfile, UserProfileList, UserProfileCreate
from .company import Company, CompanyPublic
from .user_role import UserRoleLink
from .role import Role, RolePublic
from .user_task import UserTask, UserTaskList, UserTaskCreate
from .staff import Staff, StaffPublic, StaffCreate


class UserBase(SQLModel):
    email: str
    is_active: bool = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    profile_id: Optional[int] = Field(
        default=None, foreign_key="user_profile.id")
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    profile: UserProfile = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    tasks: List[UserTask] = Relationship(
        sa_relationship_kwargs={"uselist": True, "cascade": "all, delete-orphan", "lazy": "noload"})
    staff: Staff = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    company: Company = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    roles: List["Role"] = Relationship(back_populates="users", sa_relationship_kwargs={
                                       "lazy": "noload"}, link_model=UserRoleLink)
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class UserPublic(UserBase):
    id: int
    profile: Optional[UserProfileList] = None
    roles: List[RolePublic] = None
    company: Optional[CompanyPublic] = None
    profile_id: Optional[int] = Field(
        default=None, foreign_key="user_profile.id")
    tasks: List[UserTaskList] = None
    company_id: Optional[int] = None
    staff: Optional[StaffPublic] = None


class UserCreate(UserBase):
    password: str
    profile: UserProfileCreate = None
    roles: List[int]
    tasks: Optional[List[UserTaskCreate]] = None
    staff: Optional[StaffCreate] = None
    company_id: Optional[int] = None


class UserUpdate(UserBase):
    password: str = None
    profile: UserProfileCreate = None
    roles: List[int] = None
    tasks: Optional[List[UserTaskCreate]] = None
    staff: Optional[StaffCreate] = None
    company_id: Optional[int] = None
