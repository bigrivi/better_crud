from fastapi import APIRouter,Depends
from fastapi_crud import crud
from app.models.role import Role,RolePublic,RoleCreate,RoleUpdate
from app.services.role import RoleService
router = APIRouter()

@crud(router,
    name="role",
    dto={"create":RoleCreate,"update":RoleUpdate},
    routes={},
    serialize={"get_many":RolePublic},
)
class RoleController():
    service: RoleService = Depends(RoleService)
