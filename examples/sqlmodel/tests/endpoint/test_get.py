import pytest
import json
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_get_many_basic(client: TestClient, test_user_data, init_data):
    response = client.get("/user")
    data = response.json()
    assert len(data) == len(test_user_data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,expected_count",
    [
        ({
            "s": json.dumps(
                {
                    "user_name": "jim",
                    "is_active": True
                }
            )}, 1),
        ({
            "filter": [
                "user_name||$eq||jim",
                "is_active||$eq||1",
                "email||$notnull"
            ]}, 1),
        ({
            "filter": [
                "user_name||$eq||jim",
            ],
            "or": [
                "user_name||$eq||bob",
            ]
        }, 2),
        ({
            "filter": [
                "user_name||$eq||jim",
                "is_active||$eq||1",
            ],
            "or": [
                "user_name||$eq||bob",
                "is_active||$eq||1",
            ]
        }, 2),
        ({
            "or": [
                "user_name||$eq||bob"
            ]
        }, 1),
        ({
            "or": [
                "user_name||$eq||bob",
                "user_name||$eq||jim",
                "user_name||$eq||alice",
            ]
        }, 3)
    ]
)
async def test_get_many_by_filter(client: TestClient, test_user_data, init_data, params, expected_count):
    response = client.get("/user", params=params)
    data = response.json()
    assert len(data) == expected_count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,sort,expected_first_id",
    [
        ("id", "ASC", 1),
        ("id", "DESC", 4),
        ("user_name", "ASC", 2),
        ("user_name", "DESC", 4),
    ]
)
async def test_get_many_with_sort(client: TestClient, test_user_data, init_data, field, sort, expected_first_id):
    response = client.get("/user", params={"sort": f"{field},{sort}"})
    data = response.json()
    assert data[0]["id"] == expected_first_id


@pytest.mark.asyncio
async def test_get_one_basic(client: TestClient, async_session, test_user_data, init_data):
    response = client.get("/user/1")
    data = response.json()
    assert data is not None
    assert data["id"] == 1
    assert data["email"] == test_user_data[0]["email"]
    assert data["is_active"] == test_user_data[0]["is_active"]


@pytest.mark.asyncio
async def test_get_one_non_existent_record(client: TestClient, async_session, test_user_data, init_data):
    non_existent_id = 1000
    response = client.get(f"/user/{non_existent_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "No data found"}
