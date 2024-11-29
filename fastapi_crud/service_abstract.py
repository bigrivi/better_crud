import abc
from typing import Any, Dict,List,Union,TypeVar, Generic, Optional
from fastapi import Request,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination.bases import AbstractPage

ModelType = TypeVar("ModelType")

class CrudService(Generic[ModelType],abc.ABC):

    @abc.abstractmethod
    async def get_many(
        self,
        request: Request,
        *,
        db_session:AsyncSession,
        search:Optional[Dict] = None,
        include_deleted:Optional[bool] = False,
        soft_delete:Optional[bool] = False,
        joins:Optional[List] = None,
        options:Optional[List] = None,
        sorts: List[str] = None,
        implanted_cond:Optional[List[Any]] = None
    )->Union[AbstractPage[ModelType],List[ModelType]]:
        raise NotImplementedError