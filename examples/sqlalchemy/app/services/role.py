from better_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.role import Role
from app.db.session import get_session


class RoleService(SqlalchemyCrudService[Role]):
    def __init__(self):
        super().__init__(Role)
