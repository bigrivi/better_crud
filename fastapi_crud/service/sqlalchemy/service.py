from typing import (
    Any,
    Dict,
    List,
    Union,
    TypeVar,
    Generic,
    Optional,
    Sequence
)
from datetime import datetime
from pydantic import BaseModel
import functools
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MANYTOMANY, MANYTOONE, ONETOMANY, noload, joinedload
from sqlalchemy.sql.selectable import Select
from sqlalchemy import or_, update, delete, and_, func, select
from sqlalchemy.orm.interfaces import ORMOption
from fastapi import Request, BackgroundTasks, status
from fastapi.exceptions import HTTPException
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.bases import AbstractPage
from ...helper import decide_should_paginate, build_join_option_tree
from ..abstract import AbstractCrudService
from ...types import QuerySortDict, ID_TYPE
from ...models import JoinOptions, JoinOptionModel

from ...config import FastAPICrudGlobalConfig
from .helper import (
    create_many_to_many_instances,
    create_one_to_many_instances,
    create_many_to_one_instance,
    create_one_to_one_instance,
    inject_db_session,
    Provide
)
from .errors import (
    UnSupportOperatorError,
    InvalidFieldError,
    UnSupportRelationshipQueryError
)

ModelType = TypeVar("ModelType")
Selectable = TypeVar("Selectable", bound=Select[Any])


LOGICAL_OPERATOR_AND = "$and"
LOGICAL_OPERATOR_OR = "$or"


class SqlalchemyCrudService(
    Generic[ModelType],
    AbstractCrudService[ModelType]
):

    entity: object = NotImplementedError

    def __init__(
        self,
        entity: object
    ):
        self.entity = entity
        self.primary_key = entity.__mapper__.primary_key[0].name
        self.entity_has_delete_column = hasattr(
            self.entity, FastAPICrudGlobalConfig.soft_deleted_field_key)

    def prepare_order(self, query, sorts: List[QuerySortDict]):
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

    def create_search_field_object_condition(
        self,
        logical_operator: str,
        field: str,
        obj: Any
    ):
        logical_operator = logical_operator or LOGICAL_OPERATOR_AND
        if isinstance(obj, dict):
            model_field = self.get_model_field(field)
            keys = list(obj.keys())
            if len(keys) == 1:
                if keys[0] == LOGICAL_OPERATOR_OR:
                    return self.create_search_field_object_condition(
                        LOGICAL_OPERATOR_OR,
                        field,
                        obj.get(LOGICAL_OPERATOR_OR)
                    )
                else:
                    return self.build_query_expression(
                        model_field,
                        keys[0],
                        obj[keys[0]]
                    )
            else:
                if logical_operator == LOGICAL_OPERATOR_OR:
                    return or_(*(self.build_query_expression(
                        model_field,
                        operator,
                        obj[operator]
                    ) for operator in keys))
                elif logical_operator == LOGICAL_OPERATOR_AND:
                    clauses = []
                    for operator in keys:
                        is_or = operator == LOGICAL_OPERATOR_OR
                        if isinstance(obj[operator], dict) and is_or:
                            clauses.append(
                                self.create_search_field_object_condition(
                                    LOGICAL_OPERATOR_OR,
                                    field,
                                    obj.get(operator)
                                )
                            )
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
                        clauses = [
                            and_(*self.create_search_condition(and_value))
                            for and_value in and_values
                        ]
                        conds.append(and_(*clauses))
                else:
                    for field, value in search.items():
                        field_is_or = field == LOGICAL_OPERATOR_OR
                        if field_is_or and isinstance(value, list):
                            if len(value) == 1:
                                conds.append(
                                    and_(
                                        *self.create_search_condition(value[0])
                                    )
                                )
                            else:
                                clauses = [
                                    and_(
                                        *self.create_search_condition(or_value)
                                    ) for or_value in value
                                ]
                                conds.append(or_(*clauses))
                        elif isinstance(value, Dict):
                            conds.append(
                                self.create_search_field_object_condition(
                                    LOGICAL_OPERATOR_AND,
                                    field,
                                    value
                                )
                            )
                        else:
                            conds.append(self.get_model_field(field) == value)
        return conds

    def _create_join_options(
        self,
        children,
        request: Optional[Request] = None,
        from_detail: Optional[bool] = False
    ) -> Sequence[ORMOption]:
        options: Sequence[ORMOption] = []
        for child in children:
            field_key = child["field_key"]
            join_field = self.get_model_field(field_key)
            config: JoinOptionModel = child["config"]
            should_select = config.select
            if not from_detail and config.select_only_detail:
                should_select = False
            if should_select:
                if config.additional_filter_fn:
                    filter_results = config.additional_filter_fn(request)
                    if not isinstance(filter_results, list):
                        filter_results = [filter_results]
                    loader = joinedload(join_field.and_(*filter_results))
                else:
                    loader = joinedload(join_field)
                if child["children"]:
                    options.append(loader.options(*self._create_join_options(
                        child["children"],
                        request=request,
                        from_detail=from_detail
                    )))
                else:
                    options.append(loader)
            else:
                options.append(noload(join_field))
        return options

    def _build_query(
        self,
        search: Optional[Dict] = None,
        include_deleted: Optional[bool] = False,
        soft_delete: Optional[bool] = True,
        joins: Optional[JoinOptions] = None,
        sorts: List[QuerySortDict] = None,
        request: Optional[Request] = None
    ) -> Selectable:
        conds = []
        options: Sequence[ORMOption] = []
        if search:
            conds = conds + self.create_search_condition(search)
        if self.entity_has_delete_column and soft_delete:
            soft_deleted_field = FastAPICrudGlobalConfig.soft_deleted_field_key
            if not include_deleted:
                conds.append(or_(
                    getattr(self.entity, soft_deleted_field) > func.now(),
                    getattr(self.entity, soft_deleted_field).is_(None)
                ))
        stmt = select(self.entity)
        if joins:
            for field_key, config in joins.items():
                if config.join:
                    join_field = self.get_model_field(field_key)
                    stmt = stmt.join(join_field, isouter=True)
            options = self._create_join_options(
                build_join_option_tree(joins),
                request=request
            )
        if options:
            stmt = stmt.options(*options)
        stmt = stmt.distinct()
        stmt = stmt.where(*conds)
        stmt = self.prepare_order(stmt, sorts)
        return stmt

    @inject_db_session
    async def crud_get_many(
        self,
        request: Optional[Request] = None,
        search: Optional[Dict] = None,
        include_deleted: Optional[bool] = False,
        soft_delete: Optional[bool] = False,
        sorts: List[QuerySortDict] = None,
        joins: Optional[JoinOptions] = None,
        db_session: Optional[AsyncSession] = Provide()
    ) -> Union[AbstractPage[ModelType], List[ModelType]]:
        query = self._build_query(
            search=search,
            include_deleted=include_deleted,
            soft_delete=soft_delete,
            joins=joins,
            sorts=sorts,
            request=request
        )
        if decide_should_paginate():
            return await paginate(db_session, query)
        result = await db_session.execute(query)
        return result.unique().scalars().all()

    @inject_db_session
    async def crud_get_one(
        self,
        request: Request,
        id: ID_TYPE,
        joins: Optional[JoinOptions] = None,
        db_session: Optional[AsyncSession] = Provide()
    ) -> ModelType:
        return await self._get(
            id,
            db_session,
            options=self._create_join_options(
                build_join_option_tree(joins),
                request=request,
                from_detail=True
            )
        )

    @inject_db_session
    async def crud_create_one(
        self,
        request: Request,
        model: BaseModel,
        background_tasks: Optional[BackgroundTasks] = None,
        db_session: Optional[AsyncSession] = Provide()
    ) -> ModelType:
        relationships = self.entity.__mapper__.relationships
        model_data = model.model_dump(exclude_unset=True)
        await self.on_before_create(
            model_data,
            background_tasks=background_tasks
        )
        if request:
            if hasattr(request.state, "auth_persist"):
                model_data.update(request.state.auth_persist)
            if hasattr(request.state, "params_filter"):
                model_data.update(request.state.params_filter)
        for key, value in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction
                relation_cls = relationships[key].mapper.entity

                if relation_dir == MANYTOMANY:
                    model_data[key] = await create_many_to_many_instances(
                        db_session,
                        relation_cls,
                        value
                    )
                elif relation_dir == ONETOMANY:
                    if relationships[key].uselist:
                        model_data[key] = await create_one_to_many_instances(
                            relation_cls,
                            value
                        )
                    else:
                        # one to one
                        model_data[key] = await create_one_to_one_instance(
                            relation_cls,
                            value
                        )

                elif relation_dir == MANYTOONE:
                    model_data[key] = await create_many_to_one_instance(
                        relation_cls,
                        value
                    )
        entity = self.entity(**model_data)
        db_session.add(entity)
        await db_session.flush()
        await self.on_after_create(entity, background_tasks=background_tasks)
        await db_session.commit()
        await db_session.refresh(entity)
        return entity

    @inject_db_session
    async def crud_create_many(
        self,
        request: Request,
        models: List[BaseModel],
        background_tasks: Optional[BackgroundTasks] = None,
        db_session: Optional[AsyncSession] = Provide()
    ) -> List[ModelType]:
        entities = []
        for model in models:
            entity = await self.crud_create_one(
                request,
                model=model,
                db_session=db_session,
                background_tasks=background_tasks
            )
            entities.append(entity)
        return entities

    @inject_db_session
    async def crud_update_one(
        self,
        request: Request,
        id: ID_TYPE,
        model: BaseModel,
        background_tasks: Optional[BackgroundTasks] = None,
        db_session: Optional[AsyncSession] = Provide()
    ):
        model_data = model.model_dump(exclude_unset=True)
        relationship_fields = self._guess_should_load_relationship_fields(
            model_data
        )
        joins = functools.reduce(
            lambda x, y: {**x, y: JoinOptionModel(select=True, join=False)},
            relationship_fields,
            {}
        )
        options = self._create_join_options(
            build_join_option_tree(joins),
            request=request,
            from_detail=True
        )
        entity = await self._get(id, db_session=db_session, options=options)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data not found"
            )
        await self.on_before_update(
            entity,
            update_data=model_data,
            background_tasks=background_tasks
        )
        relationships = self.entity.__mapper__.relationships
        for key, value in model_data.items():
            if key in relationships:
                relation_dir = relationships[key].direction
                relation_cls = relationships[key].mapper.entity
                if relation_dir == MANYTOMANY:
                    value = await create_many_to_many_instances(
                        db_session,
                        relation_cls,
                        value
                    )
                elif relation_dir == ONETOMANY:
                    if relationships[key].uselist:
                        value = await create_one_to_many_instances(
                            relation_cls=relation_cls,
                            data=value,
                            old_instances=getattr(entity, key)
                        )
                    else:
                        # one to one
                        value = await create_one_to_one_instance(
                            relation_cls=relation_cls,
                            data=value,
                            old_instance=getattr(entity, key)
                        )
                elif relation_dir == MANYTOONE:
                    value = await create_many_to_one_instance(
                        relation_cls=relation_cls,
                        data=value,
                        old_instance=getattr(entity, key)
                    )
            setattr(entity, key, value)
        db_session.add(entity)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(entity)
        await self.on_after_update(entity, background_tasks=background_tasks)
        return entity

    @inject_db_session
    async def crud_delete_many(
        self,
        request: Request,
        ids: List[ID_TYPE],
        soft_delete: Optional[bool] = False,
        background_tasks: Optional[BackgroundTasks] = None,
        db_session: Optional[AsyncSession] = Provide()
    ) -> List[ModelType]:
        returns = [await self._get(id, db_session) for id in ids]
        await self.on_before_delete(ids, background_tasks=background_tasks)
        if soft_delete:
            await self._soft_delete(ids, db_session=db_session)
        else:
            await self._batch_delete(
                getattr(self.entity, self.primary_key).in_(ids),
                db_session=db_session
            )
        await self.on_after_delete(ids, background_tasks=background_tasks)
        return returns

    def _guess_should_load_relationship_fields(self, model_data: Dict):
        relationships = self.entity.__mapper__.relationships
        relationship_keys = []
        for key in model_data:
            if key in relationships:
                relation_dir = relationships[key].direction
                if relation_dir == MANYTOMANY:
                    relationship_keys.append(key)
                elif relation_dir == ONETOMANY:
                    relationship_keys.append(key)
                elif relation_dir == MANYTOONE:
                    relationship_keys.append(key)
        return relationship_keys

    async def _batch_delete(self, stmt, db_session: AsyncSession):
        if not isinstance(stmt, list):
            stmt = [stmt]
        statement = delete(self.entity).where(*stmt)
        await db_session.execute(statement)
        await db_session.commit()

    async def _get(
        self,
        id: Union[int, str],
        db_session: AsyncSession,
        options: Optional[Sequence[ORMOption]] = None,
    ) -> ModelType:
        return await db_session.get(self.entity, id, options=options)

    async def _soft_delete(
        self,
        id_list: List[Union[int, str]],
        db_session: AsyncSession
    ):
        stmt = update(self.entity).where(
            getattr(self.entity, self.primary_key)
            .in_(id_list)).values({
                FastAPICrudGlobalConfig.soft_deleted_field_key: datetime.now()
            })
        await db_session.execute(stmt)
        await db_session.commit()

    async def on_before_create(
        self,
        create_data: dict,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> None:
        pass

    async def on_after_create(
        self,
        entity: ModelType,
        background_tasks: BackgroundTasks
    ) -> None:
        pass

    async def on_before_update(
        self,
        entity: ModelType,
        update_data: Dict,
        background_tasks: BackgroundTasks
    ) -> None:
        pass

    async def on_after_update(
        self,
        entity: ModelType,
        background_tasks: BackgroundTasks
    ) -> None:
        pass

    async def on_before_delete(
        self,
        ids: List[ID_TYPE],
        background_tasks: BackgroundTasks
    ) -> None:
        pass

    async def on_after_delete(
        self,
        ids: List[ID_TYPE],
        background_tasks: BackgroundTasks
    ) -> None:
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
        elif operator == "$lte":
            return field <= value
        elif operator == "$cont":
            return field.like('%{}%'.format(value))
        elif operator == "$excl":
            return field.notlike('%{}%'.format(value))
        elif operator == "$starts":
            return field.startswith(value)
        elif operator == "$ends":
            return field.endswith(value)
        elif operator == "$doesNotBeginWith":
            return field.notlike('{}%'.format(value))
        elif operator == "$doesNotEndWith":
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
            return field.between(*value.split(","))
        elif operator == "$notbetween":
            return ~field.between(*value.split(","))
        elif operator == "$length":
            return func.length(field) == int(value)
        elif operator == "$any":
            primary_key = self.get_field_primary_key(field)
            if not primary_key:
                raise UnSupportRelationshipQueryError(operator)
            return field.any(**{primary_key: value})
        elif operator == "$notany":
            primary_key = self.get_field_primary_key(field)
            if not primary_key:
                raise UnSupportRelationshipQueryError(operator)
            return func.not_(field.any(**{primary_key: value}))
        else:
            raise UnSupportOperatorError(operator)

    def get_model_field(self, field):
        field_parts = field.split(".")
        model_field = None
        if len(field_parts) > 1:
            relation_cls = None
            relationships = self.entity.__mapper__.relationships
            for index, field_part in enumerate(field_parts):
                if relation_cls:
                    model_field = getattr(relation_cls, field_part, None)
                    if index == len(field_parts)-1:
                        break
                relation_cls = relationships[field_part].mapper.entity
                relationships = relation_cls.__mapper__.relationships
        else:
            model_field = getattr(self.entity, field, None)
        if not model_field:
            raise InvalidFieldError(field)
        return model_field

    def get_model_class(self, field):
        field_parts = field.split(".")
        relationships = self.entity.__mapper__.relationships
        if len(field_parts) > 1:
            relation_cls = None
            for field_part in field_parts:
                relation_cls = relationships[field_part].mapper.entity
                relationships = relation_cls.__mapper__.relationships
            return relation_cls
        return relationships[field].mapper.entity

    def get_field_primary_key(self, field):
        try:
            relation_cls = field.mapper.entity
            return relation_cls.__mapper__.primary_key[0].name
        except Exception:
            pass
        return None
