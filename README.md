<div align="center">
  <h1>BetterCRUD</h1>
</div>
<p align="center" markdown=1>
  <i>A better CRUD library for FastAPI.</i></br>
  <sub>FastAPI CRUD routing library based on class view, you can control everything</sub>
</p>
<p align="center" markdown=1>
<a href="https://github.com/bigrivi/better_crud/actions/workflows/pytest.yml" target="_blank">
  <img src="https://github.com/bigrivi/better_crud/actions/workflows/pytest.yml/badge.svg" alt="Tests"/>
</a>
<a href="https://pypi.org/project/better_crud/" target="_blank">
  <img src="https://img.shields.io/pypi/v/better_crud?color=%2334D058&label=pypi%20package" alt="PyPi Version"/>
</a>
<a href="https://pypi.org/project/better_crud/" target="_blank">
  <img src="https://img.shields.io/pypi/pyversions/better_crud.svg?color=%2334D058" alt="Supported Python Versions"/>
</a>
<a href="https://codecov.io/github/bigrivi/better_crud" target="_blank">
 <img src="https://codecov.io/github/bigrivi/better_crud/graph/badge.svg?token=MEMUT1FH4K"/>
 </a>
</p>

---

**Documentation**: <a href="https://bigrivi.github.io/better_crud/" target="_blank">https://bigrivi.github.io/better_crud/</a>

**Source Code**: <a href="https://github.com/bigrivi/better_crud" target="_blank">https://github.com/bigrivi/better_crud</a>

---

BetterCRUD is a library that can quickly generate CRUD routes for you without any intrusion to your code. You can still control everything. When you are troubled by a large number of repeated CRUD routes, I believe it can help you, saving you a lot of time and allowing you to focus more on business logic.

BetterCRUD is reliable, fully tested, and used in project production environments.

BetterCRUD is a way to dynamically generate routes by combining your model with the crud decorator,I believe bring you a different development experience

You only need to configure some crud options and define your model to produce powerful CRUD functions

```python
@crud(
    router,
    dto={
        "create": PetCreate,
        "update": PetUpdate
    },
    serialize={
        "base": PetPublic,
    },
    **other_options
)
class PetController():
    service: PetService = Depends(PetService)

```

## Requirements
- **Python:** Version 3.9 or newer.
- **FastAPI:** BetterCRUD is built to work with FastAPI, so having FastAPI in your project is essential.
- <b>SQLAlchemy:</b> Version 2.0.30 or newer. BetterCRUD uses SQLAlchemy for database operations.
- <b>Pydantic:</b> Version 2.7.3 or newer. BetterCRUD leverages Pydantic models for data validation and serialization.

## Installation
```bash
pip install better-crud
```

## Features
- Fully Async, Synchronization is not supported
- Less boilerplate code
- Configuring static type support
- More flexible custom configuration，Less invasive
- Compatible with both class views and functional views
- Rich filter, pagination, and sorting support
- Automated relationship support, query and storage
- Extensible custom backend


## Default Routes

| Route                | Method     | Description |
| -------------------- | ---------- | ----------- |
| /resource            | **GET**    | Get Many    |
| /resource/{id}       | **GET**    | Get One     |
| /resource            | **POST**   | Create One  |
| /resource/bulk       | **POST**   | Create Many |
| /resource/{id}       | **PUT**    | Update One  |
| /resource/{ids}/bulk | **PUT**    | Update Many |
| /resource/{ids}      | **DELETE** | Delete Many |



## Minimal Example

Prerequisites,Prepare our db, Only asynchronous mode is supported,aiomysql or aiosqlite
**db.py**
```python
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

**model.py**
```python
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Pet(Base):
    __tablename__ = "pet"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(100))

```

**schema.py**
```python
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

**service.py**
```python
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from .model import Pet


class PetService(SqlalchemyCrudService[Pet]):
    def __init__(self):
        super().__init__(Pet)

```

Next we need to define the controller and decorate it with the crud decorator
Sure the controller is just a normal class,The crud decorator gives it super powers
**controller.py**
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

Next we can register router to the fastapi routing system

**main.py**
```python
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

Congratulations, your first CRUD route has been created！


![OpenAPI Route Overview](https://raw.githubusercontent.com/bigrivi/better_crud/main/resources/RouteOverview.png)

## Author

👤 **bigrivi**
* GitHub: [bigrivi](https://github.com/bigrivi)

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

[MIT](LICENSE)