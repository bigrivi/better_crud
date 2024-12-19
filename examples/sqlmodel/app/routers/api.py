
from fastapi import APIRouter
from app.routers import company, roles, users

api_router = APIRouter()

api_router.include_router(company.router, prefix="/company")
api_router.include_router(roles.router, prefix="/role")
api_router.include_router(users.router, prefix="/user")
