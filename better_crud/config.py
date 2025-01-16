from typing import Dict, Optional, ClassVar, List
from importlib import import_module
from .models import (
    GlobalQueryOptions,
    RoutesModel,
    QueryDelimOptions,
    AbstractResponseModel,
    BackendConfigModel
)
from .types import (
    GlobalQueryOptionsDict,
    RoutesModelDict,
    QueryDelimOptionsDict,
    BackendConfigDict,
    RouteSchema
)
from .pagination import Page
from fastapi_pagination.bases import AbstractPage
from .enums import RoutesEnum, CrudActions

DEFAULT_SOFT_DELETED_FIELD_KEY = "deleted_at"

DEFAULT_ACTION_MAP = {
    RoutesEnum.get_many: CrudActions.read_all,
    RoutesEnum.get_one: CrudActions.read_one,
    RoutesEnum.create_one: CrudActions.create_one,
    RoutesEnum.create_many: CrudActions.create_many,
    RoutesEnum.update_one: CrudActions.update_one,
    RoutesEnum.update_many: CrudActions.update_many,
    RoutesEnum.delete_many: CrudActions.delete_many
}


RoutesSchema: List[RouteSchema] = [
    {
        "name": RoutesEnum.get_many,
        "path": '',
        "method": "GET"
    },
    {
        "name": RoutesEnum.create_one,
        "path": '',
        "method": "POST"
    },
    {
        "name": RoutesEnum.create_many,
        "path": '/bulk',
        "method": "POST"
    },
    {
        "name": RoutesEnum.get_one,
        "path": '/{id}',
        "method": "GET"
    },
    {
        "name": RoutesEnum.update_one,
        "path": '/{id}',
        "method": "PUT"
    },
    {
        "name": RoutesEnum.update_many,
        "path": '/{ids}/bulk',
        "method": "PUT"
    },
    {
        "name": RoutesEnum.delete_many,
        "path": '/{ids}',
        "method": "DELETE"
    }
]


class BetterCrudGlobalConfig:
    query: ClassVar[GlobalQueryOptions] = GlobalQueryOptions()
    routes: ClassVar[Optional[RoutesModel]] = RoutesModel()
    delim_config: ClassVar[Optional[QueryDelimOptions]] = None
    soft_deleted_field_key: ClassVar[Optional[str]
                                     ] = DEFAULT_SOFT_DELETED_FIELD_KEY
    action_map: ClassVar[Optional[Dict[str, str]]] = None
    page_schema: ClassVar[Optional[AbstractPage]] = Page
    response_schema: ClassVar[Optional[AbstractResponseModel]] = None
    backend_config: ClassVar[BackendConfigModel] = None

    @classmethod
    def init(
        cls,
        *,
        backend_config: Optional[BackendConfigDict] = None,
        query: Optional[GlobalQueryOptionsDict] = {},
        routes: Optional[RoutesModelDict] = {},
        delim_config: Optional[QueryDelimOptionsDict] = {},
        soft_deleted_field_key: Optional[str] = None,
        action_map: Optional[Dict[str, str]] = None,
        page_schema: Optional[AbstractPage] = Page,
        response_schema: Optional[AbstractResponseModel] = None
    ) -> None:
        cls.query = GlobalQueryOptions(**query)
        cls.routes = RoutesModel(**routes)
        cls.delim_config = QueryDelimOptions(**delim_config)
        if soft_deleted_field_key:
            cls.soft_deleted_field_key = soft_deleted_field_key
        cls.page_schema = page_schema
        cls.response_schema = response_schema
        cls.action_map = action_map or DEFAULT_ACTION_MAP
        cls.backend_config = BackendConfigModel(**backend_config)
        if cls.backend_config.backend != "custom":
            import_module(
                f".service.{cls.backend_config.backend}", package="better_crud")
