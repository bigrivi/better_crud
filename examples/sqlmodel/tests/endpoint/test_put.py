import pytest
from typing import List
from fastapi.testclient import TestClient
from sqlalchemy import select
from fastapi_crud.exceptions import NotFoundException
from sqlalchemy.orm import joinedload
from app.models.user import User
from app.models.user_task import UserTask


@pytest.mark.asyncio
async def test_put_successful(client: TestClient, async_session, test_user_data, init_data):
    exist_user_id = test_user_data[0]["id"]
    update_data = dict(email="updated@email.com", is_active=False)
    client.put(f"/user/{exist_user_id}", json=update_data)
    stmt = select(User).where(User.id == exist_user_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == "updated@email.com"
    assert fetched_record.is_active == False


@pytest.mark.asyncio
async def test_put_non_existent_record(client: TestClient, async_session, test_request, init_data):
    non_existent_id = 1000
    update_data = dict(email="updated@email.com", is_active=False)
    response = client.put(f"/user/{non_existent_id}", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "No data found"}


@pytest.mark.asyncio
async def test_put_by_one_to_one(client: TestClient, async_session, test_user_data, init_data):
    exist_user_id = test_user_data[0]["id"]
    update_staff = {
        "name": "bob1 new",
        "position": "CEO1 new",
        "job_title": "The Chief Executive Officer1 new"
    }
    update_data = dict(staff=update_staff)
    client.put(f"/user/{exist_user_id}", json=update_data)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.staff))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    for key, value in update_staff.items():
        assert getattr(fetched_record.staff, key) == value


@pytest.mark.asyncio
async def test_put_by_many_to_one(client: TestClient, async_session, test_user_data, init_data):
    exist_user_id = test_user_data[0]["id"]
    update_profile = {
        "name": "andy",
        "gender": "female",
        "phone": "222222",
        "birthdate": "2020-02-01",
        "hobby": "kungfu",
        "state": "sad",
        "country": "china",
        "address": "jiangsu"
    }
    update_data = dict(profile=update_profile)
    client.put(f"/user/{exist_user_id}", json=update_data)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.profile))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    for key, value in update_profile.items():
        assert getattr(fetched_record.profile, key) == value


@pytest.mark.asyncio
async def test_put_by_one_to_many(client: TestClient, async_session, test_user_data, init_data):
    exist_user_id = test_user_data[0]["id"]
    new_tasks = [
        {
            "id": 1,
            "status": "completed",
            "description": "pending task new"
        },
        {
            "id": 2,
            "status": "completed",
            "description": "inprogress task new"
        },
        {
            "id": 3,
            "status": "inprogress",
            "description": "completed task new"
        },
        {
            "status": "completed",
            "description": "add completed task"
        }
    ]
    update_data = dict(tasks=new_tasks)
    client.put(f"/user/{exist_user_id}", json=update_data)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.tasks))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert len(fetched_record.tasks) == len(new_tasks)
    for index, task_item in enumerate(new_tasks):
        for key, value in task_item.items():
            assert getattr(fetched_record.tasks[index], key) == value

    stmt = select(UserTask)
    stmt = stmt.where(UserTask.user_id == test_user_data[0]["id"])
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_records: List[UserTask] = result.unique().scalars().all()
    assert len(fetched_records) == len(new_tasks)
    assert all(
        record.user_id == exist_user_id
        for record in fetched_records
    )


@pytest.mark.asyncio
async def test_put_by_many_to_many(client: TestClient, async_session, test_user_data, test_role_data, init_data):
    exist_user_id = test_user_data[0]["id"]
    new_roles = [
        2, 3
    ]
    update_data = dict(roles=new_roles)
    client.put(f"/user/{exist_user_id}", json=update_data)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.roles))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert len(fetched_record.roles) == len(new_roles)
    for index, role_id in enumerate(new_roles):
        assert getattr(fetched_record.roles[index], "id") == role_id
        role_data = next(x for x in test_role_data if x["id"] == role_id)
        for key, value in role_data.items():
            assert getattr(fetched_record.roles[index], key) == value


@pytest.mark.asyncio
async def test_put_many(client: TestClient, async_session, test_user_data, init_data):
    exist_user_ids = [test_user_data[0]["id"], test_user_data[1]["id"]]
    update_data = [
        dict(
            email="bobnew@gmail.com",
            staff={
                "name": "bob new",
                "position": "CEO new",
                "job_title": "The Chief Executive Officer1 new"
            }),
        dict(
            email="alicenew@gmail.com",
            staff={
                "name": "alice new",
                "position": "CFO new",
                "job_title": "Chief Financial Officer new"
            })
    ]
    exist_user_ids_str = ",".join(map(str, exist_user_ids))
    res = client.put(f"/user/{exist_user_ids_str}/bulk", json=update_data)
    stmt = select(User).where(User.id.in_(exist_user_ids))
    stmt = stmt.options(joinedload(User.staff))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_records: List[User] = result.unique().scalars().all()
    for index, item in enumerate(update_data):
        assert fetched_records[index].email == item["email"]
        for key, value in item["staff"].items():
            assert getattr(fetched_records[index].staff, key) == value


@pytest.mark.asyncio
async def test_put_many_mismatch_length(client: TestClient, async_session, test_user_data, init_data):
    exist_user_ids = [test_user_data[0]["id"], test_user_data[1]["id"]]
    update_data = [
        dict(
            email="bobnew@gmail.com",
            staff={
                "name": "bob new",
                "position": "CEO new",
                "job_title": "The Chief Executive Officer1 new"
            })
    ]
    exist_user_ids_str = ",".join(map(str, exist_user_ids))
    response = client.put(f"/user/{exist_user_ids_str}/bulk", json=update_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "The id and payload length do not match"}


@pytest.mark.asyncio
async def test_put_many_non_existent_record(client: TestClient, async_session, init_data):
    not_exist_user_ids = [1000, 1001]
    update_data = [
        dict(
            email="bobnew@gmail.com",
            staff={
                "name": "bob new",
                "position": "CEO new",
                "job_title": "The Chief Executive Officer1 new"
            }),
        dict(
            email="alicenew@gmail.com",
            staff={
                "name": "alice new",
                "position": "CFO new",
                "job_title": "Chief Financial Officer new"
            })
    ]
    not_exist_user_ids_str = ",".join(map(str, not_exist_user_ids))
    response = client.put(f"/user/{not_exist_user_ids_str}/bulk", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "No data found"}