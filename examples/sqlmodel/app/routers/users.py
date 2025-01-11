from fastapi import APIRouter, Depends, Request, Query
from fastapi_crud import crud, crud
from app.models.user import UserPublic, UserCreate, User, UserUpdate
from app.services.user import UserService
from app.core.depends import JWTDepend, ACLDepend


router = APIRouter()

@crud(
    router,
    feature="user",
    routes={
        "get_many": {
            "summary": ""
        }
    },
    summary_vars={
        "name": "test"
    },
    dto={"create": UserCreate, "update": UserUpdate},
    serialize={
        "base": UserPublic,
    },
    query={
        "joins": {
            "profile": {
                "select": True,
                "join": False
            },
            "tasks": {
                "select": True,
                "join": False
            },
            "company": {
                "select": True,
                "join": False
            },
            "roles": {
                "select": True,
                "join": False
            },
            "staff": {
                "select": True,
            },
            "projects": {
                "select": True,
            },
            "projects.company": {
                "select": True,
                "join": False
            }
        },
        "soft_delete": True,
        "sort": [
            {
                "field": "id",
                "sort": "DESC"
            }
        ]
    }
)
class UserController():
    service: UserService = Depends(UserService)
