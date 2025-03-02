If you use SQLModel, please go directly to the [SQLModel](/sqlmodel/) chapter

## Minimal Example

!!! warning
    Prerequisites,Prepare our db, Only asynchronous mode is supported,aiomysql or aiosqlite

```python title="db.py"
from sqlalchemy.orm import DeclarativeBase, declared_attr
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
DATABASE_URL = "sqlite+aiosqlite:///crud.db"

class MappedBase(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class Base(MappedBase):
    __abstract__ = True


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
        await conn.run_sync(MappedBase.metadata.create_all)
```

First Define Your Model And Schema

```python title="model.py"
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Pet(Base):
    __tablename__ = "pet"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(100))

```

```python title="schema.py"
from typing import Optional, List
from pydantic import BaseModel


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