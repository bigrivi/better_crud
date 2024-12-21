from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker
from app.core.config import ModeEnum, settings
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    poolclass=NullPool
    if settings.MODE == ModeEnum.testing
    else AsyncAdaptedQueuePool
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
