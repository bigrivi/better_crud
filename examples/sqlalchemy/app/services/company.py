from fastapi_crud.service.sqlalchemy import SqlalchemyCrudService
from ..models.company import Company


class CompanyService(SqlalchemyCrudService[Company]):
    def __init__(self):
        super().__init__(Company)

    async def on_before_create(
        self,
        create_data: dict,
        background_tasks=None
    ) -> None:
        print("on_before_create call")
