from fastapi import APIRouter, Depends
from fastapi_crud import crud
from app.models.project import ProjectPublic, ProjectCreate, ProjectUpdate
from app.services.project import ProjectService
router = APIRouter()


@crud(
    router,
    dto={"create": ProjectCreate, "update": ProjectUpdate},
    routes={},
    serialize={"base": ProjectPublic},
)
class ProjectController():
    service: ProjectService = Depends(ProjectService)
