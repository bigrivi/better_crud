# Using BetterCRUD with SQLModel

Since SQLModel combines the functionality of sqlalchemy and pydantic, all you need to do is replace the model with SQLModel

!!! warning
    Prerequisites,Prepare our db, Only asynchronous mode is supported,aiomysql or aiosqlite

```python title="db.py"
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
DATABASE_URL = "sqlite+aiosqlite:///crud.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

First Define your SQLModel model

```python title="model.py"

from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class PetBase(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = Field(default=None)


class Pet(PetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class PetPublic(PetBase):
    id: Optional[int]


class PetCreate(PetBase):
    pass


class PetUpdate(PetBase):
    pass

```

Next we need to create a service:

```python title="service.py"
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from .model import Pet


class PetService(SqlalchemyCrudService[Pet]):
    def __init__(self):
        super().__init__(Pet)

```

Next we need to define the controller and decorate it with the crud decorator
Sure the controller is just a normal class,The crud decorator gives it super powers

```python title="controller.py"
from fastapi import APIRouter, Depends
from better_crud import crud
from .model import PetCreate, PetUpdate, PetPublic
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

Next we can register router to the fastapi routing system

```python title="main.py" hl_lines="24-33"
from better_crud import BetterCrudGlobalConfig
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import get_session, init_db

BetterCrudGlobalConfig.init(
    backend_config={
        "sqlalchemy": {
            "db_session": get_session
        }
    }
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    # Shutdown
    yield

app = FastAPI(lifespan=lifespan)


def register_router():
    from app.controller import pet_router
    app.include_router(pet_router, prefix="/pet")


register_router()


```

And it's all done, just go to /docs and the crud endpoints are created.

