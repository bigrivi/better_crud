# Release Notes

## v0.2.3

**BetterCRUD v0.2.3** makes `crud_action` response models follow your type annotations, fixes a route-registration crash on unresolvable annotations, and stops double-wrapping payloads — all fully tested (183 tests).

### 🚀 Highlights

- **Annotation-driven response models** — when a global `response_schema` is configured, `crud_action` now infers the inner response model from the endpoint's return annotation instead of always falling back to `serialize.base`. Return `-> CustomResult` and the OpenAPI schema becomes `ResponseModel[CustomResult]`.
- **No more double-wrapped payloads** — endpoints that already return a response schema instance are passed through as-is instead of being wrapped a second time.
- **Robust annotation resolution** — a return annotation that cannot be resolved at import time (e.g. `from __future__ import annotations` referencing a model that is not in the module globals) no longer crashes route registration; it falls back to the bare `response_schema` (data unconstrained) and emits a `UserWarning` so you notice the untyped endpoint.

### ✨ Enhancements

#### `crud_action` response model inference

```python
from pydantic import BaseModel
from better_crud import crud, crud_action

class PetSummary(BaseModel):
    adopted: int
    available: int

@crud(pet_router, serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)

    @crud_action(method="GET", path="/summary")
    async def summary(self) -> PetSummary:
        return PetSummary(adopted=3, available=7)
```

With `response_schema=ResponseModel` configured globally, this registers with `response_model=ResponseModel[PetSummary]` — the payload is validated against `PetSummary`, and OpenAPI documents it precisely. Previously it would have been typed as `ResponseModel[PetPublic]` regardless of what the endpoint actually returned.

Inference rules:

- `-> X` → `ResponseModel[X]`
- `-> Optional[X]` / `-> X | None` → `ResponseModel[Optional[X]]` (a `None` response stays valid)
- `-> List[X]` / `-> Page[X]` → preserved as containers
- no annotation, or an annotation that cannot be resolved → bare `ResponseModel` (data unconstrained, with a `UserWarning` in the unresolvable case)
- no `response_schema` configured → FastAPI infers from the return value as before

You can still force a model explicitly with `crud_action(..., response_model=...)` — the explicit value always wins.

### 🐛 Bug Fixes

- **Route registration crash** — `crud_action` endpoints with unresolvable return annotations (string annotations referencing non-global names) raised `NameError`/`TypeError` at import time, taking down the whole app. Now caught: the endpoint registers with the bare `response_schema` and a `UserWarning` is emitted.
- **Double-wrapped payloads** — an endpoint returning a response schema instance produced `{code, msg, data: {code, msg, data: ...}}`. Now passed through untouched.

### 📦 Installation

```bash
pip install better-crud==0.2.3
```

For the complete history, see the [Changelog](changelog.md).

___

## v0.2.2

**BetterCRUD v0.2.2** adds custom endpoints via a new `crud_action` decorator, makes bulk operations atomic, and completes the soft-delete story with an opt-in recover route — all fully tested (177 tests).

### 🚀 Highlights

- **`crud_action` decorator** — attach business endpoints (`adopt`, `approve`, `reset`, ...) to your generated routes while keeping them inside the CRUD ecosystem: `service` injection, ACL action names, response schema wrapping, and `request.state` scoping all work automatically.
- **Atomic bulk operations** — `crud_create_many` / `crud_update_many` now run in a single transaction. A mid-batch failure rolls back every item instead of leaving partial data.
- **Soft-delete recover route** — `PATCH /{resource}/{id}/recover` restores soft-deleted records. Opt-in via `query={"soft_delete": True, "allow_recover": True}`; routes are not generated otherwise (zero footprint).

### ✨ Enhancements

#### `crud_action` custom endpoints

```python
from better_crud import crud, crud_action

@crud(pet_router, serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)

    @crud_action(method="POST", path="/{id}/adopt", action="adopt")
    async def adopt(self, id: int):
        return {"id": id, "adopted": True}
```

See [Custom Actions](advanced/crud_action.md) for the full guide.

#### Atomic bulk operations

`crud_create_many` and `crud_update_many` now wrap the batch in a single transaction. On any failure, all changes are rolled back — no partial writes.

#### Recover route

```python
@crud(
    router,
    serialize={"base": UserPublic},
    query={
        "soft_delete": True,
        "allow_recover": True,     # exposes PATCH /{id}/recover
    }
)
```

### 🐛 Bug Fixes

- Bulk `create_many`/`update_many` were non-atomic (per-item commits) — a mid-batch failure left partial data. Now fully transactional.

### 📦 Installation

```bash
pip install better-crud==0.2.2
```

For the complete history, see the [Changelog](changelog.md).

___

## v0.2.1

**BetterCRUD v0.2.1** adds optional pagination to the `get_many` route. List endpoints can now return a full array (no pagination) when the caller omits pagination params — ideal for small datasets like enum-like tables, reference data, and dropdown options.

### 🚀 Highlights

- **Optional pagination** — `GET /{resource}` now supports three modes via `pagination_mode`, configurable globally or per-route.
- **Backward compatible by default** — the default `"optional"` mode matches previous behavior exactly (no pagination params → full array; `page`/`size` → paginated response). All 165 tests pass.

### ✨ Enhancements

#### `pagination_mode` global config

`BetterCrudGlobalConfig.init()` accepts a new `pagination_mode` option:

```python
BetterCrudGlobalConfig.init(
    backend_config={"sqlalchemy": {"db_session": get_session}},
    pagination_mode="optional",   # "always" | "optional" | "disabled"
)
```

| Mode      | No `page`/`size`                 | `?page=1&size=20`                |
|-----------|----------------------------------|----------------------------------|
| `always`  | Paginated (default `page=1, size=50`) | Paginated                   |
| `optional` (default) | Full array                 | Paginated                        |
| `disabled` | Full array                       | Full array (params ignored)      |

#### Per-route override

Individual `@crud` decorators can override the global mode:

```python
@crud(
    router,
    serialize={"base": PetPublic},
    pagination_mode="always",
)
class PetController():
    service: PetService = Depends(PetService)
```

#### Response format

- **Paginated:** `{items: [...], total, page, size, pages}`
- **Non-paginated:** `[...]` — plain array of all matching records

`filter`/`s`/`sort` work identically in both modes. Frontends should check whether the response is an array or an object:

```js
const data = await res.json();
const items = Array.isArray(data) ? data : data.items;
```

### 📦 Installation

```bash
pip install better-crud==0.2.1
```

For the complete history, see the [Changelog](changelog.md).

___

## v0.2.0

**BetterCRUD v0.2.0** brings full compatibility with the latest FastAPI releases, more powerful lifecycle hooks, and a cleaner dependency footprint — all backed by a fully passing test suite (154 tests).

### 🚀 Highlights

- **FastAPI 0.141+ compatibility** — fixes route registration failures caused by pydantic serializing `Depends` objects into plain dicts. Routes now register correctly across FastAPI `>=0.111.0,<1.0`.
- **Richer lifecycle hooks** — `on_after_create` and `on_after_update` now receive the validated `model` payload, not just the persisted entity, giving you full access to the input data in your hook logic.
- **`$notany` filter now supports empty lists**, making the operator consistent with `$in`/`$nin` and simpler to use from dynamic query builders.

### ✨ Enhancements

#### Lifecycle hooks receive the input model

`on_after_create` / `on_after_update` gained a new `model` parameter carrying the original validated create/update schema:

```python
async def on_after_create(
    self,
    entity: Entity,            # persisted instance
    model: EntityCreate,       # NEW: validated create payload
    background_tasks: BackgroundTasks,
) -> None:
    ...
```

!!! warning

    This is a breaking change for anyone overriding these two hooks — update your signatures to accept the new `model` argument.

#### `$notany` supports empty list

```python
query = {"filter": {"$notany": {"tags": []}}}   # previously an error, now valid
```

### 🐛 Bug Fixes

- **FastAPI `>=0.141` route registration** — `Depends` instances restored after pydantic `model_dump()` serialization so `routes.dependencies` attach correctly.
- **`$notany` operator** — no longer fails when given an empty list.

### 🔧 Dependency & Compatibility

- **FastAPI:** `>=0.111.0,<1.0` (previously pinned versions could not resolve from older PyPI mirrors)
- **SQLAlchemy:** `>=2.0.30,<3.0`
- **fastapi-pagination:** `>=0.12.24,<1.0`
- **Pydantic:** `>=2.7.3,<3.0`
- Development requirements locked to versions reachable from all PyPI mirrors (fastapi 0.128.8, sqlalchemy 2.0.30, pydantic 2.7.3), with `greenlet` and `bcrypt<5` added for SQLAlchemy async and passlib compatibility.

### ✅ Verified Combinations

All tested with the full suite — **154 passed**:

| FastAPI | SQLAlchemy | fastapi-pagination | Pydantic | SQLModel |
|---------|-----------|--------------------|----------|----------|
| 0.111.0 | 2.0.30    | 0.12.24            | 2.7.3    | 0.0.22   |
| 0.128.8 | 2.0.30    | 0.12.24            | 2.7.3    | 0.0.22   |
| 0.128.8 | 2.0.51    | 0.15.16            | 2.13.4   | —        |
| 0.135.1 | 2.0.48    | 0.12.24            | 2.13.4   | 0.0.14   |
| 0.140.13| 2.0.51    | 0.15.16            | 2.13.4   | —        |
| 0.141.1 | 2.0.51    | 0.15.16            | 2.13.4   | —        |

### 📦 Installation

```bash
pip install better-crud==0.2.0
```

For the complete history, see the [Changelog](changelog.md).
