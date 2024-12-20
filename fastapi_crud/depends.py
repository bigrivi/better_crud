from typing import Callable, Optional, List, Dict
from fastapi import Query, Request
from .helper import parse_query_search, parse_query_sort, get_params_filter
from pydantic.types import Json
from pydantic import BaseModel
from .types import QuerySortDict
from .models import (
    AuthModel,
    QuerySortModel,
    PathParamModel,
    JoinOptions,
    JoinOptionModel
)


class GetQuerySearch:

    def __init__(
        self,
        option_filter: Optional[Dict] = None
    ):
        self.option_filter = option_filter

    def __call__(
        self,
        request: Request,
        search_spec: Optional[Json] = Query(None, alias="s"),
        filters: List[str] = Query(None, alias="filter"),
        ors: List[str] = Query(None, alias="or"),
    ):
        params_filter = getattr(request.state, "params_filter", None)
        auth_filter = getattr(request.state, "auth_filter", None)
        search = parse_query_search(
            search_spec=search_spec,
            ors=ors,
            filters=filters,
            option_filter=self.option_filter,
            auth_filter=auth_filter,
            params_filter=params_filter
        )
        return search


class GetQuerySorts:

    def __init__(self, option_sort: Optional[List[QuerySortDict]] = None):
        self.option_sort = option_sort
        if self.option_sort and isinstance(self.option_sort[0], BaseModel):
            self.option_sort = [item.model_dump() for item in self.option_sort]

    def __call__(
        self,
        sorts: List[str] = Query(None, alias="sort")
    ):
        if sorts:
            return parse_query_sort(sorts)
        if self.option_sort:
            return self.option_sort
        return []


class GetQueryJoins:

    def __init__(self, option_joins: Optional[JoinOptions] = None):
        self.option_joins = option_joins

    def __call__(
        self,
        loads: List[str] = Query(None, alias="load"),
        joins: List[str] = Query(None, alias="join"),
    ):

        join_options: JoinOptions = {
            **self.option_joins} if self.option_joins else {}
        if loads:
            for load_field in loads:
                if load_field in join_options:
                    join_options[load_field].select = True
                else:
                    join_options[load_field] = JoinOptionModel(
                        select=True, join=False)
        if joins:
            for join_field in joins:
                if join_field in join_options:
                    join_options[join_field].join = True
                else:
                    join_options[join_field] = JoinOptionModel(
                        select=False, join=True)
        return join_options


class GetQueryLoads:

    def __init__(self, option_joins: Optional[JoinOptions] = None):
        self.option_joins = option_joins

    def __call__(
        self,
        loads: List[str] = Query(None, alias="load"),
    ):

        join_options: JoinOptions = {
            **self.option_joins} if self.option_joins else {}
        if loads:
            for load_field in loads:
                if load_field in join_options:
                    join_options[load_field].select = True
                else:
                    join_options[load_field] = JoinOptionModel(
                        select=True, join=False)
        return join_options


class CrudAction():

    def __init__(self, feature: str, action_map: Dict, router_name: str):
        self.feature = feature
        self.action_map = action_map
        self.router_name = router_name

    def __call__(self, request: Request):
        request.state.feature = self.feature
        request.state.action = self.action_map.get(self.router_name).value


class StateAction():

    def __init__(self, auth: AuthModel, params: Dict[str, PathParamModel]):
        self.auth = auth
        self.params = params

    def __call__(self, request: Request):
        if self.auth:
            if self.auth.persist and isinstance(self.auth.persist, Callable):
                request.state.auth_persist = self.auth.persist(request)
            if self.auth.filter_ and isinstance(self.auth.filter_, Callable):
                request.state.auth_filter = self.auth.filter_(request)
        if self.params:
            params_filter = get_params_filter(self.params, request)
            request.state.params_filter = params_filter
