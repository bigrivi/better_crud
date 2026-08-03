# Release Notes

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
