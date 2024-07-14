from typing import Any,Dict
from fastapi import Request
from fastapi.exceptions import HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional
from sqlalchemy.orm import contains_eager
from sqlalchemy import or_, update, delete,and_,func
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_async_sqlalchemy import db
from sqlmodel import SQLModel, select


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

LOGICAL_OPERATOR_AND = "$and"
LOGICAL_OPERATOR_OR = "$or"


class SqlalchemyCrudService(Generic[ModelType]):

    entity: object = NotImplementedError

    def __init__(self, entity: object):
        self.entity = entity
        self.primary_key = entity.__mapper__.primary_key[0].name
        self.entity_has_delete_column = hasattr(
            self.entity, SOFT_DELETED_FIELD_KEY)

    def prepare_order(self, query, sorts):
        order_bys = []
        if sorts:
            for sort_item in sorts:
                sort_items = sort_item.split(",")
                sort_field = sort_items[0]
                method = sort_items[1].lower()
                sort_field = self.get_model_field(sort_field)
                if method == "asc":
                    order_bys.append(sort_field.asc())
                elif method == "desc":
                    order_bys.append(sort_field.desc())
        query = query.order_by(*order_bys)
        return query


    def create_search_field_object_condition(self, logical_operator: str, field: str, obj: Any):
        logical_operator = logical_operator or LOGICAL_OPERATOR_AND
        if isinstance(obj, dict):
            model_field = self.get_model_field(field)
            keys = list(obj.keys())
            if len(keys) == 1:
                if keys[0] == LOGICAL_OPERATOR_OR:
                    return self.create_search_field_object_condition(LOGICAL_OPERATOR_OR, field, obj.get(LOGICAL_OPERATOR_OR))
                else:
                    return self.build_query_expression(model_field, keys[0], obj[keys[0]])
            else:
                if logical_operator == LOGICAL_OPERATOR_OR:
                    return or_(*(self.build_query_expression(model_field, operator, obj[operator]) for operator in keys))
                elif logical_operator == LOGICAL_OPERATOR_AND:
                    clauses = []
                    for operator in keys:
                        if isinstance(obj[operator], dict) and operator == LOGICAL_OPERATOR_OR:
                            clauses.append(self.create_search_field_object_condition(
                                LOGICAL_OPERATOR_OR, field, obj.get(operator)))
                        else:
                            clauses.append(self.build_query_expression(
                                model_field, operator, obj[operator]))
                    return and_(*clauses)


    def create_search_condition(self, search: Dict):
        stmt = []
        if isinstance(search, dict):
            keys = list(search.keys())
            for key, value in search.items():
                if key == LOGICAL_OPERATOR_OR and isinstance(value,list):
                    if len(value) == 1:
                        stmt.append(and_(*self.create_search_condition(value[0])))
                    else:
                        stmt.append(or_(*(and_(*self.create_search_condition(or_value)) for or_value in value)))
                elif key == LOGICAL_OPERATOR_AND and isinstance(value,list):
                    if len(value) == 1:
                        stmt.append(and_(*self.create_search_condition(value[0])))
                    else:
                        stmt.append(and_(*(and_(*self.create_search_condition(and_value)) for and_value in value)))
                elif isinstance(value, Dict):
                    stmt.append(self.create_search_field_object_condition( LOGICAL_OPERATOR_AND, key, value))
                else:
                    stmt.append(self.get_model_field(key) == value)
        return stmt

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
        search = {
            "$and": [
                {
                    "is_active": {
                        "$gte": 1
                    }
                },
                {
                    "company_id": {
                        "$eq": 1
                    }
                }
            ],
            "is_active": {
                "$eq": 1
            },
            "is_superuser": {
                "$eq": 0,
                "$or": {
                    "$isnull": True,
                    "$eq": 0
                }
            },
            "email": {
                "$cont":"qq.com"
            }
        }
        wheres = self.create_search_condition(search)
        if self.entity_has_delete_column and soft_delete:
            if not include_deleted:
                wheres.append(or_(getattr(self.entity, SOFT_DELETED_FIELD_KEY) > datetime.now(),
                                  getattr(self.entity, SOFT_DELETED_FIELD_KEY) == None))
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
        query = query.where(*wheres)
        query = self.prepare_order(query, sorts)
        if distincts:
            query = query.distinct(*distincts)
        return query

    async def get_many(self, request: Request, page: int, size: int, session=None, pagination=True, **kwargs):
        query = await self.build_query(**kwargs)
        if pagination:
            result = await paginate(session, query, params=Params(page=page, size=size))
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

    async def create_one(self, request: Request, model: BaseModel):
        extra_data = await self.on_before_create(model)
        relationships = self.entity.__mapper__.relationships
        model_data = model.model_dump()
        if extra_data:
            model_data.update(extra_data)
        for key, val in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction.name
                relation_cls = relationships[key].mapper.entity
                if relation_dir == "MANYTOMANY":
                    if len(val) > 0 and isinstance(val[0], dict):
                        val = [elem.get("id") for elem in val]
                    primary_key = relation_cls.__mapper__.primary_key[0].name
                    instances = [(await db.session.execute(select(relation_cls).where(getattr(relation_cls, primary_key) == elem))).scalar_one_or_none() for elem in val]
                    model_data[key] = instances
                elif relation_dir == "ONETOMANY":
                    instances = [relation_cls(**elem) for elem in val]
                    model_data[key] = instances
                elif relation_dir == "MANYTOONE":
                    instance = relation_cls(**val)
                    model_data[key] = instance
        entity = self.entity(**model_data)
        db.session.add(entity)
        await db.session.flush()
        await self.on_after_create(entity)
        await db.session.commit()
        await db.session.refresh(entity)
        return entity

    async def update_one(self, request: Request, id, model: BaseModel):
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

    async def delete_many(self, request: Request, id_list: list, soft_delete: Optional[bool] = False):
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
        stmt = update(self.entity).where(getattr(self.entity, self.primary_key).in_(
            id_list)).values({"deleted_at": datetime.now()})
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



    def build_query_expression(self,field, operator, value):
        if operator == "$eq":
            return field == value
        elif operator == "$ne":
            return field != value
        elif operator == "$gt":
            return field > value
        elif operator == "$gte":
            return field >= value
        elif operator == "$lt":
            return field < value
        elif operator == "<=":
            return field <= value
        elif operator == "$cont":
            return field.like('%{}%'.format(value))
        elif operator == "exclude":
            return field.notlike('%{}%'.format(value))
        elif operator == "beginsWith":
            return field.startswith(value)
        elif operator == "endsWith":
            return field.endswith(value)
        elif operator == "doesNotBeginWith":
            return field.notlike('{}%'.format(value))
        elif operator == "doesNotEndWith":
            return field.notlike('%{}'.format(value))
        elif operator == "$isnull":
            return field.is_(None)
        elif operator == "notNull":
            return field.isnot(None)
        elif operator == "in":
            return field.in_(value.split(","))
        elif operator == "notIn":
            return field.notin_(value.split(","))
        elif operator == "between":
            return field.between(*value.split(","))
        elif operator == "notBetween":
            return ~field.between(*value.split(","))
        elif operator == "length":
            return func.length(field) == int(value)
        else:
            raise Exception("unknow operator "+operator)

    def get_model_field(self,field):
        field_parts = field.split(".")
        relationships = self.entity.__mapper__.relationships
        model_field = None
        if len(field_parts) > 1:
            field_prefix = field_parts[0]
            if field_prefix in relationships:
                relation_cls = relationships[field_prefix].mapper.entity
                model_field = getattr(relation_cls, field_parts[1])
        else:
            model_field = getattr(self.entity, field)
        return model_field
