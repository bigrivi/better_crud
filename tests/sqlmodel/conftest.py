import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))  # noqa: E402
from typing import Optional, List, Any, TypeVar, Generic, AsyncGenerator
from fastapi_crud import crud, FastAPICrudGlobalConfig, AbstractResponseModel
from sqlmodel import SQLModel
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager
import pytest_asyncio
import pytest

from examples.app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate
from examples.app.services.company import CompanyService

T = TypeVar("T")


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

    router = APIRouter()

    @crud(
        router,
        feature="test",
        dto={"create": CompanyCreate, "update": CompanyUpdate},
        serialize={
            "base": CompanyPublic,
        },

    )
    class CompanyController():
        service: CompanyService = Depends(CompanyService)

    api_router = APIRouter()
    api_router.include_router(router, prefix="/company")
    app.include_router(api_router)
    return TestClient(app)
