import pytest
from sqlalchemy import select
from fastapi import HTTPException
from app.models.company import Company, CompanyUpdate
from app.services.company import CompanyService


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
