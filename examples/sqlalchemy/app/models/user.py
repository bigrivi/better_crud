from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from pydantic import BaseModel
from .user_profile import UserProfile, UserProfilePublic, UserProfileCreate
from .company import Company, CompanyPublic
from .user_role import UserRoleLink
from .role import Role, RolePublic
from .user_task import UserTask, UserTaskPublic, UserTaskCreate, UserTaskUpdate
from .staff import Staff, StaffPublic, StaffCreate


class UserBase(BaseModel):
    email: str
    is_active: bool = None
    is_superuser: Optional[bool] = None


class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    hashed_password: Mapped[str] = mapped_column(String(250))
    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_profile.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("company.id"))
    profile: Mapped[UserProfile | None] = relationship(
        uselist=False, lazy="noload")
    staff: Mapped[Optional[Staff]] = relationship(
        uselist=False, lazy="noload")
    tasks: Mapped[List[UserTask]] = relationship(
        uselist=True, cascade="all, delete-orphan", lazy="noload")
    company: Mapped[Company] = relationship(
        uselist=False, lazy="noload")
    roles: Mapped[List[Role]] = relationship(
        back_populates="users", lazy="noload", secondary=UserRoleLink)

    deleted_at: Mapped[Optional[datetime]] = mapped_column()


class UserPublic(UserBase):
    id: int
    profile: Optional[UserProfilePublic] = None
    roles: List[RolePublic] = None
    company: Optional[CompanyPublic] = None
    profile_id: Optional[int] = None
    tasks: List[UserTaskPublic] = None
    company_id: Optional[int] = None
    staff: Optional[StaffPublic] = None


class UserCreate(UserBase):
    company_id: Optional[int] = None
    password: str
    profile: UserProfileCreate = None
    roles: List[int]
    tasks: Optional[List[UserTaskCreate]] = None
    staff: Optional[StaffCreate] = None


class UserUpdate(UserBase):
    company_id: Optional[int] = None
    password: Optional[str] = None
    profile: Optional[UserProfileCreate] = None
    roles: Optional[List[int]] = None
    tasks: Optional[List[UserTaskUpdate]] = None
    staff: Optional[StaffCreate] = None
