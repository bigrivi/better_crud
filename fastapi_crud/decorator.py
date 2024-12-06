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
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from .enums import RoutesEnum
from .models import CrudOptions,AbstractResponseModel,RouteOptions
from .types import RoutesModelDict,QueryOptionsDict,AuthModelDict,DtoModelDict,SerializeModelDict,QuerySortDict,PathParamDict
from .config import FastAPICrudGlobalConfig,RoutesSchema
from .helper import get_serialize_model,get_route_summary
from .depends import GetSearch,CrudAction,StateAction,GetSort
from fastapi_pagination import pagination_ctx
from fastapi_pagination.bases import AbstractPage
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)



T = TypeVar("T")
CONFIG = TypeVar("CONFIG", bound=CrudOptions)


CRUD_CLASS_KEY = "__crud_class__"


def crud(
    router: APIRouter,
    *,
    serialize: SerializeModelDict,
    context_vars:Optional[Dict] = {},
    feature: Optional[str] = "",
    params:Optional[Dict[str,PathParamDict]] = None,
    routes: Optional[RoutesModelDict] = {},
    dto: DtoModelDict = {},
    auth:Optional[AuthModelDict] = {},
    query: Optional[QueryOptionsDict] = {}
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        options = CrudOptions(
            feature=feature,
            dto=dto,
            auth=auth,
            params=params,
            serialize=serialize,
            context_vars=context_vars,
            routes={**FastAPICrudGlobalConfig.routes.model_dump(), **routes},
            query={**FastAPICrudGlobalConfig.query.model_dump(), **query}
        )
        return _crud(router, cls, options)
    return decorator


def _crud(router: APIRouter, cls: Type[T], options: CrudOptions) -> Type[T]:
    _init_cbv(cls)

    create_schema_type = cast(CreateSchemaType, options.dto.create)
    update_schema_type = cast(UpdateSchemaType, options.dto.update)
    page_schema_type = cast(AbstractPage,FastAPICrudGlobalConfig.page_schema)
    response_schema_type = cast(AbstractResponseModel,FastAPICrudGlobalConfig.response_schema)

    serialize = options.serialize

    async def get_many(
        self,
        request: Request,
        include_deleted: Optional[bool] = False,
        search: Dict = Depends(GetSearch(options.query.filter,options.params)),
        sorts: List[QuerySortDict] = Depends(GetSort(options.query.sort)),
    ):
        return await self.service.crud_get_many(
            request=request,
            joins=options.query.joins,
            search=search,
            sorts=sorts,
            soft_delete=options.query.soft_delete,
            include_deleted=include_deleted
        )

    async def get_one(
        self,
        request: Request,
        id: Union[int,str] = Path(..., title="The ID of the item to get")
    ):
        entity = await self.service.crud_get_one(request,id,joins=options.query.joins)
        if entity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return entity

    async def create_one(
        self,
        model: Annotated[create_schema_type, Body()],
        request: Request,
        background_tasks:BackgroundTasks
    ):
        entity = await self.service.crud_create_one(
            request,
            model,
            background_tasks = background_tasks
        )
        return entity

    async def create_many(
        self,
        model: Annotated[List[create_schema_type], Body()],
        request: Request,
        background_tasks:BackgroundTasks
    ):
        entities = await self.service.crud_create_many(
            request,
            model,
            background_tasks = background_tasks
        )
        return entities

    async def update_one(
        self,
        model: Annotated[update_schema_type, Body()],
        request: Request,
        background_tasks:BackgroundTasks,
        id: Union[int,str] = Path(..., title="The ID of the item to get")
    ):
        return await self.service.crud_update_one(
            request,
            id,
            model,
            background_tasks=background_tasks
        )

    async def delete_many(
        self,
        request: Request,
        background_tasks:BackgroundTasks,
        ids: str = Path(..., title="The ID of the item to get")
    ):
        id_list = ids.split(",")
        return await self.service.crud_delete_many(
            request,
            id_list,
            soft_delete = options.query.soft_delete,
            background_tasks = background_tasks
        )

    cls.get_many = get_many
    cls.create_one = create_one
    cls.create_many = create_many
    cls.update_one = update_one
    cls.delete_many = delete_many
    cls.get_one = get_one

    function_members = inspect.getmembers(cls, inspect.isfunction)
    functions_set = set(func for _, func in function_members)
    for func in functions_set:
        _update_route_endpoint_signature(cls, func,options)

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
                if options.params:
                    for key in options.params.keys():
                        kwargs.pop(key)
                endpoint_output = await func(*args, **kwargs)
                if response_schema_type:
                    return response_schema_type.create(endpoint_output)
                return endpoint_output
            return wrapper
        endpoint_wrapper = decorator(endpoint)
        response_model = get_serialize_model(serialize,router_name)
        if router_name == RoutesEnum.get_many:
            response_model = Union[page_schema_type[response_model],List[response_model]]
        elif router_name in [RoutesEnum.create_many,RoutesEnum.delete_many]:
            response_model = List[response_model]

        if response_schema_type:
            response_model = response_schema_type[response_model]

        dependencies = None
        route_options:RouteOptions = getattr(options.routes,router_name,None)
        if route_options and route_options.dependencies is not None:
            dependencies = [*route_options.dependencies]
        if dependencies is None and options.routes.dependencies:
            dependencies = [*options.routes.dependencies]

        if dependencies is None:
            dependencies = []
        if router_name == RoutesEnum.get_many:
            dependencies.append(Depends(pagination_ctx(FastAPICrudGlobalConfig.page_schema)))
        router.add_api_route(
            schema["path"],
            endpoint_wrapper,
            methods=[schema["method"]],
            summary=get_route_summary(route_options,options.context_vars),
            dependencies=[
                Depends(CrudAction(options.feature,FastAPICrudGlobalConfig.action_map,router_name)),
                Depends(StateAction(options.auth,options.params)),
                *dependencies
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


def _update_route_endpoint_signature(cls: Type[Any], endpoint: Callable,options:CrudOptions) -> None:
    old_signature = inspect.signature(endpoint)
    old_parameters: List[inspect.Parameter] = list(
        old_signature.parameters.values())
    old_first_parameter = old_parameters[0]
    new_first_parameter = old_first_parameter.replace(default=Depends(cls))
    new_parameters = [new_first_parameter] + [
        parameter.replace(kind=inspect.Parameter.KEYWORD_ONLY) for parameter in old_parameters[1:]
    ]
    if options.params:
        for key,param in options.params.items():
            new_param = inspect.Parameter(key,
                                        inspect.Parameter.KEYWORD_ONLY,
                                        annotation=Annotated[int if param.type=="int" else str, Path(title="")])
            new_parameters.append(new_param)
    new_signature = old_signature.replace(parameters=new_parameters)
    setattr(endpoint, "__signature__", new_signature)
