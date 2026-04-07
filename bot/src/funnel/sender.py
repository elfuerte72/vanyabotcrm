"""Send funnel messages to users in batches."""

from __future__ import annotations

import asyncio

import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.queries import (
    calculate_next_send_time,
    get_funnel_targets,
    save_user_event,
    update_funnel_stage,
)
from src.db.pool import get_pool
from src.funnel.messages import get_funnel_message
from src.services.media import send_local_media_group, send_local_photo, send_video_note_from_drive

logger = structlog.get_logger()

# Telegram allows ~30 messages/sec to different chats
_BATCH_SIZE = 25
_BATCH_DELAY = 1.0  # seconds between batches


def _build_keyboard(msg) -> InlineKeyboardMarkup | None:
    """Build inline keyboard from FunnelMessage buttons.

    Supports mixed URL + callback buttons: if has_url_button, the first button
    with empty callback_data becomes a URL button; rest are callbacks.
    """
    if not msg.buttons:
        return None

    rows = []
    for label, callback_data in msg.buttons:
        if msg.has_url_button and msg.url and not callback_data:
            rows.append([InlineKeyboardButton(text=label, url=msg.url)])
        else:
            rows.append([InlineKeyboardButton(text=label, callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_single_funnel_message(bot: Bot, chat_id: int, msg, keyboard) -> None:
    """Send a funnel message with optional photo/media group and video note.

    Order:
    - If extra_photos: media group (album) with caption on first photo → buttons separately
    - Else if photo_name: single photo with caption + keyboard
    - Else: text message with keyboard
    - Video note (circle) after the main content
    """
    if msg.extra_photos:
        # Media group: photo_name + extra_photos as album, caption on first
        all_photos = [msg.photo_name] + msg.extra_photos if msg.photo_name else msg.extra_photos
        await send_local_media_group(bot, chat_id, all_photos, caption=msg.text)
        # Buttons in a separate message after the album (Telegram API limitation)
        if keyboard:
            # Use first button label as message text so the button is fully visible
            btn_text = msg.buttons[0][0] if msg.buttons else "👇"
            await bot.send_message(
                chat_id=chat_id, text=btn_text, reply_markup=keyboard,
            )
    elif msg.photo_name:
        # Single photo with caption + inline keyboard
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
        variant = target.get("funnel_variant")

        # RU stage 0 without variant: send zone selection and reschedule +24h
        # Don't increment stage — only zone callback advances to stage 1
        # Wakeup message was already sent once after meal plan delivery
        if language == "ru" and stage == 0 and not variant:
            msg = get_funnel_message(0, "ru")
            if msg is None:
                continue
            keyboard = _build_keyboard(msg)
            try:
                await _send_single_funnel_message(bot, chat_id, msg, keyboard)
                await save_user_event(chat_id, "funnel_message", "stage_0_zone_ask", "ru", "funnel")
                # Reschedule +24h, do NOT increment stage
                next_send = calculate_next_send_time(0, "ru", has_variant=False)
                pool = await get_pool()
                await pool.execute(
                    "UPDATE users_nutrition SET last_funnel_msg_at = NOW(), next_funnel_msg_at = $2 WHERE chat_id = $1",
                    chat_id, next_send,
                )
                sent += 1
                logger.debug("funnel_stage_0_zone_ask_sent", chat_id=chat_id)
            except Exception as e:
                logger.error("funnel_stage_0_zone_ask_failed", chat_id=chat_id, error=str(e))
            if (i + 1) % _BATCH_SIZE == 0:
                await asyncio.sleep(_BATCH_DELAY)
            continue

        msg = get_funnel_message(stage, language, variant=variant)
        if msg is None:
            logger.debug("funnel_stage_out_of_range", chat_id=chat_id, stage=stage)
            continue

        keyboard = _build_keyboard(msg)

        try:
            await _send_single_funnel_message(bot, chat_id, msg, keyboard)
            await save_user_event(chat_id, "funnel_message", f"stage_{stage}", language, "funnel")
            await update_funnel_stage(chat_id, language=language, current_stage=stage, variant=variant)
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
