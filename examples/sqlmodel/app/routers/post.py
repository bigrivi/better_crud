from fastapi import APIRouter, Depends
from better_crud import crud
from app.models.post import PostPublic, PostCreate, PostUpdate
from app.services.post import PostService
from app.models.user import User
from sqlalchemy.orm import aliased
ModifierUser = aliased(User)
router = APIRouter()


@crud(
    router,
    dto={"create": PostCreate, "update": PostUpdate},
    serialize={"base": PostPublic},
    query={
        "joins": {
            "creater_user": {
                "select": True,
                "join": True
            },
            "modifier_user": {
                "select": True,
                "join": True,
                "alias": ModifierUser
            }
        },
    }
)
class PostController():
    service: PostService = Depends(PostService)
