import pytest
from app.services.user import UserService
from fastapi_crud.models import JoinOptionModel
from fastapi_crud.exceptions import NotSupportOperatorException,InvalidFieldException


@pytest.mark.asyncio
async def test_get_many_basic(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    fetched_records = await user_service.crud_get_many(test_request, db_session=async_session)
    assert len(fetched_records) == len(test_user_data)


@pytest.mark.asyncio
async def test_get_many_basic_filter(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    search = {
        "user_name": "jim",
        "is_active": True
    }
    fetched_records = await user_service.crud_get_many(test_request, search=search, db_session=async_session)
    assert len(fetched_records) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,operator,value,expected_count",
    [
        ("user_name", "$eq", "tom", 1),
        ("user_name", "$eq", "jack", 0),
        ("is_superuser", "$eq", True, 2),
        ("user_name", "$ne", "alice", 3),
        ("user_name", "$starts", "alice", 1),
        ("email", "$ends", ".com", 4),
        ("user_name", "$cont", "i", 2),
        ("user_name", "$excl", "i", 2),
        ("profile.address", "$isnull", None, 1),
        ("profile.address", "$notnull", None, 3),
        ("profile.birthdate", "$gt", "2022-01-01", 1),
        ("profile.birthdate", "$gte", "2022-01-01", 2),
        ("profile.birthdate", "$lt", "2025-01-01", 4),
        ("profile.birthdate", "$lte", "2022-01-01", 3),
        ("user_name", "$notstarts", "alice", 3),
        ("email", "$notends", ".com", 0),
        ("profile.gender", "$in", "male,female", 4),
        ("profile.gender", "$notin", "male,female", 0),
        ("profile.birthdate", "$between", "2022-01-01,2025-01-01", 2),
        ("profile.birthdate", "$between", "2010-01-01,2025-01-01", 4),
        ("profile.birthdate", "$notbetween", "2010-01-01,2025-01-01", 0),
        ("user_name", "$length", 3, 3),
        ("roles", "$any", 1, 2),
        ("roles", "$notany", 1, 2),
    ]
)
async def test_get_many_filter_width_operator(
    async_session,
    test_request,
    init_data,
    field,
    operator,
    value,
    expected_count
):
    user_service = UserService()
    joins = {
        "profile": JoinOptionModel(
            select=False,
            join=True
        ),
        "roles":JoinOptionModel(
            select=True,
            join=False
        ),
    }
    search = {
        field: {
            operator: value
        }
    }
    fetched_records = await user_service.crud_get_many(test_request, search=search, joins=joins, db_session=async_session)
    assert len(fetched_records) == expected_count

@pytest.mark.asyncio
async def test_get_many_filter_width_invalid_operator(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    search = {
        "user_name": {
            "invalid_operator": "jim"
        }
    }
    with pytest.raises(NotSupportOperatorException):
        await user_service.crud_get_many(test_request, search=search, db_session=async_session)

@pytest.mark.asyncio
async def test_get_many_filter_width_invalid_field(async_session, test_user_data, test_request, init_data):
    user_service = UserService()
    search = {
        "invalid_field": {
            "$eq": "jim"
        }
    }
    with pytest.raises(InvalidFieldException):
        await user_service.crud_get_many(test_request, search=search, db_session=async_session)