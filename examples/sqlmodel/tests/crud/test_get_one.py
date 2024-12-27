import pytest
from fastapi_crud.exceptions import NotFoundException
from app.services.user import UserService


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
