from fastapi import APIRouter, Depends
from better_crud import crud
from app.models.role import Role, RolePublic, RoleCreate, RoleUpdate
from app.services.role import RoleService
router = APIRouter()


@crud(
    router,
    dto={"create": RoleCreate, "update": RoleUpdate},
    routes={},
    serialize={"base": RolePublic},
)
class RoleController():
    service: RoleService = Depends(RoleService)
