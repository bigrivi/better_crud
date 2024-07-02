from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi_crud import crud,CrudOptions
from app.models.role import Role,RolePublic,RoleCreate,RoleUpdate
from app.services.role import RoleService
from app.core.schema import Route

auth_scheme = HTTPBearer()

# router = APIRouter(dependencies=[Depends(auth_scheme)])
router = APIRouter()

# @crudauth({
#   property: 'user',
# persist?: (req: any) => ObjectLiteral;
#   filter: (user: User) => ({
#     id: user.id,
#     isActive: true,
#   })
# })

@crud(router,
    name="role",
    dto={"create":RoleCreate,"update":RoleUpdate},
    routes={},
    serialize={"get_many":RolePublic},
)
class RoleController():
    service: RoleService = Depends(RoleService)
