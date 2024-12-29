import pytest
from fastapi_crud.exceptions import NotFoundException
from fastapi_crud.models import JoinOptionModel
from app.services.user import UserService
from app.models.role import Role


@pytest.mark.asyncio
async def test_get_one_successful(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_id = test_user_data[0]["id"]
    fetched_record = await user_service.crud_get_one(test_request, exist_user_id, db_session=async_session)
    assert fetched_record is not None
    assert fetched_record.email == test_user_data[0]["email"]
    assert fetched_record.is_active == test_user_data[0]["is_active"]


@pytest.mark.asyncio
async def test_get_one_non_existent_record(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    non_existent_id = 1000
    with pytest.raises(NotFoundException):
        await user_service.crud_get_one(test_request, non_existent_id, db_session=async_session)


@pytest.mark.asyncio
async def test_get_one_relations(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    joins = {
        "profile": JoinOptionModel(
            select=True,
        ),
        "tasks": JoinOptionModel(select=True),
        "company": JoinOptionModel(select=True),
        "roles": JoinOptionModel(select=True, select_only_detail=True),
        "staff": JoinOptionModel(select=False)
    }
    exist_user_id = test_user_data[0]["id"]
    fetched_record = await user_service.crud_get_one(test_request, exist_user_id, db_session=async_session, joins=joins)
    assert fetched_record is not None
    assert fetched_record.profile is not None
    assert fetched_record.tasks is not None
    assert fetched_record.company is not None
    assert fetched_record.roles is not None
    assert fetched_record.staff is None
    assert len(fetched_record.roles) == 2


@pytest.mark.asyncio
async def test_get_one_relations_with_additional_filter_fn(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    joins = {
        "roles": JoinOptionModel(
            select=True,
            select_only_detail=True,
            additional_filter_fn=lambda _: Role.id == 2
        ),
    }
    exist_user_id = test_user_data[0]["id"]
    fetched_record = await user_service.crud_get_one(test_request, exist_user_id, db_session=async_session, joins=joins)
    assert fetched_record is not None
    assert fetched_record.roles is not None
    assert len(fetched_record.roles) == 1
    assert fetched_record.roles[0].id == 2
