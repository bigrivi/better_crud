from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, String, Column


class StaffBase(SQLModel):
    name: Optional[str] = None
    position: Optional[str] = None
    job_title: Optional[str] = None


class Staff(StaffBase, table=True):
    __tablename__ = "staff"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id"
    )


class StaffPublic(StaffBase):
    id: int


class StaffCreate(StaffBase):
    pass
