import abc
from typing import Dict, List, Union, TypeVar, Generic, Optional
from fastapi import Request, BackgroundTasks
from fastapi_pagination.bases import AbstractPage
from ..types import QuerySortDict, ID_TYPE, CreateSchemaType, UpdateSchemaType
from ..models import JoinOptions

ModelType = TypeVar("ModelType")


class AbstractCrudService(Generic[ModelType], abc.ABC):

    @abc.abstractmethod
    async def crud_get_many(
        self,
        request: Optional[Request] = None,
        search: Optional[Dict] = None,
        include_deleted: Optional[bool] = False,
        soft_delete: Optional[bool] = False,
        sorts: List[QuerySortDict] = None,
        joins: Optional[JoinOptions] = None,
    ) -> Union[AbstractPage[ModelType], List[ModelType]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def crud_get_one(
        self,
        request: Request,
        id: ID_TYPE,
        joins: Optional[JoinOptions] = None,
    ) -> ModelType:
        raise NotImplementedError

    @abc.abstractmethod
    async def crud_create_one(
        self,
        request: Request,
        model: CreateSchemaType,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> ModelType:
        raise NotImplementedError

    @abc.abstractmethod
    async def crud_create_many(
        self,
        request: Request,
        models: List[CreateSchemaType],
        background_tasks: Optional[BackgroundTasks] = None
    ) -> List[ModelType]:
        raise NotImplementedError

    @abc.abstractmethod
    async def crud_update_one(
        self,
        request: Request,
        id: ID_TYPE,
        model: UpdateSchemaType,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> ModelType:
        raise NotImplementedError

    @abc.abstractmethod
    async def crud_update_many(
        self,
        request: Request,
        ids: List[ID_TYPE],
        model: List[UpdateSchemaType],
        background_tasks: Optional[BackgroundTasks] = None
    ) -> List[ModelType]:
        raise NotImplementedError

    @abc.abstractmethod
    async def crud_delete_many(
        self,
        request: Request,
        ids: List[ID_TYPE],
        soft_delete: Optional[bool] = False,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> List[ModelType]:
        raise NotImplementedError
