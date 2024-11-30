from typing import List, Optional, Any, Dict,Callable,Sequence,TypeVar,Generic,Type
from abc import ABC,abstractmethod
from pydantic import BaseModel,Field,ConfigDict,SerializeAsAny
from .enums import RoutesEnum,QuerySortType

class DtoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    create: Any = None
    update: Any = None

class AuthModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    property_:str = Field(default=None, alias='property')
    filter_: Callable[[Any], Dict] = Field(default=None, alias='filter')
    persist: Callable[[Any], Dict] = None

class SerializeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    get_many: Optional[Any] = None
    get_one: Optional[Any] = None
    create_one: Optional[Any] = None
    create_many: Optional[Any] = None
    update_one: Optional[Any] = None
    delete_many: Optional[Any] = None

class RouteOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dependencies: Optional[Sequence[Any]] = None,


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

class QueryOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    joins: Optional[List[Any]] = None
    soft_delete: Optional[bool] = None
    filter: Optional[Dict] = None
    sort: Optional[List[QuerySortModel]] = None



class CrudOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dto: DtoModel = None
    serialize: Optional[SerializeModel] = None
    routes: Optional[RoutesModel] = None
    name: str = None
    feature: str = None
    query: Optional[QueryOptions] = None
    auth:Optional[AuthModel] = None

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
