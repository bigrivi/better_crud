from fastapi_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.user import User
from app.core.security import get_hashed_password


class UserService(SqlalchemyCrudService[User]):
    def __init__(self):
        super().__init__(User)

    async def on_before_create(self, create_data: dict, **kwargs):
        hashed_password = get_hashed_password(create_data["password"])
        create_data["hashed_password"] = hashed_password
        del create_data["password"]

    async def on_before_update(self, entity: User, update_data: dict, **kwargs):
        if "password" in update_data:
            hashed_password = get_hashed_password(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
