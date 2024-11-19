from typing import Annotated, Union,Optional,List,Dict
from fastapi import Query,Request
from .helper import build_search
from pydantic.types import Json


class GetQuerySearch:

    def __init__(self, options_filter:Optional[Dict] = None):
        self.options_filter = options_filter

    def __call__(
        self,
        search_spec: Optional[Json] = Query(None, alias="s"),
        filters: List[str] = Query(None, alias="filter"),
        ors: List[str] = Query(None, alias="or"),
    ):
        search = build_search(
            search_spec=search_spec,
            ors=ors,
            filters=filters,
            extra_filter=self.options_filter
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