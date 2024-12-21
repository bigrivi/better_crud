from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from pydantic import BaseModel


class StaffBase(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    job_title: Optional[str] = None


class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(100))
    job_title: Mapped[str] = mapped_column(String(100))


class StaffPublic(StaffBase):
    id: int


class StaffCreate(StaffBase):
    pass
