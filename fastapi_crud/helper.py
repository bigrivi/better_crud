from typing import Any, Optional, Callable, List, Literal, Type, TypeVar, get_type_hints, Literal, Dict, Annotated
from fastapi import Request
import json
from fastapi_pagination.api import resolve_params
from fastapi_pagination.bases import  AbstractParams, RawParams
from .types import QuerySortDict
from .models import SerializeModel
from .enums import RoutesEnum


from .config import FastAPICrudGlobalConfig
FindType = TypeVar('FindType')

def find(data:List[FindType], fun:Callable[[FindType],bool])->FindType:
    for item in data:
        if fun(item):
            return item

def get_feature(request: Request)-> str | None:
    return getattr(request.state, 'feature', None)


def get_action(request: Request)-> str | None:
    return getattr(request.state, 'action', None)


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

def parse_query_search(
    search_spec: Optional[str] = None,
    ors: Optional[List[str]] = None,
    filters: Optional[List[str]] = None,
    option_filter:Optional[Dict] = None,
    auth_filter:Optional[Dict] = None
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

    if option_filter:
        search_list.append(option_filter)
    if auth_filter:
        search_list.append(auth_filter)
    if len(search_list)>0:
        search = {"$and": search_list}

    return search


def parse_query_sort(
    raw_query_sorts: Optional[List[str]] = None,
)->List[QuerySortDict]:
    sorts = []
    for item in raw_query_sorts:
        if FastAPICrudGlobalConfig.delim_config.delim_str not in item:
            raise Exception("invalid query sort")
        field,sort = item.split(FastAPICrudGlobalConfig.delim_config.delim_str)
        sorts.append(QuerySortDict(field=field,sort=sort))
    return sorts

def update_entity_attr(entity,update_value:Dict):
    for key, value in update_value.items():
        if value is not None:
            setattr(entity, key, value)


def decide_should_paginate():
    try:
        params:AbstractParams = resolve_params()
        raw_params = (params.to_raw_params().as_limit_offset())
        return raw_params.limit>0
    except:
        return False

def get_serialize_model(serialize:SerializeModel,router_name):
    serialize_model = getattr(serialize,router_name,None)
    if serialize_model is None:
        if router_name == RoutesEnum.get_one:
            return get_serialize_model(serialize,RoutesEnum.get_many)
        if router_name == RoutesEnum.create_many:
            return get_serialize_model(serialize,RoutesEnum.create_one)
    return serialize_model
