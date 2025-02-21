
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
from better_crud import register_backend
from better_crud.service.abstract import AbstractCrudService
from .model import Pet

@register_backend("custom")
class YourCustomCrudService(
    Generic[ModelType],
    AbstractCrudService[ModelType]
):
    pass

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

Used to exclude or include only some routes, and to set route dependencies

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

Used to set the value returned by the corresponding route get_action function in [ACL Guard](/advanced/acl_guard)


## page_schema

BetterCRUD uses [fastapi-pagination](https://github.com/uriyyo/fastapi-pagination)
 as the built-in paging method, so you can customize your paging model more flexibly

By default, page and size are used as paging query parameters.

?page=1&size=10

Of course you can change this behavior,the following example uses page1 and size1 as URL query parameters

```python title="pagination.py"
from __future__ import annotations

import math
from typing import Generic, Sequence, TypeVar, Optional, Any
from fastapi import Query
from fastapi_pagination.bases import AbstractPage, AbstractParams, RawParams
from pydantic import BaseModel


T = TypeVar('T')


class Params(BaseModel, AbstractParams):
    page1: Optional[int] = Query(
        default=None, gte=0, description='Page number')
    size1: Optional[int] = Query(
        default=None,
        gte=0,
        le=100,
        description='Page size'
    )

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size1,
            offset=self.size1 * (self.page1 - 1),
        )


class Page(AbstractPage[T], Generic[T]):
    records: Sequence[T]
    total: int
    page: int
    size: int
    pages: int
    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: Params,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> Page[T]:
        size = params.size1 if params.size1 is not None else (total or None)
        page = params.page1 if params.page1 is not None else 1
        if size in {0, None}:
            pages = 0
        elif total is not None:
            pages = math.ceil(total / size)
        else:
            pages = None
        return cls(records=items, total=total, page=page, size=size, pages=pages)

```

```python title="main.py"

BetterCrudGlobalConfig.init(
    page_schema=Page
)

```

## response_schema

Configure your response schema

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