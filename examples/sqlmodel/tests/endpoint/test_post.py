from fastapi.testclient import TestClient
import pytest
from typing import List
from sqlalchemy import select
from app.models.user import User



@pytest.mark.asyncio
async def test_post_successful(client: TestClient, async_session,test_user_data):
    first_test_user_data = test_user_data[0]
    response = client.post("/user", json=first_test_user_data)
    assert response.status_code == 200
    stmt = select(User).where(User.user_name == first_test_user_data["user_name"])
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.user_name == first_test_user_data["user_name"]
    assert fetched_record.email == first_test_user_data["email"]
    assert fetched_record.company_id == first_test_user_data["company_id"]

@pytest.mark.asyncio
async def test_post_many_successful(client: TestClient,async_session, test_user_data):
    response = client.post("/user/bulk", json=test_user_data)
    assert response.status_code == 200
    stmt = select(User).where(
        User.user_name.in_([item["user_name"] for item in test_user_data]))
    result = await async_session.execute(stmt)
    fetched_records: List[User] = result.scalars().all()
    assert len(fetched_records) == len(test_user_data)
    for index, item in enumerate(test_user_data):
        assert fetched_records[index].user_name == item["user_name"]
        assert fetched_records[index].email == item["email"]
        assert fetched_records[index].company_id == item["company_id"]