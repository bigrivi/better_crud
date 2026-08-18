import inspect
import warnings
from typing import (
    Any,
    Callable,
    List,
    Tuple,
    Type,
    TypeVar,
    Annotated,
    cast,
    Union,
    Dict,
    Literal,
    Optional,
    get_type_hints,
    get_origin,
    get_args,
)
try:
    from types import UnionType  # Python 3.10+
except ImportError:  # pragma: no cover
    UnionType = None
from functools import wraps
from fastapi import (
    APIRouter,
    status,
    Body,
    Depends,
    Request,
    Path,
    Query,
    HTTPException,
    BackgroundTasks
)
from fastapi.params import Depends as DependsParam
from .enums import RoutesEnum
from .models import (
    CrudOptions,
    AbstractResponseModel,
    RouteOptions,
    JoinOptions
)
from .types import QuerySortDict, CreateSchemaType, UpdateSchemaType
from .config import BetterCrudGlobalConfig, RoutesSchema
from .helper import get_serialize_model, get_route_summary
from .depends import (
    CrudAction,
    StateAction,
    GetQuerySearch,
    GetQueryLoads,
    GetQuerySorts,
    GetQueryJoins,
)
from fastapi_pagination import pagination_ctx
from fastapi_pagination.bases import AbstractPage
from .pagination import PageAlways, PageOptional
from .exceptions import NotFoundException

T = TypeVar("T")
CRUD_CLASS_KEY = "__crud_class__"
UNBIND_KIND_TYPE = (
    inspect.Parameter.VAR_POSITIONAL,
    inspect.Parameter.VAR_KEYWORD
)
INCLUDE_DELETED_KEY = "include_deleted"
CRUD_ACTION_KEY = "__crud_action__"

_crud_routes: List[Tuple[APIRouter, Type, CrudOptions]] = []


def crud_action(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    *,
    response_model: Optional[Any] = None,
    action: Optional[str] = None,
    summary: Optional[str] = None,
    dependencies: Optional[List[Any]] = None,
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        setattr(func, CRUD_ACTION_KEY, {
            "method": method,
            "path": path,
            "response_model": response_model,
            "action": action,
            "summary": summary,
            "dependencies": dependencies,
        })
        return func
    return decorator


def _extract_inner_model(hint: Any) -> Optional[Any]:
    """Extract inner model from a return type annotation.

    - Response shell (AbstractResponseModel subclass, e.g. ResponseModel[X]) -> X
    - Optional[X] / Union[X, None] -> preserved as-is so None responses stay
      valid, unless the non-None branch is itself a response shell (then its
      inner model is used)
    - Container types (List[X] / Page[X]) are preserved as-is
    - None / NoneType / non-parameterized response model -> None (no data)
    """
    if hint is None or hint is type(None):
        return None
    pydantic_args = getattr(hint, "__pydantic_generic_metadata__", {}).get("args", ())
    if pydantic_args and len(pydantic_args) == 1:
        inner = pydantic_args[0]
        origin_cls = getattr(hint, "__pydantic_generic_metadata__", {}).get("origin")
        if isinstance(origin_cls, type) and issubclass(origin_cls, AbstractResponseModel):
            return inner
        return hint
    if isinstance(hint, type) and hasattr(hint, "__pydantic_generic_metadata__"):
        if hint.__pydantic_generic_metadata__["parameters"]:
            return None
        return hint
    origin = get_origin(hint)
    if origin is not None:
        args = get_args(hint)
        if origin is Union or (UnionType is not None and origin is UnionType):
            non_none = [arg for arg in args if arg is not type(None)]
            if len(non_none) == 1:
                inner = non_none[0]
                inner_args = getattr(
                    inner, "__pydantic_generic_metadata__", {}).get("args", ())
                origin_cls = getattr(
                    inner, "__pydantic_generic_metadata__", {}).get("origin")
                if (inner_args and len(inner_args) == 1
                        and isinstance(origin_cls, type)
                        and issubclass(origin_cls, AbstractResponseModel)):
                    return inner_args[0]
                return hint
            return None
        if args and len(args) == 1:
            return hint
        return None
    return hint


def _restore_depends(dep: Any) -> Any:
    if isinstance(dep, dict) and "dependency" in dep:
        return DependsParam(
            dep["dependency"],
            use_cache=dep.get("use_cache", True),
            scope=dep.get("scope"),
        )
    return dep


def crud_routes_factory(router: APIRouter, cls: Type[T], options: CrudOptions) -> Type[T]:
    create_schema_type = cast(CreateSchemaType, options.dto.create)
    update_schema_type = cast(UpdateSchemaType, options.dto.update)
    page_schema_type = cast(AbstractPage, BetterCrudGlobalConfig.page_schema)
    response_schema_type = cast(
        AbstractResponseModel,
        BetterCrudGlobalConfig.response_schema
    )

    serialize = options.serialize
    _crud_routes.append((router, cls, options))
    pagination_mode = options.pagination_mode or BetterCrudGlobalConfig.pagination_mode

    async def get_many(
        self,
        request: Request,
        search: Dict = Depends(
            GetQuerySearch(options.query.filter)
        ),
        joins: JoinOptions = Depends(
            GetQueryJoins(options.query.joins)
        ),
        sorts: List[QuerySortDict] = Depends(
            GetQuerySorts(options.query.sort)),
    ):
        return await self.service.crud_get_many(
            request=request,
            joins=joins,
            search=search,
            sorts=sorts,
            soft_delete=options.query.soft_delete,
            include_deleted=request.query_params.get(
                INCLUDE_DELETED_KEY) == "true" if options.query.allow_include_deleted else False
        )

    async def get_one(
        self,
        request: Request,
        joins: JoinOptions = Depends(
            GetQueryLoads(options.query.joins)
        ),
        id: Union[int, str] = Path(..., title="The ID of the item to get")
    ):
        try:
            return await self.service.crud_get_one(
                request,
                id,
                joins=joins
            )
        except NotFoundException:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No data found"
            )

    async def recover_one(
        self,
        request: Request,
        id: Union[int, str] = Path(..., title="The ID of the item to recover")
    ):
        try:
            return await self.service.crud_recover_one(
                request,
                id,
            )
        except NotFoundException:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No data found"
            )

    async def create_one(
        self,
        model: Annotated[create_schema_type, Body()],  # type: ignore
        request: Request,
        background_tasks: BackgroundTasks
    ):
        return await self.service.crud_create_one(
            request,
            model,
            background_tasks=background_tasks
        )

    async def create_many(
        self,
        model: Annotated[List[create_schema_type], Body()],  # type: ignore
        request: Request,
        background_tasks: BackgroundTasks
    ):
        return await self.service.crud_create_many(
            request,
            model,
            background_tasks=background_tasks
        )

    async def update_one(
        self,
        model: Annotated[update_schema_type, Body()],  # type: ignore
        request: Request,
        background_tasks: BackgroundTasks,
        id: Union[int, str] = Path(..., title="The ID of the item to get")
    ):
        try:
            return await self.service.crud_update_one(
                request,
                id,
                model,
                background_tasks=background_tasks
            )
        except NotFoundException:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No data found"
            )

    async def update_many(
        self,
        request: Request,
        models: Annotated[List[update_schema_type], Body()],  # type: ignore
        background_tasks: BackgroundTasks,
        ids: str = Path(...,
                        description="Primary key values, use commas to separate multiple values")
    ):
        id_list = ids.split(",")
        if len(id_list) != len(models):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="The id and payload length do not match"
            )
        try:
            return await self.service.crud_update_many(
                request,
                id_list,
                models,
                background_tasks=background_tasks
            )
        except NotFoundException:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No data found"
            )

    async def delete_many(
        self,
        request: Request,
        background_tasks: BackgroundTasks,
        ids: str = Path(...,
                        description="Primary key values, use commas to separate multiple values")
    ):
        id_list = ids.split(",")
        try:
            return await self.service.crud_delete_many(
                request,
                id_list,
                soft_delete=options.query.soft_delete,
                background_tasks=background_tasks
            )
        except NotFoundException:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No data found"
            )

    cls.get_many = get_many
    cls.create_one = create_one
    cls.create_many = create_many
    cls.update_one = update_one
    cls.update_many = update_many
    cls.delete_many = delete_many
    cls.get_one = get_one
    if options.query.soft_delete and options.query.allow_recover:
        cls.recover_one = recover_one

    function_members = inspect.getmembers(cls, inspect.isfunction)
    functions_set = set(func for _, func in function_members)
    for func in functions_set:
        _update_route_endpoint_signature(cls, func, options)

    for name, member in inspect.getmembers(cls, inspect.isfunction):
        action_meta = getattr(member, CRUD_ACTION_KEY, None)
        if not action_meta:
            continue
        action_path = action_meta["path"]
        action_method = action_meta["method"]
        overrides = list(filter(lambda route: route.path ==
                         action_path and action_method in route.methods, router.routes))
        if overrides:
            continue
        endpoint = getattr(cls, name)

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                if options.params:
                    for key in options.params.keys():
                        kwargs.pop(key)
                endpoint_output = await func(*args, **kwargs)
                if response_schema_type and not isinstance(endpoint_output, response_schema_type):
                    return response_schema_type.create(endpoint_output)
                return endpoint_output
            return wrapper
        endpoint_wrapper = decorator(endpoint)

        action_response_model = action_meta["response_model"]
        if response_schema_type:
            if action_response_model is None:
                try:
                    hint = get_type_hints(endpoint).get("return", None)
                    action_response_model = _extract_inner_model(hint)
                except (NameError, TypeError) as e:
                    # Annotation may be unresolvable at import time (e.g.
                    # `from __future__ import annotations` + a local model).
                    # Fall back to the bare response_schema (data unconstrained)
                    # rather than crash the app at route registration.
                    warnings.warn(
                        "Failed to resolve return annotation for %s: %s. "
                        "Falling back to the bare response schema."
                        % (endpoint.__qualname__, e)
                    )
                if action_response_model is None:
                    response_model = response_schema_type
                else:
                    response_model = response_schema_type[action_response_model]
            else:
                # Explicit response_model is the final response shape; use as-is.
                response_model = action_response_model
        else:
            response_model = action_response_model

        action_dependencies = None
        if action_meta["dependencies"]:
            action_dependencies = [
                _restore_depends(dep) for dep in action_meta["dependencies"]]
        if action_dependencies is None:
            action_dependencies = []

        router.add_api_route(
            action_path,
            endpoint_wrapper,
            methods=[action_method],
            summary=action_meta["summary"],
            dependencies=[
                Depends(CrudAction(
                    options.feature,
                    action_meta["action"] or name,
                    BetterCrudGlobalConfig.action_map,
                    name
                )),
                *action_dependencies,
                Depends(StateAction(options.auth, options.params)),
            ],
            response_model=response_model,
        )

    for schema in RoutesSchema:
        router_name = schema["name"].value
        path = schema["path"]
        method = schema["method"]
        if options.routes and options.routes.only is not None:
            if router_name not in options.routes.only:
                continue
        if options.routes and options.routes.exclude:
            if router_name in options.routes.exclude:
                continue
        if router_name == RoutesEnum.recover_one:
            if not (options.query.soft_delete and options.query.allow_recover):
                continue
        overrides = list(filter(lambda route: route.path ==
                         path and method in route.methods, router.routes))
        if overrides:
            continue
        endpoint = getattr(cls, router_name)

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                if options.params:
                    for key in options.params.keys():
                        kwargs.pop(key)
                if INCLUDE_DELETED_KEY in kwargs:
                    kwargs.pop(INCLUDE_DELETED_KEY)
                endpoint_output = await func(*args, **kwargs)
                if response_schema_type:
                    return response_schema_type.create(endpoint_output)
                return endpoint_output
            return wrapper
        endpoint_wrapper = decorator(endpoint)
        response_model = get_serialize_model(serialize, router_name)
        if router_name == RoutesEnum.get_many:
            response_model = Union[
                page_schema_type[response_model],
                List[response_model]
            ]
        elif router_name in [RoutesEnum.create_many, RoutesEnum.update_many, RoutesEnum.delete_many]:
            response_model = List[response_model]

        if response_schema_type:
            response_model = response_schema_type[response_model]

        dependencies = None
        route_options: RouteOptions = getattr(
            options.routes,
            router_name,
            None
        )
        if route_options and route_options.dependencies is not None:
            dependencies = [*route_options.dependencies]
        if dependencies is None and options.routes.dependencies:
            dependencies = [*options.routes.dependencies]

        # pydantic model_dump() serializes fastapi Depends instances into
        # dicts ({"dependency": ..., "use_cache": ..., "scope": ...}); restore
        # them so that fastapi >=0.141 route registration works again.
        if dependencies:
            dependencies = [_restore_depends(dep) for dep in dependencies]

        if dependencies is None:
            dependencies = []
        if router_name == RoutesEnum.get_many:
            if pagination_mode == "always":
                page_cls = PageAlways
            elif pagination_mode == "optional":
                page_cls = PageOptional
            else:
                page_cls = None
            if page_cls is not None:
                dependencies.append(
                    Depends(
                        pagination_ctx(page_cls)
                    )
                )
        router.add_api_route(
            path,
            endpoint_wrapper,
            methods=[method],
            summary=get_route_summary(route_options, options.summary_vars),
            dependencies=[
                Depends(CrudAction(
                    options.feature,
                    route_options.action if route_options else None,
                    BetterCrudGlobalConfig.action_map,
                    router_name
                )),
                *dependencies,
                Depends(StateAction(options.auth, options.params)),
            ],
            response_model=response_model,
        )
    return cls


def _update_route_endpoint_signature(
    cls: Type[Any],
    endpoint: Callable,
    options: CrudOptions
) -> None:
    old_signature = inspect.signature(endpoint)
    old_parameters: List[inspect.Parameter] = list(
        old_signature.parameters.values())
    if not old_parameters:
        return
    old_first_parameter = old_parameters[0]
    new_first_parameter = old_first_parameter.replace(default=Depends(cls))
    new_parameters = [new_first_parameter] + [
        parameter.replace(kind=inspect.Parameter.KEYWORD_ONLY)
        for parameter in old_parameters[1:]
    ]
    is_crud_route = endpoint in [
        cls.get_many,
        cls.create_one,
        cls.create_many,
        cls.update_one,
        cls.update_many,
        cls.delete_many,
        cls.get_one
    ]
    if is_crud_route and options.params:
        for key, param in options.params.items():
            new_param = inspect.Parameter(
                key,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[
                    int if param.type == "int" else str, Path(title="")
                ]
            )
            new_parameters.append(new_param)
    if endpoint == cls.get_many:
        if options.query.allow_include_deleted:
            new_param = inspect.Parameter(
                INCLUDE_DELETED_KEY,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[bool, Query(
                    description="include deleted data")]
            )
            new_parameters.append(new_param)

    new_signature = old_signature.replace(parameters=new_parameters)
    setattr(endpoint, "__signature__", new_signature)


def get_crud_routes():
    return _crud_routes
