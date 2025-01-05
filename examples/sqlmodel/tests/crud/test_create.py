import pytest
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.user import User, UserCreate
from app.models.role import RoleCreate, Role
from app.models.user_task import UserTaskCreateWithoutId
from app.services.user import UserService
from app.services.role import RoleService
from app.services.user_task import UserTaskService


@pytest.mark.asyncio
async def test_create_successful(async_session, test_request,test_user_data):
    first_test_user_data = test_user_data[0]
    user_service = UserService()
    user_create = UserCreate(**first_test_user_data)
    await user_service.crud_create_one(test_request, user_create, db_session=async_session)
    stmt = select(User).where(User.user_name == first_test_user_data["user_name"])
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.user_name == first_test_user_data["user_name"]
    assert fetched_record.email == first_test_user_data["email"]
    assert fetched_record.company_id == first_test_user_data["company_id"]



@pytest.mark.asyncio
async def test_create_many_successful(async_session, test_request, test_user_data):
    user_service = UserService()
    new_data = [UserCreate(**item) for item in test_user_data]
    await user_service.crud_create_many(test_request, new_data, db_session=async_session)
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
async def test_create_by_one_to_one(async_session, test_user_data, test_request):
    user_service = UserService()

    new_data = UserCreate(
        **test_user_data[0],
    )
    await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.staff))
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    for key, value in test_user_data[0]["staff"].items():
        assert getattr(fetched_record.staff, key) == value


@pytest.mark.asyncio
async def test_create_by_many_to_one(async_session, test_user_data, test_request):
    user_service = UserService()
    new_data = UserCreate(
        **test_user_data[0],
    )
    res = await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.profile))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert fetched_record.profile_id == res.profile_id
    for key, value in test_user_data[0]["profile"].items():
        assert getattr(fetched_record.profile, key) == value


@pytest.mark.asyncio
async def test_create_by_one_to_many(async_session, test_user_data, test_request):
    user_service = UserService()
    new_data = UserCreate(
        **test_user_data[0],
    )
    await user_service.crud_create_one(test_request, new_data, db_session=async_session)
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
async def test_create_by_many_to_many(async_session, test_request, test_user_data, test_role_data):
    user_service = UserService()
    role_service = RoleService()
    for role_data in test_role_data:
        await role_service.crud_create_one(test_request, RoleCreate(**role_data), db_session=async_session)
    result = await async_session.execute(select(Role))
    fetched_roles: List[Role] = result.unique().scalars().all()
    fetched_role_ids = [item.id for item in fetched_roles]
    new_data = UserCreate(
        **test_user_data[0],
        roles=fetched_role_ids
    )
    await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data[0]["email"])
    stmt = stmt.options(joinedload(User.roles))
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert len(fetched_record.roles) == len(fetched_roles)
    for index, role_item in enumerate(test_role_data):
        for key, value in role_item.items():
            assert getattr(fetched_record.roles[index], key) == value
        assert fetched_record.roles[index].id == fetched_role_ids[index]


@pytest.mark.asyncio
async def test_create_by_auth_persist(async_session, test_request):
    user_task_service = UserTaskService()
    new_data = UserTaskCreateWithoutId(
        status="pending", description="pending task")
    test_request.state.auth_persist = {
        "user_id": 1
    }
    res = await user_task_service.crud_create_one(test_request, new_data, db_session=async_session)
    assert res.user_id == 1


@pytest.mark.asyncio
async def test_create_by_params_filter(async_session, test_request):
    user_task_service = UserTaskService()
    new_data = UserTaskCreateWithoutId(
        status="pending", description="pending task")
    test_request.state.params_filter = {
        "user_id": 1
    }
    res = await user_task_service.crud_create_one(test_request, new_data, db_session=async_session)
    assert res.user_id == 1
