# Custom Actions

CRUD routes cover the standard operations, but real-world resources always have business actions that don't fit the CRUD verbs — `adopt`, `approve`, `reset`, `archive`, etc.

BetterCRUD provides the `crud_action` decorator to attach custom endpoints to your generated routes while keeping them inside the CRUD ecosystem.

## Basic Usage

Decorate any method of your controller with `crud_action`:

```python
from better_crud import crud, crud_action

@crud(
    pet_router,
    serialize={"base": PetPublic},
)
class PetController():
    service: PetService = Depends(PetService)

    @crud_action(method="POST", path="/{id}/adopt", action="adopt")
    async def adopt(self, id: int):
        return {"id": id, "adopted": True}
```

This registers `POST /pet/{id}/adopt` automatically. The method behaves like any generated route:

- **`self.service` is available** — dependency injection works out of the box.
- **ACL works** — `get_action(request)` returns `"adopt"` for permission guards.
- **Response schema is applied** — the global `response_schema` wrapper (if configured) is applied to the return value.
- **Path params are parsed** — FastAPI handles `{id}` natively.

## Decorator Parameters

| Parameter         | Type                        | Description                                              |
| ----------------- | --------------------------- | -------------------------------------------------------- |
| `method`          | `"GET"/"POST"/"PUT"/"PATCH"/"DELETE"` | HTTP method for the route                      |
| `path`            | `str`                       | Route path, relative to the router prefix                |
| `response_model`  | `Any`                       | Optional explicit response model. Defaults to `None` (FastAPI infers from the return value) |
| `action`          | `str`                       | ACL action name returned by `get_action()`. Defaults to the method name |
| `summary`         | `str`                       | OpenAPI summary                                          |
| `dependencies`    | `Sequence[Depends]`         | Extra route dependencies                                 |

## Static Paths

Static action paths (e.g. `/summary`) are registered **before** the generated routes, so they are matched before the dynamic `/{id}` segment. You don't need to worry about route ordering:

```python
@crud_action(method="GET", path="/summary")
async def summary(self):
    return {"count": 42}
```

`GET /pet/summary` hits your action — not `get_one` with `id="summary"`.

## Overriding

If you also register the same path+method manually with `@router.xxx`, the manually registered route wins and the auto-registered action is skipped:

```python
@crud(pet_router, serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)

    @pet_router.post("/{id}/adopt")
    async def manual_adopt(self, id: int):
        return {"manual": True}

    @crud_action(method="POST", path="/{id}/adopt")
    async def adopt(self, id: int):
        return {"auto": True}
```

`POST /pet/{id}/adopt` → `{"manual": True}`.

## Method Without `self`

Actions can also be `@staticmethod`-style methods without `self`. They are handled safely:

```python
@staticmethod
@crud_action(method="GET", path="/ping")
async def ping():
    return "pong"
```

## When to Use `crud_action` vs Manual Registration

| | Manual `@router.xxx` | `crud_action` |
| --- | :---: | :---: |
| Route registration | ✅ | ✅ |
| `service` injection | ✅ | ✅ |
| ACL action name (`get_action`) | ❌ | ✅ |
| Response schema wrapping | ❌ | ✅ |
| `request.state` scoping (auth/params filters) | ❌ | ✅ |
| Static-path priority over `/{id}` | ❌ (manual ordering) | ✅ |

Use `crud_action` when the endpoint belongs to the resource and should inherit its permissions, serialization, and scoping. Use manual registration when you need full control outside the CRUD ecosystem.
