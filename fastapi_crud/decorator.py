import inspect
from typing import (
    Any,
    Optional,
    Callable,
    List,
    Type,
    TypeVar,
    get_type_hints,
    Annotated,
    cast,
    Union,
    Dict
)
from functools import wraps
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
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from .enums import RoutesEnum, CrudActions
from .models import CrudOptions,AbstractResponseModel,RouteOptions
from .types import RoutesModelDict,QueryOptionsDict,AuthModelDict,DtoModelDict,SerializeModelDict,QuerySortDict
from .config import FastAPICrudGlobalConfig
from .depends import GetSearch,CrudAction,AuthAction,GetSort
from fastapi_pagination import pagination_ctx
from fastapi_pagination.bases import AbstractPage
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

DBSession = Annotated[AsyncSession, Depends(FastAPICrudGlobalConfig.get_db_session)]


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
        "name": RoutesEnum.create_many,
        "path": '/bulk',
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
    routes: Optional[RoutesModelDict] = {},
    dto: DtoModelDict = {},
    serialize: SerializeModelDict = {},
    auth:Optional[AuthModelDict] = {},
    query: Optional[QueryOptionsDict] = {}
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        options = CrudOptions(
            name=name,
            feature=feature,
            dto=dto,
            auth=auth,
            serialize=serialize,
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
    page_schema_type = cast(AbstractPage,FastAPICrudGlobalConfig.page_schema)
    response_schema_type = cast(AbstractResponseModel,FastAPICrudGlobalConfig.response_schema)

    serialize = options.serialize

    async def get_many(
        request: Request,
        self = Depends(cls),
        include_deleted: Optional[int] = 0,
        search: Dict = Depends(GetSearch(option_filter=options.query.filter)),
        sorts: List[QuerySortDict] = Depends(GetSort(option_sort=options.query.sort)),
        db_session:DBSession = None
    ):
        return await self.service.get_many(
            db_session=db_session,
            request=request,
            joins=options.query.joins,
            search=search,
            sorts=sorts,
            soft_delete=options.query.soft_delete,
            include_deleted=include_deleted
        )

    async def get_one(
        request: Request,
        self=Depends(cls),
        id: Union[int,str] = Path(..., title="The ID of the item to get"),
        db_session:DBSession = None
    ):
        entity = await self.service.get(id,db_session=db_session)
        if entity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return entity

    async def create_one(
        model: Annotated[create_schema_type, Body()],
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls),
        db_session:DBSession = None
    ):
        entity = await self.service.create_one(request, model,db_session=db_session,background_tasks = background_tasks)
        return entity

    async def create_many(
        model: Annotated[List[create_schema_type], Body()],
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls),
        db_session:DBSession = None
    ):
        entities = await self.service.create_many(request, model,db_session=db_session,background_tasks = background_tasks)
        return entities

    async def update_one(
        model: Annotated[update_schema_type, Body()],
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls),
        id: int = Path(..., title="The ID of the item to get"),
        db_session:DBSession = None
    ):
        return await self.service.update_one(request, id, model,db_session=db_session,background_tasks=background_tasks)

    async def delete_many(
        request: Request,
        background_tasks:BackgroundTasks,
        self=Depends(cls),
        ids: str = Path(..., title="The ID of the item to get"),
        db_session:DBSession = None
    ):
        id_list = ids.split(",")
        return await self.service.delete_many(
            request,
            id_list,
            soft_delete = options.query.soft_delete,
            background_tasks = background_tasks,
            db_session=db_session
        )

    cls.get_many = get_many
    cls.create_one = create_one
    cls.create_many = create_many
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

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                endpoint_output = await func(*args, **kwargs)
                if response_schema_type:
                    return response_schema_type.create(endpoint_output)
                return endpoint_output
            return wrapper
        endpoint_wrapper = decorator(endpoint)
        response_model = None
        if router_name == RoutesEnum.get_many:
            response_model = Union[page_schema_type[serialize.get_many],List[serialize.get_many]]
        elif router_name == RoutesEnum.get_one:
            response_model = serialize.get_one or serialize.get_many
        if response_schema_type:
            response_model = response_schema_type[response_model]
        route_dependencies = None
        route_options:RouteOptions = getattr(options.routes,router_name)
        if route_options and route_options.dependencies is not None:
            route_dependencies = [*route_options.dependencies]
        if route_dependencies is None and options.routes.dependencies:
            route_dependencies = [*options.routes.dependencies]
        if route_dependencies is None:
            route_dependencies = []
        if router_name == RoutesEnum.get_many:
            route_dependencies.append(Depends(pagination_ctx(FastAPICrudGlobalConfig.page_schema)))
        router.add_api_route(
            schema["path"],
            endpoint_wrapper,
            methods=[schema["method"]],
            dependencies=[
                Depends(CrudAction(options.feature,action_map,router_name)),
                Depends(AuthAction(options.auth)),
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
