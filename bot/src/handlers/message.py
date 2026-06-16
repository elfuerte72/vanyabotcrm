"""Handler for text and voice messages — main conversation flow.

Flow:
1. Check if user already got food (get_food=True) → reject
2. Text: detect language → send to AGENT MAIN
3. Voice: download → transcribe → send to AGENT MAIN
4. Parse agent response:
   - conversation → send text to user
   - generate → calculate macros → save to DB → AGENT FOOD → send menu
"""

from __future__ import annotations

import asyncio

import structlog
from aiogram import Bot, Router, F
from aiogram.enums import ChatAction
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from pydantic import ValidationError

from config.settings import settings
from src.db.queries import save_chat_message, save_user_data, save_user_event, set_food_received
from src.handlers.start import LANGUAGE_CHOOSE_MESSAGE, _make_language_keyboard
from src.i18n import get_strings, ru as ru_strings
from src.models.user import User
from src.models.user_data import CollectedUserData
from src.services.ai_agent import run_agent_main
from src.services.ai_client import get_ai_client
from src.services.ai_food import run_agent_food
from src.services.calculator import calculate_macros
from src.services.tracking import build_cta_url
from src.services.formatter import (
    format_meal_plan_html,
    parse_agent_output,
    validate_meal_plan,
)
from src.services.language import detect_language
from src.services.subscription import is_subscribed

logger = structlog.get_logger()

router = Router()

# Test account — always allow recalculation (skip get_food check)
TEST_CHAT_ID = 379336096

# Pending KBJU calculations awaiting channel subscription (RU users only).
# Keyed by chat_id; value is everything needed to resume the meal-plan flow
# after the user confirms they subscribed.
_PENDING_SUBSCRIPTION: dict[int, dict[str, object]] = {}


def _build_subscription_keyboard() -> InlineKeyboardMarkup:
    """Subscribe + verify keyboard shown to RU users before KBJU."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=ru_strings.SUBSCRIPTION_SUBSCRIBE_BUTTON,
            url=settings.telegram_channel_url,
        )],
        [InlineKeyboardButton(
            text=ru_strings.SUBSCRIPTION_CHECK_BUTTON,
            callback_data="check_subscription",
        )],
    ])


# Confirmation button labels per language
_CONFIRM_BUTTONS = {
    "ru": ("Да, подтверждаю", "Исправить"),
    "en": ("Yes, confirm", "Fix data"),
    "ar": ("نعم، أؤكد", "تصحيح"),
}


def _is_confirmation_request(text: str) -> bool:
    """Check if the agent is asking the user to confirm collected data."""
    markers = [
        "подтверди", "все верно", "всё верно", "правильно",
        "confirm", "everything correct", "did i get everything right",
        "هل كل شيء صحيح", "أؤكد",
    ]
    lower = text.lower()
    return any(m in lower for m in markers)


def _make_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Create inline keyboard with Confirm / Fix buttons."""
    confirm_text, fix_text = _CONFIRM_BUTTONS.get(lang, _CONFIRM_BUTTONS["en"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=confirm_text, callback_data="confirm_data"),
            InlineKeyboardButton(text=fix_text, callback_data="fix_data"),
        ]
    ])


async def _require_language(message: Message, db_user: User | None) -> bool:
    """If user hasn't chosen a language yet, show language buttons. Returns True if blocked."""
    if db_user is None:
        logger.info("no_language_selected", chat_id=message.chat.id)
        await message.answer(
            LANGUAGE_CHOOSE_MESSAGE,
            reply_markup=_make_language_keyboard(),
        )
        return True
    return False


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot, db_user: User | None) -> None:
    """Handle voice messages: download → transcribe → process as text."""
    if await _require_language(message, db_user):
        return
    if db_user and db_user.get_food and message.chat.id != TEST_CHAT_ID:
        lang = db_user.language or "en"
        strings = get_strings(lang)
        await message.answer(strings.ALREADY_CALCULATED, parse_mode="HTML")
        return

    # Download voice file
    voice = message.voice
    file = await bot.get_file(voice.file_id)
    file_bytes = await bot.download_file(file.file_path)

    # Transcribe using OpenAI Whisper via OpenRouter
    client = get_ai_client()

    try:
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.ogg", file_bytes.read(), "audio/ogg"),
        )
        text = transcription.text
        logger.info("voice_transcribed", chat_id=message.chat.id, text=text[:100])
    except Exception as e:
        logger.error("voice_transcription_failed", error=str(e), chat_id=message.chat.id)
        lang = (db_user.language if db_user else None) or "en"
        await message.answer(get_strings(lang).VOICE_ERROR)
        return

    await _process_text_message(message, bot, db_user, text)


@router.message(F.text)
async def handle_text(message: Message, bot: Bot, db_user: User | None) -> None:
    """Handle text messages."""
    if await _require_language(message, db_user):
        return
    if db_user and db_user.get_food and message.chat.id != TEST_CHAT_ID:
        lang = db_user.language or "en"
        strings = get_strings(lang)
        await message.answer(strings.ALREADY_CALCULATED, parse_mode="HTML")
        return

    await _process_text_message(message, bot, db_user, message.text or "")


async def _process_text_message(
    message: Message,
    bot: Bot,
    db_user: User | None,
    text: str,
    *,
    override_username: str | None = None,
    override_first_name: str | None = None,
) -> None:
    """Core message processing logic.

    override_username/override_first_name: used when called from callback handlers
    where message.from_user is the bot, not the actual user.
    """
    chat_id = message.chat.id
    username = override_username or (message.from_user.username if message.from_user else "unknown")
    detected_lang = db_user.language if db_user and db_user.language else detect_language(text)

    logger.debug("processing_message", chat_id=chat_id, lang=detected_lang, text=text[:100])

    # Show typing indicator while AI processes
    await bot.send_chat_action(chat_id, ChatAction.TYPING)

    # Run AI agent
    try:
        agent_output = await run_agent_main(chat_id, text)
    except Exception as e:
        logger.error("agent_main_failed", chat_id=chat_id, error=str(e))
        strings = get_strings(detected_lang)
        await message.answer(strings.AI_ERROR)
        return

    response = parse_agent_output(agent_output)

    if response.route_type == "conversation":
        # Normal conversation — send text response
        if response.text_response:
            # If the agent is asking for confirmation, add buttons
            if _is_confirmation_request(response.text_response):
                keyboard = _make_confirm_keyboard(detected_lang)
                await message.answer(
                    response.text_response,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            else:
                await message.answer(response.text_response, parse_mode="HTML")
        else:
            logger.warning("empty_agent_response", chat_id=chat_id)
        return

    # route_type == "generate" — user data collected, calculate macros
    data = response.data
    if not data:
        logger.error("generate_route_but_no_data", chat_id=chat_id)
        return

    # Validate collected data with Pydantic
    try:
        user_data = CollectedUserData.model_validate(data)
    except ValidationError as e:
        logger.warning("user_data_validation_failed", chat_id=chat_id, errors=str(e))
        strings = get_strings(detected_lang)
        await message.answer(strings.AI_ERROR)
        return

    logger.info(
        "data_collection_finished",
        chat_id=chat_id,
        sex=user_data.sex,
        weight=user_data.weight,
        height=user_data.height,
        age=user_data.age,
    )

    first_name = override_first_name or (message.from_user.first_name if message.from_user else "")

    # RU users must be subscribed to Ivan's channel before we generate KBJU.
    # Test account is exempt so funnel testing isn't blocked.
    if detected_lang == "ru" and chat_id != TEST_CHAT_ID:
        if not await is_subscribed(bot, chat_id):
            logger.info("subscription_required", chat_id=chat_id)
            _PENDING_SUBSCRIPTION[chat_id] = {
                "user_data": user_data,
                "username": username,
                "first_name": first_name,
            }
            await save_user_event(
                chat_id, "subscription_gate", "shown", "ru", "subscription"
            )
            await message.answer(
                ru_strings.SUBSCRIPTION_REQUIRED,
                parse_mode="HTML",
                reply_markup=_build_subscription_keyboard(),
            )
            return

    await _calculate_and_send_meal_plan(
        message, bot, chat_id, user_data,
        username=username,
        first_name=first_name,
        detected_lang=detected_lang,
    )


async def _calculate_and_send_meal_plan(
    message: Message,
    bot: Bot,
    chat_id: int,
    user_data: CollectedUserData,
    *,
    username: str,
    first_name: str,
    detected_lang: str,
) -> None:
    """Run KBJU calc + meal plan generation and post-send actions.

    Extracted so it can be invoked both from the normal text flow and from
    the subscription-check callback once the RU user confirms they joined
    the channel.
    """
    macros = calculate_macros(
        sex=user_data.sex,
        weight=user_data.weight,
        height=user_data.height,
        age=user_data.age,
        activity_level=user_data.activity_level,
        goal=user_data.goal,
    )

    strings = get_strings(detected_lang)

    async def _save() -> None:
        await save_user_data(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            sex=user_data.sex,
            age=user_data.age,
            weight=user_data.weight,
            height=user_data.height,
            activity_level=user_data.activity_level,
            goal=user_data.goal,
            allergies=user_data.allergies,
            excluded_foods=user_data.excluded_foods,
            calories=macros.calories,
            protein=macros.protein,
            fats=macros.fats,
            carbs=macros.carbs,
            language=detected_lang,
        )

    async def _notify() -> None:
        await message.answer(strings.CALCULATING_MENU, parse_mode="HTML")

    await asyncio.gather(_save(), _notify())

    try:
        menu_data = await run_agent_food(
            calories=macros.calories,
            protein=macros.protein,
            fats=macros.fats,
            carbs=macros.carbs,
            excluded_foods=user_data.excluded_foods,
            allergies=user_data.allergies,
            language=detected_lang,
        )
    except Exception as e:
        logger.error("agent_food_failed", chat_id=chat_id, error=str(e))
        await message.answer(strings.AI_ERROR)
        return

    logger.info("agent_food_result", chat_id=chat_id, meals_count=len(menu_data) if isinstance(menu_data, list) else 1)

    target_stats = {
        "calories": macros.calories,
        "protein": macros.protein,
        "fats": macros.fats,
        "carbs": macros.carbs,
    }

    is_valid, error, calc_stats = validate_meal_plan(
        menu_data, macros.calories, user_data.excluded_foods
    )

    if not is_valid:
        logger.warning("meal_plan_validation_failed", error=error, chat_id=chat_id)

    html = format_meal_plan_html(menu_data, calc_stats, target_stats, language=detected_lang)
    await save_chat_message(str(chat_id), "ai", html)
    await message.answer(html, parse_mode="HTML")

    if chat_id != TEST_CHAT_ID:
        await set_food_received(chat_id, language=detected_lang)

        if detected_lang == "ru":
            # After the meal plan, RU users get a single CTA message that sends
            # them to the results site. There is no scheduled RU funnel anymore.
            try:
                cta_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=ru_strings.MEAL_PLAN_CTA_BUTTON,
                        # Route through our /go endpoint so the click-through to the
                        # results site is tracked (cta_click event) before redirect.
                        url=build_cta_url(chat_id),
                    )]
                ])
                await message.answer(
                    ru_strings.MEAL_PLAN_CTA,
                    reply_markup=cta_kb,
                    parse_mode="HTML",
                )
                await save_user_event(
                    chat_id, "funnel_message", "meal_plan_cta", "ru", "funnel",
                    message_text=ru_strings.MEAL_PLAN_CTA,
                )
                logger.info("meal_plan_cta_sent", chat_id=chat_id)
            except Exception as e:
                logger.error("meal_plan_cta_failed", chat_id=chat_id, error=str(e))

    logger.info("meal_plan_sent", chat_id=chat_id, calories=macros.calories)


# ─── Confirmation callbacks ──────────────────────────────────────────────

_FIX_PROMPTS = {
    "ru": "Что нужно исправить? Напиши, какие данные неверны, и я обновлю.",
    "en": "What needs to be fixed? Tell me which data is incorrect and I'll update it.",
    "ar": "ما الذي يحتاج إلى تصحيح؟ أخبرني بالبيانات غير الصحيحة وسأقوم بتحديثها.",
}

# Confirmation phrases per language — sent as user message to the agent
_CONFIRM_PHRASES = {
    "ru": "Да, всё верно, подтверждаю",
    "en": "Yes, everything is correct, I confirm",
    "ar": "نعم، كل شيء صحيح، أؤكد",
}


@router.callback_query(F.data == "confirm_data")
async def handle_confirm_data(callback: CallbackQuery, bot: Bot, db_user: User | None) -> None:
    """User confirmed collected data — send confirmation to agent to trigger generation."""
    await callback.answer()
    if not callback.message:
        return

    chat_id = callback.message.chat.id
    lang = (db_user.language if db_user else None) or "en"
    confirm_text = _CONFIRM_PHRASES.get(lang, _CONFIRM_PHRASES["en"])

    logger.info("confirm_data_callback", chat_id=chat_id, lang=lang)
    await save_user_event(chat_id, "button_click", "confirm_data", lang, "conversation")

    # Remove buttons from the confirmation message
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Process as if the user typed the confirmation
    # Use override_ params because callback.message.from_user is the bot, not the user
    await _process_text_message(
        callback.message, bot, db_user, confirm_text,
        override_username=callback.from_user.username if callback.from_user else None,
        override_first_name=callback.from_user.first_name if callback.from_user else None,
    )


@router.callback_query(F.data == "fix_data")
async def handle_fix_data(callback: CallbackQuery, bot: Bot, db_user: User | None) -> None:
    """User wants to fix data — ask what to change."""
    await callback.answer()
    if not callback.message:
        return

    chat_id = callback.message.chat.id
    lang = (db_user.language if db_user else None) or "en"

    logger.info("fix_data_callback", chat_id=chat_id, lang=lang)
    await save_user_event(chat_id, "button_click", "fix_data", lang, "conversation")

    # Remove buttons from the confirmation message
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    fix_prompt = _FIX_PROMPTS.get(lang, _FIX_PROMPTS["en"])
    await bot.send_message(chat_id, fix_prompt)


@router.callback_query(F.data == "check_subscription")
async def handle_check_subscription(callback: CallbackQuery, bot: Bot, db_user: User | None) -> None:
    """RU user clicked "Я подписалась" — verify and resume KBJU flow."""
    await callback.answer()
    if not callback.message or not callback.from_user:
        return

    chat_id = callback.from_user.id
    logger.info("check_subscription_callback", chat_id=chat_id)
    await save_user_event(chat_id, "button_click", "check_subscription", "ru", "subscription")

    if not await is_subscribed(bot, chat_id):
        await save_user_event(chat_id, "subscription_gate", "not_subscribed", "ru", "subscription")
        await bot.send_message(chat_id, ru_strings.SUBSCRIPTION_NOT_FOUND)
        return

    pending = _PENDING_SUBSCRIPTION.pop(chat_id, None)
    if pending is None:
        # Cache lost (bot restart, etc.) — ask the user to start over.
        logger.warning("subscription_pending_missing", chat_id=chat_id)
        await bot.send_message(chat_id, ru_strings.SUBSCRIPTION_EXPIRED)
        return

    await save_user_event(chat_id, "subscription_gate", "passed", "ru", "subscription")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await bot.send_message(chat_id, ru_strings.SUBSCRIPTION_CONFIRMED, parse_mode="HTML")

    user_data = pending["user_data"]
    username = pending["username"] or (callback.from_user.username or "unknown")
    first_name = pending["first_name"] or (callback.from_user.first_name or "")

    await _calculate_and_send_meal_plan(
        callback.message, bot, chat_id, user_data,
        username=username,
        first_name=first_name,
        detected_lang="ru",
    )
