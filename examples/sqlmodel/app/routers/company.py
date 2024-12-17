from fastapi import APIRouter, Depends
from fastapi_crud import crud
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate
from app.services.company import CompanyService
router = APIRouter()


@crud(
    router,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic},
)
class CompanyController():
    service: CompanyService = Depends(CompanyService)
