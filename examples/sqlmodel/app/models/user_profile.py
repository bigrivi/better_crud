from typing import Optional,List
from sqlmodel import Field, SQLModel,Relationship,String,Column
from enum import Enum
from sqlalchemy_utils import ChoiceType


class IGenderEnum(str, Enum):
    female = "female"
    male = "male"
    other = "other"

class UserProfileBase(SQLModel):
    name: str
    gender: Optional[IGenderEnum] = Field(
        default=IGenderEnum.other,
        sa_column=Column(ChoiceType(IGenderEnum, impl=String(20))),
    )
    phone: Optional[str] = None
    birthdate:str = Field(default=None)
    hobby:Optional[str] = Field(default=None)
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None


class UserProfile(UserProfileBase, table=True):
    __tablename__ = "user_profile"
    id: Optional[int] = Field(default=None, primary_key=True)


class UserProfileList(UserProfileBase):
    id:int

class UserProfileCreate(UserProfileBase):
    pass