import pytest
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.company import Company, CompanyCreate
from app.models.user import User, UserCreate
from app.models.role import RoleCreate, Role
from app.models.user_task import UserTaskCreateWithoutId
from app.services.company import CompanyService
from app.services.user import UserService
from app.services.role import RoleService
from app.services.user_task import UserTaskService, UserTask


@pytest.mark.asyncio
async def test_create_successful(async_session, test_request):
    company_service = CompanyService()
    new_data = CompanyCreate(name="New Company", domain="test", description="")
    await company_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(Company).where(Company.name == "New Company")
    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.name == "New Company"
    assert fetched_record.domain == "test"


@pytest.mark.asyncio
async def test_create_many_successful(async_session, test_request):
    company_service = CompanyService()
    test_data = [
        {
            "name": "New Company1",
            "domain": "domain1",
            "description": "description1"
        },
        {
            "name": "New Company2",
            "domain": "domain2",
            "description": "description2"
        },
        {
            "name": "New Company3",
            "domain": "domain3",
            "description": "description3"
        }
    ]
    new_data = [CompanyCreate(**item) for item in test_data]
    await company_service.crud_create_many(test_request, new_data, db_session=async_session)
    stmt = select(Company).where(
        Company.name.in_([item.name for item in new_data]))
    result = await async_session.execute(stmt)
    fetched_records: List[Company] = result.scalars().all()
    assert len(fetched_records) == len(test_data)
    for index, item in enumerate(test_data):
        for key, value in item.items():
            assert getattr(fetched_records[index], key) == value


@pytest.mark.asyncio
async def test_create_by_one_to_one(async_session, test_user_data, test_request):
    user_service = UserService()
    staff_data = {
        "name": "bob",
        "position": "CEO",
        "job_title": "The Chief Executive Officer"
    }
    new_data = UserCreate(
        **test_user_data,
        staff=staff_data
    )
    await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.staff))
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    for key, value in staff_data.items():
        assert getattr(fetched_record.staff, key) == value


@pytest.mark.asyncio
async def test_create_by_many_to_one(async_session, test_user_data, test_request):
    user_service = UserService()
    profile_data = {
        "name": "bob",
        "gender": "male",
        "phone": "111111",
        "birthdate": "2020-01-01",
        "hobby": "music",
        "state": "nice",
        "country": "china",
        "address": "anhui"
    }
    new_data = UserCreate(
        **test_user_data,
        profile=profile_data
    )
    res = await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.profile))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    assert fetched_record.profile_id == res.profile_id
    for key, value in profile_data.items():
        assert getattr(fetched_record.profile, key) == value


@pytest.mark.asyncio
async def test_create_by_one_to_many(async_session, test_user_data, test_request):
    user_service = UserService()
    tasks = [
        {
            "status": "pending",
            "description": "pending task"
        },
        {
            "status": "inprogress",
            "description": "inprogress task"
        },
        {
            "status": "completed",
            "description": "completed task"
        }
    ]
    new_data = UserCreate(
        **test_user_data,
        tasks=tasks
    )
    await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.tasks))
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    assert len(fetched_record.tasks) == len(tasks)
    for index, task_item in enumerate(tasks):
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
        **test_user_data,
        roles=fetched_role_ids
    )
    await user_service.crud_create_one(test_request, new_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.roles))
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
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
