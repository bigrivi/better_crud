from fastapi import APIRouter, Depends, Request
from fastapi_crud import crud_generator
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate, Company
router = APIRouter()


async def on_before_create(*args, **kwargs) -> None:
    print("on_before_create call")

crud_generator(
    router,
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic},
    on_before_create=on_before_create
)
