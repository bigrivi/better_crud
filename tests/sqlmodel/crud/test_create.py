import pytest
from sqlalchemy import select
from examples.app.models.company import Company, CompanyCreate
from examples.app.services.company import CompanyService


@pytest.mark.asyncio
async def test_create_successful(async_session):
    company_service = CompanyService()
    new_data = CompanyCreate(name="New Company", domain="test", description="")
    await company_service.crud_create_one(None, new_data, db_session=async_session)
    stmt = select(Company).where(Company.name == "New Company")
    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.name == "New Company"
    assert fetched_record.domain == "test"
