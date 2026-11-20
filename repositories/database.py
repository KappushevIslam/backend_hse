import os

import asyncpg

_pool: asyncpg.Pool | None = None


def _dsn() -> str:
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5435/hw")


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(_dsn())
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
