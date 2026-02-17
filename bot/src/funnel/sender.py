"""Send funnel messages to users in batches."""

from __future__ import annotations

import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.queries import get_funnel_targets, update_funnel_stage
from src.funnel.messages import get_funnel_message

logger = structlog.get_logger()


async def send_funnel_messages(bot: Bot) -> None:
    """Fetch all funnel targets and send appropriate stage messages.

    Port of n8n 'days router' + 'DAYS_ru/en/ar' workflows.
    """
    targets = await get_funnel_targets()
    logger.info("funnel_targets_fetched", count=len(targets))

    for target in targets:
        chat_id = int(target["chat_id"])
        stage = int(target["funnel_stage"])
        language = target.get("language", "en")

        msg = get_funnel_message(stage, language)
        if msg is None:
            logger.debug("funnel_stage_out_of_range", chat_id=chat_id, stage=stage)
            continue

        # Build inline keyboard
        keyboard_buttons = []
        for label, callback_data in msg.buttons:
            if msg.has_url_button and msg.url:
                keyboard_buttons.append(
                    InlineKeyboardButton(text=label, url=msg.url)
                )
            else:
                keyboard_buttons.append(
                    InlineKeyboardButton(text=label, callback_data=callback_data)
                )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[keyboard_buttons])

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=msg.text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            await update_funnel_stage(chat_id)
            logger.debug("funnel_message_sent", chat_id=chat_id, stage=stage, lang=language)
        except Exception as e:
            logger.error(
                "funnel_message_failed",
                chat_id=chat_id, stage=stage, error=str(e),
            )
