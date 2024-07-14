import inspect
import json
from typing import Any, Optional, Callable, List, Literal, Type, TypeVar, get_type_hints, Literal, Dict, Annotated
from fastapi import APIRouter, status, Body, Depends, Request, Path, HTTPException, Query
from fastapi_pagination import Page
from functools import wraps
from .enums import RoutesEnum, CrudActions
from .models import CrudOptions, QueryOptions, RoutesModel
from .config import FastAPICrudGlobalConfig
from .helper import filter_to_search

RoutesSchema = [
    {
        "name": RoutesEnum.get_many,
        "path": '/',
        "method": "get"
    },
    {
        "name": RoutesEnum.create_one,
        "path": '/',
        "method": "post"
    },
    {
        "name": RoutesEnum.get_one,
        "path": '/{id}',
        "method": "get"
    },
    {
        "name": RoutesEnum.update_one,
        "path": '/{id}',
        "method": "put"
    },
    {
        "name": RoutesEnum.delete_many,
        "path": '/{ids}',
        "method": "delete"
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
    query: Optional[QueryOptions] = {}
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        return _crud(router, cls,
                     CrudOptions(
                         name=name,
                         feature=feature,
                         dto=dto,
                         serialize=serialize,
                         routes={
                             **FastAPICrudGlobalConfig.routes.model_dump(), **routes},
                         query={**FastAPICrudGlobalConfig.query.model_dump(),
                                **query}
                     )
                     )
    return decorator


def _crud(router: APIRouter, cls: Type[T], options: CrudOptions) -> Type[T]:
    _init_cbv(cls)
    function_members = inspect.getmembers(cls, inspect.isfunction)
    functions_set = set(func for _, func in function_members)
    for func in functions_set:
        _update_route_endpoint_signature(cls, func)

    async def get_many(
        request: Request,
        self=Depends(cls),
        search_json: Optional[str] = Query(None, alias="s"),
        page: int = 1,
        size: int = 30,
        include_deleted: Optional[int] = 0,
        sort: List[str] = Query(None),
        filters: List[str] = Query(None, alias="filter"),
        session=Depends(FastAPICrudGlobalConfig.get_session)
    ):
        search = None
        if search_json:
            try:
                search = json.loads(search_json)
            except:
                search = None
        elif filters:
            search = dict([filter_to_search(filter_item)
                          for filter_item in filters])
        res = await self.service.get_many(
            request,
            page=page,
            size=size,
            joins=options.query.join,
            search=search,
            session=session,
            sorts=sort,
            soft_delete=options.query.soft_delete,
            include_deleted=include_deleted,
            pagination=options.query.pagination
        )
        return res

    async def get_one(request: Request, self=Depends(cls), id: int = Path(..., title="The ID of the item to get")):
        entity = await self.service.get_by_id(id)
        if entity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return entity

    async def delete_many(request: Request, self=Depends(cls), ids: str = Path(..., title="The ID of the item to get")):
        id_list = ids.split(",")
        return await self.service.delete_many(request, id_list, soft_delete=options.query.soft_delete)

    cls.get_many = get_many
    if options.dto and options.dto.create:
        async def create_one(model: Annotated[options.dto.create, Body()], request: Request, self=Depends(cls)):
            entity = await self.service.create_one(request, model)
            return entity
        cls.create_one = create_one

    if options.dto and options.dto.update:
        async def update_one(model: Annotated[options.dto.update, Body()], request: Request, self=Depends(cls), id: int = Path(..., title="The ID of the item to get")):
            return await self.service.update_one(request, id, model)
        cls.update_one = update_one
    cls.delete_many = delete_many
    cls.get_one = get_one

    for schema_item in RoutesSchema:
        router_name = schema_item["name"].value
        if options.routes and options.routes.only:
            if router_name not in options.routes.only:
                continue
        if options.routes and options.routes.exclude:
            if router_name in options.routes.exclude:
                continue
        exist_overrides = list(filter(lambda route: route.path ==
                               schema_item["path"] and schema_item["method"].upper() in route.methods, router.routes))
        if exist_overrides:
            continue
        if schema_item.get("summary"):
            summary = schema_item["summary"].replace(
                "{name}", options.name if options.name else "")
        else:
            summary = None
        endpoint = getattr(cls, router_name)

        def decorator(func: Callable, inner_router_name) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                request = kwargs.get("request")
                request.state.feature = options.feature
                request.state.action = action_map.get(inner_router_name).value
                if FastAPICrudGlobalConfig.interceptor:
                    await FastAPICrudGlobalConfig.interceptor(request)
                endpoint_output = await func(*args, **kwargs)
                return endpoint_output
            return wrapper
        endpoint_wrapper = decorator(endpoint, router_name)

        if router_name == RoutesEnum.get_many:
            if options.query.pagination:
                router.add_api_route(schema_item["path"], endpoint_wrapper, summary=summary, methods=[
                    schema_item["method"]], response_model=Page[options.serialize.get_many])
            else:
                router.add_api_route(schema_item["path"], endpoint_wrapper, summary=summary, methods=[
                                     schema_item["method"]], response_model=List[options.serialize.get_many])
        elif router_name == RoutesEnum.get_one:
            router.add_api_route(schema_item["path"], endpoint_wrapper, summary=summary, methods=[
                                 schema_item["method"]], response_model=options.serialize.get_one or options.serialize.get_many)
        else:
            router.add_api_route(
                schema_item["path"], endpoint_wrapper, summary=summary, methods=[schema_item["method"]])
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
