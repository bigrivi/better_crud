from typing import Any, Dict,List
from fastapi import Request,BackgroundTasks
from fastapi.exceptions import HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional
from sqlalchemy.orm import contains_eager,joinedload,MANYTOMANY,MANYTOONE,ONETOMANY
from sqlalchemy.sql.selectable import Select
from sqlalchemy import or_, update, delete, and_, func
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_async_sqlalchemy import db
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)
Selectable = TypeVar("Selectable", bound=Select[Any])

SOFT_DELETED_FIELD_KEY = "deleted_at"
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
        search:Dict,
        include_deleted:Optional[bool] = False,
        soft_delete:Optional[bool] = False,
        joins:Optional[List] = None,
        options:Optional[List] = None,
        sorts: List[str] = None,
        implanted_cond:Optional[List[Any]] = None
    )->Selectable:
        conds = []
        if implanted_cond:
            conds = conds+implanted_cond
        options = options or []
        if search:
            conds = conds + self.create_search_condition(search)
        if self.entity_has_delete_column and soft_delete:
            if not include_deleted:
                conds.append(or_(getattr(self.entity, SOFT_DELETED_FIELD_KEY) > datetime.now(),
                                  getattr(self.entity, SOFT_DELETED_FIELD_KEY) == None))
        stmt = select(self.entity)
        if joins and len(joins) > 0:
            for join in joins:
                if isinstance(join, tuple):
                    stmt = stmt.join(*join, isouter=True)
                else:
                    stmt = stmt.join(join, isouter=True)
                    options.append(contains_eager(join))
        if options:
            for option in options:
                stmt = stmt.options(option)
        stmt = stmt.where(*conds)
        stmt = self.prepare_order(stmt, sorts)
        return stmt

    async def get_many(
        self,
        request: Request,
        page: int,
        size: int,
        search:Dict,
        include_deleted:Optional[bool] = False,
        soft_delete:Optional[bool] = False,
        joins:Optional[List] = None,
        options:Optional[List] = None,
        sorts: List[str] = None,
        session=None,
        pagination:Optional[bool]=True,
    ):
        if hasattr(request.state,"auth_filter"):
            if search:
                search = {
                    "$and": [request.state.auth_filter,*search["$and"]]
                }
            else:
                search = {
                    "$and": [request.state.auth_filter]
                }
        stmt = await self.build_query(search=search,include_deleted=include_deleted,soft_delete=soft_delete,joins=joins,options=options,sorts=sorts)
        if pagination:
            result = await paginate(session, stmt, params=Params(page=page, size=size))
            return result
        else:
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    async def get_by_id(self, id: int) -> ModelType:
        stmt = select(self.entity)
        stmt = stmt.where(getattr(self.entity, self.primary_key) == id)
        result = await db.session.execute(stmt)
        return result.unique().scalar_one_or_none()


    async def create_one(self, request: Request, model: BaseModel,background_tasks:BackgroundTasks
):
        extra_data = await self.on_before_create(model,background_tasks=background_tasks)
        relationships = self.entity.__mapper__.relationships
        model_data = model.model_dump()
        if extra_data:
            model_data.update(extra_data)
        if hasattr(request.state,"auth_persist"):
            model_data.update(request.state.auth_persist)
        for key, value in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction
                relation_cls = relationships[key].mapper.entity
                if relation_dir == MANYTOMANY:
                    primary_key = relation_cls.__mapper__.primary_key[0].name
                    if len(value) > 0 and isinstance(value[0], dict):
                        value = [elem.primary_key for elem in value]
                    instances = [(await db.session.execute(select(relation_cls).where(getattr(relation_cls, primary_key) == elem))).scalar_one_or_none() for elem in value]
                    model_data[key] = instances
                elif relation_dir == ONETOMANY:
                    instances = [relation_cls(**elem) for elem in value]
                    model_data[key] = instances
                elif relation_dir == MANYTOONE:
                    instance = relation_cls(**value)
                    model_data[key] = instance
        entity = self.entity(**model_data)
        db.session.add(entity)
        await db.session.flush()
        await self.on_after_create(entity,background_tasks=background_tasks)
        await db.session.commit()
        await db.session.refresh(entity)
        return entity

    async def update_one(self,
        request: Request,
        id:int,
        model: BaseModel,
        background_tasks:BackgroundTasks = None
    ):
        model_data = model.model_dump()
        entity = await self.get_by_id(id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Data not found")
        await self.assign_entity_update_attrs(entity, model_data)
        relationships = self.entity.__mapper__.relationships
        for key, value in model_data.items():
            if value is None:
                continue
            if key in relationships:
                relation_dir = relationships[key].direction
                relation_cls = relationships[key].mapper.entity
                if relation_dir == MANYTOMANY:
                    primary_key = relation_cls.__mapper__.primary_key[0].name
                    if len(value) > 0 and isinstance(value[0], dict):
                        value = [elem.primary_key for elem in value]
                    instances = [(await db.session.execute(select(relation_cls).where(getattr(relation_cls, primary_key) == elem))).scalar_one_or_none() for elem in value]
                    value = instances
                elif relation_dir == MANYTOONE:
                    if getattr(entity,key) is None:
                        instance = relation_cls(**value)
                    else:
                        instance = getattr(entity,key)
                        for sub_key, sub_value in value.items():
                            if sub_value is not None:
                                setattr(instance, sub_key, sub_value)
                    value = instance
            setattr(entity, key, value)
        await self.on_before_update(entity,background_tasks=background_tasks)
        db.session.add(entity)
        await db.session.flush()
        await db.session.commit()
        await db.session.refresh(entity)
        await self.on_after_update(entity,background_tasks=background_tasks)

    async def delete_many(self, request: Request, id_list: list, soft_delete: Optional[bool] = False,background_tasks:BackgroundTasks=None):
        await self.on_before_delete(id_list,background_tasks=background_tasks)
        if soft_delete:
            await self.soft_delete(id_list)
        else:
            await self.batch_delete(getattr(self.entity, self.primary_key).in_(id_list))
        await self.on_after_delete(id_list,background_tasks=background_tasks)

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

    async def on_before_create(self, model: Optional[BaseModel],background_tasks:Optional[BackgroundTasks]=None) -> None:
        pass

    async def on_after_create(self, entity: ModelType,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_before_update(self, entity: ModelType,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_after_update(self, entity: ModelType,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_before_delete(self, id_list: list,background_tasks:BackgroundTasks) -> None:
        pass

    async def on_after_delete(self, id_list: list,background_tasks:BackgroundTasks) -> None:
        pass

    async def assign_entity_update_attrs(self, entity_data: ModelType, update_data: dict) -> None:
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
        elif operator == "length":
            return func.length(field) == int(value)
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
