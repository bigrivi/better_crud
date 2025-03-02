Sometimes you don't want to use class-based views. Of course, BetterCRUD provides another way based on the traditional function view mode.

```python title="company_router.py"
from fastapi import APIRouter, Depends, Request
from better_crud import crud_generator
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate, Company
router = APIRouter()
crud_generator(
    router,
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic}
)

```
crud_generator function and crud decorator parameters are basically the same

In this mode, there is no need to define a service

If you just want to quickly generate your CRUD routing port without too much business logic in it, this mode will suit you

In addition, crud_generator also provides hooks calls

```python

crud_generator(
    router,
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic},
    on_before_create=on_before_create,
    on_after_create=on_after_create,
    on_before_update=on_before_update,
    on_after_update=on_after_update,
    on_before_delete=on_before_delete,
    on_after_delete=on_after_delete
)
```


!!! warning
    In this mode, if you need to define a route rewrite, put the definition before calling crud_generator


```python hl_lines="8-10"

from fastapi import APIRouter, Depends, Request
from better_crud import crud_generator
from app.models.company import CompanyPublic, CompanyCreate, CompanyUpdate, Company
from app.services.company import CompanyService
router = APIRouter()


@router.get("")
async def override_get_many():
    return []


crud_generator(
    router,
    Company,
    dto={"create": CompanyCreate, "update": CompanyUpdate},
    routes={},
    serialize={"base": CompanyPublic}
)



```