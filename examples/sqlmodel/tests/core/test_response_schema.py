from typing import Optional, Any, Generic, TypeVar
from better_crud import BetterCrudGlobalConfig, crud, AbstractResponseModel
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from app.services.user import UserService
from app.models.user import UserPublic
T = TypeVar("T")


class ResponseModel(AbstractResponseModel, Generic[T]):
    code: int = 200
    msg: str = "success"
    data: Optional[T] = None

    @classmethod
    def create(cls, content: Any):
        return cls(
            data=content,
            msg="success"
        )


def test_custom_response_schema(async_session):
    app = FastAPI()
    BetterCrudGlobalConfig.init(
        response_schema=ResponseModel,
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
        response = test_client.get("/user")
        assert response.json() == {'code': 200, 'msg': 'success', 'data': []}
