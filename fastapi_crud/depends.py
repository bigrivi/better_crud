from typing import Annotated, Union,Optional,List,Dict
from fastapi import Query
from .helper import make_search



class GetFilterParameters:

    def __init__(self, options_filter:Optional[Dict] = None):
        self.options_filter = options_filter

    def __call__(
        self,
        search_json: Optional[str] = Query(None, alias="s"),
        filters: List[str] = Query(None, alias="filter"),
        ors: List[str] = Query(None, alias="or"),
    ):
        search = make_search(search_json=search_json,ors=ors,filters=filters,options_filter=self.options_filter)
        print("search")
        print(search)
        return search