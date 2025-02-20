import pytest
from typing import List
from sqlalchemy import select
from better_crud.exceptions import NotFoundException
from sqlalchemy.orm import joinedload
from app.models.user import User, UserUpdate
from app.models.user_task import UserTask
from app.services.user import UserService


@pytest.mark.asyncio
async def test_update_successful(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_id = test_user_data[0]["id"]
    new_email = "updated@email.com"
    update_data = UserUpdate(email=new_email, is_active=False)
    res = await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session)
    assert res.email == new_email
    stmt = select(User).where(User.id == exist_user_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == new_email
    assert fetched_record.is_active == False


@pytest.mark.asyncio
async def test_update_non_existent_record(async_session, test_request, init_data):
    non_existent_id = 1000
    user_service = UserService()
    update_data = UserUpdate(email="updated@email.com", is_active=False)
    with pytest.raises(NotFoundException) as exc_info:
        await user_service.crud_update_one(test_request, non_existent_id, update_data, db_session=async_session)


@pytest.mark.asyncio
async def test_update_by_one_to_one(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_id = test_user_data[0]["id"]
    update_staff = {
        "name": "bob1 new",
        "position": "CEO1 new",
        "job_title": "The Chief Executive Officer1 new"
    }
    update_data = UserUpdate(staff=update_staff)
    await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session)
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
async def test_update_by_many_to_one(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
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
    update_data = UserUpdate(profile=update_profile)
    res = await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.profile))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert fetched_record.profile_id == res.profile_id
    for key, value in update_profile.items():
        assert getattr(fetched_record.profile, key) == value


@pytest.mark.asyncio
async def test_update_by_one_to_many(async_session, test_user_data, test_request, init_data):
    exist_user_id = test_user_data[0]["id"]
    user_service = UserService()
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
    update_data = UserUpdate(tasks=new_tasks)
    await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session,)
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
async def test_update_by_many_to_many(async_session, test_user_data, test_role_data, test_request, init_data):
    exist_user_id = test_user_data[0]["id"]
    user_service = UserService()
    new_roles = [
        2, 3
    ]
    update_data = UserUpdate(roles=new_roles)
    await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session)
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
async def test_update_many(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_ids = [test_user_data[0]["id"], test_user_data[1]["id"]]
    update_data = [
        UserUpdate(
            email="bobnew@gmail.com",
            staff={
                "name": "bob new",
                "position": "CEO new",
                "job_title": "The Chief Executive Officer1 new"
            }),
        UserUpdate(
            email="alicenew@gmail.com",
            staff={
                "name": "alice new",
                "position": "CFO new",
                "job_title": "Chief Financial Officer new"
            })
    ]
    res = await user_service.crud_update_many(test_request, exist_user_ids, update_data, db_session=async_session)
    stmt = select(User).where(User.id.in_(exist_user_ids))
    stmt = stmt.options(joinedload(User.staff))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_records: List[User] = result.unique().scalars().all()
    for index, item in enumerate(update_data):
        assert fetched_records[index].email == item.email
        assert res[index].email == item.email
        for key, value in item.staff.model_dump().items():
            assert getattr(fetched_records[index].staff, key) == value
            assert getattr(res[index].staff, key) == value


@pytest.mark.asyncio
async def test_update_many_id_model_length_mismatch(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_ids = [test_user_data[0]["id"], test_user_data[1]["id"]]
    update_data = [
        UserUpdate(
            email="bobnew@gmail.com",
            staff={
                "name": "bob new",
                "position": "CEO new",
                "job_title": "The Chief Executive Officer1 new"
            })
    ]
    with pytest.raises(Exception) as exc_info:
        await user_service.crud_update_many(test_request, exist_user_ids, update_data, db_session=async_session)
