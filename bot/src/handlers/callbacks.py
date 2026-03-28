"""Callback query handlers — inline button presses.

Callbacks: buy_now, confirm_paid_ru, show_info, show_results, check_suitability,
           remind_later, none, video_workout, learn_workout, video_circle,
           en_funnel_q_<stage>, ar_funnel_q_<stage>, upsell_decline
"""

from __future__ import annotations

from typing import Any

import structlog
from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import settings, media_config
from src.db.queries import get_user, mark_as_buyer, save_user_event, save_ziina_payment, update_funnel_stage
from src.funnel.messages import get_funnel_message
from src.funnel.sender import _build_keyboard, _send_single_funnel_message
from src.i18n import get_strings
from src.models.user import User
from src.services.ziina import ZiinaAPIError, create_payment_intent
from src.services.media import (
    send_info_video,
    send_random_result_photo,
    send_suitability_video,
    send_video_note_from_drive,
)

logger = structlog.get_logger()

router = Router()


def _get_language(db_user: User | None, fallback: str = "en") -> str:
    """Extract language from db_user loaded by UserDataMiddleware, avoiding extra DB query."""
    language = db_user.language if db_user else fallback
    logger.debug("callback_language_resolved", source="db_user" if db_user else "fallback", language=language)
    return language


def _get_payment_url(language: str) -> str:
    """Get fallback payment URL based on language (Tribute for RU, Ziina for EN/AR)."""
    if language == "ru":
        return settings.tribute_link
    return settings.ziina_link or settings.tribute_link


def _get_payment_amount(db_user: User | None) -> int:
    """Determine payment amount (AED) based on user's funnel stage.

    Stage is incremented AFTER sending, so callback from stage N message
    arrives when user is at stage N+1. Upsell buttons come from stages 9,10.
    """
    if not db_user:
        return 49
    stage = db_user.funnel_stage
    if stage >= 11:  # clicked upsell stage 10 button (129 AED)
        return 129
    if stage >= 10:  # clicked upsell stage 9 button (79 AED)
        return 79
    return 49  # main product (stages 0-8)


@router.callback_query(F.data == "buy_now")
async def handle_buy_now(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    strings = get_strings(language)

    await save_user_event(chat_id, "button_click", "buy_now", language, "funnel")

    payment_url = _get_payment_url(language)

    if language == "ru":
        # RU: two-step confirmation — Tribute has no webhook,
        # so we don't mark as buyer until user confirms payment
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=strings.BUY_BUTTON, url=payment_url)],
            [InlineKeyboardButton(text=strings.CONFIRM_PAID_BUTTON, callback_data="confirm_paid_ru")],
        ])
        await bot.send_message(
            chat_id=chat_id,
            text=strings.BUY_MESSAGE_WITH_CONFIRM,
            reply_markup=keyboard,
        )
        logger.info("buy_now_link_sent", user_id=user_id, language="ru", marked_buyer=False)
    else:
        # EN/AR: create Ziina payment intent — don't mark buyer until webhook confirms
        amount_aed = _get_payment_amount(db_user)
        try:
            intent_id, redirect_url = await create_payment_intent(
                amount_aed, message=f"Workout access — {amount_aed} AED",
            )
            await save_ziina_payment(user_id, intent_id, amount_aed)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=strings.BUY_BUTTON, url=redirect_url)]
            ])
            await bot.send_message(
                chat_id=chat_id,
                text=strings.BUY_MESSAGE,
                reply_markup=keyboard,
            )
            logger.info("buy_now_ziina_intent", user_id=user_id, language=language, intent_id=intent_id, amount=amount_aed)
        except (ZiinaAPIError, Exception) as exc:
            # Fallback: static link only (webhook will still confirm if user pays)
            logger.error("buy_now_ziina_fallback", user_id=user_id, error=str(exc))
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=strings.BUY_BUTTON, url=payment_url)]
            ])
            await bot.send_message(
                chat_id=chat_id,
                text=strings.BUY_MESSAGE,
                reply_markup=keyboard,
            )


@router.callback_query(F.data == "confirm_paid_ru")
async def handle_confirm_paid_ru(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """RU user confirms they paid on Tribute."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    await mark_as_buyer(user_id)
    await save_user_event(chat_id, "button_click", "confirm_paid_ru", "ru", "funnel")

    strings = get_strings("ru")
    await bot.send_message(
        chat_id=chat_id,
        text=strings.PAYMENT_CONFIRMED,
    )
    logger.info("confirm_paid_ru", user_id=user_id)


@router.callback_query(F.data == "show_info")
async def handle_show_info(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    await save_user_event(chat_id, "button_click", "show_info", language, "funnel")
    try:
        await send_info_video(bot, chat_id)
    except Exception as e:
        logger.error("show_info_failed", error=str(e), chat_id=chat_id, language=language)
        await bot.send_message(chat_id, get_strings(language).VIDEO_UNAVAILABLE)


@router.callback_query(F.data == "show_results")
async def handle_show_results(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    strings = get_strings(language)

    await save_user_event(chat_id, "button_click", "show_results", language, "funnel")
    try:
        await send_random_result_photo(bot, chat_id, caption=strings.RESULTS_CAPTION)
    except Exception as e:
        logger.error("show_results_failed", error=str(e), chat_id=chat_id)


@router.callback_query(F.data == "check_suitability")
async def handle_check_suitability(callback: CallbackQuery, bot: Bot) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    await save_user_event(chat_id, "button_click", "check_suitability", language=None, workflow_name="funnel")
    try:
        await send_suitability_video(bot, chat_id)
    except Exception as e:
        logger.error("check_suitability_failed", error=str(e), chat_id=chat_id)


@router.callback_query(F.data == "remind_later")
async def handle_remind_later(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    strings = get_strings(language)

    await save_user_event(chat_id, "button_click", "remind_later", language, "funnel")
    await bot.send_message(chat_id, strings.REMIND_LATER, parse_mode="HTML")


@router.callback_query(F.data == "none")
async def handle_none(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    strings = get_strings(language)

    await save_user_event(chat_id, "button_click", "none", language, "funnel")
    await bot.send_message(chat_id, strings.NONE_RESPONSE, parse_mode="HTML")


@router.callback_query(F.data == "video_workout")
async def handle_video_workout(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """Stage 0 button: send free 7-min workout video link."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    strings = get_strings(language)

    await save_user_event(chat_id, "button_click", "video_workout", language, "funnel")

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
async def handle_learn_workout(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """Stage 1 button (RU): show workout details + buy button (690₽)."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    db_user = data.get("db_user")
    language = _get_language(db_user, fallback="ru")
    strings = get_strings(language)

    await save_user_event(chat_id, "button_click", "learn_workout", language, "funnel")

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
async def handle_video_circle(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """Stage 3 button (RU): send 'how it works' video note (circle)."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    db_user = data.get("db_user")
    language = _get_language(db_user, fallback="ru")
    await save_user_event(chat_id, "button_click", "video_circle", language, "funnel")

    video_notes = media_config.get("video_notes", {})
    file_id = video_notes.get("how_it_works", "")

    if not file_id:
        logger.error("video_circle_no_file_id", user_id=user_id)
        return

    try:
        await send_video_note_from_drive(bot, chat_id, file_id)
        logger.info("video_circle_callback", user_id=user_id)
    except Exception as e:
        strings = get_strings(language)
        logger.error("video_circle_failed", error=str(e), chat_id=chat_id)
        await bot.send_message(chat_id, strings.VIDEO_UNAVAILABLE)


@router.callback_query(F.data.startswith("en_funnel_q_"))
async def handle_en_funnel_question(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """EN funnel question button — instantly sends next stage message."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return

    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    # Parse stage from callback data: en_funnel_q_0 → 0
    try:
        clicked_stage = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        logger.error("en_funnel_q_invalid_data", data=callback.data, user_id=user_id)
        return

    await save_user_event(chat_id, "button_click", callback.data, "en", "funnel")

    # Fetch current user state
    db_user = data.get("db_user")
    if not db_user:
        db_user = await get_user(user_id)
    if not db_user:
        logger.debug("en_funnel_q_no_user", user_id=user_id)
        return

    # Skip if user is buyer or already past this stage
    if db_user.is_buyer:
        logger.debug("en_funnel_q_buyer_skip", user_id=user_id, stage=clicked_stage)
        return
    if db_user.funnel_stage != clicked_stage:
        logger.debug(
            "en_funnel_q_stage_mismatch",
            user_id=user_id, clicked=clicked_stage, current=db_user.funnel_stage,
        )
        return

    # Send next stage message instantly
    next_stage = clicked_stage + 1
    next_msg = get_funnel_message(next_stage, "en")
    if next_msg is None:
        logger.debug("en_funnel_q_no_next_msg", user_id=user_id, next_stage=next_stage)
        return

    keyboard = _build_keyboard(next_msg)
    try:
        await _send_single_funnel_message(bot, chat_id, next_msg, keyboard)
        await update_funnel_stage(chat_id, language="en", current_stage=next_stage)
        logger.info(
            "en_funnel_question_advance",
            user_id=user_id, from_stage=clicked_stage, to_stage=next_stage,
        )
    except Exception as e:
        logger.error(
            "en_funnel_question_send_failed",
            user_id=user_id, stage=next_stage, error=str(e),
        )


@router.callback_query(F.data.startswith("ar_funnel_q_"))
async def handle_ar_funnel_question(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """AR funnel question button — instantly sends next stage message."""
    try:
        await callback.answer()
    except Exception:
        pass

    if not callback.message:
        return

    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    # Parse stage from callback data: ar_funnel_q_0 → 0
    try:
        clicked_stage = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        logger.error("ar_funnel_q_invalid_data", data=callback.data, user_id=user_id)
        return

    await save_user_event(chat_id, "button_click", callback.data, "ar", "funnel")

    # Fetch current user state
    db_user = data.get("db_user")
    if not db_user:
        db_user = await get_user(user_id)
    if not db_user:
        logger.debug("ar_funnel_q_no_user", user_id=user_id)
        return

    # Skip if user is buyer or already past this stage
    if db_user.is_buyer:
        logger.debug("ar_funnel_q_buyer_skip", user_id=user_id, stage=clicked_stage)
        return
    if db_user.funnel_stage != clicked_stage:
        logger.debug(
            "ar_funnel_q_stage_mismatch",
            user_id=user_id, clicked=clicked_stage, current=db_user.funnel_stage,
        )
        return

    # Send next stage message instantly
    next_stage = clicked_stage + 1
    next_msg = get_funnel_message(next_stage, "ar")
    if next_msg is None:
        logger.debug("ar_funnel_q_no_next_msg", user_id=user_id, next_stage=next_stage)
        return

    keyboard = _build_keyboard(next_msg)
    try:
        await _send_single_funnel_message(bot, chat_id, next_msg, keyboard)
        await update_funnel_stage(chat_id, language="ar", current_stage=next_stage)
        logger.info(
            "ar_funnel_question_advance",
            user_id=user_id, from_stage=clicked_stage, to_stage=next_stage,
        )
    except Exception as e:
        logger.error(
            "ar_funnel_question_send_failed",
            user_id=user_id, stage=next_stage, error=str(e),
        )


@router.callback_query(F.data == "upsell_decline")
async def handle_upsell_decline(callback: CallbackQuery, bot: Bot, **data: Any) -> None:
    """User declined an upsell offer."""
    try:
        await callback.answer()
    except Exception:
        pass

    user_id = callback.from_user.id
    chat_id = callback.message.chat.id if callback.message else user_id
    db_user = data.get("db_user")
    language = _get_language(db_user)
    await save_user_event(chat_id, "button_click", "upsell_decline", language, "funnel")
    logger.info("upsell_declined", user_id=user_id)
