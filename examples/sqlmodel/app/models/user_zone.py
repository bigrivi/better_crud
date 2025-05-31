from typing import Optional,List
from sqlmodel import Field, SQLModel,Relationship

class UserZoneLink(SQLModel, table=True):
    __tablename__ = "user_zone"
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    zone_id: Optional[int] = Field(
        default=None, foreign_key="zone.id", primary_key=True
    )