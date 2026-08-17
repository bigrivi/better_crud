import pytest
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


def _make_app(async_session, controller_cls):
    from pydantic import BaseModel, ConfigDict
    from typing import Generic, TypeVar, Optional
    from better_crud import AbstractResponseModel

    T = TypeVar("T")

    class TestResponse(AbstractResponseModel, BaseModel, Generic[T]):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        code: int = 200
        msg: str = "success"
        data: Optional[T] = None

        @classmethod
        def create(cls, content):
            return cls(data=content)

    BetterCrudGlobalConfig.init(
        backend_config={
            "sqlalchemy": {
                "db_session": lambda: async_session
            }
        },
        response_schema=TestResponse,
    )
    user_router = APIRouter()

    @crud(user_router, feature="user", serialize={"base": UserPublic})
    class UserController(controller_cls):
        pass

    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app = FastAPI()
    app.include_router(api_router)
    return app


def test_crud_action_infers_response_model_from_annotation(async_session):
    """When crud_action omits response_model, infer it from the return annotation instead of falling back to serialize.base."""
    from typing import List
    from pydantic import BaseModel

    class CustomResult(BaseModel):
        count: int

    class UserController():
        service: UserService = Depends(UserService)

        @crud_action(method="GET", path="/summary")
        async def summary(self) -> CustomResult:
            return CustomResult(count=1)

    app = _make_app(async_session, UserController)
    route = next(r for r in app.routes if getattr(r, "path", "") == "/user/summary")
    rm = route.response_model
    # response_model should be TestResponse[CustomResult] (inferred from annotation)
    assert rm is not None
    assert getattr(rm, "__pydantic_generic_metadata__", {}).get("args", ()) == (CustomResult,)


def test_crud_action_no_annotation_uses_bare_response_schema(async_session):
    """When crud_action has no return annotation, use the bare response_schema (data unconstrained) instead of serialize.base."""
    class UserController():
        service: UserService = Depends(UserService)

        @crud_action(method="POST", path="/do-something")
        async def do_something(self):
            return {"done": True}

    app = _make_app(async_session, UserController)
    route = next(r for r in app.routes if getattr(r, "path", "") == "/user/do-something")
    rm = route.response_model
    # Bare response model: no generic args (data unconstrained)
    assert rm is not None
    assert getattr(rm, "__pydantic_generic_metadata__", {}).get("args", ()) == ()


def test_crud_action_response_not_double_wrapped(async_session):
    """When an endpoint already returns a response model instance, it must not be wrapped a second time."""
    class UserController():
        service: UserService = Depends(UserService)

        @crud_action(method="GET", path="/wrapped")
        async def wrapped(self):
            rm = BetterCrudGlobalConfig.response_schema
            return rm(data={"id": 1})

    app = _make_app(async_session, UserController)
    with TestClient(app) as client:
        response = client.get("/user/wrapped")
        assert response.status_code == 200
        body = response.json()
        # data should be the bare dict, not a nested response model
        assert body["data"] == {"id": 1}


def test_crud_action_optional_annotation_keeps_optional(async_session):
    """Optional[X] return annotations must stay Optional so a None response does not fail validation."""
    from typing import Optional
    from pydantic import BaseModel

    class CustomResult(BaseModel):
        count: int

    class UserController():
        service: UserService = Depends(UserService)

        @crud_action(method="GET", path="/maybe")
        async def maybe(self) -> Optional[CustomResult]:
            return None

    app = _make_app(async_session, UserController)
    route = next(r for r in app.routes if getattr(r, "path", "") == "/user/maybe")
    rm = route.response_model
    assert getattr(rm, "__pydantic_generic_metadata__", {}).get("args", ()) == (Optional[CustomResult],)
    with TestClient(app) as client:
        response = client.get("/user/maybe")
        assert response.status_code == 200
        assert response.json()["data"] is None


def test_crud_action_unresolvable_annotation_uses_bare_response_schema(async_session):
    """A return annotation that cannot be resolved at import time must not crash route registration; fall back to the bare response_schema with a warning."""
    class UserController():
        service: UserService = Depends(UserService)

        @crud_action(method="GET", path="/broken")
        async def broken(self) -> "UndefinedModel":
            return {"id": 1}

    with pytest.warns(UserWarning):
        app = _make_app(async_session, UserController)
    route = next(r for r in app.routes if getattr(r, "path", "") == "/user/broken")
    rm = route.response_model
    assert getattr(rm, "__pydantic_generic_metadata__", {}).get("args", ()) == ()
    with TestClient(app) as client:
        response = client.get("/user/broken")
        assert response.status_code == 200
        assert response.json()["data"] == {"id": 1}


def test_crud_action_list_annotation_keeps_container(async_session):
    """List[X] return annotations are preserved as containers."""
    from typing import List
    from pydantic import BaseModel

    class CustomResult(BaseModel):
        count: int

    class UserController():
        service: UserService = Depends(UserService)

        @crud_action(method="GET", path="/all")
        async def all_(self) -> List[CustomResult]:
            return [CustomResult(count=1)]

    app = _make_app(async_session, UserController)
    route = next(r for r in app.routes if getattr(r, "path", "") == "/user/all")
    rm = route.response_model
    assert getattr(rm, "__pydantic_generic_metadata__", {}).get("args", ()) == (List[CustomResult],)
    with TestClient(app) as client:
        response = client.get("/user/all")
        assert response.status_code == 200
        assert response.json()["data"] == [{"count": 1}]
