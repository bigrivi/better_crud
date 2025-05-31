from fastapi.testclient import TestClient
import pytest
from typing import List
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role
from app.models.zone import Zone
from app.models.user_task import UserTask
from sqlalchemy.orm import joinedload




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

@pytest.mark.asyncio
async def test_post_by_one_to_one(client: TestClient,async_session, test_user_data):
    client.post("/user", json=test_user_data[0])
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.staff))
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    for key, value in test_user_data[0]["staff"].items():
        assert getattr(fetched_record.staff, key) == value


@pytest.mark.asyncio
async def test_post_by_one_to_many(client: TestClient,async_session, test_user_data):
    client.post("/user", json=test_user_data[0])
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.tasks))
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert len(fetched_record.tasks) == len(test_user_data[0]["tasks"])
    for index, task_item in enumerate(test_user_data[0]["tasks"]):
        for key, value in task_item.items():
            assert getattr(fetched_record.tasks[index], key) == value


@pytest.mark.asyncio
async def test_post_by_many_to_many(client: TestClient,async_session, test_user_data,test_role_data):
    role_ids = []
    for role_data in test_role_data:
        role = Role(**role_data)
        role_ids.append(role_data["id"])
        async_session.add(role)
    await async_session.commit()
    client.post("/user", json={**test_user_data[0],"roles":role_ids})
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.roles))
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert len(fetched_record.roles) == len(role_ids)
    for index, role_item in enumerate(test_role_data):
        for key, value in role_item.items():
            assert getattr(fetched_record.roles[index], key) == value
        assert fetched_record.roles[index].id == role_ids[index]


@pytest.mark.asyncio
async def test_post_by_many_to_many_single_object(client: TestClient,async_session, test_user_data,test_zone_data):
    test_zone = test_zone_data[1]
    zone = Zone(**test_zone)
    async_session.add(zone)
    await async_session.commit()
    client.post("/user", json={**test_user_data[0],"zone":test_zone["id"]})
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.zone))
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    for key, value in test_zone.items():
        assert getattr(fetched_record.zone, key) == value


@pytest.mark.asyncio
async def test_post_by_auth_persist(auth_client: TestClient,async_session, test_request):
    res = auth_client.post("/user_task", json=dict(status="pending", description="pending task"))
    task_id = res.json()["id"]
    stmt = select(UserTask).where(UserTask.id == task_id)
    result = await async_session.execute(stmt)
    fetched_record: UserTask = result.scalar_one_or_none()
    assert fetched_record.user_id == 1

@pytest.mark.asyncio
async def test_post_by_params_persist(params_client: TestClient,async_session, test_request):
    res = params_client.post("/2/user_task", json=dict(status="pending", description="pending task"))
    task_id = res.json()["id"]
    stmt = select(UserTask).where(UserTask.id == task_id)
    result = await async_session.execute(stmt)
    fetched_record: UserTask = result.scalar_one_or_none()
    assert fetched_record.user_id == 2