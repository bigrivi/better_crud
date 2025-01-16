from typing import TypeVar, Any
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
from .config import BetterCrudGlobalConfig
from .factory import crud_routes_factory
from .service.abstract import AbstractCrudService
from .backend import get_backend

ModelType = TypeVar("ModelType", bound=Any)


def crud_generator(
    router: APIRouter,
    model: ModelType,
    *,
    serialize: SerializeModelDict,
    params: Optional[Dict[str, PathParamDict]] = None,
    routes: Optional[RoutesModelDict] = {},
    dto: DtoModelDict = {},
    auth: Optional[AuthModelDict] = {},
    query: Optional[QueryOptionsDict] = {},
    summary_vars: Optional[Dict] = {},
    feature: Optional[str] = "",
    service_cls: Optional[AbstractCrudService] = None,
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
        routes={**BetterCrudGlobalConfig.routes.model_dump(), **routes},
        query={**BetterCrudGlobalConfig.query.model_dump(), **query}
    )
    backend_name = BetterCrudGlobalConfig.backend_config.backend
    backend_cls = get_backend(backend_name)

    class LocalCrudService(backend_cls[model]):
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

    class LocalCrudController:
        def __init__(self):
            self.service = service_cls() if service_cls else LocalCrudService()
    crud_routes_factory(router, LocalCrudController, options)
