"""Manually trigger funnel sender for testing."""

import asyncio
import logging

import structlog

from config.settings import settings
from src.bot import create_bot
from src.db.pool import close_pool, get_pool
from src.funnel.sender import send_funnel_messages


def configure_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.DEBUG)
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


async def main() -> None:
    configure_logging()
    logger = structlog.get_logger()

    await get_pool()
    bot = create_bot()

    logger.info("triggering_funnel_manually")
    await send_funnel_messages(bot)
    logger.info("funnel_done")

    await close_pool()
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
