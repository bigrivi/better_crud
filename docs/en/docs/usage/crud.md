An ordinary class is decorated with a CRUD decorator to give it CRUD capabilities, just like Spider-Man, who was bitten by a spider and gained super powers.

I think this is a good use case for python decorators

```python

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
    }
)
class PetController():
    service: PetService = Depends(PetService)

```

!!! warning
    crud is a python class decorator,cannot be used in decorated functions

Let me introduce the parameters of the decorator below

```python

def crud(
    router: APIRouter,
    *,
    serialize: SerializeModelDict,
    params: Optional[Dict[str, PathParamDict]] = None,
    routes: Optional[RoutesModelDict] = {},
    dto: DtoModelDict = {},
    auth: Optional[AuthModelDict] = {},
    query: Optional[QueryOptionsDict] = {},
    summary_vars: Optional[Dict] = {},
    feature: Optional[str] = "",
) -> Callable[[Type[T]], Type[T]]:

```

- [serialize](#serialize)
- [params](#params)
- [routes](#routes)
- [dto](#dto)
- [auth](#auth)
- [query](#query)
- [summary\_vars](#summary_vars)
- [feature](#feature)



## serialize
Response serialization DTO classes.
Compatible with [fastapi serialization](https://fastapi.tiangolo.com/tutorial/response-model/)

```python

class SerializeModelDict(TypedDict, total=False):
    base: Any
    get_many: Optional[Any] = None
    get_one: Optional[Any] = None
    create_one: Optional[Any] = None
    create_many: Optional[Any] = None
    update_one: Optional[Any] = None
    delete_many: Optional[Any] = None
```

```python
from pydantic import BaseModel

class GetManyModel(BaseModel):
    id:int
    name: Optional[str] = None
    description: Optional[str] = None

```

If you use SQLModel

```python
from sqlmodel import Field, SQLModel, Relationship

class GetManyModel(SQLModel):
    id:int
    name: Optional[str] = None
    description: Optional[str] = Field(default=None)

```

```python
@crud(
    router,
    serialize={
        "get_many":GetManyModel
        **others
    }
)

```

Of course, if all your response model structures are the same, you only need to define base,this means that all responses are serialized in the same structure.

```python
@crud(
    router,
    serialize={
        "base":GetManyModel
    }
)

```

## params

If you have a router path with that looks kinda similar to this /:user_id/user_task you need to add this param option:

```python
@crud(
    user_task_router,
    params={
        "user_id": {
            "field": "user_id",
            "type": "int"
        }
    }
)
api_router.include_router(user_task_router, prefix="/{user_id}/user_task")
```

## routes

The function is the same as routes in [Global Config](/usage/global_config/#routes)

## dto

Request body model classes. see fastapi [Request Body](https://fastapi.tiangolo.com/tutorial/body/)

Used in create/update routes respectively

```python
@crud(
    dto={
        "create": PetCreate, #create one/create many
        "update": PetUpdate #update one/update many
    },
)
```

## auth

In order to perform data filtering for authenticated requests,

```python

@crud(
    auth={
        "persist": lambda x: {"user_id": 1},
        "filter": lambda x: {"user_id": 1},
    }
)
```
persist - a function that can return an object that will be added to the DTO on create, update actions. Useful in case if you need to prevent changing some sensitive entity properties even if it's allowed in DTO validation.

filter - a function that should return search condition and will be added to the query search params and path params as a $and condition:

## query

Some query related configuration

```python
class QueryOptionsDict(TypedDict, total=False):
    joins: Optional[Dict[str, JoinOptionsDict]] = None
    soft_delete: Optional[bool] = None
    allow_include_deleted: Optional[bool] = False
    filter: Optional[Dict] = None
    sort: Optional[List[QuerySortDict]] = None
```

| Name                  | Type                       | Description                                        |
| --------------------- | -------------------------- | -------------------------------------------------- |
| joins                 | Dict[str, JoinOptionsDict] | Set the depends of the route                       |
| soft_delete           | bool                       | Whether to allow soft deletion                     |
| allow_include_deleted | bool                       | Set whether to allow the inclusion of deleted data |
| filter                | Dict                       | Some filter conditions                             |
| sort                  | List[QuerySortDict]        | Set query sorting method                           |


## summary_vars

You can set some variables used in summary

For example, if you set a summary of some routes globally

```python

BetterCrudGlobalConfig.init(
    backend_config={
        "sqlalchemy": {
            "db_session": get_session
        }
    },
    page_schema=Page,
    routes={
        "get_many": {
            "summary": "Get Many for {name}"
        }
    }
)

```
You used the variable name in the summary of the get_many route

```python

@crud(
    summary_vars={
        "name": "cat"
    }
)
```
Now the summary inside the get_many route will be 'Get Many for cat'

![OpenAPI Route Summary Overview](https://raw.githubusercontent.com/bigrivi/better_crud/main/resources/RouteSummary.png)


## feature

Used to set the value returned by the corresponding route get_feature function in [ACL Guard](/advanced/acl_guard)

