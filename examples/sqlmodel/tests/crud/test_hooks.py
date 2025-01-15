import pytest
from asyncio import Future
from typing import Optional, Any
from unittest.mock import MagicMock
from sqlalchemy import select
from sqlmodel import SQLModel, Field
from better_crud.service.sqlalchemy import SqlalchemyCrudService


def async_return(result: Optional[Any] = None):
    f = Future()
    f.set_result(result)
    return f


class Entity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    description: Optional[str] = None
    key: Optional[str] = None


class EntityCreate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class EntityUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class EntityService(SqlalchemyCrudService[Entity]):
    def __init__(self):
        super().__init__(Entity)
        self.method_called = True


@pytest.fixture(scope="function")
def entity_service() -> EntityService:
    service = EntityService()
    service.on_before_create = MagicMock(
        return_value=async_return({"key": "mykey"}))
    service.on_after_create = MagicMock(return_value=async_return())
    service.on_before_update = MagicMock(
        return_value=async_return({"key": "mykey"}))
    service.on_after_update = MagicMock(return_value=async_return())
    service.on_before_delete = MagicMock(return_value=async_return())
    service.on_after_delete = MagicMock(return_value=async_return())
    return service


@pytest.mark.asyncio
async def test_hooks_create_call(async_session, test_request, entity_service):
    entity_name = "entity name"
    entity_create = EntityCreate(
        name=entity_name, description="entity description")
    entity = await entity_service.crud_create_one(test_request, entity_create, db_session=async_session)
    entity_service.on_before_create.assert_called()
    entity_service.on_before_create.assert_called_once_with(
        entity_create, background_tasks=None)
    entity_service.on_after_create.assert_called()
    entity_service.on_after_create.assert_called_once_with(
        entity, background_tasks=None)
    stmt = select(Entity).where(Entity.name == entity_name)
    result = await async_session.execute(stmt)
    fetched_record: Entity = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.key == "mykey"


@pytest.mark.asyncio
async def test_hooks_update_call(async_session, test_request, entity_service):
    entity_name = "entity name"
    entity = Entity(name=entity_name, description="entity description")
    async_session.add(entity)
    await async_session.commit()
    entity_update = EntityUpdate(
        name="updated entity name", description="updated entity description")
    entity = await entity_service.crud_update_one(test_request, entity.id, entity_update, db_session=async_session)
    entity_service.on_before_update.assert_called()
    entity_service.on_before_update.assert_called_once_with(
        entity, entity_update, background_tasks=None)
    entity_service.on_after_update.assert_called()
    entity_service.on_after_update.assert_called_once_with(
        entity, background_tasks=None)
    stmt = select(Entity).where(Entity.id == entity.id)
    result = await async_session.execute(stmt)
    fetched_record: Entity = result.scalar_one_or_none()
    assert fetched_record is not None
    assert fetched_record.key == "mykey"


@pytest.mark.asyncio
async def test_hooks_delete_call(async_session, test_request, entity_service):
    entity = Entity(name="entity name", description="entity description")
    async_session.add(entity)
    await async_session.commit()
    entities = await entity_service.crud_delete_many(test_request, [entity.id], False, db_session=async_session)
    entity_service.on_before_delete.assert_called()
    entity_service.on_before_delete.assert_called_once_with(
        entities, background_tasks=None)
    entity_service.on_after_delete.assert_called()
    entity_service.on_after_delete.assert_called_once_with(
        entities, background_tasks=None)
