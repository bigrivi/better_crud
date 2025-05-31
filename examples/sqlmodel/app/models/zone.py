from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel


class ZoneBase(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)


class Zone(ZoneBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)



class ZonePublic(ZoneBase):
    id: Optional[int]


