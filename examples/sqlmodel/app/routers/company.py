from fastapi import APIRouter, Depends
from fastapi_crud import crud, crud_router
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate, Company
from app.services.company import CompanyService
# router = APIRouter()
# @crud(
#     router,
#     dto={"create": CompanyCreate, "update": CompanyUpdate},
#     routes={},
#     serialize={"base": CompanyPublic},
# )
# class CompanyController():
#     service: CompanyService = Depends(CompanyService)

router = crud_router(
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic},
)
