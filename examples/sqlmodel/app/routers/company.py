from fastapi import APIRouter, Depends, Request
from fastapi_crud import crud_generator
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate, Company
router = APIRouter()
crud_generator(
    router,
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic}
)
