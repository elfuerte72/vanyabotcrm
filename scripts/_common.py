"""Common setup for funnel test scripts.

Usage: python scripts/stage_N.py  (from project root or any directory)
"""

import os
import sys
from pathlib import Path

# Resolve paths
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPTS_DIR.parent
_BOT_DIR = _PROJECT_DIR / "bot"

# cd into bot/ so config/settings.py finds .env
os.chdir(_BOT_DIR)

# Add bot/ to sys.path so we can import bot modules
if str(_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(_BOT_DIR))

import asyncio
import logging

import structlog
from aiogram import Bot

from config.settings import settings
from src.bot import create_bot
from src.db.pool import close_pool, get_pool
from src.funnel.messages import get_funnel_message
from src.funnel.sender import _build_keyboard, _send_single_funnel_message

CHAT_ID = 379336096


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


async def send_stage(stage: int, language: str = "ru") -> None:
    """Set funnel_stage in DB and send the funnel message to test user."""
    configure_logging()
    logger = structlog.get_logger()

    pool = await get_pool()
    bot = create_bot()

    # Set stage in DB
    await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = $1, get_food = TRUE, is_buyer = FALSE,
            next_funnel_msg_at = NOW(), last_funnel_msg_at = NOW() - interval '1 hour'
        WHERE chat_id = $2
        """,
        stage,
        CHAT_ID,
    )
    logger.info("stage_set", stage=stage, chat_id=CHAT_ID)

    # Get and send funnel message
    msg = get_funnel_message(stage, language)
    if msg is None:
        logger.error("no_message_for_stage", stage=stage, language=language)
    else:
        keyboard = _build_keyboard(msg)
        await _send_single_funnel_message(bot, CHAT_ID, msg, keyboard)
        logger.info(
            "message_sent",
            stage=stage,
            has_photo=bool(msg.photo_name),
            has_video_note=bool(msg.video_note_id),
            has_buttons=bool(msg.buttons),
        )

    await close_pool()
    await bot.session.close()


async def reset_user() -> None:
    """Reset test user to initial state."""
    configure_logging()
    logger = structlog.get_logger()

    pool = await get_pool()

    await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = 0, is_buyer = FALSE, get_food = TRUE,
            next_funnel_msg_at = NULL, last_funnel_msg_at = NULL
        WHERE chat_id = $1
        """,
        CHAT_ID,
    )
    logger.info("user_reset", chat_id=CHAT_ID)

    await close_pool()
