from typing import Any, Callable, List, Type, TypeVar, Union, get_type_hints, Literal,Dict,Annotated

from fastapi import APIRouter,Depends,Request,Query
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi_crud import crud,CrudOptions,crud
from app.models.user import UserPublic,UserCreate,User,UserUpdate
from app.services.user import UserService
from app.core.schema import Route
from fastapi.routing import APIRoute
from fastapi_pagination import  Page

auth_scheme = HTTPBearer()

# router = APIRouter(dependencies=[Depends(auth_scheme)])
# {"rules":[{"field":"email","operator":"contains","value":"孙"}],"combinator":"and","not":false}

router = APIRouter(route_class=Route)

# @crudauth({
#   property: 'user',
# persist?: (req: any) => ObjectLiteral;
#   filter: (user: User) => ({
#     id: user.id,
#     isActive: true,
#   })
# })

@crud(router,
    name="user",
    feature="user",
    # routes={"only":["get_many"]},
    dto={"create":UserCreate,"update":UserUpdate},
    serialize={"get_many":UserPublic},
    query={
        "soft_delete":True,
        "pagination":True,
        "join":[
            User.profile,
            User.company,
            User.roles
        ]
    }
)
class UserController():
    service: UserService = Depends(UserService)

    @router.get("/xxxxx")
    async def override_get_many(self,request:Request):
        return []

