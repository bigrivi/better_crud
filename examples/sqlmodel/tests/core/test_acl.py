from unittest.mock import MagicMock
from better_crud import BetterCrudGlobalConfig, crud,get_feature,get_action
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter,Request
from app.services.user import UserService
from app.models.user import UserPublic


def test_get_feature(async_session,test_user_data):
    app = FastAPI()
    acl_fn_mock = MagicMock()

    async def acl(request: Request):
        feature = get_feature(request)
        action = get_action(request)
        acl_fn_mock(feature,action)

    ACLDepend = Depends(acl)

    BetterCrudGlobalConfig.init(
        backend_config={
            "sqlalchemy": {
                "db_session": lambda: async_session
            }
        },
        routes={
            "dependencies":[ACLDepend],
        },
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
        test_client.get("/user")
        acl_fn_mock.assert_called_with("user", "read")
        first_test_user_data = test_user_data[0]
        test_client.post("/user",json=first_test_user_data)
        acl_fn_mock.assert_called_with("user", "create")
        exist_user_id = test_user_data[0]["id"]
        update_data = dict(email="updated@email.com", is_active=False)
        test_client.put(f"/user/{exist_user_id}", json=update_data)
        acl_fn_mock.assert_called_with("user", "update")
        exist_user_id = test_user_data[0]["id"]
        test_client.delete(f"/user/{exist_user_id}")
        acl_fn_mock.assert_called_with("user", "delete")



