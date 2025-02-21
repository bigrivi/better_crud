Sometimes we want to implement an ACL Guard function
```python title="acl.py"
from fastapi import Depends, Request
from better_crud import get_feature

async def acl(request: Request):
    feature = get_feature(request)
    action = get_action(request)
    #Your ACL logic implementation

ACLDepend = Depends(acl)
```

```python title="main.py"
from .acl import ACLDepend

BetterCrudGlobalConfig.init(
    routes={
        "dependencies":[ACLDepend],
    },
)
```

```python title="some_router.py"

@crud(
    feature="test"
)
class TestController():
    pass

```

- get_action will return the action_map value set in BetterCrudGlobalConfig for the corresponding route
- get_feature will return the feature parameter value of the corresponding route in the crud decorator