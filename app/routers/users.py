from fastapi import APIRouter,Depends,Request,Query
from fastapi_crud import crud,crud
from app.models.user import UserPublic,UserCreate,User,UserUpdate
from app.services.user import UserService
from app.core.depends import JWTDepend,ACLDepend


router = APIRouter()

def persist_fn(request:Request):
    return {}

def filter_fn(request:Request):
    return {
        "id":100
    }

@crud(router,
    name="user",
    feature="user",
    routes={
        # "dependencies":[JWTDepend,ACLDepend],
        # "only":["get_many","create_one"]
    },
    dto={"create":UserCreate,"update":UserUpdate},
    serialize={"get_many":UserPublic,"get_one":UserPublic},
    auth = {
        # "filter":filter_fn
    },
    query={
        "joins":[
            User.profile,
            User.company,
            User.roles
        ],
        "soft_delete":True,
        "sort":[
            {
                "field":"id",
                "sort":"DESC"
            }
        ]
    }
)
class UserController():
    service: UserService = Depends(UserService)

    # @router.get("/xxxxx")
    # async def override_get_many(self,request:Request):
    #     return []

