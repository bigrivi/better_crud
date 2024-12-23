import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))  # noqa: E402
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402
from typing import AsyncGenerator, List, Dict
from fastapi_crud import FastAPICrudGlobalConfig, AbstractResponseModel
from sqlmodel import SQLModel
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from starlette.requests import Request
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager
import pytest_asyncio
import pytest


@asynccontextmanager
async def _setup_database(url: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(url, echo=False, future=True)
    session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        try:
            yield session
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
    async with _setup_database("sqlite+aiosqlite:///:memory:") as session:
        yield session


@pytest.fixture(scope="function")
def test_user_data() -> List[Dict]:
    return [
        {
            "id": 1,
            "email": "bob@gmail.com",
            "password": "111111",
            "is_active": True,
            "profile": {
                "name": "bob",
                "gender": "male",
                "phone": "111111",
                "birthdate": "2020-01-01",
                "hobby": "music",
                "state": "nice",
                "country": "china",
                "address": "anhui"
            },
            "staff": {
                "name": "bob",
                "position": "CEO",
                "job_title": "The Chief Executive Officer"
            },
            "tasks": [
                {
                    "status": "pending",
                    "description": "pending task"
                },
                {
                    "status": "inprogress",
                    "description": "inprogress task"
                },
                {
                    "status": "completed",
                    "description": "completed task"
                }
            ]
        },
        {
            "id": 2,
            "email": "alice@gmail.com",
            "password": "111111",
            "is_active": True,
            "profile": {
                "name": "alice",
                "gender": "female",
                "phone": "111111",
                "birthdate": "2020-01-01",
                "hobby": "music",
                "state": "nice",
                "country": "china",
                "address": "anhui"
            },
            "staff": {
                "name": "alice",
                "position": "CFO",
                "job_title": "Chief Financial Officer"
            },
            "tasks": [
                {
                    "status": "pending",
                    "description": "pending task"
                },
                {
                    "status": "inprogress",
                    "description": "inprogress task"
                },
                {
                    "status": "completed",
                    "description": "completed task"
                }
            ]
        }
    ]


@pytest.fixture(scope="function")
def test_role_data() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "test1",
            "description": "test1 des"
        },
        {
            "id": 2,
            "name": "test2",
            "description": "test2 des"
        },
        {
            "id": 3,
            "name": "test3",
            "description": "test3 des"
        }
    ]


@pytest.fixture(scope="function")
def test_request() -> Request:
    return Request(scope={
        "type": "http",
    })


@pytest.fixture
def client(
    async_session
):
    app = FastAPI()
    FastAPICrudGlobalConfig.init(
        backend_config={
            "sqlalchemy": {
                "db_session": lambda: async_session
            }
        }
    )
    from app.routers.company import router as company_router
    api_router = APIRouter()
    api_router.include_router(company_router, prefix="/company")
    app.include_router(api_router)
    return TestClient(app)
