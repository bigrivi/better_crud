from typing import Any, Dict,List,Union,TypeVar, Generic, Optional,Sequence
from fastapi import Request,BackgroundTasks
from fastapi.exceptions import HTTPException
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager,MANYTOMANY,MANYTOONE,ONETOMANY,noload
from sqlalchemy.sql.selectable import Select
from sqlalchemy import or_, update, delete, and_, func,select
from sqlalchemy.orm.interfaces import ORMOption
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.bases import AbstractPage
from .helper import decide_should_paginate
from .service_abstract import CrudService
from .types import QuerySortDict

from .config import FastAPICrudGlobalConfig
from .relationship import (
    create_many_to_many_instances,
    create_one_to_many_instances,
    create_many_to_one_instance
)

ModelType = TypeVar("ModelType")
Selectable = TypeVar("Selectable", bound=Select[Any])

LOGICAL_OPERATOR_AND = "$and"
LOGICAL_OPERATOR_OR = "$or"

class SqlalchemyCrudService(Generic[ModelType],CrudService[ModelType]):

    entity: object = NotImplementedError

    def __init__(self, entity: object):
        self.entity = entity
        self.primary_key = entity.__mapper__.primary_key[0].name
        self.entity_has_delete_column = hasattr(
            self.entity, FastAPICrudGlobalConfig.soft_deleted_field_key)

    def prepare_order(self, query, sorts:List[QuerySortDict]):
        order_bys = []
        if sorts:
            for sort_item in sorts:
                field = self.get_model_field(sort_item["field"])
                sort = sort_item["sort"]
                if sort == "ASC":
                    order_bys.append(field.asc())
                elif sort == "DESC":
                    order_bys.append(field.desc())
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
        conds = []
        if isinstance(search, dict):
            keys = list(search.keys())
            if len(keys) > 0:
                if LOGICAL_OPERATOR_AND in search:  # {$and: [...], ...}
                    and_values = search.get(LOGICAL_OPERATOR_AND)
                    if len(and_values) == 1:  # {$and: [{}]}
                        conds.append(
                            and_(*self.create_search_condition(and_values[0])))
                    else:  # {$and: [{},{},...]}
                        clauses = [and_(*self.create_search_condition(and_value)) for and_value in and_values]
                        conds.append(and_(*clauses))
                else:
                    for field, value in search.items():
                        if field == LOGICAL_OPERATOR_OR and isinstance(value, list):
                            if len(value) == 1:
                                conds.append(
                                    and_(*self.create_search_condition(value[0])))
                            else:
                                clauses = [and_(*self.create_search_condition(or_value)) for or_value in value]
                                conds.append(or_(*clauses))
                        elif isinstance(value, Dict):
                            conds.append(self.create_search_field_object_condition(
                                LOGICAL_OPERATOR_AND, field, value))
                        else:
                            conds.append(self.get_model_field(field) == value)
        return conds

    async def build_query(
        self,
        search:Optional[Dict] = None,
        include_deleted:Optional[bool] = False,
        soft_delete:Optional[bool] = False,
        joins:Optional[List] = None,
        options: Optional[Sequence[ORMOption]] = None,
        sorts: List[QuerySortDict] = None,
        implanted_cond:Optional[List[Any]] = None
    )->Selectable:
        conds = []
        if implanted_cond:
            conds = conds+implanted_cond
        options = options or []
        if search:
            conds = conds + self.create_search_condition(search)
        if self.entity_has_delete_column and soft_delete:
            soft_deleted_field_key = FastAPICrudGlobalConfig.soft_deleted_field_key
            if not include_deleted:
                conds.append(or_(getattr(self.entity, soft_deleted_field_key) > datetime.now(),
                                  getattr(self.entity, soft_deleted_field_key) == None))
        stmt = select(self.entity)
        if joins and len(joins) > 0:
            for join in joins:
                if isinstance(join, tuple):
                    stmt = stmt.join(*join, isouter=True)
                else:
                    stmt = stmt.join(join, isouter=True)
                    options.append(contains_eager(join))
        if options:
            stmt = stmt.options(*options)
        stmt = stmt.where(*conds)
        stmt = self.prepare_order(stmt, sorts)
        return stmt

    async def get_many(
        self,
        *,
        db_session:AsyncSession,
        request: Optional[Request] = None,
        search:Optional[Dict] = None,
        include_deleted:Optional[bool] = False,
        soft_delete:Optional[bool] = False,
        joins:Optional[List] = None,
        options: Optional[Sequence[ORMOption]] = None,
        sorts: List[QuerySortDict] = None,
        implanted_cond:Optional[List[Any]] = None
    )->Union[AbstractPage[ModelType],List[ModelType]]:
        stmt = await self.build_query(
            search=search,
            include_deleted=include_deleted,
            soft_delete=soft_delete,
            joins=joins,
            options=options,
            sorts=sorts,
            implanted_cond=implanted_cond
        )
        if decide_should_paginate():
            return await paginate(db_session, stmt)
        result = await db_session.execute(stmt)
        return result.unique().scalars().all()

    async def get(
        self,
        id: Union[int,str],
        db_session:AsyncSession,
        options: Optional[Sequence[ORMOption]] = None,
    ) -> ModelType:
        return await db_session.get(self.entity,id,options=options)

    async def create_one(
        self,
        request: Request,
        model: BaseModel,
        db_session:AsyncSession,
        background_tasks:BackgroundTasks
    )->ModelType:
        relationships = self.entity.__mapper__.relationships
        model_data = model.model_dump(exclude_unset=True)
        await self.on_before_create(model_data,background_tasks=background_tasks)
        if hasattr(request.state,"auth_persist"):
            model_data.update(request.state.auth_persist)
        for key, value in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction
                relation_cls = relationships[key].mapper.entity
                if relation_dir == MANYTOMANY:
                    model_data[key] = await create_many_to_many_instances(db_session,relation_cls,value)
                elif relation_dir == ONETOMANY:
                    model_data[key] = await create_one_to_many_instances(relation_cls,value)
                elif relation_dir == MANYTOONE:
                    model_data[key] = await create_many_to_one_instance(relation_cls,value)
        entity = self.entity(**model_data)
        db_session.add(entity)
        await db_session.flush()
        await self.on_after_create(entity,background_tasks=background_tasks)
        await db_session.commit()
        await db_session.refresh(entity)
        return entity

    async def create_many(
        self,
        request: Request,
        models: List[BaseModel],
        db_session:AsyncSession,
        background_tasks:BackgroundTasks
    )->List[ModelType]:
        entities = []
        for model in models:
            entity = await self.create_one(
                request,
                db_session=db_session,
                model=model,
                background_tasks=background_tasks
            )
            entities.append(entity)
        return entities

    async def update_one(self,
        request: Request,
        id:int,
        model: BaseModel,
        db_session:AsyncSession,
        background_tasks:BackgroundTasks = None
    ):
        entity = await self.get_by_id(id,db_session=db_session)
        if entity is None:
            raise HTTPException(status_code=404, detail="Data not found")
        model_data = model.model_dump(exclude_unset=True)
        await self.on_before_update(entity,update_data=model_data,background_tasks=background_tasks)
        relationships = self.entity.__mapper__.relationships
        for key, value in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction
                relation_cls = relationships[key].mapper.entity
                if relation_dir == MANYTOMANY:
                    value = await create_many_to_many_instances(db_session,relation_cls,value)
                elif relation_dir == ONETOMANY:
                    value = await create_one_to_many_instances(relation_cls=relation_cls,data=value,old_value=getattr(entity,key))
                elif relation_dir == MANYTOONE:
                    value = await create_many_to_one_instance(relation_cls=relation_cls,data=value,old_value=getattr(entity,key))
            setattr(entity, key, value)
        db_session.add(entity)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(entity)
        await self.on_after_update(entity,background_tasks=background_tasks)

    async def delete_many(self, request: Request, id_list: list,db_session:AsyncSession, soft_delete: Optional[bool] = False,background_tasks:BackgroundTasks=None):
        await self.on_before_delete(id_list,background_tasks=background_tasks)
        if soft_delete:
            await self.soft_delete(id_list,db_session=db_session)
        else:
            await self.batch_delete(getattr(self.entity, self.primary_key).in_(id_list),db_session=db_session)
        await self.on_after_delete(id_list,background_tasks=background_tasks)

    async def batch_delete(self, stmt,db_session:AsyncSession):
        if not isinstance(stmt, list):
            stmt = [stmt]
        statement = delete(self.entity).where(*stmt)
        await db_session.execute(statement)
        await db_session.commit()

    async def soft_delete(self, id_list: list,db_session:AsyncSession):
        stmt = update(self.entity).where(getattr(self.entity, self.primary_key).in_(
            id_list)).values({FastAPICrudGlobalConfig.soft_deleted_field_key: datetime.now()})
        await db_session.execute(stmt)
        await db_session.commit()

    async def on_before_create(self, create_data: dict,background_tasks:Optional[BackgroundTasks]=None) -> None:
        pass

    async def on_after_create(self, entity: ModelType,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_before_update(self, entity: ModelType,update_data: dict,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_after_update(self, entity: ModelType,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_before_delete(self, id_list: list,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_after_delete(self, id_list: list,background_tasks:BackgroundTasks) -> None:
        pass


    def build_query_expression(self, field, operator, value):
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
        elif operator == "$starts":
            return field.startswith(value)
        elif operator == "$ends":
            return field.endswith(value)
        elif operator == "doesNotBeginWith":
            return field.notlike('{}%'.format(value))
        elif operator == "doesNotEndWith":
            return field.notlike('%{}'.format(value))
        elif operator == "$isnull":
            return field.is_(None)
        elif operator == "$notnull":
            return field.isnot(None)
        elif operator == "$in":
            return field.in_(value.split(","))
        elif operator == "$notin":
            return field.notin_(value.split(","))
        elif operator == "$between":
            return field.between(*value)
        elif operator == "$notbetween":
            return ~field.between(*value.split(","))
        elif operator == "$length":
            return func.length(field) == int(value)
        elif operator == "$any":
            return field.any(value)
        elif operator == "$notany":
            return func.not_(field.any(value))
        else:
            raise Exception("unknow operator "+operator)

    def get_model_field(self, field):
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
