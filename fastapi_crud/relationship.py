from typing import Dict,List,Union,Optional,Any
from sqlalchemy.ext.asyncio import AsyncSession
from .helper import find,update_entity_attr

async def create_many_to_many_instances(session:AsyncSession,relation_cls,data:List[Union[Dict,int]])->List[Any]:
    primary_key = relation_cls.__mapper__.primary_key[0].name
    if len(data) > 0 and isinstance(data[0], dict):
        data = [elem[primary_key] for elem in data]
    instances = [await session.get(relation_cls,primary_value) for primary_value in data]
    return instances

async def create_one_to_many_instances(relation_cls,data:List[Dict],old_instances:Optional[Any] = None)->List[Any]:
    primary_key = relation_cls.__mapper__.primary_key[0].name
    instances = []
    for item_data in data:
        if old_instances and primary_key in item_data:
            instance = find(old_instances,lambda x:getattr(x,primary_key)==item_data.get(primary_key))
            if instance:
                update_entity_attr(instance,item_data)
                instances.append(instance)
                continue
        instances.append(relation_cls(**item_data))
    return  instances

async def create_many_to_one_instance(relation_cls,data:Dict,old_instance:Optional[Any] = None):
    if old_instance is None:
        return relation_cls(**data)
    update_entity_attr(old_instance,data)
    return  old_instance
