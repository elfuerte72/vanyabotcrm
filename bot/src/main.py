"""Entry point — start bot polling + scheduler + payment webhook."""

from __future__ import annotations

import asyncio
import logging

import structlog
from aiohttp import web

from config.settings import settings
from src.bot import create_bot, create_dispatcher
from src.db.pool import close_pool, get_pool
from src.funnel.scheduler import setup_scheduler
from src.handlers.payment import setup_payment_routes


def configure_logging() -> None:
    """Configure structlog with human-readable console output."""
    log_level = getattr(logging, settings.log_level.upper(), logging.DEBUG)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


async def start_webhook_server(bot) -> web.AppRunner:
    """Start aiohttp server for payment webhooks."""
    app = web.Application()
    app["bot"] = bot
    setup_payment_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logger = structlog.get_logger()
    logger.info("webhook_server_started", port=8080)
    return runner


async def main() -> None:
    configure_logging()
    logger = structlog.get_logger()
    logger.info("bot_starting", log_level=settings.log_level)

    if not settings.ziina_webhook_secret:
        logger.warning("ZIINA_WEBHOOK_SECRET not set — payment webhooks will be rejected")

    # Initialize DB pool
    await get_pool()

    bot = create_bot()
    dp = create_dispatcher()

    # Start payment webhook server
    webhook_runner = await start_webhook_server(bot)

    # Start funnel scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()

    try:
        logger.info("bot_polling_started")
        await dp.start_polling(bot)
    finally:
        logger.info("bot_shutting_down")
        scheduler.shutdown(wait=False)
        await webhook_runner.cleanup()
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
