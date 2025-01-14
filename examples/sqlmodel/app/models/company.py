from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class CompanyBase(SQLModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = Field(default=None)


class Company(CompanyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class CompanyPublic(CompanyBase):
    id: Optional[int]


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass
