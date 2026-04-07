"""Common setup for RU glutes funnel test scripts.

Usage: python scripts/glutes/stage_N.py  (from project root or any directory)
"""

import os
import sys
from pathlib import Path

# Resolve paths
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPTS_DIR.parent.parent
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


async def send_stage(stage: int, variant: str = "glutes") -> None:
    """Set funnel_stage in DB and send the RU glutes funnel message to test user."""
    configure_logging()
    logger = structlog.get_logger()

    pool = await get_pool()
    bot = create_bot()

    # Set stage in DB with variant
    await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = $1, get_food = TRUE, is_buyer = FALSE,
            language = 'ru', funnel_variant = $3,
            next_funnel_msg_at = NOW(), last_funnel_msg_at = NOW() - interval '1 hour'
        WHERE chat_id = $2
        """,
        stage,
        CHAT_ID,
        variant if stage > 0 else None,
    )
    logger.info("stage_set", stage=stage, language="ru", variant=variant, chat_id=CHAT_ID)

    # Stage 0: send wakeup first, then zone selection after 3 sec
    if stage == 0:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        from src.i18n import get_strings
        s = get_strings("ru")
        wakeup_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=s.FUNNEL_STAGE_0_WAKEUP_BUTTON, url=s.FUNNEL_STAGE_0_WAKEUP_URL)]
        ])
        await bot.send_message(chat_id=CHAT_ID, text=s.FUNNEL_STAGE_0_WAKEUP, reply_markup=wakeup_kb)
        logger.info("wakeup_sent", chat_id=CHAT_ID)
        await asyncio.sleep(3)

    # Get and send funnel message
    msg = get_funnel_message(stage, "ru", variant=variant if stage > 0 else None)
    if msg is None:
        logger.error("no_message_for_stage", stage=stage, language="ru", variant=variant)
    else:
        keyboard = _build_keyboard(msg)
        await _send_single_funnel_message(bot, CHAT_ID, msg, keyboard)
        logger.info(
            "message_sent",
            stage=stage,
            variant=variant,
            has_photo=bool(msg.photo_name),
            has_extra_photos=bool(msg.extra_photos),
            has_video_note=bool(msg.video_note_id),
            has_buttons=bool(msg.buttons),
            buttons=[b[1] for b in msg.buttons],
        )

    await close_pool()
    await bot.session.close()


async def reset_user() -> None:
    """Reset test user to initial RU funnel state."""
    configure_logging()
    logger = structlog.get_logger()

    pool = await get_pool()

    await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = 0, is_buyer = FALSE, get_food = TRUE,
            language = 'ru', funnel_variant = NULL,
            next_funnel_msg_at = NULL, last_funnel_msg_at = NULL
        WHERE chat_id = $1
        """,
        CHAT_ID,
    )
    logger.info("user_reset", chat_id=CHAT_ID, language="ru")

    await close_pool()
