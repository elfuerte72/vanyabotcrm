"""Send funnel messages to users in batches."""

from __future__ import annotations

import asyncio

import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.queries import get_funnel_targets, update_funnel_stage
from src.funnel.messages import get_funnel_message

logger = structlog.get_logger()

# Telegram allows ~30 messages/sec to different chats
_BATCH_SIZE = 25
_BATCH_DELAY = 1.0  # seconds between batches


async def send_funnel_messages(bot: Bot) -> None:
    """Fetch all funnel targets and send appropriate stage messages.

    Port of n8n 'days router' + 'DAYS_ru/en/ar' workflows.
    """
    targets = await get_funnel_targets()
    logger.info("funnel_targets_fetched", count=len(targets))

    sent = 0
    for i, target in enumerate(targets):
        chat_id = int(target["chat_id"])
        stage = int(target["funnel_stage"])
        language = target.get("language", "en")

        msg = get_funnel_message(stage, language)
        if msg is None:
            logger.debug("funnel_stage_out_of_range", chat_id=chat_id, stage=stage)
            continue

        # Build inline keyboard — one button per row
        rows = []
        for label, callback_data in msg.buttons:
            if msg.has_url_button and msg.url:
                rows.append([InlineKeyboardButton(text=label, url=msg.url)])
            else:
                rows.append([InlineKeyboardButton(text=label, callback_data=callback_data)])
        keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=msg.text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            await update_funnel_stage(chat_id)
            sent += 1
            logger.debug("funnel_message_sent", chat_id=chat_id, stage=stage, lang=language)
        except Exception as e:
            logger.error(
                "funnel_message_failed",
                chat_id=chat_id, stage=stage, error=str(e),
            )

        # Rate limiting: pause between batches
        if (i + 1) % _BATCH_SIZE == 0:
            await asyncio.sleep(_BATCH_DELAY)

    logger.info("funnel_send_complete", sent=sent, total=len(targets))
