
from fastapi import APIRouter
from app.routers import company, users, roles, project, post, user_task

api_router = APIRouter()

api_router.include_router(project.router, prefix="/project")
api_router.include_router(company.router, prefix="/company")
api_router.include_router(roles.router, prefix="/role")
api_router.include_router(users.router, prefix="/user")
api_router.include_router(user_task.router, prefix="/user/{user_id}/user_task")
api_router.include_router(post.router, prefix="/post")
