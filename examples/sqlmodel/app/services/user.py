from better_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_hashed_password


class UserService(SqlalchemyCrudService[User]):
    def __init__(self):
        super().__init__(User)

    async def on_before_create(self, user_create: UserCreate, **kwargs):
        hashed_password = get_hashed_password(user_create.password)
        user_create.password = None
        return {
            "hashed_password": hashed_password
        }

    async def on_before_update(self, entity: User, user_update: UserUpdate, **kwargs):
        if user_update.password is not None:
            hashed_password = get_hashed_password(user_update.password)
            user_update.password = None
            return {
                "hashed_password": hashed_password
            }
