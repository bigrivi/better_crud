In some cases, the query conditions are so complex that they are difficult to express in the way that the JSON filtering is currently provided.
For example, we might encounter conditional queries based on cases
```python
from sqlalchemy import case
case_stmt = case((SomeModel.user_pick_type == 1,
    SomeModel.user_id == user_id),
    else_=SomeModel.position_id.in_(position_ids))
```
At this point, we need to override the default behavior completely

First, let's rewrite the routing method
```python hl_lines="6-8 14-18"

from better_crud import crud, Page, GetQuerySearch, GetQuerySorts, QuerySortDict
from fastapi_pagination import pagination_ctx
from app.models.user import UserPublic, UserCreate, UserUpdate
from app.services.user import UserService

@crud(
    router,
    dto={"create": UserCreate, "update": UserUpdate},
    routes={
        "exclude": ["get_many"]
    },
    serialize={"base": UserPublic}
)

class UserController():
    service: UserService = Depends(UserService)
    @router.get("", dependencies=[Depends(pagination_ctx(Page)), DependsJwtAuth])
    async def get_list(
        self,
        request: Request,
        search: Dict = Depends(GetQuerySearch()),
        sorts: List[QuerySortDict] = Depends(GetQuerySorts()),
    ) -> ResponseModel[Page[BudgetCompileConfigList] | List[BudgetCompileConfigList]]:
       pass

```

Then explicitly call the crud_get_many method of service,and set the corresponding query and join parameters

```python hl_lines="24-30"

from better_crud import crud, Page, GetQuerySearch, GetQuerySorts, QuerySortDict
from fastapi_pagination import pagination_ctx
from app.models.user import UserPublic, UserCreate, UserUpdate
from app.services.user import UserService

@crud(
    router,
    dto={"create": UserCreate, "update": UserUpdate},
    routes={
        "exclude": ["get_many"]
    },
    serialize={"base": UserPublic}
)

class UserController():
    service: UserService = Depends(UserService)
    @router.get("", dependencies=[Depends(pagination_ctx(Page)), DependsJwtAuth])
    async def get_list(
        self,
        request: Request,
        search: Dict = Depends(GetQuerySearch()),
        sorts: List[QuerySortDict] = Depends(GetQuerySorts()),
    ) -> ResponseModel[Page[UserPublic] | List[UserPublic]]:
        joins = [(UserProfile, UserProfile.id == User.profile_id)]
        options = [joinedload(User.profile), joinedload(User.roles)]
        criterions = [UserProfile.gender == "female"]
        data = await user_service.crud_get_many(
            joins=joins,
            criterions=criterions,
            options=options,
            search=search,
            sorts=sorts
        )
        return data

```

  - **criterions** embedded query criteria
  - **options** load options
  - **joins** relationship joins

You'll end up with the same endpoint as the default get_many route, but the query conditions, join, load options are all based on SQLAlchemy's native way