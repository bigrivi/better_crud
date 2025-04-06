from sqlalchemy import text
from sqlmodel import SQLModel
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


@asynccontextmanager
async def setup_database(url: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(url, echo=False, future=True)
    session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            await conn.execute(text("PRAGMA case_sensitive_like = true;"))
        try:
            yield session
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()
