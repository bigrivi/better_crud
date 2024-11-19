from typing import Callable,Any,Dict,Optional,ClassVar,Generator
from typing_extensions import Annotated
from fastapi import Request
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import GlobalQueryOptions,RoutesModel,QueryDelimOptions

DBSessionFunc = Callable[...,Generator[AsyncSession, None, None]]


class FastAPICrudGlobalConfig:
    get_db_session_fn:ClassVar[DBSessionFunc] = None
    query:ClassVar[GlobalQueryOptions] = None
    routes: ClassVar[Optional[RoutesModel]] = None
    delim_config:ClassVar[Optional[QueryDelimOptions]] = None

    @classmethod
    def init(
        cls,
        get_db_session:DBSessionFunc,
        query:Optional[GlobalQueryOptions] = {},
        routes:Optional[RoutesModel] = {},
        delim_config:Optional[QueryDelimOptions] = {}
    ) -> None:
        cls.get_db_session_fn = get_db_session
        cls.query = GlobalQueryOptions(**query)
        cls.routes = RoutesModel(**routes)
        cls.delim_config = QueryDelimOptions(**delim_config)


    @classmethod
    async def get_session(cls):
        session_gen = cls.get_db_session_fn()
        session = await anext(session_gen)
        yield session