from fastapi_crud import SqlalchemyCrudService
from app.models.role import Role

class RoleService(SqlalchemyCrudService[Role]):
    def __init__(self):
        super().__init__(Role)
