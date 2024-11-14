from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from datetime import datetime
from .user_profile import UserProfile, UserProfileList, UserProfileCreate
from .company import Company, CompanyPublic
from .user_role import UserRoleLink
from .role import Role, RolePublic


class UserBase(SQLModel):
    email: str
    is_active: bool = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")



class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    profile_id: Optional[int] = Field(
        default=None, foreign_key="user_profile.id")
    profile: UserProfile = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "joined"})
    company: Company = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "joined"})
    roles: List["Role"] = Relationship(back_populates="users", sa_relationship_kwargs={
                                       "lazy": "joined"}, link_model=UserRoleLink)
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

class UserCreate(UserBase):
    password: str
    profile: UserProfileCreate = None
    roles: List[int]


class UserUpdate(UserBase):
    profile: UserProfileCreate = None
    roles: List[int] = None
