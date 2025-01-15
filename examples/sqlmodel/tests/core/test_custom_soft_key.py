from typing import Optional, List
import pytest
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from datetime import datetime
from sqlalchemy import select
from better_crud import FastAPICrudGlobalConfig, crud
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, APIRouter


class PersonBase(SQLModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    nick_name: Optional[str] = None
    expiry_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class Person(PersonBase, table=True):
    __tablename__ = "person"
    id: Optional[int] = Field(default=None, primary_key=True)


class PersonPublic(PersonBase):
    id: int


class PersonCreate(PersonBase):
    pass


class PersonService(SqlalchemyCrudService[Person]):
    def __init__(self):
        super().__init__(Person)


@pytest.mark.order("last")
@pytest.mark.asyncio
async def test_custom_soft_key(async_session):
    app = FastAPI()
    FastAPICrudGlobalConfig.init(
        backend_config={
            "sqlalchemy": {
                "db_session": lambda: async_session
            }
        },
        soft_deleted_field_key="expiry_at",
    )
    person_router = APIRouter()

    @crud(
        person_router,
        feature="person",
        query={
            "soft_delete": True
        },
        serialize={
            "base": PersonPublic,
        }
    )
    class PersonController():
        service: PersonService = Depends(PersonService)
    api_router = APIRouter()
    api_router.include_router(person_router, prefix="/person")
    app.include_router(api_router)
    with TestClient(app) as test_client:
        person_id = 1
        person = Person()
        person.name = "andy"
        person.gender = "male"
        person.nick_name = "bigrivi"
        person.id = person_id
        async_session.add(person)
        await async_session.commit()
        response = test_client.get("/person")
        assert len(response.json()) == 1
        test_client.delete(f"/person/{person_id}")
        stmt = select(Person).where(Person.id == person_id)
        stmt = stmt.execution_options(populate_existing=True)
        result = await async_session.execute(stmt)
        fetched_record: Person = result.scalar_one_or_none()
        assert fetched_record is not None
        assert fetched_record.expiry_at is not None
        response = test_client.get("/person")
        assert len(response.json()) == 0
