import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from better_crud import FastAPICrudGlobalConfig, crud
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from examples.sqlmodel.tests.helper import setup_database
from app.services.user import UserService
from app.models.user import UserPublic


@pytest.mark.asyncio
async def test_gen_async_session():
    async def async_session() -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
        async with setup_database("sqlite+aiosqlite:///:memory:") as session:
            yield session

    app = FastAPI()
    FastAPICrudGlobalConfig.init(
        backend_config={
            "sqlalchemy": {
                "db_session": async_session
            }
        }
    )
    user_router = APIRouter()

    @crud(
        user_router,
        feature="user",
        serialize={
            "base": UserPublic,
        }
    )
    class UserController():
        service: UserService = Depends(UserService)
    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        response = test_client.get("/user")
        data = response.json()
        assert len(data) == 0


@pytest.mark.asyncio
async def test_async_session(async_session):
    app = FastAPI()
    FastAPICrudGlobalConfig.init(
        backend_config={
            "sqlalchemy": {
                "db_session": lambda: async_session
            }
        }
    )
    user_router = APIRouter()

    @crud(
        user_router,
        feature="user",
        serialize={
            "base": UserPublic,
        }
    )
    class UserController():
        service: UserService = Depends(UserService)
    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        response = test_client.get("/user")
        data = response.json()
        assert len(data) == 0
