from fastapi_crud.service.sqlalchemy import SqlalchemyCrudService
from ..models.company import Company


class CompanyService(SqlalchemyCrudService[Company]):
    def __init__(self):
        super().__init__(Company)
