
## Hooks on your crud action

| Name             | Description            |
| ---------------- | ---------------------- |
| on_before_create | Called before creation |
| on_after_create  | Called after creation  |
| on_before_update | Called before update   |
| on_after_update  | Called after update    |
| on_before_delete | Called before deletion |
| on_after_delete  | Called after deletion  |


The corresponding function signature is as follows

```python

from pydantic import BaseModel
from fastapi import BackgroundTasks


CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

async def on_before_create(
    self,
    model: CreateSchemaType,
    background_tasks: Optional[BackgroundTasks] = None
) -> Union[Dict[str, Any], None]:
    pass

async def on_after_create(
    self,
    entity: ModelType,
    background_tasks: BackgroundTasks
) -> None:
    pass

async def on_before_update(
    self,
    entity: ModelType,
    model: UpdateSchemaType,
    background_tasks: BackgroundTasks
) -> Union[Dict[str, Any], None]:
    pass

async def on_after_update(
    self,
    entity: ModelType,
    background_tasks: BackgroundTasks
) -> None:
    pass

async def on_before_delete(
    self,
    entities: List[ModelType],
    background_tasks: BackgroundTasks
) -> None:
    pass

async def on_after_delete(
    self,
    entities: List[ModelType],
    background_tasks: BackgroundTasks
) -> None:
    pass


```

## Example1

Process the password passed in by the user

```python title="user_service.py"

from fastapi import Depends
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
```

## Example2

Check if it exists before creating it


```python title="user_service.py"

from fastapi import Depends
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_hashed_password

class UserService(SqlalchemyCrudService[User]):
    def __init__(self):
        super().__init__(User)

    async def on_before_create(self, user_create: UserCreate, **kwargs):
        exist_by_user_name = await self.get_one([User.user_name == user_create.user_name])
        if exist_by_user_name:
            raise BadRequestError(msg=f"The user_name {user_create.user_name} already exists")
```