import inspect
from typing import (
    Any,
    Optional,
    Callable,
    List,
    Type,
    TypeVar,
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
    BackgroundTasks
)
from pydantic import BaseModel
from .enums import RoutesEnum
from .models import (
    CrudOptions,
    AbstractResponseModel,
    RouteOptions,
    JoinOptions
)
from .types import QuerySortDict
from .config import FastAPICrudGlobalConfig, RoutesSchema
from .helper import get_serialize_model, get_route_summary
from .depends import (
    CrudAction,
    StateAction,
    DependGetJoins,
    DependGetSearch,
    DependGetLoads,
    DependGetSort
)
from fastapi_pagination import pagination_ctx
from fastapi_pagination.bases import AbstractPage
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
T = TypeVar("T")
CONFIG = TypeVar("CONFIG", bound=CrudOptions)
CRUD_CLASS_KEY = "__crud_class__"
UNBIND_KIND_TYPE = (
    inspect.Parameter.VAR_POSITIONAL,
    inspect.Parameter.VAR_KEYWORD
)


def crud_routes_factory(router: APIRouter, cls: Type[T], options: CrudOptions) -> Type[T]:
    create_schema_type = cast(CreateSchemaType, options.dto.create)
    update_schema_type = cast(UpdateSchemaType, options.dto.update)
    page_schema_type = cast(AbstractPage, FastAPICrudGlobalConfig.page_schema)
    response_schema_type = cast(
        AbstractResponseModel,
        FastAPICrudGlobalConfig.response_schema
    )

    serialize = options.serialize

    async def get_many(
        self,
        request: Request,
        include_deleted: Optional[bool] = False,
        search: Dict = Depends(
            DependGetSearch(options.query.filter, options.params)
        ),
        joins: JoinOptions = Depends(
            DependGetJoins(options.query.joins)
        ),
        sorts: List[QuerySortDict] = Depends(
            DependGetSort(options.query.sort)),
    ):
        print(self.service)
        return await self.service.crud_get_many(
            request=request,
            joins=joins,
            search=search,
            sorts=sorts,
            soft_delete=options.query.soft_delete,
            include_deleted=include_deleted
        )

    async def get_one(
        self,
        request: Request,
        joins: JoinOptions = Depends(
            DependGetLoads(options.query.joins)
        ),
        id: Union[int, str] = Path(..., title="The ID of the item to get")
    ):
        print(self.service)
        entity = await self.service.crud_get_one(
            request,
            id,
            joins=joins
        )
        if entity is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No data found"
            )
        return entity

    async def create_one(
        self,
        model: Annotated[create_schema_type, Body()],
        request: Request,
        background_tasks: BackgroundTasks
    ):
        entity = await self.service.crud_create_one(
            request,
            model,
            background_tasks=background_tasks
        )
        return entity

    async def create_many(
        self,
        model: Annotated[List[create_schema_type], Body()],
        request: Request,
        background_tasks: BackgroundTasks
    ):
        entities = await self.service.crud_create_many(
            request,
            model,
            background_tasks=background_tasks
        )
        return entities

    async def update_one(
        self,
        model: Annotated[update_schema_type, Body()],
        request: Request,
        background_tasks: BackgroundTasks,
        id: Union[int, str] = Path(..., title="The ID of the item to get")
    ):
        return await self.service.crud_update_one(
            request,
            id,
            model,
            background_tasks=background_tasks
        )

    async def update_many(
        self,
        request: Request,
        models: Annotated[List[update_schema_type], Body()],
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
        return await self.service.crud_update_many(
            request,
            id_list,
            models,
            background_tasks=background_tasks
        )

    async def delete_many(
        self,
        request: Request,
        background_tasks: BackgroundTasks,
        ids: str = Path(...,
                        description="Primary key values, use commas to separate multiple values")
    ):
        id_list = ids.split(",")
        return await self.service.crud_delete_many(
            request,
            id_list,
            soft_delete=options.query.soft_delete,
            background_tasks=background_tasks
        )

    cls.get_many = get_many
    cls.create_one = create_one
    cls.create_many = create_many
    cls.update_one = update_one
    cls.update_many = update_many
    cls.delete_many = delete_many
    cls.get_one = get_one

    function_members = inspect.getmembers(cls, inspect.isfunction)
    functions_set = set(func for _, func in function_members)
    for func in functions_set:
        _update_route_endpoint_signature(cls, func, options)

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

        if dependencies is None:
            dependencies = []
        if router_name == RoutesEnum.get_many:
            dependencies.append(
                Depends(
                    pagination_ctx(FastAPICrudGlobalConfig.page_schema)
                )
            )
        router.add_api_route(
            schema["path"],
            endpoint_wrapper,
            methods=[schema["method"]],
            summary=get_route_summary(route_options, options.summary_vars),
            dependencies=[
                Depends(CrudAction(
                    options.feature,
                    FastAPICrudGlobalConfig.action_map,
                    router_name
                )),
                *dependencies,
                Depends(StateAction(options.auth, options.params)),
            ],
            response_model=response_model,
        )
    for route in router.routes:
        if route.path == "/":
            route.path = route.path.lstrip('/')
    return cls


def _update_route_endpoint_signature(
    cls: Type[Any],
    endpoint: Callable,
    options: CrudOptions
) -> None:
    old_signature = inspect.signature(endpoint)
    old_parameters: List[inspect.Parameter] = list(
        old_signature.parameters.values())
    old_first_parameter = old_parameters[0]
    new_first_parameter = old_first_parameter.replace(default=Depends(cls))
    new_parameters = [new_first_parameter] + [
        parameter.replace(kind=inspect.Parameter.KEYWORD_ONLY)
        for parameter in old_parameters[1:]
    ]
    if options.params:
        for key, param in options.params.items():
            new_param = inspect.Parameter(
                key,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[
                    int if param.type == "int" else str, Path(title="")
                ]
            )
            new_parameters.append(new_param)
    new_signature = old_signature.replace(parameters=new_parameters)
    setattr(endpoint, "__signature__", new_signature)
