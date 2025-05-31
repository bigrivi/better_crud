from typing import Dict, List, Union, Optional, Any
import inspect
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from ...helper import find, update_entity_attr
from ...config import BetterCrudGlobalConfig


class Provide:
    pass


async def create_many_to_many_instances(
    session: AsyncSession,
    relation_cls,
    data: Union[List[Union[Dict, int, str]], int, str]
) -> Any:
    primary_key = relation_cls.__mapper__.primary_key[0].name
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            data = [elem[primary_key] for elem in data]
        instances = [
            await session.get(relation_cls, primary_value)
            for primary_value in data
        ]
        return instances
    # Many to many may not be an array, but an object,pass in the primary key value
    instance = await session.get(relation_cls, data)
    return instance


async def create_one_to_many_instances(
    relation_cls: Any,
    data: List[Dict],
    old_instances: Optional[Any] = None
) -> List[Any]:
    primary_key = relation_cls.__mapper__.primary_key[0].name
    instances = []
    for item_data in data:
        if old_instances and primary_key in item_data:
            instance = find(
                old_instances,
                lambda x: getattr(x, primary_key) == item_data.get(primary_key)
            )
            if instance:
                update_entity_attr(instance, item_data)
                instances.append(instance)
                continue
        instances.append(relation_cls(**item_data))
    return instances


async def create_many_to_one_instance(
    relation_cls: Any,
    data: Dict,
    old_instance: Optional[Any] = None
):
    if old_instance is None:
        return relation_cls(**data)
    update_entity_attr(old_instance, data)
    return old_instance


async def create_one_to_one_instance(
    relation_cls: Any,
    data: Dict,
    old_instance: Optional[Any] = None
):
    if old_instance is None:
        return relation_cls(**data)
    update_entity_attr(old_instance, data)
    return old_instance


def inject_db_session(f):
    sig = inspect.signature(f)

    async def wrapper(*args, **kwargs):
        for param in sig.parameters.values():
            if isinstance(param.default, Provide):
                if kwargs.get(param.name) is None:
                    sqlalchemy_config = BetterCrudGlobalConfig.backend_config.sqlalchemy
                    if inspect.isasyncgenfunction(sqlalchemy_config.db_session):
                        DBSession = asynccontextmanager(
                            sqlalchemy_config.db_session)
                        async with DBSession() as db_session:
                            kwargs[param.name] = db_session
                            return await f(*args, **kwargs)
                    else:
                        kwargs[param.name] = sqlalchemy_config.db_session()
                        return await f(*args, **kwargs)
                else:
                    return await f(*args, **kwargs)
    return wrapper
