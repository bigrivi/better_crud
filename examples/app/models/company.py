from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class CompanyBase(SQLModel):
    name: str | None = None
    domain: str | None = None
    description: str | None = Field(default=None)


class Company(CompanyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class CompanyPublic(CompanyBase):
    id: Optional[int]


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass
