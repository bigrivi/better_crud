from typing import Optional, List
from enum import Enum
from sqlalchemy_utils import ChoiceType
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from pydantic import BaseModel


class IGenderEnum(str, Enum):
    female = "female"
    male = "male"
    other = "other"


class UserProfileBase(BaseModel):
    name: str
    phone: str | None = None
    birthdate: str = None
    hobby: str | None = None
    state: str | None = None
    country: str | None = None
    address: str | None = None
    gender: Optional[IGenderEnum] = None


class UserProfile(Base):
    __tablename__ = "user_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gender: Mapped[IGenderEnum | None] = mapped_column(
        ChoiceType(IGenderEnum, impl=String(20)),
        default=IGenderEnum.other,
    )
    name: Mapped[str | None] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(50))
    birthdate: Mapped[str | None] = mapped_column(String(50))
    hobby: Mapped[str | None] = mapped_column(String(50))
    state: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(50))


class UserProfilePublic(UserProfileBase):
    id: int


class UserProfileCreate(UserProfileBase):
    pass
