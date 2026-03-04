"""Handler for text and voice messages — main conversation flow.

Flow (port of n8n MAIN v2):
1. Check if user already got food (get_food=True) → reject
2. Text: detect language → send to AGENT MAIN
3. Voice: download → transcribe → send to AGENT MAIN
4. Parse agent response:
   - conversation → send text to user
   - generate → calculate macros → save to DB → AGENT FOOD → send menu
"""

from __future__ import annotations

import structlog
from aiogram import Bot, Router, F
from aiogram.types import Message

from src.db.queries import save_user_data, set_food_received
from src.i18n import get_strings
from src.models.user import User
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


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot, db_user: User | None) -> None:
    """Handle voice messages: download → transcribe → process as text."""
    if db_user and db_user.get_food:
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
    if db_user and db_user.get_food:
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
) -> None:
    """Core message processing logic."""
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user else "unknown"
    detected_lang = detect_language(text)

    logger.debug("processing_message", chat_id=chat_id, lang=detected_lang, text=text[:100])

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
            await message.answer(response.text_response, parse_mode="HTML")
        else:
            logger.warning("empty_agent_response", chat_id=chat_id)
        return

    # route_type == "generate" — user data collected, calculate macros
    data = response.data
    if not data:
        logger.error("generate_route_but_no_data", chat_id=chat_id)
        return

    logger.info("data_collection_finished", chat_id=chat_id, data=data)

    # Calculate KBJU
    macros = calculate_macros(
        sex=data.get("sex", "female"),
        weight=float(data.get("weight", 70)),
        height=float(data.get("height", 165)),
        age=int(data.get("age", 25)),
        activity_level=data.get("activity_level", "moderate"),
        goal=data.get("goal", "maintenance"),
    )

    # Save to database
    await save_user_data(
        chat_id=chat_id,
        username=username,
        first_name=message.from_user.first_name if message.from_user else "",
        sex=data.get("sex", ""),
        age=int(data.get("age", 0)),
        weight=float(data.get("weight", 0)),
        height=float(data.get("height", 0)),
        activity_level=data.get("activity_level", ""),
        goal=data.get("goal", ""),
        allergies=data.get("allergies", "none"),
        excluded_foods=data.get("excluded_foods", "none"),
        calories=macros.calories,
        protein=macros.protein,
        fats=macros.fats,
        carbs=macros.carbs,
        language=detected_lang,
    )

    # Send "calculating..." message
    strings = get_strings(detected_lang)
    await message.answer(strings.CALCULATING_MENU, parse_mode="HTML")

    # Generate meal plan
    try:
        menu_data = await run_agent_food(
            calories=macros.calories,
            protein=macros.protein,
            fats=macros.fats,
            carbs=macros.carbs,
            excluded_foods=data.get("excluded_foods", "none"),
            allergies=data.get("allergies", "none"),
            language=detected_lang,
        )
    except Exception as e:
        logger.error("agent_food_failed", chat_id=chat_id, error=str(e))
        await message.answer(strings.AI_ERROR)
        return

    logger.info("agent_food_result", chat_id=chat_id, menu_data=menu_data)

    # Validate
    target_stats = {
        "calories": macros.calories,
        "protein": macros.protein,
        "fats": macros.fats,
        "carbs": macros.carbs,
    }

    is_valid, error, calc_stats = validate_meal_plan(
        menu_data, macros.calories, data.get("excluded_foods", "none")
    )

    if not is_valid:
        logger.warning("meal_plan_validation_failed", error=error, chat_id=chat_id)

    # Format and send
    html = format_meal_plan_html(menu_data, calc_stats, target_stats, language=detected_lang)
    await message.answer(html, parse_mode="HTML")

    # Mark as food received → starts funnel
    await set_food_received(chat_id)
    logger.info("meal_plan_sent", chat_id=chat_id, calories=macros.calories)
