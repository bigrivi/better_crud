from typing import Any, Callable, List, Type, TypeVar, Union, get_type_hints, Literal,Dict,Annotated

from fastapi import APIRouter,Depends,Request,Query
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi_crud import crud,CrudOptions,crud
from app.models.user import UserPublic,UserCreate,User,UserUpdate
from app.services.user import UserService
from app.core.schema import Route
from fastapi.routing import APIRoute
from fastapi_pagination import  Page



# router = APIRouter(dependencies=[Depends(auth_scheme)])
# {"rules":[{"field":"email","operator":"contains","value":"孙"}],"combinator":"and","not":false}

router = APIRouter(route_class=Route)

def persist_fn(request:Request):
    return {}

def filter_fn(request:Request):
    return {
        # "id":1
    }

@crud(router,
    name="user",
    feature="user",
    routes={

    },
    dto={"create":UserCreate,"update":UserUpdate},
    serialize={"get_many":UserPublic},
    auth = {
        "filter":filter_fn,
        "persist":persist_fn
    },
    query={
        "soft_delete":True,
        # "filter":{
        #     "id":1
        # },
        "pagination":True,
        "joins":[
            User.profile,
            User.company,
            User.roles
        ]
    }
)
class UserController():
    service: UserService = Depends(UserService)

    # @router.get("/xxxxx")
    # async def override_get_many(self,request:Request):
    #     return []

