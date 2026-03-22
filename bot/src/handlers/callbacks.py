"""Callback query handlers — inline button presses.

Callbacks: buy_now, show_info, show_results, check_suitability,
           remind_later, none, video_workout, learn_workout, video_circle
"""

from __future__ import annotations

import structlog
from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import settings, media_config
from src.db.queries import get_user_language, mark_as_buyer
from src.i18n import get_strings
from src.services.media import (
    send_info_video,
    send_random_result_photo,
    send_suitability_video,
    send_video_note_from_drive,
)

logger = structlog.get_logger()

router = Router()


def _get_payment_url(language: str) -> str:
    """Get payment URL based on language (Tribute for RU, Ziina for EN/AR)."""
    if language == "ru":
        return settings.tribute_link
    return settings.ziina_link or settings.tribute_link


@router.callback_query(F.data == "buy_now")
async def handle_buy_now(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    language = await get_user_language(user_id) or "en"
    strings = get_strings(language)

    await mark_as_buyer(user_id)

    payment_url = _get_payment_url(language)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=strings.BUY_BUTTON, url=payment_url)]
    ])

    await bot.send_message(
        chat_id=chat_id,
        text=strings.BUY_MESSAGE,
        reply_markup=keyboard,
    )
    await callback.answer()
    logger.info("buy_now_callback", user_id=user_id, language=language)


@router.callback_query(F.data == "show_info")
async def handle_show_info(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return
    chat_id = callback.message.chat.id
    try:
        await send_info_video(bot, chat_id)
    except Exception as e:
        language = await get_user_language(callback.from_user.id) or "en"
        logger.error("show_info_failed", error=str(e), chat_id=chat_id, language=language)
        await bot.send_message(chat_id, get_strings(language).VIDEO_UNAVAILABLE)
    await callback.answer()


@router.callback_query(F.data == "show_results")
async def handle_show_results(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    language = await get_user_language(user_id) or "en"
    strings = get_strings(language)

    try:
        await send_random_result_photo(bot, chat_id, caption=strings.RESULTS_CAPTION)
    except Exception as e:
        logger.error("show_results_failed", error=str(e), chat_id=chat_id)
    await callback.answer()


@router.callback_query(F.data == "check_suitability")
async def handle_check_suitability(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return
    chat_id = callback.message.chat.id
    try:
        await send_suitability_video(bot, chat_id)
    except Exception as e:
        logger.error("check_suitability_failed", error=str(e), chat_id=chat_id)
    await callback.answer()


@router.callback_query(F.data == "remind_later")
async def handle_remind_later(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    language = await get_user_language(user_id) or "en"
    strings = get_strings(language)

    await bot.send_message(chat_id, strings.REMIND_LATER, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "none")
async def handle_none(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    language = await get_user_language(user_id) or "en"
    strings = get_strings(language)

    await bot.send_message(chat_id, strings.NONE_RESPONSE, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "video_workout")
async def handle_video_workout(callback: CallbackQuery, bot: Bot) -> None:
    """Stage 0 button: send free 7-min workout video link."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    language = await get_user_language(user_id) or "en"
    strings = get_strings(language)

    workout_url = media_config["videos"].get("workout_url", "")
    rows = []
    if workout_url:
        rows.append([InlineKeyboardButton(text=strings.WATCH_VIDEO_BUTTON, url=workout_url)])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await bot.send_message(
        chat_id=chat_id,
        text=strings.WATCH_VIDEO_PROMPT,
        reply_markup=keyboard,
    )
    logger.info("video_workout_callback", user_id=user_id, language=language)


@router.callback_query(F.data == "learn_workout")
async def handle_learn_workout(callback: CallbackQuery, bot: Bot) -> None:
    """Stage 1 button (RU): show workout details + buy button (690₽)."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    language = await get_user_language(user_id) or "ru"
    strings = get_strings(language)

    payment_url = _get_payment_url(language)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=strings.LEARN_WORKOUT_BUTTON, url=payment_url)]
    ])

    await bot.send_message(
        chat_id=chat_id,
        text=strings.LEARN_WORKOUT_RESPONSE,
        reply_markup=keyboard,
    )
    logger.info("learn_workout_callback", user_id=user_id, language=language)


@router.callback_query(F.data == "video_circle")
async def handle_video_circle(callback: CallbackQuery, bot: Bot) -> None:
    """Stage 3 button (RU): send 'how it works' video note (circle)."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    video_notes = media_config.get("video_notes", {})
    file_id = video_notes.get("how_it_works", "")

    if not file_id:
        logger.error("video_circle_no_file_id", user_id=user_id)
        return

    try:
        await send_video_note_from_drive(bot, chat_id, file_id)
        logger.info("video_circle_callback", user_id=user_id)
    except Exception as e:
        language = await get_user_language(user_id) or "ru"
        strings = get_strings(language)
        logger.error("video_circle_failed", error=str(e), chat_id=chat_id)
        await bot.send_message(chat_id, strings.VIDEO_UNAVAILABLE)
