from typing import Callable,Any,Dict,Optional
from typing_extensions import Annotated
from fastapi import Depends,Request,FastAPI
from fastapi_pagination import add_pagination
from .models import GlobalQueryOptions,RoutesModel,QueryDelimOptions


class FastAPICrudGlobalConfig:
    get_db_session_fn = None
    interceptor:Callable[[Request,str,str], Any] = None
    query:GlobalQueryOptions = None
    routes: Optional[RoutesModel] = None
    delim_config:Optional[QueryDelimOptions] = None

    @classmethod
    def init(
        cls,
        get_db_session,
        interceptor = None,
        query:Optional[GlobalQueryOptions] = {},
        routes:Optional[RoutesModel] = {},
        delim_config:Optional[QueryDelimOptions] = {}
    ) -> None:
        cls.get_db_session_fn = get_db_session
        cls.interceptor = interceptor
        cls.query = GlobalQueryOptions(**query)
        cls.routes = RoutesModel(**routes)
        cls.delim_config = QueryDelimOptions(**delim_config)


    @classmethod
    async def get_session(cls):
        session_gen = cls.get_db_session_fn()
        session = await anext(session_gen)
        yield session


