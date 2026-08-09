from unittest.mock import MagicMock
from better_crud import BetterCrudGlobalConfig, crud, crud_action
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from app.services.user import UserService
from app.models.user import UserPublic


def test_only(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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
        routes={
            "only": ["get_many"]
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
        response = test_client.post("/user")
        assert response.status_code == 405
        response = test_client.delete("/user/1")
        assert response.status_code == 404
        response = test_client.put("/user/1")
        assert response.status_code == 404


def test_only_empty(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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
        routes={
            "only": []
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
        response = test_client.get("/user")
        assert response.status_code == 404
        response = test_client.post("/user")
        assert response.status_code == 404
        response = test_client.delete("/user/1")
        assert response.status_code == 404
        response = test_client.put("/user/1")
        assert response.status_code == 404


def test_exclude(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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
        routes={
            "exclude": ["create_many", "create_one"]
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
        response = test_client.post("/user")
        assert response.status_code == 405
        response = test_client.post("/user/bulk")
        assert response.status_code == 405


def test_override(async_session, init_data):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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

        @user_router.get("")
        async def override_get_many(self):
            return []

    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        response = test_client.get("/user")
        assert len(response.json()) == 0


def test_dependencies(async_session):
    depend_fn_mock = MagicMock()

    async def depend_fn():
        depend_fn_mock()
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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
        },
        routes={
            "dependencies": [Depends(depend_fn)]
        }
    )
    class UserController():
        service: UserService = Depends(UserService)
    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        test_client.get("/user")
        depend_fn_mock.assert_called()


def test_dependencies_override(async_session):
    depend_fn_mock1 = MagicMock()
    depend_fn_mock2 = MagicMock()

    async def depend_fn1():
        depend_fn_mock1()

    async def depend_fn2():
        depend_fn_mock2()
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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
        },
        routes={
            "dependencies": [Depends(depend_fn1)],
            "get_many": {
                "dependencies": [Depends(depend_fn2)]
            }
        }
    )
    class UserController():
        service: UserService = Depends(UserService)
    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        test_client.get("/user")
        depend_fn_mock1.assert_not_called()
        depend_fn_mock2.assert_called()


def test_crud_action_registered(action_client, test_user_data, init_data):
    response = action_client.post("/user/1/adopt")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "adopted": True}


def test_crud_action_response_schema(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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

        @crud_action(method="GET", path="/summary")
        async def summary(self):
            return {"count": 1}

    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        response = test_client.get("/user/summary")
        assert response.status_code == 200
        assert response.json() == {"count": 1}


def test_crud_action_override(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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

        @user_router.post("/{id}/adopt")
        async def manual_adopt(self, id: int):
            return {"manual": True}

        @crud_action(method="POST", path="/{id}/adopt")
        async def adopt(self, id: int):
            return {"auto": True}

    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        response = test_client.post("/user/1/adopt")
        assert response.status_code == 200
        assert response.json() == {"manual": True}


def test_crud_action_no_self_method(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
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

        @staticmethod
        @crud_action(method="GET", path="/ping")
        async def ping():
            return "pong"

    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        response = test_client.get("/user/ping")
        assert response.status_code == 200
        assert response.json() == "pong"
