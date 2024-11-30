from typing import List, Optional, Any, Dict,Callable,Sequence,Literal,TypeAlias
from typing_extensions import TypedDict
from fastapi import params

RoutesEnumType:TypeAlias = Literal[
    "get_many",
    "get_one",
    "create_one",
    "create_many",
    "update_one",
    "delete_many"
]


class RouteOptionsDict(TypedDict,total=False):
    dependencies: Optional[Sequence[params.Depends]] = None,

class RoutesModelDict(TypedDict,total=False):
    dependencies: Optional[Sequence[params.Depends]] = None
    only: Optional[List[RoutesEnumType]] = None
    exclude: Optional[List[RoutesEnumType]] = None
    get_many: Optional[RouteOptionsDict] = None
    get_one: Optional[RouteOptionsDict] = None
    create_one: Optional[RouteOptionsDict] = None
    create_many: Optional[RouteOptionsDict] = None
    update_one: Optional[RouteOptionsDict] = None
    delete_many: Optional[RouteOptionsDict] = None

class QueryCriterion(TypedDict,total=False):
    field: str
    value: str
    operator: str

class QuerySortDict(TypedDict):
    field: str
    sort:Literal["ASC","DESC"]

class GlobalQueryOptionsDict(TypedDict,total=False):
    soft_delete: Optional[bool] = False
    sort: Optional[List[QuerySortDict]] = None


class QueryDelimOptionsDict(TypedDict,total=False):
    delim: Optional[str] = "||"
    delim_str: Optional[str] = ","

class QueryOptionsDict(TypedDict,total=False):
    joins: Optional[List[Any]] = None
    soft_delete: Optional[bool] = None
    filter: Optional[Dict] = None
    sort: Optional[List[QuerySortDict]] = None


class AuthModelDict(TypedDict,total=False):
    property:Optional[str]
    filter: Optional[Callable[[Any], Dict]]
    persist: Optional[Callable[[Any], Dict]]

class DtoModelDict(TypedDict,total=False):
    create: Optional[Any] = None
    update: Optional[Any] = None

class SerializeModelDict(TypedDict,total=False):
    get_many: Optional[Any] = None
    get_one: Optional[Any] = None
    create_one: Optional[Any] = None
    create_many: Optional[Any] = None
    update_one: Optional[Any] = None
    delete_many: Optional[Any] = None
