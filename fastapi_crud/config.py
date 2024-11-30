from typing import Callable,Dict,Optional,ClassVar,Generator,Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from .models import GlobalQueryOptions,RoutesModel,QueryDelimOptions,AbstractResponseModel
from .types import GlobalQueryOptionsDict,RoutesModelDict,QueryDelimOptionsDict
from .pagination import Page
from fastapi_pagination.bases import AbstractPage
from .enums import RoutesEnum, CrudActions

DBSessionFunc = Callable[...,Generator[AsyncSession, None, None]]
DEFAULT_SOFT_DELETED_FIELD_KEY = "deleted_at"

DEFAULT_ACTION_MAP = {
    RoutesEnum.get_many: CrudActions.ReadAll,
    RoutesEnum.get_one: CrudActions.ReadOne,
    RoutesEnum.create_one: CrudActions.CreateOne,
    RoutesEnum.create_many: CrudActions.CreateMany,
    RoutesEnum.update_one: CrudActions.UpdateOne,
    RoutesEnum.delete_many: CrudActions.DeleteMany
}

class FastAPICrudGlobalConfig:
    get_db_session_fn:ClassVar[DBSessionFunc] = None
    query:ClassVar[GlobalQueryOptions] = GlobalQueryOptions()
    routes: ClassVar[Optional[RoutesModel]] = RoutesModel()
    delim_config:ClassVar[Optional[QueryDelimOptions]] = None
    soft_deleted_field_key:ClassVar[Optional[str]] = None
    action_map:ClassVar[Optional[Dict[str,str]]] = None
    page_schema:ClassVar[Optional[AbstractPage]] = Page
    response_schema:ClassVar[Optional[AbstractResponseModel]] = None

    @classmethod
    def init(
        cls,
        get_db_session:DBSessionFunc,
        query:Optional[GlobalQueryOptionsDict] = {},
        routes:Optional[RoutesModelDict] = {},
        delim_config:Optional[QueryDelimOptionsDict] = {},
        soft_deleted_field_key:Optional[str] = None,
        action_map:Optional[Dict[str,str]] = None,
        page_schema:Optional[AbstractPage] = Page,
        response_schema:Optional[AbstractResponseModel] = None
    ) -> None:
        cls.get_db_session_fn = get_db_session
        cls.query = GlobalQueryOptions(**query)
        cls.routes = RoutesModel(**routes)
        cls.delim_config = QueryDelimOptions(**delim_config)
        cls.soft_deleted_field_key = soft_deleted_field_key or DEFAULT_SOFT_DELETED_FIELD_KEY
        cls.page_schema = page_schema
        cls.response_schema = response_schema
        cls.action_map = action_map or DEFAULT_ACTION_MAP


    @classmethod
    async def get_db_session(cls):
        session_generator = cls.get_db_session_fn()
        session = await anext(session_generator)
        yield session

