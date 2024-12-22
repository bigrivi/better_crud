import pytest
from typing import List
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from app.models.company import Company, CompanyUpdate
from app.models.user import User, UserUpdate
from app.models.role import Role
from app.models.user_task import UserTask
from app.models.staff import Staff
from app.models.user_profile import UserProfile
from app.services.company import CompanyService
from app.services.company import CompanyService
from app.services.user import UserService


async def add_test_init_data(async_session, test_user_data, test_role_data):
    roles = []
    for role_data in test_role_data:
        role = Role()
        role.name = role_data["name"]
        role.description = role_data["description"]
        async_session.add(role)
        roles.append(role)
    await async_session.flush()
    user = User()
    user.email = test_user_data["email"]
    user.hashed_password = test_user_data["password"]
    user.is_active = test_user_data["is_active"]
    user.profile = UserProfile(**test_user_data["profile"])
    user.staff = Staff(**test_user_data["staff"])
    user.tasks = [UserTask(**task_data)
                  for task_data in test_user_data["tasks"]]
    user.roles = [roles[0]]
    async_session.add(user)
    await async_session.commit()


@pytest.mark.asyncio
async def test_update_successful(async_session):
    company = Company(name="Original Name")
    async_session.add(company)
    await async_session.commit()
    company_id = company.id
    company_service = CompanyService()
    update_data = CompanyUpdate(name="Updated Name")
    await company_service.crud_update_one(None, company_id, update_data, db_session=async_session)
    stmt = select(Company).where(Company.id == company_id)
    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_non_existent_record(async_session):
    non_existent_id = 1
    update_data = CompanyUpdate(name="Updated Name")
    company_service = CompanyService()
    with pytest.raises(HTTPException) as exc_info:
        await company_service.crud_update_one(None, non_existent_id, update_data, db_session=async_session)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Data not found"
    record = await async_session.execute(
        select(Company).where(Company.id == non_existent_id)
    )
    assert record.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_update_by_one_to_one(async_session, test_user_data, test_role_data, test_request):
    user_service = UserService()
    await add_test_init_data(async_session, test_user_data, test_role_data)
    update_staff = {
        "name": "bob1 new",
        "position": "CEO1 new",
        "job_title": "The Chief Executive Officer1 new"
    }
    update_data = UserUpdate(staff=update_staff)
    res = await user_service.crud_update_one(test_request, 1, update_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.staff))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    for key, value in update_staff.items():
        assert getattr(fetched_record.staff, key) == value


@pytest.mark.asyncio
async def test_update_by_many_to_one(async_session, test_user_data, test_role_data, test_request):
    user_service = UserService()
    await add_test_init_data(async_session, test_user_data, test_role_data)
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
    res = await user_service.crud_update_one(test_request, 1, update_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.profile))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    assert fetched_record.profile_id == res.profile_id
    for key, value in update_profile.items():
        assert getattr(fetched_record.profile, key) == value


@pytest.mark.asyncio
async def test_update_by_one_to_many(async_session, test_user_data, test_role_data, test_request):
    exist_user_id = test_user_data["id"]
    user_service = UserService()
    await add_test_init_data(async_session, test_user_data, test_role_data)
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
    res = await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.tasks))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    assert len(fetched_record.tasks) == len(new_tasks)
    for index, task_item in enumerate(new_tasks):
        for key, value in task_item.items():
            assert getattr(fetched_record.tasks[index], key) == value

    stmt = select(UserTask)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_records: List[UserTask] = result.unique().scalars().all()
    assert len(fetched_records) == len(new_tasks)
    assert all(
        record.user_id == exist_user_id
        for record in fetched_records
    )


@pytest.mark.asyncio
async def test_update_by_many_to_many(async_session, test_user_data, test_role_data, test_request):
    exist_user_id = test_user_data["id"]
    user_service = UserService()
    await add_test_init_data(async_session, test_user_data, test_role_data)
    new_roles = [
        2, 3
    ]
    update_data = UserUpdate(roles=new_roles)
    res = await user_service.crud_update_one(test_request, exist_user_id, update_data, db_session=async_session)
    stmt = select(User).where(User.email == test_user_data["email"])
    stmt = stmt.options(joinedload(User.roles))
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.unique().scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.email == test_user_data["email"]
    assert len(fetched_record.roles) == len(new_roles)
    for index, role_id in enumerate(new_roles):
        assert getattr(fetched_record.roles[index], "id") == role_id
        role_data = next(x for x in test_role_data if x["id"] == role_id)
        for key, value in role_data.items():
            assert getattr(fetched_record.roles[index], key) == value
