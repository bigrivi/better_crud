from fastapi import APIRouter, Depends
from better_crud import crud
from app.models.user_task import UserTaskCreateWithoutId, UserTaskPublic
from app.services.user_task import UserTaskService
router = APIRouter()


@crud(
    router,
    dto={"create": UserTaskCreateWithoutId, "update": UserTaskCreateWithoutId},
    routes={},
    serialize={"base": UserTaskPublic},
)
class UserTaskController():
    service: UserTaskService = Depends(UserTaskService)
