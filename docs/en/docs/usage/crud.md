An ordinary class is decorated with a CRUD decorator to give it CRUD capabilities, just like Spider-Man, who was bitten by a spider and gained super powers.

I think this is a good use case for python decorators

```python

from fastapi import APIRouter, Depends
from better_crud import crud
from .schema import PetCreate, PetUpdate, PetPublic
from .service import PetService
pet_router = APIRouter()
@crud(
    pet_router,
    dto={
        "create": PetCreate,
        "update": PetUpdate
    },
    serialize={
        "base": PetPublic,
    }
)
class PetController():
    service: PetService = Depends(PetService)

```

!!! warning
    crud is a python class decorator,cannot be used in decorated functions

Let me introduce the parameters of the decorator below

```python

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

```




