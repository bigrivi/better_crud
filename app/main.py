from fastapi import FastAPI, Request,status,HTTPException,Depends
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
import gc
from contextlib import asynccontextmanager
from fastapi_responseschema import wrap_app_responses
import uvicorn
from app.core.config import ModeEnum, settings
from app.db.init_db import init_db
from fastapi_crud import FastAPICrudGlobalConfig, get_action, get_feature
from app.db.session import get_session
from app.core.schema import ResponseSchema
from app.core.depends import JWTDepend,ACLDepend

FastAPICrudGlobalConfig.init(
    get_db_session=get_session,
    response_schema=ResponseSchema,
    query={
        "soft_delete":True
    },
    routes={
        "dependencies":[JWTDepend,ACLDepend],
        # "only":["create_many","create_one"]
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # shutdown
    gc.collect()


app = FastAPI(title="FastAPI CRUD", lifespan=lifespan)

app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=str(settings.ASYNC_DATABASE_URL),
    engine_args={
        "echo": False,
        "poolclass": NullPool
        if settings.MODE == ModeEnum.testing
        else AsyncAdaptedQueuePool
        # "pool_pre_ping": True,
        # "pool_size": settings.POOL_SIZE,
        # "max_overflow": 64,
    },
)


def register_router():
    from app.routers.api import api_router
    app.include_router(api_router, prefix="/api")


register_router()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1",
                reload=True, port=8090, log_level="info")
