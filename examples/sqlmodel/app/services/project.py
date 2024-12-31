from fastapi_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.project import Project


class ProjectService(SqlalchemyCrudService[Project]):
    def __init__(self):
        super().__init__(Project)
