from asyncio import Future
from typing import Optional, Any
from unittest.mock import MagicMock
from better_crud import FastAPICrudGlobalConfig, crud_generator
from sqlalchemy import select
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter
from app.models.company import CompanyCreate, CompanyUpdate, CompanyPublic, Company
import pytest


def async_return(result: Optional[Any] = None):
    f = Future()
    f.set_result(result)
    return f


on_before_create = MagicMock(return_value=async_return())
on_after_create = MagicMock(return_value=async_return())
on_before_update = MagicMock(return_value=async_return())
on_after_update = MagicMock(return_value=async_return())
on_before_delete = MagicMock(return_value=async_return())
on_after_delete = MagicMock(return_value=async_return())


@pytest.fixture
def company_client(
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
    entity_router = APIRouter()
    crud_generator(
        entity_router,
        Company,
        dto={"create": CompanyCreate, "update": CompanyUpdate},
        routes={},
        serialize={"base": CompanyPublic},
        on_before_create=on_before_create,
        on_after_create=on_after_create,
        on_before_update=on_before_update,
        on_after_update=on_after_update,
        on_before_delete=on_before_delete,
        on_after_delete=on_after_delete
    )

    api_router = APIRouter()
    api_router.include_router(entity_router, prefix="/company")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_get_many(company_client: TestClient, test_company_data, init_data):
    response = company_client.get("/company")
    data = response.json()
    assert len(data) == len(test_company_data)


@pytest.mark.asyncio
async def test_get_one(company_client: TestClient, async_session, init_data, test_company_data):
    exist_id = 1
    response = company_client.get(f"/company/{exist_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exist_id
    assert data["name"] == test_company_data[0]["name"]


@pytest.mark.asyncio
async def test_post(company_client: TestClient, async_session):
    test_data = {
        "name": "new company"
    }
    response = company_client.post("/company", json=test_data)
    assert response.status_code == 200
    stmt = select(Company).where(Company.name == test_data["name"])
    result = await async_session.execute(stmt)
    fetched_record: Company = result.scalar_one_or_none()
    assert fetched_record is not None
    on_before_create.assert_called()
    on_after_create.assert_called()


@pytest.mark.asyncio
async def test_put(company_client: TestClient, async_session, test_user_data, init_data):
    exist_id = 1
    update_data = dict(name="updated name")
    company_client.put(f"/company/{exist_id}", json=update_data)
    stmt = select(Company).where(Company.id == exist_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: Company = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.name == update_data["name"]
    on_before_update.assert_called()
    on_after_update.assert_called()


@pytest.mark.asyncio
async def test_delete(company_client: TestClient, async_session, test_user_data, init_data):
    exist_id = 1
    company_client.delete(f"/company/{exist_id}")
    stmt = select(Company).where(Company.id == exist_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: Company = result.scalar_one_or_none()
    assert fetched_record is None
    on_before_delete.assert_called()
    on_after_delete.assert_called()
