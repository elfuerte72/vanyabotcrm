"""APScheduler-based funnel sender — runs every 15 minutes."""

from __future__ import annotations

import structlog
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.funnel.sender import send_funnel_messages

logger = structlog.get_logger()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and configure the funnel scheduler.

    Runs every 15 minutes to check for users whose delay has elapsed:
    - Stage 0: 2 hours after receiving meal plan
    - Stages 1-5: 23 hours after previous funnel message
    """
    scheduler = AsyncIOScheduler()

    async def _job():
        logger.info("funnel_scheduler_triggered")
        await send_funnel_messages(bot)

    scheduler.add_job(
        _job,
        "interval",
        minutes=15,
        id="funnel_check",
        replace_existing=True,
    )

    logger.info("funnel_scheduler_configured", schedule="every 15 minutes")
    return scheduler
