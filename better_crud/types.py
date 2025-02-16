from typing import (
    List,
    Optional,
    Any,
    Dict,
    Callable,
    Sequence,
    Literal,
    Union,
    AsyncGenerator,
    TypeVar
)
from typing_extensions import TypedDict
from fastapi import params
from pydantic import BaseModel


RoutesEnumType = Literal[
    "get_many",
    "get_one",
    "create_one",
    "create_many",
    "update_one",
    "update_many",
    "delete_many"
]

BackendType = Literal[
    "sqlalchemy",
    "custom"
]

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ID_TYPE = Union[int, str]
DBSessionFactory = Callable[..., Union[AsyncGenerator[Any, None], Any]]


class RouteSchema(TypedDict):
    name: str
    path: str
    method: Literal[
        "GET",
        "POST",
        "PUT",
        "DELETE"
    ]


class RouteOptionsDict(TypedDict, total=False):
    dependencies: Optional[Sequence[params.Depends]] = None
    summary: Optional[str] = None


class RoutesModelDict(TypedDict, total=False):
    dependencies: Optional[Sequence[params.Depends]] = None
    only: Optional[List[RoutesEnumType]] = None
    exclude: Optional[List[RoutesEnumType]] = None
    get_many: Optional[RouteOptionsDict] = None
    get_one: Optional[RouteOptionsDict] = None
    create_one: Optional[RouteOptionsDict] = None
    create_many: Optional[RouteOptionsDict] = None
    update_one: Optional[RouteOptionsDict] = None
    update_many: Optional[RouteOptionsDict] = None
    delete_many: Optional[RouteOptionsDict] = None


class QueryCriterion(TypedDict, total=False):
    field: str
    value: str
    operator: str


class QuerySortDict(TypedDict):
    field: str
    sort: Literal["ASC", "DESC"]


class PathParamDict(TypedDict):
    field: str
    type: Literal["str", "int"]


class GlobalQueryOptionsDict(TypedDict, total=False):
    soft_delete: Optional[bool] = False
    sort: Optional[List[QuerySortDict]] = None
    allow_include_deleted: Optional[bool] = False


class QueryDelimOptionsDict(TypedDict, total=False):
    delim: Optional[str] = "||"
    delim_str: Optional[str] = ","


class JoinOptionsDict(TypedDict, total=False):
    select: Optional[bool] = True
    join: Optional[bool] = True
    select_only_detail: Optional[bool] = False
    additional_filter_fn: Optional[Callable[[Any], List[Any]]] = None
    alias: Optional[Any] = None


class QueryOptionsDict(TypedDict, total=False):
    joins: Optional[Dict[str, JoinOptionsDict]] = None
    soft_delete: Optional[bool] = None
    allow_include_deleted: Optional[bool] = False
    filter: Optional[Dict] = None
    sort: Optional[List[QuerySortDict]] = None


class AuthModelDict(TypedDict, total=False):
    filter: Optional[Callable[[Any], Dict]]
    persist: Optional[Callable[[Any], Dict]]


class DtoModelDict(TypedDict, total=False):
    create: Optional[Any] = None
    update: Optional[Any] = None


class SerializeModelDict(TypedDict, total=False):
    base: Any
    get_many: Optional[Any] = None
    get_one: Optional[Any] = None
    create_one: Optional[Any] = None
    create_many: Optional[Any] = None
    update_one: Optional[Any] = None
    delete_many: Optional[Any] = None


class SqlalchemyBackendDict(TypedDict):
    db_session: DBSessionFactory


class BackendConfigDict(TypedDict):
    backend: BackendType
    sqlalchemy: SqlalchemyBackendDict
