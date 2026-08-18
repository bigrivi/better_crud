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
| `response_model`  | `Any`                       | Optional explicit **final** response model, used as-is (e.g. `ResponseModel[CurrentUser]`). Defaults to `None` (see [Response Model Inference](#response-model-inference)) |
| `action`          | `str`                       | ACL action name returned by `get_action()`. Defaults to the method name |
| `summary`         | `str`                       | OpenAPI summary                                          |
| `dependencies`    | `Sequence[Depends]`         | Extra route dependencies                                 |

## Response Model Inference

When a global `response_schema` is configured, the inner response model is inferred from the endpoint's return type annotation:

```python
from pydantic import BaseModel

class PetSummary(BaseModel):
    adopted: int
    available: int

@crud_action(method="GET", path="/summary")
async def summary(self) -> PetSummary:   # -> ResponseModel[PetSummary]
    return PetSummary(adopted=3, available=7)
```

Inference rules:

| Return annotation                    | Registered response model                  |
| ------------------------------------ | ------------------------------------------ |
| `-> X`                               | `ResponseModel[X]`                         |
| `-> Optional[X]` / `-> X \| None`     | `ResponseModel[Optional[X]]` (None stays valid) |
| `-> List[X]` / `-> Page[X]`          | `ResponseModel[List[X]]` / `ResponseModel[Page[X]]` |
| no annotation / unresolvable         | bare `ResponseModel` (data unconstrained; `UserWarning` if unresolvable) |
| no `response_schema` configured      | FastAPI infers from the return value       |

An explicit `response_model=...` always wins over inference and is used as the **final response shape as-is** — pass the parameterized response shell (e.g. `ResponseModel[CurrentUser]`), not a bare inner model. If an annotation cannot be resolved at import time (e.g. `from __future__ import annotations` referencing a model that is not in the module globals), route registration falls back to the bare `ResponseModel` (data unconstrained) and emits a `UserWarning` instead of crashing.

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
