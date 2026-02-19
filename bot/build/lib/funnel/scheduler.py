"""APScheduler-based daily funnel sender."""

from __future__ import annotations

import structlog
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.funnel.sender import send_funnel_messages

logger = structlog.get_logger()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and configure the funnel scheduler.

    Runs daily at 23:00 UTC (matching the n8n Schedule Trigger).
    """
    scheduler = AsyncIOScheduler()

    async def _job():
        logger.info("funnel_scheduler_triggered")
        await send_funnel_messages(bot)

    scheduler.add_job(
        _job,
        "cron",
        hour=23,
        minute=0,
        id="daily_funnel",
        replace_existing=True,
    )

    logger.info("funnel_scheduler_configured", schedule="daily at 23:00 UTC")
    return scheduler
