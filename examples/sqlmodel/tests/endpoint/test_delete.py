import pytest
from typing import List
from fastapi.testclient import TestClient
from sqlalchemy import select
from better_crud.exceptions import NotFoundException
from sqlalchemy.orm import joinedload
from app.models.user import User
from app.models.user_task import UserTask


@pytest.mark.asyncio
async def test_delete_successful(client: TestClient, async_session, test_user_data):
    exist_user_id = test_user_data[0]["id"]
    client.delete(f"/user/{exist_user_id}")
    stmt = select(User).where(User.id == exist_user_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is None


@pytest.mark.asyncio
async def test_delete_many_non_existent_record(client: TestClient, async_session):
    not_exist_user_ids = [1000, 1001]
    not_exist_user_ids_str = ",".join(map(str, not_exist_user_ids))
    response = client.delete(f"/user/{not_exist_user_ids_str}")
    assert response.status_code == 404
    assert response.json() == {"detail": "No data found"}
