from fastapi import APIRouter, Depends, Request
from fastapi_crud import crud, crud_router
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate, Company
# from app.services.company import CompanyService
# router = APIRouter()
# @crud(
#     router,
#     dto={"create": CompanyCreate, "update": CompanyUpdate},
#     routes={},
#     serialize={"base": CompanyPublic},
# )
# class CompanyController():
#     service: CompanyService = Depends(CompanyService)


async def on_before_create(*args, **kwargs) -> None:
    print("on_before_create")
    print(args)
    print(kwargs)

router = crud_router(
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic},
    on_before_create=on_before_create
)


@router.get("/")
async def override_get_many(request: Request):
    return []
