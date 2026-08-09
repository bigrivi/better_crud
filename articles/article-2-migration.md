---
title: "fastapi-crudrouter is Dead. Here's How to Migrate to BetterCRUD"
published: false
description: "fastapi-crudrouter has been unmaintained since Nov 2023. Migrate your FastAPI CRUD routes to BetterCRUD — same REST semantics, drop-in routes, and you gain filtering, pagination modes, ACL, soft delete, and relationship storage."
tags: [fastapi, python, migration, backend]
---

# fastapi-crudrouter is Dead. Here's How to Migrate to BetterCRUD

[fastapi-crudrouter](https://github.com/awtkns/fastapi-crudrouter) was the de-facto CRUD library for FastAPI — generating 6 CRUD routes from a model in a few lines. It's been **unmaintained since November 2023**. No FastAPI 0.141+ support, no new features, and its SQLAlchemy backend doesn't keep up with SQLAlchemy 2.0 async best practices.

If you're still on it, it's time to migrate. The good news: **the route layout is nearly identical**, so the move is mostly drop-in.

## Why migrate?

| | fastapi-crudrouter | BetterCRUD |
| --- | :---: | :---: |
| Maintained (2026) | ❌ stalled since Nov 2023 | ✅ active |
| FastAPI 0.141+ | ❌ | ✅ |
| SQLAlchemy 2.0 async | ✅ (basic) | ✅ |
| Filter operators | ❌ | ✅ 27 operators |
| Pagination modes | ❌ basic only | ✅ always/optional/disabled |
| Relationship queries & storage | ❌ | ✅ joins, M2M, O2M, O2O |
| Soft delete + recover | ❌ | ✅ |
| ACL hooks | ❌ | ✅ |
| Lifecycle hooks | ❌ | ✅ |
| Custom endpoints | ❌ | ✅ `@crud_action` |
| Test coverage | — | ✅ 99%+, 177 tests |

## The migration

### Before (fastapi-crudrouter)

```python
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from database import get_session
from models import Pet, PetCreate, PetUpdate

router = SQLAlchemyCRUDRouter(
    schema=PetUpdate,
    create_schema=PetCreate,
    update_schema=PetUpdate,
    db_model=Pet,
    db=get_session,
    prefix="pet",
)
```

### After (BetterCRUD)

```python
from fastapi import APIRouter, Depends
from better_crud import crud
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from models import Pet, PetCreate, PetUpdate, PetPublic

pet_router = APIRouter()

class PetService(SqlalchemyCrudService[Pet]):
    def __init__(self):
        super().__init__(Pet)

@crud(
    pet_router,
    dto={"create": PetCreate, "update": PetUpdate},
    serialize={"base": PetPublic},
)
class PetController():
    service: PetService = Depends(PetService)
```

That's the whole migration. Register `pet_router` with `app.include_router(pet_router, prefix="/pet")` and you're live.

## What you get for free after migrating

### 1. Filtering you actually need

fastapi-crudrouter had no filtering. BetterCRUD's `GET /pet` supports 27 operators out of the box:

```bash
GET /pet?filter=name||$cont||Re        # contains
GET /pet?filter=age||$between||1,5     # range
GET /pet?filter=species||$in||dog,cat  # in list
GET /pet?s={"$or":[{"age":{"$gt":3}},{"species":{"$eq":"cat"}}]}  # nested logic
```

### 2. Pagination that fits your API

```python
BetterCrudGlobalConfig.init(pagination_mode="optional")
```

Three modes — `always`, `optional`, `disabled` — so small reference datasets can return plain arrays while large tables stay paginated.

### 3. Relationships, done properly

Store nested payloads (many-to-many, one-to-many, one-to-one) automatically, and query them with `?load=` / `?join=`:

```python
class UserCreate(UserBase):
    profile: Optional[UserProfileCreate] = None
    roles: Optional[List[int]] = None
    tasks: Optional[List[UserTaskCreate]] = None
```

### 4. Soft delete + recover

```python
@crud(router, query={"soft_delete": True, "allow_recover": True})
```

`DELETE` becomes soft delete; `PATCH /pet/{id}/recover` restores records.

### 5. Security hooks

Every generated route exposes `feature`/`action` on the request state — wire your existing permission guards directly:

```python
from better_crud import get_feature, get_action

async def acl(request: Request):
    feature = get_feature(request)
    action = get_action(request)
    # your ACL logic
```

### 6. Business logic without leaving the CRUD pattern

```python
@crud_action(method="POST", path="/{id}/adopt", action="adopt")
async def adopt(self, id: int):
    return await self.service.do_adopt(id)
```

Registers `POST /pet/{id}/adopt` with service injection, ACL, and response wrapping — no manual router wiring.

## Migration checklist

1. ✅ Add `better_crud` to requirements (remove `fastapi-crudrouter`)
2. ✅ Add a `PetService(SqlalchemyCrudService[Pet])` class (thin, no logic needed initially)
3. ✅ Replace the `SQLAlchemyCRUDRouter(...)` call with `@crud(...)` on a controller class
4. ✅ Register the router — prefix stays the same, routes are identical
5. ✅ Point your frontend at the same endpoints — no client changes needed
6. ✅ Optionally enable soft delete, ACL, and custom actions as you go

The route layout (`GET/POST /resource`, `GET/PUT/DELETE /resource/{id}`) is preserved, so **your existing clients keep working** while the backend gains capabilities fastapi-crudrouter never had.

## Resources

- Docs: [https://bigrivi.github.io/better_crud/](https://bigrivi.github.io/better_crud/)
- Source: [https://github.com/bigrivi/better_crud](https://github.com/bigrivi/better_crud)
- Install: `pip install better-crud`

---

*Migrating? If BetterCRUD saves you time, give it a ⭐ on GitHub.*
