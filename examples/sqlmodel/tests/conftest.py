import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))  # noqa: E402
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402
from typing import AsyncGenerator, List, Dict
from sqlalchemy.orm import noload
from fastapi_crud import FastAPICrudGlobalConfig, AbstractResponseModel, crud
from sqlmodel import SQLModel
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from starlette.requests import Request
from sqlalchemy.orm import sessionmaker
from app.models.user import User, UserPublic
from app.models.role import Role
from app.models.company import Company
from app.models.project import Project
from app.models.user_task import UserTask, UserTaskCreateWithoutId, UserTaskPublic
from app.models.staff import Staff
from app.models.user_profile import UserProfile
from app.services.user_task import UserTaskService
from app.services.user import UserService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager
import pytest_asyncio
import pytest
from .data import USER_DATA, ROLE_DATA, COMPANY_DATA, PROJECT_DATA


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
    return USER_DATA


@pytest.fixture(scope="function")
def test_role_data() -> list[dict]:
    return ROLE_DATA


@pytest.fixture(scope="function")
def test_company_data() -> list[dict]:
    return COMPANY_DATA


@pytest.fixture(scope="function")
def test_project_data() -> list[dict]:
    return PROJECT_DATA


@pytest_asyncio.fixture(scope="function")
async def init_data(async_session, test_user_data, test_role_data, test_company_data, test_project_data):
    for company_data in test_company_data:
        company = Company()
        company.id = company_data["id"]
        company.name = company_data["name"]
        company.domain = company_data["domain"]
        company.description = company_data["description"]
        async_session.add(company)
    for project_data in test_project_data:
        project = Project()
        project.id = project_data["id"]
        project.name = project_data["name"]
        project.description = project_data["description"]
        project.company_id = project_data["company_id"]
        project.is_active = project_data["is_active"]
        async_session.add(project)
    for role_data in test_role_data:
        role = Role()
        role.id = role_data["id"]
        role.name = role_data["name"]
        role.description = role_data["description"]
        async_session.add(role)
    await async_session.commit()
    for user_data in test_user_data:
        user = User()
        user.email = user_data["email"]
        user.company_id = user_data["company_id"]
        user.user_name = user_data["user_name"]
        user.hashed_password = user_data["password"]
        user.is_active = user_data["is_active"]
        user.is_superuser = user_data["is_superuser"]
        user.profile = UserProfile(**user_data["profile"])
        user.staff = Staff(**user_data["staff"])
        user.tasks = [UserTask(**task_data)
                      for task_data in user_data["tasks"]]
        user.roles = [await async_session.get(Role, role_id) for role_id in user_data["role_ids"]]
        user.projects = [await async_session.get(Project, project_id) for project_id in user_data["project_ids"]]
        async_session.add(user)
    await async_session.commit()
    yield


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
    from app.routers.users import router as user_router
    from app.routers.company import router as company_router
    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(
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
    user_task_router = APIRouter()

    @crud(
        user_task_router,
        feature="user_task",
        dto={"create": UserTaskCreateWithoutId,
             "update": UserTaskCreateWithoutId},
        serialize={
            "base": UserTaskPublic,
        },
        auth={
            "persist": lambda x: {"user_id": 1},
            "filter": lambda x: {"user_id": 1},
        }
    )
    class UserTaskController():
        service: UserTaskService = Depends(UserTaskService)
    api_router = APIRouter()
    api_router.include_router(user_task_router, prefix="/user_task")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def params_client(
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
    user_task_router = APIRouter()

    @crud(
        user_task_router,
        feature="user_task",
        dto={"create": UserTaskCreateWithoutId,
             "update": UserTaskCreateWithoutId},
        serialize={
            "base": UserTaskPublic,
        },
        params={
            "user_id": {
                "field": "user_id",
                "type": "int"
            }
        }
    )
    class UserTaskController():
        service: UserTaskService = Depends(UserTaskService)
    api_router = APIRouter()
    api_router.include_router(user_task_router, prefix="/{user_id}/user_task")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fixed_filter_client(
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
    user_router = APIRouter()

    @crud(
        user_router,
        feature="user",
        query={
            "filter": {
                "is_active": True,
            },
        },
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
        yield test_client


@pytest.fixture
def include_deleted_client(
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
    user_router = APIRouter()

    @crud(
        user_router,
        feature="user",
        query={
           "allow_include_deleted":True,
           "soft_delete":True
        },
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
        yield test_client



@pytest.fixture
def join_config_client(
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
    user_router = APIRouter()

    @crud(
        user_router,
        feature="user",
        query={
           "joins": {
                "profile": {
                    "select": True,
                    "join": False
                },
                "tasks": {
                    "select": True,
                    "join": False
                },
                "company": {
                    "select": True,
                    "join": False
                },
                "projects": {
                    "select": True,
                },
                "projects.company": {
                    "select": True,
                    "join": False
                }
        },
        },
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
        yield test_client