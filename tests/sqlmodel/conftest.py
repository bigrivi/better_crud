import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from typing import Optional,List,Any,TypeVar,Generic,AsyncGenerator
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel,Relationship
from fastapi_crud import SqlalchemyCrudService,FastAPICrudGlobalConfig,AbstractResponseModel

T = TypeVar("T")


@asynccontextmanager
async def _setup_database(url: str) -> AsyncGenerator[AsyncSession,None]:
    engine = create_async_engine(url, echo=False, future=True)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        try:
            yield session
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
    print("====dispose===")
    await engine.dispose()

class ResponseSchema(AbstractResponseModel,Generic[T]):
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
) -> AsyncGenerator[AsyncSession,None]:  # pragma: no cover
    async with _setup_database("sqlite+aiosqlite:///:memory:") as session:
        yield session


class CompanyBase(SQLModel):
    name: str | None = None
    domain: str | None = None
    description:str = Field(default=None)

class Company(CompanyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class CompanyCreate(CompanyBase):
    pass

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
    print(async_session)
    test_company_service = TestCompanyService()
    return test_company_service
