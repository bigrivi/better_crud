import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))  # noqa: E402
from fastapi import FastAPI, Request, status, HTTPException, Depends
from app.core.depends import JWTDepend, ACLDepend
from better_crud import FastAPICrudGlobalConfig, get_action, get_feature
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware, db
from app.core.schema import ResponseSchema
from app.db.session import engine
from app.db.init_db import init_db
import uvicorn
from contextlib import asynccontextmanager
import gc


FastAPICrudGlobalConfig.init(
    backend_config={
        "sqlalchemy": {
            "db_session": lambda: db.session
        }
    },
    response_schema=ResponseSchema,
    query={
        "soft_delete": True
    },
    routes={
        # "dependencies":[JWTDepend,ACLDepend],
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
    custom_engine=engine
)


def register_router():
    from app.routers.api import api_router
    app.include_router(api_router, prefix="/api")


register_router()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1",
                reload=True, port=8090, log_level="info")
