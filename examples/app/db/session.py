from sqlalchemy.orm import sessionmaker
from app.core.config import ModeEnum, settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from fastapi_async_sqlalchemy import  db

DB_POOL_SIZE = 83
WEB_CONCURRENCY = 9
POOL_SIZE = max(DB_POOL_SIZE // WEB_CONCURRENCY, 5)

connect_args = {"check_same_thread": False}

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    poolclass=NullPool
    if settings.MODE == ModeEnum.testing
    else AsyncAdaptedQueuePool,  # Asincio pytest works with NullPool
    # pool_size=POOL_SIZE,
    # max_overflow=64,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    yield db.session
    # async with SessionLocal() as session:
    #     yield session
    # session = SessionLocal()
    # try:
    #     yield session
    # finally:
    #     await session.close()
