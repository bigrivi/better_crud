from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from examples.app.models.company import Company


@pytest.mark.asyncio
async def test_post(client: TestClient, async_session):
    test_data = {"name": "New Company"}
    response = client.post("/company", json=test_data)
    assert response.status_code == 200
    stmt = select(Company).where(Company.name == test_data["name"])
    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()
    assert fetched_record is not None, response.text
    assert fetched_record.name == test_data["name"]
