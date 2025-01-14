from typing import Optional, List
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from pydantic import BaseModel


class Company(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    domain: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))


class CompanyBase(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None


class CompanyPublic(CompanyBase):
    id: Optional[int]


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass
