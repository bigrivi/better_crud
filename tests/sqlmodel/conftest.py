import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))  # noqa: E402
from typing import Optional, List, Any, TypeVar, Generic, AsyncGenerator
from fastapi_crud import crud, SqlalchemyCrudService, FastAPICrudGlobalConfig, AbstractResponseModel
from sqlmodel import Field, SQLModel, Relationship
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager
import pytest_asyncio
import pytest


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


class ResponseSchema(AbstractResponseModel, Generic[T]):
    data: T
    msg: str

    @classmethod
    def create(
        cls, content: Any
    ):
        return cls(
            data=content,
            msg="success"
        )


@pytest_asyncio.fixture(scope="function")
async def async_session(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
    async with _setup_database("sqlite+aiosqlite:///:memory:") as session:
        yield session


class CompanyBase(SQLModel):
    name: str | None = None
    domain: str | None = None
    description: str | None = Field(default=None)


class Company(CompanyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass


class CompanyPublic(CompanyBase):
    id: int


class TestCompanyService(SqlalchemyCrudService[Company]):
    def __init__(self):
        super().__init__(Company)


@pytest.fixture
def create_schema():
    return CompanyCreate


@pytest.fixture
def test_model():
    return Company


@pytest.fixture
def my_test_company_service(async_session):
    test_company_service = TestCompanyService()
    return test_company_service


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
        },
        response_schema=ResponseSchema,
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
    class TestCompanyController():
        service: TestCompanyService = Depends(TestCompanyService)

    api_router = APIRouter()
    api_router.include_router(router, prefix="/test")
    app.include_router(api_router)
    return TestClient(app)
