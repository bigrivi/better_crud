from pydantic import BaseModel,Field
from typing import List, Optional, Any, Dict,Callable
from .enums import RoutesEnum
from typing_extensions import TypedDict


class NodeDict(TypedDict):
    id: str
    value: int
    parent: 'NodeDict | None'


class QueryCriterion(TypedDict):
    field: str
    value: str
    operator: str


class DtoModel(BaseModel):
    create: Any = None
    update: Any = None

class AuthModel(BaseModel):
    property_:str = Field(default=None, alias='property')
    filter_: Callable[[Any], Dict] = Field(default=None, alias='filter')
    persist: Callable[[Any], Dict] = None

class SerializeModel(BaseModel):
    get_many: Any = None
    get_one: Any = None
    create_one: Any = None


class RoutesModel(BaseModel):
    only: Optional[List[RoutesEnum]] = None
    exclude: Optional[List[RoutesEnum]] = None


class QueryOptions(BaseModel):
    join: Optional[List[Any]] = None
    soft_delete: Optional[bool] = None
    pagination: Optional[bool] = True
    filter: Optional[Dict] = None


class CrudOptions(BaseModel):
    dto: DtoModel = None
    serialize: Optional[SerializeModel] = None
    routes: Optional[RoutesModel] = None
    name: str = None
    feature: str = None
    query: Optional[QueryOptions] = None
    auth:Optional[AuthModel] = None


class GlobalQueryOptions(BaseModel):
    soft_delete: Optional[bool] = False
    pagination: Optional[bool] = True


class QueryDelimOptions(BaseModel):
    delim: Optional[str] = "||"
    delim_str: Optional[str] = ","
