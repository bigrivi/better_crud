import pytest
from typing import List
import pytest_asyncio
from sqlalchemy import select
from fastapi import HTTPException
from app.models.user import User, UserUpdate
from app.services.user import UserService


@pytest.mark.asyncio
async def test_delete_successful(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_id = test_user_data[0]["id"]
    await user_service.crud_delete_many(test_request, [exist_user_id], soft_delete=False, db_session=async_session)
    stmt = select(User).where(User.id == exist_user_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is None


@pytest.mark.asyncio
async def test_soft_delete_successful(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    exist_user_id = test_user_data[0]["id"]
    await user_service.crud_delete_many(test_request, [exist_user_id], soft_delete=True, db_session=async_session)
    stmt = select(User).where(User.id == exist_user_id)
    stmt = stmt.execution_options(populate_existing=True)
    result = await async_session.execute(stmt)
    fetched_record: User = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.deleted_at is not None
