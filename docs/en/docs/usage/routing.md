The following are the routes that BetterCRUD automatically generates. You can disable and rewrite them.

## Default Routes

| Route                | Method     | Description |
| -------------------- | ---------- | ----------- |
| /resource            | **GET**    | Get Many    |
| /resource/{id}       | **GET**    | Get One     |
| /resource            | **POST**   | Create One  |
| /resource/bulk       | **POST**   | Create Many |
| /resource/{id}       | **PUT**    | Update One  |
| /resource/{ids}/bulk | **PUT**    | Update Many |
| /resource/{ids}      | **DELETE** | Delete Many |


## Disabling Routes

### 1. Globally disable

```python

BetterCrudGlobalConfig.init(
    routes={
        "exclude":["update_many","create_many"]
    }
)

```

### 2. Disable in specific routes
```python

@crud(
    routes={
        "exclude":["update_many","create_many"]
    }
)
class PetController():
    service: PetService = Depends(PetService)

```


## Overriding Routes

Sometimes you want to rewrite some routes

```python hl_lines="22-30"
from fastapi import APIRouter, Depends
from better_crud import crud
from .schema import PetCreate, PetUpdate, PetPublic
from .service import PetService
pet_router = APIRouter()
@crud(
    pet_router,
    dto={
        "create": PetCreate,
        "update": PetUpdate
    },
    serialize={
        "base": PetPublic,
    },
    summary_vars={
        "name": "cat"
    }
)
class PetController():
    service: PetService = Depends(PetService)

    @pet_router.get("")
    async def override_get_many(self):
        return []

    @pet_router.get('/{id}')
    def override_get_one(self, id: int):
        return 'return one'

```

## Nested Routes

The following implements a nested route to get user tasks by user_id

```python hl_lines="10-15 20"

app = FastAPI()
user_task_router = APIRouter()
@crud(
    user_task_router,
    feature="user_task",
    dto={"create": UserTaskCreateWithoutId,"update": UserTaskCreateWithoutId},
    serialize={
        "base": UserTaskPublic,
    },
    params={
        "user_id": {
            "field": "user_id",
            "type": "int"
        }
    }
)
class UserTaskController():
    service: UserTaskService = Depends(UserTaskService)
api_router = APIRouter()
api_router.include_router(user_task_router, prefix="/user/{user_id}/user_task")
app.include_router(api_router)

```

![Nested Router](https://raw.githubusercontent.com/bigrivi/better_crud/main/resources/NestedRouter.png)