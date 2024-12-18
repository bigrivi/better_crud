from typing import TypeVar, Any
from fastapi import APIRouter
from typing import (
    Any,
    Optional,
    TypeVar,
    Dict
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

    class CrudController:
        def __init__(self):
            self.service = SqlalchemyCrudService(model)
    crud_routes_factory(router, CrudController, options)
    return router
