---
title: "Stop Writing CRUD Boilerplate: Generate a Complete FastAPI API From One Decorator"
published: false
description: "How BetterCRUD generates 8 production-ready CRUD routes — with filtering, pagination, relationships, soft delete, and ACL — from a single decorator. Includes a working example and migration notes."
tags: [fastapi, python, backend, api]
---

# Stop Writing CRUD Boilerplate: Generate a Complete FastAPI API From One Decorator

Every FastAPI project needs the same endpoints. `GET /resource`, `POST /resource`, `GET/PUT/DELETE /resource/{id}` — plus filtering, pagination, and sorting. And every project writes them by hand. Over. And over.

I've seen codebases with 2,000 lines of nearly identical route handlers, where filtering is bolted on inconsistently, pagination is reinvented per endpoint, and permission checks are copy-pasted with subtle bugs.

There's a better way. **[BetterCRUD](https://github.com/bigrivi/better_crud)** generates the entire CRUD layer from a single decorator — while keeping you in full control.

## What you get from one decorator

```python
from fastapi import APIRouter, Depends
from better_crud import crud

pet_router = APIRouter()

@crud(
    pet_router,
    dto={"create": PetCreate, "update": PetUpdate},
    serialize={"base": PetPublic},
)
class PetController():
    service: PetService = Depends(PetService)
```

That's it. This generates **8 routes**:

| Route | Method | Description |
|-------|--------|-------------|
| `/pet` | GET | List with filtering, pagination, sorting |
| `/pet/{id}` | GET | Get one |
| `/pet` | POST | Create one |
| `/pet/bulk` | POST | Create many (atomic) |
| `/pet/{id}` | PUT | Update one (partial) |
| `/pet/{ids}/bulk` | PUT | Update many (atomic) |
| `/pet/{ids}` | DELETE | Delete many |
| `/pet/{id}/recover` | PATCH | Soft-delete recover *(opt-in)* |

## The setup

First, a standard async SQLAlchemy setup:

```python
# db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

engine = create_async_engine("sqlite+aiosqlite:///crud.db", poolclass=NullPool)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with SessionLocal() as session:
        yield session
```

Define your model:

```python
# model.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class Pet(Base):
    __tablename__ = "pet"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(100))
```

Your schemas:

```python
# schema.py
from pydantic import BaseModel
from typing import Optional

class PetBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PetPublic(PetBase):
    id: int

class PetCreate(PetBase):
    pass

class PetUpdate(PetBase):
    pass
```

A thin service:

```python
# service.py
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from model import Pet

class PetService(SqlalchemyCrudService[Pet]):
    def __init__(self):
        super().__init__(Pet)
```

And wire it all together:

```python
# main.py
from fastapi import FastAPI
from better_crud import BetterCrudGlobalConfig

BetterCrudGlobalConfig.init(
    backend_config={"sqlalchemy": {"db_session": get_session}}
)

app = FastAPI()
app.include_router(pet_router, prefix="/pet")
```

You now have a complete, documented (OpenAPI/Swagger) CRUD API.

## The real power: everything comes free

### Rich filtering

The generated `GET /pet` endpoint supports 27 filter operators out of the box:

```bash
# exact match
GET /pet?filter=name||$eq||Rex

# contains
GET /pet?filter=name||$cont||Re

# range
GET /pet?filter=age||$between||1,5

# in list
GET /pet?filter=species||$in||dog,cat
```

And JSON search with nested logic:

```bash
GET /pet?s={"name":{"$cont":"Re"},"$or":[{"age":{"$gt":3}},{"species":{"$eq":"cat"}}]}
```

### Pagination — three modes

Control pagination behavior globally or per-route:

```python
BetterCrudGlobalConfig.init(
    pagination_mode="always",   # "always" | "optional" | "disabled"
)
```

- `always` — always return `{items, total, page, size, pages}`
- `optional` *(default)* — paginated only when `page`/`size` passed; otherwise a plain array
- `disabled` — never paginate

Perfect for small reference datasets that frontends need as a full array.

### Relationship queries & storage

```python
# One-to-many, many-to-many, one-to-one — all handled automatically
class UserCreate(UserBase):
    profile: Optional[UserProfileCreate] = None
    roles: Optional[List[int]] = None
    tasks: Optional[List[UserTaskCreate]] = None
```

Post a nested payload and BetterCRUD stores the relationships for you. Query them with `?load=` and `?join=`.

### Soft delete + recover

```python
@crud(
    router,
    query={"soft_delete": True, "allow_recover": True},
)
```

Deletes become soft deletes; `PATCH /pet/{id}/recover` brings records back.

### ACL hooks

Every generated route exposes its `feature` and `action` on the request state, so permission guards slot in naturally:

```python
from better_crud import get_feature, get_action

async def acl(request: Request):
    feature = get_feature(request)   # e.g. "pet"
    action = get_action(request)     # e.g. "read", "create", "update"
    # your permission logic
```

### Lifecycle hooks

```python
class PetService(SqlalchemyCrudService[Pet]):
    async def on_before_create(self, pet_create: PetCreate, **kwargs):
        pet_create.name = pet_create.name.title()
```

### Custom endpoints for business logic

CRUD doesn't cover everything. Attach business actions with `@crud_action`:

```python
@crud_action(method="POST", path="/{id}/adopt", action="adopt")
async def adopt(self, id: int):
    return {"id": id, "adopted": True}
```

This registers `POST /pet/{id}/adopt` **inside** the CRUD ecosystem — with service injection, ACL, and response schema wrapping.

## Migrating from fastapi-crudrouter

[fastapi-crudrouter](https://github.com/awtkns/fastapi-crudrouter) — the long-time de-facto CRUD library — has been **unmaintained since November 2023**. If you're on it, the routes are nearly identical, so migration is mostly drop-in:

```python
# Before
from fastapi_crudrouter import SQLAlchemyCRUDRouter
router = SQLAlchemyCRUDRouter(
    schema=PetCreate, create_schema=PetCreate,
    update_schema=PetUpdate, db_model=Pet, db=get_session,
)

# After
from better_crud import crud
pet_router = APIRouter()

@crud(pet_router,
      dto={"create": PetCreate, "update": PetUpdate},
      serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)
```

Same REST semantics — but you gain 27 filter operators, pagination modes, ACL, soft delete, relationship storage, and an overridable service layer.

## Production-ready by default

- **99%+ test coverage** with 177 passing tests
- Fully async (SQLAlchemy 2.0)
- Works with SQLAlchemy **and** SQLModel
- Extensible: custom backends, custom response schemas, custom pagination models
- Class-based views **and** functional views (`crud_generator`)

## Try it

```bash
pip install better-crud
```

Full docs: [https://bigrivi.github.io/better_crud/](https://bigrivi.github.io/better_crud/)

Source: [https://github.com/bigrivi/better_crud](https://github.com/bigrivi/better_crud)

---

*If BetterCRUD saves you time, give it a ⭐ on GitHub — it helps more developers discover it.*
