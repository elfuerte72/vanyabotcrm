"""Bot factory — creates Bot instance and configures Dispatcher."""

from __future__ import annotations

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config.settings import settings
from src.handlers import callbacks, message, start
from src.handlers.payment import setup_payment_routes
from src.middlewares.logging import LoggingMiddleware
from src.middlewares.user_data import UserDataMiddleware

logger = structlog.get_logger()


def create_bot() -> Bot:
    """Create Bot instance with HTML parse mode."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )


def create_dispatcher() -> Dispatcher:
    """Create Dispatcher with all routers and middlewares registered."""
    dp = Dispatcher()

    # Register middlewares (order matters: logging → user_data)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    dp.message.middleware(UserDataMiddleware())
    dp.callback_query.middleware(UserDataMiddleware())


    # Register routers (order matters: start first, then callbacks, then messages)
    dp.include_router(start.router)
    dp.include_router(callbacks.router)
    dp.include_router(message.router)

    logger.info("dispatcher_configured", routers=3, middlewares=3)
    return dp
