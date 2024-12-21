from typing import Annotated
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, declared_attr, mapped_column

# id_key = Annotated[
#     int, mapped_column(primary_key=True, index=True,
#                        autoincrement=True, sort_order=-999)
# ]


class MappedBase(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


# class Base(MappedAsDataclass, MappedBase):
#     __abstract__ = True

class Base(MappedBase):
    __abstract__ = True
