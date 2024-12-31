import pytest
from app.services.user import UserService


@pytest.mark.asyncio
async def test_get_many_basic(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    fetched_records = await user_service.crud_get_many(test_request, db_session=async_session)
    assert len(fetched_records) == len(test_user_data)
