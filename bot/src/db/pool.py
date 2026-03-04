import asyncio
import ssl
from urllib.parse import urlparse

import asyncpg
import structlog

from config.settings import settings

logger = structlog.get_logger()

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        async with _pool_lock:
            if _pool is None:
                _pool = await create_pool()
    return _pool


async def create_pool() -> asyncpg.Pool:
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        ssl=ssl_ctx,
    )
    # Log only host, not credentials
    parsed = urlparse(settings.database_url)
    logger.info("database_pool_created", host=parsed.hostname, port=parsed.port)
    return pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("database_pool_closed")
