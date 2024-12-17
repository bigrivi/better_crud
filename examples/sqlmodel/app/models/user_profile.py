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
    gender: IGenderEnum | None = Field(
        default=IGenderEnum.other,
        sa_column=Column(ChoiceType(IGenderEnum, impl=String(20))),
    )
    phone: str | None = None
    birthdate:str = Field(default=None)
    hobby:str | None = Field(default=None)
    state: str | None = None
    country: str | None = None
    address: str | None = None


class UserProfile(UserProfileBase, table=True):
    __tablename__ = "user_profile"
    id: Optional[int] = Field(default=None, primary_key=True)


class UserProfileList(UserProfileBase):
    id:int

class UserProfileCreate(UserProfileBase):
    pass