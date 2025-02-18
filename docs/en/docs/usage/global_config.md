
Some configurations are for the route level, of course, you can also configure it globally, otherwise each route needs to be reconfigured once.
The design is designed to be configured globally, and can be overridden at the routing level

```python
from better_crud import BetterCrudGlobalConfig

BetterCrudGlobalConfig.init(**config)

@classmethod
def init(
    cls,
    *,
    backend_config: Optional[BackendConfigDict] = None,
    query: Optional[GlobalQueryOptionsDict] = {},
    routes: Optional[RoutesModelDict] = {},
    delim_config: Optional[QueryDelimOptionsDict] = {},
    soft_deleted_field_key: Optional[str] = None,
    action_map: Optional[Dict[str, str]] = None,
    page_schema: Optional[AbstractPage] = Page,
    response_schema: Optional[AbstractResponseModel] = None
) -> None:
```

!!! warning
    So in order to apply the global configuration you need to execute init before importing the routing class. This is because python decorators are executed when we declare the class, not when we create a new class instance. So in your main.py:
```python title="main.py" hl_lines="1-7"
BetterCrudGlobalConfig.init(
    backend_config={
        "sqlalchemy": {
            "db_session": get_session
        }
    }
)
app = FastAPI(lifespan=lifespan)


def register_router():
    from app.controller import pet_router
    app.include_router(pet_router, prefix="/pet")


register_router()
```

- [backend\_config](#backend_config)
  - [1. Define Your db\_session](#1-define-your-db_session)
  - [2. Custom Your Backend](#2-custom-your-backend)
- [query](#query)
- [routes](#routes)
  - [1. Set global dependencies](#1-set-global-dependencies)
  - [2. Only Get Many,Get One route](#2-only-get-manyget-one-route)
  - [3. Exclude Create Many route](#3-exclude-create-many-route)
- [delim\_config](#delim_config)
- [soft\_deleted\_field\_key](#soft_deleted_field_key)
- [action\_map](#action_map)
- [page\_schema](#page_schema)
- [response\_schema](#response_schema)




## backend_config

```python

DBSessionFactory = Callable[..., Union[AsyncGenerator[Any, None], Any]]

class SqlalchemyBackendDict(TypedDict):
    db_session: DBSessionFactory

BackendType = Literal[
    "sqlalchemy",
    "custom"
]

class BackendConfigDict(TypedDict):
    backend: BackendType
    sqlalchemy: SqlalchemyBackendDict
```
### 1. Define Your db_session

db_session is an asynchronous generator function that returns type AsyncSession

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

BetterCrudGlobalConfig.init(
    backend_config={
        "sqlalchemy": {
            "db_session": get_session
        }
    }
)
```

If you use fastapi_sqlalchemy

```python
from fastapi_sqlalchemy import db
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    yield db.session
```


### 2. Custom Your Backend

Currently, only the backend of sqlalchemy is implemented
Of course, you can implement your own backend by setting backend to custom,
For example, here's how


```python
from better_crud import BetterCrudGlobalConfig

BetterCrudGlobalConfig.init(
    backend_config={
        "backend":"custom"
    }
)
```
Your backend class inherits AbstractCrudService and implements its abstract methods

<!-- ::: better_crud.service.abstract.AbstractCrudService -->

The business service inherits from it
```python title="service.py"
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from .model import Pet


class PetService(YourCustomCrudService[Pet]):
    def __init__(self):
        super().__init__(Pet)

```

## query
Configuration of some global query parameters
```python
class GlobalQueryOptionsDict(TypedDict, total=False):
    soft_delete: Optional[bool] = False
    sort: Optional[List[QuerySortDict]] = None
    allow_include_deleted: Optional[bool] = False

class QuerySortDict(TypedDict):
    field: str
    sort: Literal["ASC", "DESC"]
```

GlobalQueryOptionsDict

| Name                  | Type                | Description                                              |
| --------------------- | ------------------- | -------------------------------------------------------- |
| soft_delete           | bool                | Decide whether soft delete is enabled                    |
| sort                  | List[QuerySortDict] | Sort configuration and support for multiple fields       |
| allow_include_deleted | bool                | Query whether data that has been soft-deleted is allowed |


QuerySortDict

| Name  | Type                   | Description                       |
| ----- | ---------------------- | --------------------------------- |
| field | str                    | Sort fields                       |
| sort  | Literal["ASC", "DESC"] | ASC ascending and DESC descending |

## routes


| Name         | Type                     | Description                     |
| ------------ | ------------------------ | ------------------------------- |
| dependencies | Sequence[params.Depends] | Set the depends of the route    |
| only         | List[RoutesEnumType]     | Only contain routes             |
| exclude      | List[RoutesEnumType]     | Routes that need to be excluded |
| get_many     | RouteOptionsDict         | Route config for get_many       |
| get_one      | RouteOptionsDict         | Route config for get_one        |
| create_one   | RouteOptionsDict         | Route config for create_one     |
| create_many  | RouteOptionsDict         | Route config for create_many    |
| update_one   | RouteOptionsDict         | Route config for update_one     |
| update_many  | RouteOptionsDict         | Route config for update_many    |
| delete_many  | RouteOptionsDict         | Route config for delete_many    |

```python

RoutesEnumType = Literal[
    "get_many",
    "get_one",
    "create_one",
    "create_many",
    "update_one",
    "update_many",
    "delete_many"
]

class RouteOptionsDict(TypedDict, total=False):
    dependencies: Optional[Sequence[params.Depends]] = None
    summary: Optional[str] = None

```

RouteOptionsDict

| Name         | Type                     | Description                    |
| ------------ | ------------------------ | ------------------------------ |
| dependencies | Sequence[params.Depends] | Set the depends of the route   |
| summary      | str                      | Set the summary of the swagger |

### 1. Set global dependencies

```python
from fastapi.security import HTTPBearer
from fastapi import Depends
JWTDepend = Depends(HTTPBearer())

BetterCrudGlobalConfig.init(
    routes={
        "dependencies":[JWTDepend],
    }
)

```

### 2. Only Get Many,Get One route

```python
from fastapi.security import HTTPBearer
from fastapi import Depends
JWTDepend = Depends(HTTPBearer())

BetterCrudGlobalConfig.init(
    routes={
        "only":["get_many","get_one"]
    }
)

```

### 3. Exclude Create Many route


```python
from fastapi.security import HTTPBearer
from fastapi import Depends
JWTDepend = Depends(HTTPBearer())

BetterCrudGlobalConfig.init(
    routes={
        "exclude":["create_many"]
    }
)

```


## delim_config

Splitter config
```python
class QueryDelimOptionsDict(TypedDict, total=False):
    delim: Optional[str] = "||"
    delim_str: Optional[str] = ","
```
delim is used to split multiple query criteria

- ?filter=field||condition||value
- ?filter=user_name||$eq||alice
- ?filter=age||$gt||20

delim_str is used to split order field and sort by

- ?order=age,ASC
- ?order=id,DESC


## soft_deleted_field_key

To set up a soft-delete field, you can use e.g. deleted_at, expiry_at,Represents a timestamp,When the data was deleted

## action_map

Default ACL action map

| Route       | Action     |
| ----------- | ---------- |
| get_many    | **read**   |
| read_one    | **read**   |
| create_one  | **create** |
| create_many | **create** |
| update_one  | **update** |
| update_many | **update** |
| delete_many | **delete** |

Your can custom your action map

```python

BetterCrudGlobalConfig.init(
    action_map={
        RoutesEnum.get_many: "read-all",
        RoutesEnum.get_one: "read-one",
        RoutesEnum.create_one:"create-one"
        RoutesEnum.create_many: "create-many",
        RoutesEnum.update_one: "update-one",
        RoutesEnum.update_many: "update-many",
        RoutesEnum.delete_many: "delete-many"
    }
)


```

## page_schema

## response_schema

Configure global response schema

```python

from typing import Any, TypeVar, Generic
from better_crud import AbstractResponseModel
T = TypeVar("T")

class ResponseModel(AbstractResponseModel, Generic[T]):

    code: int = 200
    msg: str = "Success"
    data: T | None = None

    @classmethod
    def create(
        cls, content: Any
    ):
        return cls(
            data=content,
            msg="success"
        )


BetterCrudGlobalConfig.init(
    response_schema=ResponseModel,
)



```