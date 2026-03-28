"""Send funnel messages to users in batches."""

from __future__ import annotations

import asyncio

import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.queries import get_funnel_targets, save_user_event, update_funnel_stage
from src.funnel.messages import get_funnel_message
from src.services.media import send_local_photo, send_video_note_from_drive

logger = structlog.get_logger()

# Telegram allows ~30 messages/sec to different chats
_BATCH_SIZE = 25
_BATCH_DELAY = 1.0  # seconds between batches


def _build_keyboard(msg) -> InlineKeyboardMarkup | None:
    """Build inline keyboard from FunnelMessage buttons."""
    if not msg.buttons:
        return None

    rows = []
    for label, callback_data in msg.buttons:
        if msg.has_url_button and msg.url:
            rows.append([InlineKeyboardButton(text=label, url=msg.url)])
        else:
            rows.append([InlineKeyboardButton(text=label, callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_single_funnel_message(bot: Bot, chat_id: int, msg, keyboard) -> None:
    """Send a funnel message with optional photo and video note.

    Order: photo (with caption) → video note → text with keyboard (if no photo).
    If photo is present, caption goes on the photo; buttons in a follow-up message.
    """
    if msg.photo_name:
        # Photo with caption + inline keyboard attached to the photo
        await send_local_photo(
            bot, chat_id, photo_name=msg.photo_name,
            caption=msg.text, reply_markup=keyboard,
        )
    else:
        # Text message with keyboard
        await bot.send_message(
            chat_id=chat_id,
            text=msg.text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    # Video note (circle) after the main message
    if msg.video_note_id:
        try:
            await send_video_note_from_drive(bot, chat_id, msg.video_note_id)
        except Exception as e:
            logger.error("video_note_send_failed", chat_id=chat_id, error=str(e))


async def send_funnel_messages(bot: Bot) -> None:
    """Fetch all funnel targets and send appropriate stage messages."""
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

        keyboard = _build_keyboard(msg)

        try:
            await _send_single_funnel_message(bot, chat_id, msg, keyboard)
            await save_user_event(chat_id, "funnel_message", f"stage_{stage}", language, "funnel")
            await update_funnel_stage(chat_id, language=language, current_stage=stage)
            sent += 1
            logger.debug(
                "funnel_message_sent",
                chat_id=chat_id, stage=stage, lang=language,
                has_photo=bool(msg.photo_name),
                has_video_note=bool(msg.video_note_id),
            )
        except Exception as e:
            logger.error(
                "funnel_message_failed",
                chat_id=chat_id, stage=stage, error=str(e),
            )

        # Rate limiting: pause between batches
        if (i + 1) % _BATCH_SIZE == 0:
            await asyncio.sleep(_BATCH_DELAY)

    logger.info("funnel_send_complete", sent=sent, total=len(targets))
