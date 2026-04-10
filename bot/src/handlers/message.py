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

from src.db.queries import save_chat_message, save_user_data, save_user_event, set_food_received
from src.handlers.start import LANGUAGE_CHOOSE_MESSAGE, _make_language_keyboard
from src.i18n import get_strings
from src.models.user import User
from src.models.user_data import CollectedUserData
from src.services.ai_agent import run_agent_main
from src.services.ai_client import get_ai_client
from src.services.ai_food import run_agent_food
from src.services.calculator import calculate_macros
from src.services.formatter import (
    format_meal_plan_html,
    parse_agent_output,
    validate_meal_plan,
)
from src.services.language import detect_language

logger = structlog.get_logger()

router = Router()

# Test account — always allow recalculation (skip get_food check)
TEST_CHAT_ID = 379336096

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

    # Calculate KBJU
    macros = calculate_macros(
        sex=user_data.sex,
        weight=user_data.weight,
        height=user_data.height,
        age=user_data.age,
        activity_level=user_data.activity_level,
        goal=user_data.goal,
    )

    # Send "calculating..." message and save to database in parallel
    strings = get_strings(detected_lang)

    async def _save() -> None:
        await save_user_data(
            chat_id=chat_id,
            username=username,
            first_name=override_first_name or (message.from_user.first_name if message.from_user else ""),
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

    # Generate meal plan
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

    # Validate
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

    # Format, save to chat history, and send
    html = format_meal_plan_html(menu_data, calc_stats, target_stats, language=detected_lang)
    await save_chat_message(str(chat_id), "ai", html)
    await message.answer(html, parse_mode="HTML")

    # Mark as food received → starts funnel (skip for test account)
    if chat_id != TEST_CHAT_ID:
        await set_food_received(chat_id, language=detected_lang)

        # RU: send "Разбуди тело" + zone selection (5 sec apart)
        if detected_lang == "ru":
            try:
                ru_strings = get_strings("ru")
                # Message 1: wakeup
                wakeup_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=ru_strings.FUNNEL_STAGE_0_WAKEUP_BUTTON,
                        url=ru_strings.FUNNEL_STAGE_0_WAKEUP_URL,
                    )]
                ])
                await message.answer(
                    ru_strings.FUNNEL_STAGE_0_WAKEUP,
                    reply_markup=wakeup_kb,
                )
                await save_user_event(chat_id, "funnel_message", "wakeup_sent", "ru", "funnel")
                logger.info("wakeup_message_sent", chat_id=chat_id)

                # Message 2: zone selection (5 sec later)
                await asyncio.sleep(5)
                from src.funnel.messages import get_funnel_message
                from src.funnel.sender import _build_keyboard
                zone_msg = get_funnel_message(0, "ru")
                if zone_msg:
                    zone_kb = _build_keyboard(zone_msg)
                    await message.answer(
                        zone_msg.text,
                        reply_markup=zone_kb,
                    )
                    await save_user_event(chat_id, "funnel_message", "stage_0_zone_ask", "ru", "funnel")
                    logger.info("zone_selection_sent", chat_id=chat_id)
            except Exception as e:
                logger.error("wakeup_message_failed", chat_id=chat_id, error=str(e))

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
