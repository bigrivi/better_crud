from typing import TypeVar, Any
from fastapi import APIRouter
from typing import (
    Any,
    Optional,
    TypeVar,
    Dict,
    Callable,
    Awaitable
)
from fastapi import APIRouter
from .models import CrudOptions
from .types import (
    RoutesModelDict,
    QueryOptionsDict,
    AuthModelDict,
    DtoModelDict,
    SerializeModelDict,
    PathParamDict
)
from .config import FastAPICrudGlobalConfig
from .factory import crud_routes_factory
from .service.sqlalchemy import SqlalchemyCrudService
from .service import AbstractCrudService

ModelType = TypeVar("ModelType", bound=Any)


def crud_router(
    model: ModelType,
    serialize: SerializeModelDict,
    params: Optional[Dict[str, PathParamDict]] = None,
    routes: Optional[RoutesModelDict] = {},
    dto: DtoModelDict = {},
    auth: Optional[AuthModelDict] = {},
    query: Optional[QueryOptionsDict] = {},
    summary_vars: Optional[Dict] = {},
    feature: Optional[str] = "",
    service: Optional[AbstractCrudService] = None,
    on_before_create: Optional[Callable[..., Awaitable[Any]]] = None,
    on_after_create: Optional[Callable[..., Awaitable[Any]]] = None,
    on_before_update: Optional[Callable[..., Awaitable[Any]]] = None,
    on_after_update: Optional[Callable[..., Awaitable[Any]]] = None,
    on_before_delete: Optional[Callable[..., Awaitable[Any]]] = None,
    on_after_delete: Optional[Callable[..., Awaitable[Any]]] = None
):
    options = CrudOptions(
        feature=feature,
        dto=dto,
        auth=auth,
        params=params,
        serialize=serialize,
        summary_vars=summary_vars,
        routes={**FastAPICrudGlobalConfig.routes.model_dump(), **routes},
        query={**FastAPICrudGlobalConfig.query.model_dump(), **query}
    )
    router = APIRouter()

    class LocalCrudService(SqlalchemyCrudService):
        def __init__(self):
            super().__init__(model)

        async def on_before_create(self, *args, **kwargs) -> None:
            on_before_create and await on_before_create(*args, **kwargs)

        async def on_after_create(self, *args, **kwargs) -> None:
            on_after_create and await on_after_create(*args, **kwargs)

        async def on_before_update(self, *args, **kwargs) -> None:
            on_before_update and await on_before_update(*args, **kwargs)

        async def on_after_update(self, *args, **kwargs) -> None:
            on_after_update and await on_after_update(*args, **kwargs)

        async def on_before_delete(self, *args, **kwargs) -> None:
            on_before_delete and await on_before_delete(*args, **kwargs)

        async def on_after_delete(self, *args, **kwargs) -> None:
            on_after_delete and await on_after_delete(*args, **kwargs)

    class CrudController:
        def __init__(self):
            self.service = service or LocalCrudService()
    crud_routes_factory(router, CrudController, options)
    return router
