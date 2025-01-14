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
async def test_get_many_with_invalid_sort(client: TestClient, test_user_data, init_data):
    with pytest.raises(Exception):
        response = client.get("/user", params={"sort": f"user_name"})
        response.json()

@pytest.mark.asyncio
async def test_get_many_with_include_delete(include_deleted_client: TestClient, test_user_data, init_data):
    exist_user_id = test_user_data[0]["id"]
    include_deleted_client.delete(f"/user/{exist_user_id}")
    response = include_deleted_client.get("/user", params={"include_deleted": False})
    data = response.json()
    assert len(data) == len(test_user_data)-1
    response = include_deleted_client.get("/user", params={"include_deleted": True})
    data = response.json()
    assert len(data) == len(test_user_data)

@pytest.mark.asyncio
async def test_get_many_filters_with_params(params_client: TestClient, test_user_data, init_data):
    response = params_client.get("/1/user_task")
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_many_filters_with_auth(auth_client: TestClient, test_user_data, init_data):
    response = auth_client.get("/user_task")
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_many_filters_with_fixed(fixed_filter_client: TestClient, test_user_data, init_data):
    response = fixed_filter_client.get("/user")
    data = response.json()
    assert len(data) == 3

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "page,size,expected_pages,expected_size,expected_first_id",
    [
        (1,1,4,1,4),
        (1,2,2,2,4),
        (1,3,2,3,4),
        (1,4,1,4,4),
        (2,1,4,1,3),
        (2,2,2,2,2),
        (2,3,2,1,1)
    ]
)
async def test_get_many_pagination(
    client: TestClient,
    test_user_data,
    init_data,
    page,
    size,
    expected_pages,
    expected_size,
    expected_first_id
):
    response = client.get("/user",params={
        "page":page,
        "size":size,
        "sort": "id,DESC"
    })
    data = response.json()
    assert data["total"] == len(test_user_data)
    assert data["pages"] == expected_pages
    assert len(data["items"]) == expected_size
    assert data["items"][0]["id"] == expected_first_id


@pytest.mark.asyncio
async def test_get_many_select_relation(join_config_client: TestClient, test_user_data,test_company_data, init_data):
    response = join_config_client.get("/user",params={
        "load":["roles","company"]
    })
    data = response.json()
    assert len(data) == len(test_user_data)
    assert len(data[0]["roles"]) == len(test_user_data[0]["role_ids"])
    assert data[0]["company"]["name"] == test_company_data[0]["name"]

@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")
async def test_get_many_join_relation(join_config_client: TestClient, test_user_data,test_company_data, init_data):
    response = join_config_client.get("/user",
        params={
            "filter":["staff.position||$eq||CFO","company.name||$eq||Cunningham Inc"]
        },
    )
    assert len(response.json()) == len(test_user_data)
    response = join_config_client.get("/user",
        params={
            "join":["staff","company"],
            "filter":["staff.position||$eq||CFO","company.name||$eq||Cunningham Inc"]
        },
    )
    assert len(response.json()) == 1


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


@pytest.mark.asyncio
async def test_get_one_load_relation(join_config_client: TestClient, test_user_data,test_company_data, init_data):
    response = join_config_client.get(f"/user/1",params={
        "load":["roles","company"]
    })
    data = response.json()
    assert len(data["roles"]) == len(test_user_data[0]["role_ids"])
    assert data["company"]["name"] == test_company_data[0]["name"]