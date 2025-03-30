from typing import Optional, Callable, List, TypeVar, Dict, Any, Union
from fastapi import Request
import json
from fastapi_pagination.api import resolve_params
from fastapi_pagination.bases import AbstractParams
from .types import QuerySortDict
from .models import SerializeModel, RouteOptions, PathParamModel, JoinOptions
from .enums import RoutesEnum

from .config import BetterCrudGlobalConfig
FindType = TypeVar('FindType')


def find(data: List[FindType], fun: Callable[[FindType], bool]) -> FindType:
    for item in data:
        if fun(item):
            return item


def get_feature(request: Request) -> Optional[str]:
    return getattr(request.state, 'feature', None)


def get_action(request: Request) -> Optional[str]:
    return getattr(request.state, 'action', None)


def filter_to_search(filter_str: str) -> Dict:
    filters = filter_str.split(BetterCrudGlobalConfig.delim_config.delim)
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
    search_spec: Optional[Dict] = None,
    ors: Optional[List[str]] = None,
    filters: Optional[List[str]] = None,
    query_filter: Union[Optional[Dict], Callable[[Any], Dict]] = None,
    auth_filter: Optional[Dict] = None,
    params_filter: Optional[Dict] = None
):
    search = {"$and": []}
    search_list = []
    if search_spec:
        search_list.append(search_spec)
    if filters and ors:
        if len(filters) == 1 and len(ors) == 1:
            search_list.append({
                "$or": [
                    {
                        **filter_to_search(filters[0])
                    },
                    {
                        **filter_to_search(ors[0])
                    }
                ]
            })
        else:
            search_list.append({
                "$or": [
                    {
                        "$and": list(map(filter_to_search, filters))
                    },
                    {
                        "$and": list(map(filter_to_search, ors))
                    }
                ]
            })
    elif filters and len(filters) > 0:
        search_list = search_list + list(map(filter_to_search, filters))
    elif ors and len(ors) > 0:
        if len(ors) == 1:
            search_list.append(filter_to_search(ors[0]))
        else:
            search_list.append({
                "$or": list(map(filter_to_search, ors))
            })
    if auth_filter:
        search_list.append(auth_filter)
    if params_filter:
        search_list.append(params_filter)
    if len(search_list) > 0:
        search["$and"] = search_list
    if query_filter is not None:
        if isinstance(query_filter, Callable):
            search = query_filter(search)
        else:
            # ignore any other query search conditions
            search["$and"] = [{**query_filter}]
    if search["$and"]:
        return search
    return None


def parse_query_sort(
    raw_query_sorts: Optional[List[str]] = None,
) -> List[QuerySortDict]:
    sorts = []
    for item in raw_query_sorts:
        if BetterCrudGlobalConfig.delim_config.delim_str not in item:
            raise Exception("invalid query sort")
        field, sort = item.split(
            BetterCrudGlobalConfig.delim_config.delim_str
        )
        sorts.append(QuerySortDict(field=field, sort=sort))
    return sorts


def update_entity_attr(entity, update_value: Dict):
    for key, value in update_value.items():
        if value is not None:
            setattr(entity, key, value)


def decide_should_paginate():
    try:
        params: AbstractParams = resolve_params()
        raw_params = (params.to_raw_params().as_limit_offset())
        return raw_params.limit > 0
    except Exception:
        return False


def get_serialize_model(serialize: SerializeModel, router_name):
    serialize_model = getattr(serialize, router_name, None)
    if serialize_model is None:
        if router_name == RoutesEnum.get_one:
            return get_serialize_model(serialize, RoutesEnum.get_many)
        elif router_name == RoutesEnum.create_many:
            return get_serialize_model(serialize, RoutesEnum.create_one)
        elif router_name == RoutesEnum.update_many:
            return get_serialize_model(serialize, RoutesEnum.update_one)
    return serialize_model or getattr(serialize, "base", None)


class DefaultMap(dict):
    def __missing__(self, key):
        return key


def get_route_summary(route_options: RouteOptions, summary_vars: Dict):
    if not route_options:
        return None
    if not route_options.summary:
        return None
    return route_options.summary.format_map(DefaultMap(**summary_vars))


def get_params_filter(params: Dict[str, PathParamModel], request: Request):
    params_filter = {}
    if params and request.path_params:
        for key, value in params.items():
            if key in request.path_params:
                params_filter[value.field] = request.path_params[key]
    return params_filter


def build_join_options_tree(join_options: JoinOptions) -> List[Dict]:
    if join_options is None:
        return []
    join_options = dict(sorted(join_options.items()))
    join_tree_nodes = []
    node_dict: Dict[str,] = {}
    for field_key, config in join_options.items():
        segments = field_key.split(".")
        parent_key = ".".join(segments[:-1])
        node_data = {
            "field_key": field_key,
            "config": config,
            "children": []
        }
        if parent_key == "":
            node_dict[field_key] = node_data
            join_tree_nodes.append(node_dict[field_key])
        else:
            parent_node = node_dict.get(parent_key)
            if parent_node:
                node_dict[field_key] = node_data
                parent_node.get("children").append(node_dict[field_key])
    return join_tree_nodes
