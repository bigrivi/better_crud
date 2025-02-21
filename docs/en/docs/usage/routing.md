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

### 2. Disable a specific route
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