from pydantic import BaseModel
from typing import List, Optional, Any,Dict
from .enums import RoutesEnum
from sqlmodel import SQLModel,Relationship
from typing_extensions import TypedDict

class NodeDict(TypedDict):
    id: str
    value: int
    parent: 'NodeDict | None'

class DtoModel(BaseModel):
    create: Any = None
    update: Any = None


class SerializeModel(BaseModel):
    get_many: Any = None
    get_one: Any = None
    create_one:Any = None


class RoutesModel(BaseModel):
    only: Optional[List[RoutesEnum]] = None
    exclude: Optional[List[RoutesEnum]] = None

class QueryOptions(BaseModel):
    join: Optional[List[Any]] = None
    soft_delete: Optional[bool] = None
    pagination : Optional[bool] = True

class CrudOptions(BaseModel):
    dto: DtoModel = None
    serialize: Optional[SerializeModel] = None
    routes: Optional[RoutesModel] = None
    name:str = None
    feature:str = None
    query:Optional[QueryOptions] = None


class GlobalQueryOptions(BaseModel):
    soft_delete: Optional[bool] = False
    pagination : Optional[bool] = True

