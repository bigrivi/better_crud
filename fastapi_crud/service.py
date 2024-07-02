from fastapi import Request
from fastapi.exceptions import HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import TypeVar, Generic,Optional
from sqlalchemy.orm import contains_eager
from sqlalchemy import or_, update,delete
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_async_sqlalchemy import  db
from sqlmodel import SQLModel,select
from .helper import get_model_field,generate_filter_condition


ModelType = TypeVar("ModelType", bound=SQLModel)


FILTERS_KEY = "filters"
CUSTOM_QUERY_PARSE_KEY = "custom_query_parse"
SORT_KEY = "sorts"
OPTIONS_KEY = "options"
JOIN_KEY = "joins"
ALIASED_KEY = "aliased"
SELECT_KEY = "selects"
ORDER_KEY = "orders"
DISTINCTS_KEY = "distincts"
INCLUDE_DELETED_KEY = "include_deleted"
SOFT_DELETED_FIELD_KEY = "deleted_at"
SOFT_DELETED_KEY = "soft_delete"



class SqlalchemyCrudService(Generic[ModelType]):

    entity: object = NotImplementedError

    def __init__(self, entity: object):
        self.entity = entity
        self.primary_key = entity.__mapper__.primary_key[0].name
        self.entity_has_delete_column = hasattr(self.entity, SOFT_DELETED_FIELD_KEY)

    async def prepare_common_filter(self, filters=None, custom_parse=None,include_deleted=False,aliased=None,soft_delete = False):
        stmt = []
        if filters:
            filter_condition = generate_filter_condition(self.entity, filters, custom_parse,aliased=aliased)
            stmt.append(filter_condition)
        if self.entity_has_delete_column and soft_delete:
            if not include_deleted:
                stmt.append(or_(getattr(self.entity, SOFT_DELETED_FIELD_KEY) > datetime.now(),
                        getattr(self.entity, SOFT_DELETED_FIELD_KEY) == None))
        return stmt

    def prepare_order(self, query, sorts):
        order_bys = []
        if sorts:
            for sort_item in sorts:
                sort_items = sort_item.split(",")
                sort_field = sort_items[0]
                method = sort_items[1].lower()
                sort_field = get_model_field(self.entity, sort_field)
                if method=="asc":
                    order_bys.append(sort_field.asc())
                elif method=="desc":
                    order_bys.append(sort_field.desc())
        query = query.order_by(*order_bys)
        return query

    async def build_query(self, **kwargs):
        filters = kwargs.get(FILTERS_KEY)
        custom_parse = kwargs.get(CUSTOM_QUERY_PARSE_KEY)
        include_deleted = kwargs.get(INCLUDE_DELETED_KEY)
        selects = kwargs.get(SELECT_KEY)
        soft_delete = kwargs.get(SOFT_DELETED_KEY)
        sorts = kwargs.get(SORT_KEY)
        options = kwargs.get(OPTIONS_KEY) or []
        joins = kwargs.get(JOIN_KEY) or []
        distincts = kwargs.get(DISTINCTS_KEY)
        aliased = kwargs.get(ALIASED_KEY)
        stmt = await self.prepare_common_filter(filters, custom_parse,aliased=aliased,include_deleted=include_deleted==1,soft_delete=soft_delete)
        if selects:
            query = select(self.entity, *selects)
        else:
            query = select(self.entity)
        if joins and len(joins) > 0:
            for join_item in joins:
                if isinstance(join_item, tuple):
                    query = query.join(*join_item, isouter=True)
                else:
                    query = query.join(join_item, isouter=True)
                    options.append(contains_eager(join_item))
        if options:
            for option in options:
                query = query.options(option)
        query = query.where(*stmt)
        query = self.prepare_order(query,sorts)
        if distincts:
            query = query.distinct(*distincts)
        return query


    async def get_many(self,request:Request,page:int,size:int,session=None,pagination=True, **kwargs):
        query = await self.build_query(**kwargs)
        if pagination:
            result = await paginate(session, query,params=Params(page=page, size=size))
            return result
        else:
            result = await session.execute(query)
            return result.unique().scalars().all()

    async def get_by_id(self, id: int, **kwargs) -> ModelType:
        options = kwargs.get(OPTIONS_KEY)
        query = select(self.entity)
        if options:
            for option_item in options:
                query = query.options(option_item)
        query = query.where(getattr(self.entity, self.primary_key) == id)
        result = await db.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def create_one(self,request:Request, model:BaseModel):
        extra_data = await self.on_before_create(model)
        relationships = self.entity.__mapper__.relationships
        model_data = model.model_dump()
        if extra_data:
            model_data.update(extra_data)
        for key, val in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction.name
                relation_cls = relationships[key].mapper.entity
                if relation_dir=="MANYTOMANY":
                    if len(val) > 0 and isinstance(val[0], dict):
                        val = [elem.get("id") for elem in val]
                    primary_key = relation_cls.__mapper__.primary_key[0].name
                    instances = [(await db.session.execute(select(relation_cls).where(getattr(relation_cls,primary_key)==elem))).scalar_one_or_none() for elem in val]
                    model_data[key] = instances
                elif relation_dir=="ONETOMANY":
                    instances = [relation_cls(**elem) for elem in val]
                    model_data[key] = instances
                elif relation_dir=="MANYTOONE":
                    instance = relation_cls(**val)
                    model_data[key] = instance
        entity = self.entity(**model_data)
        db.session.add(entity)
        await db.session.flush()
        await self.on_after_create(entity)
        await db.session.commit()
        await db.session.refresh(entity)
        return entity

    async def update_one(self,request: Request, id, model:BaseModel):
        update_values = model.model_dump()
        entity = await self.get_by_id(id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Data not found")
        for key, value in update_values.items():
            if value is not None:
                setattr(entity, key, value)
        await self.on_before_update(entity)
        db.session.add(entity)
        await db.session.flush()
        await db.session.commit()
        await db.refresh(entity)
        await self.on_after_update(entity)

    async def delete_many(self,request:Request,id_list: list,soft_delete:Optional[bool] = False):
        await self.on_before_delete(id_list)
        if soft_delete:
            await self.soft_delete(id_list)
        else:
            await self.batch_delete(getattr(self.entity, self.primary_key).in_(id_list))
        await self.on_after_delete(id_list)

    async def batch_delete(self, stmt):
        if not isinstance(stmt, list):
            stmt = [stmt]
        statement = delete(self.entity).where(*stmt)
        await db.session.execute(statement)
        await db.session.commit()

    async def soft_delete(self, id_list: list):
        stmt = update(self.entity).where(getattr(self.entity, self.primary_key).in_(id_list)).values({"deleted_at": datetime.now()})
        await db.session.execute(stmt)
        await db.session.commit()


    async def on_before_create(self, model: Optional[BaseModel]) -> None:
        pass

    async def on_after_create(self, entity: ModelType) -> None:
        pass

    async def on_before_update(self, entity: ModelType) -> None:
        pass

    async def on_after_update(self, entity: ModelType) -> None:
        pass

    async def on_before_delete(self, id_list: list) -> None:
        pass

    async def on_after_delete(self, id_list: list) -> None:
        pass


