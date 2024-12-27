import pytest
from asyncio import Future
from typing import Optional
from unittest.mock import MagicMock
from sqlmodel import SQLModel, Field
from fastapi_crud.service.sqlalchemy import SqlalchemyCrudService



class AsyncMock(MagicMock):
    def __await__(self, *args, **kwargs):
        future = Future()
        future.set_result(self)
        result = yield from future
        return result


class Entity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str | None = None
    description: str | None = None


class EntityCreate(SQLModel):
    name: str | None = None
    description: str | None = None

class EntityUpdate(SQLModel):
    name: str | None = None
    description: str | None = None

class EntityService(SqlalchemyCrudService[Entity]):
    def __init__(self):
        super().__init__(Entity)
        self.method_called = True

@pytest.fixture(scope="function")
def entity_service() -> EntityService:
    service = EntityService()
    service.on_before_create = AsyncMock()
    service.on_after_create = AsyncMock()
    service.on_before_update = AsyncMock()
    service.on_after_update = AsyncMock()
    service.on_before_delete = AsyncMock()
    service.on_after_delete = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_hooks_create_call(async_session, test_request,entity_service):
    new_data = EntityCreate(name="entity name", description="entity description")
    await entity_service.crud_create_one(test_request, new_data, db_session=async_session)
    entity_service.on_before_create.assert_called()
    entity_service.on_after_create.assert_called()

@pytest.mark.asyncio
async def test_hooks_update_call(async_session, test_request,entity_service):
    entity = Entity(name="entity name", description="entity description")
    async_session.add(entity)
    await async_session.commit()
    update_data = EntityUpdate(name="updated entity name", description="updated entity description")
    await entity_service.crud_update_one(test_request,entity.id, update_data, db_session=async_session)
    entity_service.on_before_update.assert_called()
    entity_service.on_after_update.assert_called()

@pytest.mark.asyncio
async def test_hooks_delete_call(async_session, test_request,entity_service):
    entity = Entity(name="entity name", description="entity description")
    async_session.add(entity)
    await async_session.commit()
    await entity_service.crud_delete_many(test_request,[entity.id], False, db_session=async_session)
    entity_service.on_before_delete.assert_called()
    entity_service.on_after_delete.assert_called()