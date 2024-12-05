from typing import List, Optional, Any, Dict,Callable,Sequence,TypeVar,Union,Type,Literal
from abc import ABC,abstractmethod
from pydantic import BaseModel,Field,ConfigDict
from .enums import RoutesEnum,QuerySortType

class DtoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    create: Optional[Any] = None
    update: Optional[Any] = None

class AuthModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    property_:str = Field(default=None, alias='property')
    filter_: Callable[[Any], Dict] = Field(default=None, alias='filter')
    persist: Callable[[Any], Dict] = None

class SerializeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base:Any = Field(...)
    get_many: Optional[Any] = None
    get_one: Optional[Any] = None
    create_one: Optional[Any] = None
    create_many: Optional[Any] = None
    update_one: Optional[Any] = None
    delete_many: Optional[Any] = None

class RouteOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dependencies: Optional[Sequence[Any]] = None
    summary:Optional[str] = None

class RoutesModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dependencies: Optional[Sequence[Any]] = None
    only: Optional[List[RoutesEnum]] = None
    exclude: Optional[List[RoutesEnum]] = None
    get_many: Optional[RouteOptions] = None
    get_one: Optional[RouteOptions] = None
    create_one: Optional[RouteOptions] = None
    create_many: Optional[RouteOptions] = None
    update_one: Optional[RouteOptions] = None
    delete_many: Optional[RouteOptions] = None

class QuerySortModel(BaseModel):
    field: str
    sort:QuerySortType


class JoinOptionModel(BaseModel):
    select:Optional[bool] = True
    join:Optional[bool] = True
    allow:Optional[List[str]] = None

JoinOptions = Dict[str,JoinOptionModel]
class QueryOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    joins: Optional[JoinOptions] = None
    soft_delete: Optional[bool] = None
    filter: Optional[Dict] = None
    sort: Optional[List[QuerySortModel]] = None

class PathParamModel(BaseModel):
    field: str
    type:Literal["str","int"]

class CrudOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dto: DtoModel = None
    serialize: Optional[SerializeModel] = None
    routes: Optional[RoutesModel] = None
    feature: str = None
    query: Optional[QueryOptions] = None
    auth:Optional[AuthModel] = None
    context_vars:Dict = None
    params:Optional[Dict[str,PathParamModel]] = None

class GlobalQueryOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    soft_delete: Optional[bool] = False
    sort: Optional[List[QuerySortModel]] = None

class QueryDelimOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delim: Optional[str] = "||"
    delim_str: Optional[str] = ","



C = TypeVar("C")
class AbstractResponseModel(BaseModel, ABC):
    @classmethod
    @abstractmethod
    def create(
        cls: Type[C],
        *args: Any,
        **kwargs: Any,
    ) -> C:
        raise NotImplementedError
