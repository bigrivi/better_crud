from typing import Callable,Optional,List,Dict
from fastapi import Query,Request
from .helper import parse_query_search,parse_query_sort,get_params_filter
from pydantic.types import Json
from .models import AuthModel,QuerySortModel,PathParamModel

class GetSearch:

    def __init__(self, option_filter:Optional[Dict] = None,params_def:Optional[Dict] = None):
        self.option_filter = option_filter
        self.params = params_def

    def __call__(
        self,
        request: Request,
        search_spec: Optional[Json] = Query(None, alias="s"),
        filters: List[str] = Query(None, alias="filter"),
        ors: List[str] = Query(None, alias="or"),
    ):
        params_filter = request.state.params_filter if hasattr(request.state,"params_filter") else None
        auth_filter = request.state.auth_filter if hasattr(request.state,"auth_filter") else None
        search = parse_query_search(
            search_spec=search_spec,
            ors=ors,
            filters=filters,
            option_filter=self.option_filter,
            auth_filter=auth_filter,
            params_filter=params_filter
        )
        return search

class GetSort:

    def __init__(self, option_sort:Optional[List[QuerySortModel]] = None):
        self.option_sort = option_sort

    def __call__(
        self,
        sorts: List[str] = Query(None, alias="sort")
    ):
        if sorts:
            return parse_query_sort(sorts)
        if self.option_sort:
            return [item.model_dump() for item in self.option_sort]
        return []
class CrudAction():

    def __init__(self, feature:str,action_map:Dict,router_name:str):
        self.feature = feature
        self.action_map = action_map
        self.router_name = router_name

    def __call__(self,request: Request):
        request.state.feature = self.feature
        request.state.action = self.action_map.get(self.router_name).value


class StateAction():

    def __init__(self, auth:AuthModel,params:Dict[str,PathParamModel]):
        self.auth = auth
        self.params = params

    def __call__(self,request: Request):
        if self.auth:
            if self.auth.persist and isinstance(self.auth.persist, Callable):
                request.state.auth_persist = self.auth.persist(request)
            if self.auth.filter_ and isinstance(self.auth.filter_, Callable):
                request.state.auth_filter = self.auth.filter_(request)
        if self.params:
            params_filter = get_params_filter(self.params,request)
            request.state.params_filter = params_filter
