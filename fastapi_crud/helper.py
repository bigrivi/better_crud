from typing import Any, Optional, Callable, List, Literal, Type, TypeVar, get_type_hints, Literal, Dict, Annotated
from fastapi import Request
import json
from pydantic.types import Json
from .config import FastAPICrudGlobalConfig


def get_feature(request: Request):
    return request.state.feature


def get_action(request: Request):
    return request.state.action


def filter_to_search(filter_str: str)->Dict:
    filters = filter_str.split(FastAPICrudGlobalConfig.delim_config.delim)
    field = filters[0]
    operator = filters[1]
    value = filters[2] if len(filters) == 3 else None
    search = {}
    if operator in ["$isnull", "$notnull"]:
        search = {
            field: {
                operator: True
            }
        }
    else:
        search = {
            field: {
                operator: value
            }
        }
    return search

def build_search(
    search_spec: Optional[str] = None,
    ors: Optional[List[str]] = None,
    filters: Optional[List[str]] = None,
    extra_filter:Optional[Dict] = None
):
    search = None
    search_list = []
    if search_spec:
        try:
            search = json.loads(search_spec)
            search_list = [search]
        except:
            search_list = None
    elif filters and ors:
        if len(filters) == 1 and len(ors) == 1:
            search_list = [{
                "$or": [
                    {
                        filter_to_search(
                            filters[0], delim=FastAPICrudGlobalConfig.delim_config.delim)
                    },
                    {
                        filter_to_search(
                            ors[0], delim=FastAPICrudGlobalConfig.delim_config.delim)
                    }
                ]
            }]
        else:
            search_list = [{
                "$or": [
                    {
                        "$and": list(map(filter_to_search, filters))
                    },
                    {
                        "$and": list(map(filter_to_search, ors))
                    }
                ]
            }]

    elif filters and len(filters) > 0:
        search_list = list(map(filter_to_search, filters))
    elif ors and len(ors) > 0:
        if len(ors) == 1:
            search_list = [filter_to_search(
                ors[0])]
        else:
            search_list = [{
                "$or": list(map(filter_to_search, ors))
            }]

    if extra_filter:
        search_list.append(extra_filter)
    if len(search_list)>0:
        search = {"$and": search_list}

    return search
