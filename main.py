from fastapi import FastAPI, Request
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
from app.core.schema import Route


async def acl(request: Request):
    print("global acl")
    print(request)
    print(request.state.__dict__)
    feature = get_feature(request)
    action = get_action(request)
    print(feature)
    print(action)
    # raise HTTPException(status.HTTP_401_UNAUTHORIZED,"Permission Denied")

FastAPICrudGlobalConfig.init(
    get_db_session=get_session,
    interceptor=acl,
    query={
        "soft_delete": True
    }
    # routes={"only":["get_many"]},
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # shutdown
    gc.collect()


app = FastAPI(title="FastAPI CRUD", lifespan=lifespan)

wrap_app_responses(app, Route)
app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=str(settings.ASYNC_DATABASE_URL),
    engine_args={
        "echo": True,
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
