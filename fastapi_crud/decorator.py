import inspect
from typing import (
    Any,
    Optional,
    Callable,
    List,
    Type,
    TypeVar,
    get_type_hints,
    Literal,
    Dict,
    Annotated,
    cast,
    Sequence,
    Union
)
from fastapi import (
    APIRouter,
    status,
    Body,
    Depends,
    Request,
    Path,
    HTTPException,
    Query,
    BackgroundTasks,
    params
)
from fastapi_pagination import Page
from pydantic import BaseModel
from functools import wraps
from .enums import RoutesEnum, CrudActions
from .models import CrudOptions, QueryOptions, RoutesModel, RouteOptions
from .config import FastAPICrudGlobalConfig
from .depends import GetQuerySearch,CrudAction,AuthAction


CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


RoutesSchema = [
    {
        "name": RoutesEnum.get_many,
        "path": '/',
        "method": "GET"
    },
    {
        "name": RoutesEnum.create_one,
        "path": '/',
        "method": "POST"
    },
    {
        "name": RoutesEnum.get_one,
        "path": '/{id}',
        "method": "GET"
    },
    {
        "name": RoutesEnum.update_one,
        "path": '/{id}',
        "method": "PUT"
    },
    {
        "name": RoutesEnum.delete_many,
        "path": '/{ids}',
        "method": "DELETE"
    }
]

action_map = {
    RoutesEnum.get_many.value: CrudActions.ReadAll,
    RoutesEnum.get_one.value: CrudActions.ReadOne,
    RoutesEnum.create_one.value: CrudActions.CreateOne,
    RoutesEnum.update_one.value: CrudActions.UpdateOne,
    RoutesEnum.delete_many.value: CrudActions.DeleteMany
}

T = TypeVar("T")
CONFIG = TypeVar("CONFIG", bound=CrudOptions)


CRUD_CLASS_KEY = "__crud_class__"


def crud(
    router: APIRouter,
    name: Optional[str] = "",
    feature: Optional[str] = "",
    routes: Optional[RoutesModel] = {},
    dto: Optional[Dict[
        Literal["create", "update"],
        Any,
    ]] = None,
    serialize: Optional[Dict[
        Literal["get_many", "get_one"],
        Any,
    ]] = None,
    dependencies: Optional[Sequence[params.Depends]] = None,
    auth:Optional[Dict] = None,
    query: Optional[QueryOptions] = {}
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        options = CrudOptions(
            name=name,
            feature=feature,
            dto=dto,
            auth=auth,
            serialize=serialize,
            dependencies=dependencies,
            routes={**FastAPICrudGlobalConfig.routes.model_dump(), **routes},
            query={**FastAPICrudGlobalConfig.query.model_dump(), **query}
        )
        return _crud(router, cls, options)
    return decorator


def _crud(router: APIRouter, cls: Type[T], options: CrudOptions) -> Type[T]:
    _init_cbv(cls)
    function_members = inspect.getmembers(cls, inspect.isfunction)
    functions_set = set(func for _, func in function_members)
    for func in functions_set:
        _update_route_endpoint_signature(cls, func)

    create_schema_type = cast(CreateSchemaType, options.dto.create)
    update_schema_type = cast(UpdateSchemaType, options.dto.update)
    serialize = options.serialize

    async def get_many(
        request: Request,
        self = Depends(cls),
        page: Optional[int] = None,
        size: Optional[int] = None,
        include_deleted: Optional[int] = 0,
        sort: List[str] = Query(None),
        search: dict = Depends(GetQuerySearch(option_filter=options.query.filter)),
        session = Depends(FastAPICrudGlobalConfig.get_session)
    ):
        return await self.service.get_many(
            request,
            page=page,
            size=size,
            joins=options.query.joins,
            search=search,
            session=session,
            sorts=sort,
            soft_delete=options.query.soft_delete,
            include_deleted=include_deleted
        )

    async def get_one(
        request: Request,
        self=Depends(cls),
        id: int = Path(..., title="The ID of the item to get")
    ):
        entity = await self.service.get_by_id(id)
        if entity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return entity

    async def create_one(
        model: Annotated[create_schema_type, Body()],
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls)
    ):
        entity = await self.service.create_one(request, model,background_tasks = background_tasks)
        return entity

    async def update_one(
        model: Annotated[update_schema_type, Body()],
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls),
        id: int = Path(..., title="The ID of the item to get")
    ):
        return await self.service.update_one(request, id, model,background_tasks=background_tasks)

    async def delete_many(
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls),
        ids: str = Path(..., title="The ID of the item to get")
    ):
        id_list = ids.split(",")
        return await self.service.delete_many(
            request,
            id_list,
            soft_delete = options.query.soft_delete,
            background_tasks = background_tasks
        )

    cls.get_many = get_many
    cls.create_one = create_one
    cls.update_one = update_one
    cls.delete_many = delete_many
    cls.get_one = get_one

    for schema in RoutesSchema:
        router_name = schema["name"].value
        path = schema["path"]
        method = schema["method"]
        if options.routes and options.routes.only:
            if router_name not in options.routes.only:
                continue
        if options.routes and options.routes.exclude:
            if router_name in options.routes.exclude:
                continue
        overrides = list(filter(lambda route: route.path ==
                         path and method in route.methods, router.routes))
        if overrides:
            continue
        endpoint = getattr(cls, router_name)
        response_model = None
        if router_name == RoutesEnum.get_many:
            response_model = Union[Page[serialize.get_many],List[serialize.get_many]]
        elif router_name == RoutesEnum.get_one:
            response_model = serialize.get_one or serialize.get_many
        route_dependencies = []
        route_options:RouteOptions = getattr(options.routes,router_name)
        if route_options and route_options.dependencies:
            route_dependencies = route_options.dependencies
        router.add_api_route(
            schema["path"],
            endpoint,
            methods=[schema["method"]],
            dependencies=[
                Depends(CrudAction(options.feature,action_map,router_name)),
                Depends(AuthAction(options.auth)),
                *options.routes.dependencies,
                *route_dependencies
            ],
            response_model=response_model,
        )
    for route in router.routes:
        if route.path == "/":
            route.path = route.path.lstrip('/')
    return cls


def _init_cbv(cls: Type[Any]) -> None:
    if getattr(cls, CRUD_CLASS_KEY, False):
        return
    old_init: Callable[..., Any] = cls.__init__
    old_signature = inspect.signature(old_init)
    old_parameters = list(old_signature.parameters.values())[
        1:]
    new_parameters = [
        x for x in old_parameters if x.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    dependency_names: List[str] = []
    for name, hint in get_type_hints(cls).items():
        parameter_kwargs = {"default": getattr(cls, name, Ellipsis)}
        dependency_names.append(name)
        new_parameters.append(
            inspect.Parameter(
                name=name, kind=inspect.Parameter.KEYWORD_ONLY, annotation=hint, **parameter_kwargs)
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


def _update_route_endpoint_signature(cls: Type[Any], endpoint: Callable) -> None:
    old_signature = inspect.signature(endpoint)
    old_parameters: List[inspect.Parameter] = list(
        old_signature.parameters.values())
    old_first_parameter = old_parameters[0]
    new_first_parameter = old_first_parameter.replace(default=Depends(cls))
    new_parameters = [new_first_parameter] + [
        parameter.replace(kind=inspect.Parameter.KEYWORD_ONLY) for parameter in old_parameters[1:]
    ]
    new_signature = old_signature.replace(parameters=new_parameters)
    setattr(endpoint, "__signature__", new_signature)
