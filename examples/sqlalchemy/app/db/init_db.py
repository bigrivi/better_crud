from .session import engine
from .base import MappedBase


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(MappedBase.metadata.create_all)
