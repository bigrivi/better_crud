import pytest
from fastapi import FastAPI, Depends, APIRouter
from fastapi.testclient import TestClient
from better_crud import BetterCrudGlobalConfig, crud
from app.services.user import UserService
from app.models.user import UserPublic


FILTER_QUERY = {
    "filters": {
        "company_id": {"field": "company_id", "type": "int", "description": "按公司ID过滤"},
        "by_company": {"field": "company.name", "type": "str", "description": "按公司名过滤"},
    },
    "joins": {"company": {"join": True, "select": False}},
}


def _make_filter_app(async_session, query):
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
        routes={"only": ["get_many"]},
        serialize={"base": UserPublic},
        query=query,
    )
    class UserController():
        service: UserService = Depends(UserService)

    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/user")
    app.include_router(api_router)
    return app


def test_query_filters_openapi_visible(async_session):
    """Declared filters appear as typed Query params in OpenAPI."""
    app = _make_filter_app(async_session, FILTER_QUERY)
    params = {
        p["name"]: p
        for p in app.openapi()["paths"]["/user"]["get"]["parameters"]
    }
    assert params["company_id"]["in"] == "query"
    assert params["company_id"]["required"] is False
    assert {"type": "integer"} in params["company_id"]["schema"]["anyOf"]
    assert params["company_id"]["description"] == "按公司ID过滤"
    assert {"type": "string"} in params["by_company"]["schema"]["anyOf"]
    assert params["by_company"]["description"] == "按公司名过滤"


def test_query_filters_base_field(async_session, init_data):
    """?company_id=1 returns only users of company 1."""
    app = _make_filter_app(async_session, FILTER_QUERY)
    with TestClient(app) as client:
        response = client.get("/user/", params={"company_id": 1})
        assert response.status_code == 200
        body = response.json()
        assert {u["user_name"] for u in body} == {"bob", "tom"}
        assert all(u["company_id"] == 1 for u in body)


def test_query_filters_relationship_field(async_session, init_data):
    """?by_company=<name> filters through the declared join (company.name)."""
    app = _make_filter_app(async_session, FILTER_QUERY)
    with TestClient(app) as client:
        response = client.get("/user/", params={"by_company": "Gonzalez Inc"})
        assert response.status_code == 200
        body = response.json()
        assert {u["user_name"] for u in body} == {"bob", "tom"}


def test_query_filters_absent_returns_all(async_session, test_user_data, init_data):
    """No filter params returns everything."""
    app = _make_filter_app(async_session, FILTER_QUERY)
    with TestClient(app) as client:
        response = client.get("/user/")
        assert response.status_code == 200
        assert len(response.json()) == len(test_user_data)


def test_query_filters_invalid_type_422(async_session, init_data):
    """Wrong-typed filter value is rejected by FastAPI validation."""
    app = _make_filter_app(async_session, FILTER_QUERY)
    with TestClient(app) as client:
        response = client.get("/user/", params={"company_id": "abc"})
        assert response.status_code == 422


def test_query_filters_combine_with_filter_param(async_session, init_data):
    """Declared filters AND-combine with the generic ?filter= conditions."""
    app = _make_filter_app(async_session, FILTER_QUERY)
    with TestClient(app) as client:
        response = client.get("/user/", params={
            "company_id": 1,
            "filter": "user_name||$eq||bob",
        })
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["user_name"] == "bob"


def test_query_filters_missing_join_raises(async_session):
    """A relationship field without a declared join fails fast at registration."""
    with pytest.raises(ValueError, match="must be declared in query.joins"):
        _make_filter_app(async_session, {
            "filters": {
                "by_company": {"field": "company.name", "type": "str"},
            },
        })


def test_query_filters_name_collision_raises(async_session):
    """A filter name colliding with a reserved get_many parameter fails fast."""
    with pytest.raises(ValueError, match="collides with a reserved"):
        _make_filter_app(async_session, {
            "filters": {
                "search": {"field": "company_id", "type": "int"},
            },
        })


def test_query_filters_required_422(async_session, init_data):
    """A required filter rejects requests that omit it."""
    app = _make_filter_app(async_session, {
        "filters": {
            "must_company": {"field": "company_id", "type": "int", "required": True},
        },
    })
    with TestClient(app) as client:
        assert client.get("/user/").status_code == 422
        response = client.get("/user/", params={"must_company": 1})
        assert response.status_code == 200
        assert len(response.json()) == 2
