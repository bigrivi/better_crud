from better_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.user_task import UserTask


class UserTaskService(SqlalchemyCrudService[UserTask]):
    def __init__(self):
        super().__init__(UserTask)
