from fastapi_crud import SqlalchemyCrudService
from app.models.user import User,UserCreate
from app.core.security import get_hashed_password

class UserService(SqlalchemyCrudService[User]):
    def __init__(self):
        super().__init__(User)

    async def on_before_create(self,user:UserCreate):
        hashed_password = get_hashed_password(user.password)
        return {"hashed_password":hashed_password}

