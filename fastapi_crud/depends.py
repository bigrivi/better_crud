from typing import Callable,Optional,List,Dict
from fastapi import Query,Request
from .helper import build_query_search
from pydantic.types import Json
from .models import AuthModel

class GetQuerySearch:

    def __init__(self, option_filter:Optional[Dict] = None):
        self.option_filter = option_filter

    def __call__(
        self,
        request: Request,
        search_spec: Optional[Json] = Query(None, alias="s"),
        filters: List[str] = Query(None, alias="filter"),
        ors: List[str] = Query(None, alias="or"),
    ):
        search = build_query_search(
            search_spec=search_spec,
            ors=ors,
            filters=filters,
            option_filter=self.option_filter,
            auth_filter=request.state.auth_filter if hasattr(request.state,"auth_filter") else None
        )
        return search

class CrudAction():

    def __init__(self, feature:str,action_map:Dict,router_name:str):
        self.feature = feature
        self.action_map = action_map
        self.router_name = router_name

    def __call__(self,request: Request):
        request.state.feature = self.feature
        request.state.action = self.action_map.get(self.router_name).value


class AuthAction():

    def __init__(self, auth:AuthModel):
        self.auth = auth

    def __call__(self,request: Request):
        if self.auth:
            if self.auth.persist and isinstance(self.auth.persist, Callable):
                request.state.auth_persist = self.auth.persist(request)
            if self.auth.filter_ and isinstance(self.auth.filter_, Callable):
                request.state.auth_filter = self.auth.filter_(request)