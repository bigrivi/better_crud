from sqlalchemy import INT, Column, ForeignKey, Integer, Table
from app.db.base import MappedBase

UserRoleLink = Table(
    'user_role',
    MappedBase.metadata,
    Column('id', INT, primary_key=True, unique=True,
           index=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey(
        'user.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey(
        'role.id', ondelete='CASCADE'), primary_key=True),
)
