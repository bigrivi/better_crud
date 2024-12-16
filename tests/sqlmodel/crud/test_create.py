import pytest
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_successful(my_test_company_service,test_model,create_schema,async_session):
    new_data = create_schema(name="New Company", domain="test",description="")
    await my_test_company_service.crud_create_one(None,new_data,db_session=async_session)
    stmt = select(test_model).where(test_model.name == "New Company")
    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.name == "New Company"
    assert fetched_record.domain == "test"

