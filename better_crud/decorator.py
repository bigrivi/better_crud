import inspect
from typing import (
    Any,
    Optional,
    Callable,
    List,
    Type,
    TypeVar,
    get_type_hints,
    Dict
)
from fastapi import APIRouter
from pydantic import BaseModel
from .models import (
    CrudOptions,
)
from .types import (
    RoutesModelDict,
    QueryOptionsDict,
    AuthModelDict,
    DtoModelDict,
    SerializeModelDict,
    PathParamDict
)
from .config import BetterCrudGlobalConfig
from .factory import crud_routes_factory
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
T = TypeVar("T")
CONFIG = TypeVar("CONFIG", bound=CrudOptions)
CRUD_CLASS_KEY = "__crud_class__"
UNBIND_KIND_TYPE = (
    inspect.Parameter.VAR_POSITIONAL,
    inspect.Parameter.VAR_KEYWORD
)


def crud(
    router: APIRouter,
    *,
    serialize: SerializeModelDict,
    params: Optional[Dict[str, PathParamDict]] = None,
    routes: Optional[RoutesModelDict] = {},
    dto: DtoModelDict = {},
    auth: Optional[AuthModelDict] = {},
    query: Optional[QueryOptionsDict] = {},
    summary_vars: Optional[Dict] = {},
    feature: Optional[str] = "",
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        options = CrudOptions(
            feature=feature,
            dto=dto,
            auth=auth,
            params=params,
            serialize=serialize,
            summary_vars=summary_vars,
            routes={**BetterCrudGlobalConfig.routes.model_dump(), **routes},
            query={**BetterCrudGlobalConfig.query.model_dump(), **query}
        )
        _init_cbv(cls)
        return crud_routes_factory(router, cls, options)
    return decorator


def _init_cbv(cls: Type[Any]) -> None:
    if getattr(cls, CRUD_CLASS_KEY, False):
        return
    old_init: Callable[..., Any] = cls.__init__
    old_signature = inspect.signature(old_init)
    old_parameters = list(old_signature.parameters.values())[
        1:]
    new_parameters = [
        x for x in old_parameters if x.kind not in UNBIND_KIND_TYPE
    ]
    dependency_names: List[str] = []
    for name, hint in get_type_hints(cls).items():
        parameter_kwargs = {"default": getattr(cls, name, Ellipsis)}
        dependency_names.append(name)
        new_parameters.append(
            inspect.Parameter(
                name=name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                annotation=hint,
                **parameter_kwargs
            )
        )
    new_signature = old_signature.replace(parameters=new_parameters)

    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        for dep_name in dependency_names:
            dep_value = kwargs.pop(dep_name)
            setattr(self, dep_name, dep_value)
        old_init(self, *args, **kwargs)

    setattr(cls, "__signature__", new_signature)
    setattr(cls, "__init__", new_init)
    setattr(cls, CRUD_CLASS_KEY, True)
