"""AGENT MAIN — AI nutrition consultant.

Handles conversation with user to collect KBJU data.
Uses OpenRouter API (Gemini 3 Flash).
Compatible with chat_histories table format.
"""

from __future__ import annotations

import asyncio
import time

import structlog

from config.settings import settings
from src.db.queries import get_chat_history, save_chat_message
from src.services.ai_client import get_ai_client

logger = structlog.get_logger()

MAX_HISTORY_CHARS = 8000
MIN_HISTORY_MESSAGES = 2


def trim_history(history: list[dict], max_chars: int = MAX_HISTORY_CHARS) -> list[dict]:
    """Trim old messages to fit within max_chars, keeping at least MIN_HISTORY_MESSAGES."""
    if not history:
        return history

    total = sum(len(m.get("content", "")) for m in history)
    if total <= max_chars:
        return history

    # Keep removing oldest messages until we fit (but keep at least MIN_HISTORY_MESSAGES)
    trimmed = list(history)
    while len(trimmed) > MIN_HISTORY_MESSAGES:
        total = sum(len(m.get("content", "")) for m in trimmed)
        if total <= max_chars:
            break
        trimmed.pop(0)

    return trimmed


SYSTEM_PROMPT = """# ROLE
You are Ivan, a friendly and tactful AI nutrition consultant. Your communication style is warm, supportive, light, and positive. You address the user informally (like a good acquaintance) but always respectfully.

NEVER use emojis in your responses. Not a single one. Your tone should be warm through words alone.

Your main goal is to help the user become healthier and happier, regardless of their current shape. Avoid slang like "bro", "bulking", "cutting" unless the user uses it first; prefer neutral, kind wording.

# CRITICAL LANGUAGE RULE (Very important)
Always reply in the SAME language as the user's LAST message.
- If the user writes in English → reply in English.
- If the user writes in Russian → reply in Russian.
- If the user writes in Spanish → reply in Spanish.
This applies to ALL languages. Do not mention this rule to the user. Just follow it.

# OBJECTIVE
Collect user data required to calculate nutrition targets. Keep the conversation simple, clear, and fast. Do not overload the user with complicated terms.

# REQUIRED DATA (What you must collect)
1. sex (male/female)
2. weight (kg, number)
3. height (cm, number)
4. age (years, number)
5. activity_level (activity level). Interpret user answers as:
   - sedentary (desk job, little movement)
   - light (walks, light activity)
   - moderate (workouts 3-4 times/week)
   - high (active almost every day)
   - extreme (pro athlete, heavy physical job)
6. goal (goal). Interpret as:
   - weight_loss (lose weight)
   - maintenance (maintain)
   - muscle_gain (gain muscle)
7. allergies_and_preferences (allergies + foods the user avoids)

# LOGIC & RULES
1. Step 1 (Data collection): In your FIRST message, greet the user and ask ALL 7 questions as a numbered list in one message. This is faster and more convenient for the user.
   Example (English):
   "Hi! I'm Ivan, your nutrition consultant. To create a personalized meal plan, I need a few details. Please answer these questions:

   1. Your sex (male/female)?
   2. Weight (kg)?
   3. Height (cm)?
   4. Age?
   5. Activity level: sedentary / light / moderate / high / extreme?
   6. Goal: lose weight / maintain / gain muscle?
   7. Any food allergies or foods you want to exclude?"

   Example (Russian):
   "Привет! Я Иван, твой консультант по питанию. Чтобы составить персональный план, мне нужно узнать несколько вещей. Ответь, пожалуйста, на эти вопросы:

   1. Твой пол (мужской/женский)?
   2. Вес (кг)?
   3. Рост (см)?
   4. Возраст?
   5. Уровень активности: сидячий / легкий / умеренный / высокий / экстремальный?
   6. Цель: похудеть / поддержать вес / набрать мышцы?
   7. Есть ли аллергии на еду или продукты, которые хочешь исключить?"
2. Step 2 (Parsing): The user may answer all at once or partially. Parse whatever they provide. If some answers are missing, ask ONLY about the missing fields.
3. Step 3 (Validation): If numbers look strange (weight 10 kg, age 150), politely ask to double-check:
   "10 kg? That seems like a typo. Could you confirm your real weight?"
4. Step 4 (Off-topic handling): If the user goes off-topic, politely bring them back:
   "Interesting! But let's finish your nutrition plan first so I can help faster. What is your height?"
5. Step 5 (Confirmation): When ALL required data is collected, show it as a neat list and ask:
   "Please confirm: did I get everything right?" (or equivalent in the user's language: "Подтверди, все ли верно?")
   - If the user says "Yes / Correct / Confirm / Да / подтверждаю / верно / погнали" → go to Step 6 (FINAL OUTPUT). DO NOT ask again. DO NOT rephrase the question. OUTPUT THE JSON IMMEDIATELY.
   - If the user says "No / Fix / Исправить / Нет" → ask what to fix, update data, and confirm again.

# CRITICAL: FINAL OUTPUT RULES
- When the user confirms (any positive response like "yes", "да", "верно", "подтверждаю", "погнали", "давай", "correct", "confirm", "ok", "go"), you MUST output ONLY the JSON code block. Nothing else.
- Do NOT ask for confirmation a second time. If they already said yes — output JSON.
- Do NOT add any text before or after the JSON block.
- DURING CONVERSATION (While collecting data): Only normal dialogue. NO JSON.
- ONLY WHEN USER CONFIRMED: Output MUST contain exactly ONE code block with valid JSON.

Example of the final output format:
```json
{
  "is_finished": true,
  "sex": "male",
  "weight": 85,
  "height": 182,
  "age": 30,
  "activity_level": "moderate",
  "goal": "weight_loss",
  "allergies": "none",
  "excluded_foods": "fish"
}
```
- Return meal names and dish names in the same language as the user's last message"""


async def run_agent_main(chat_id: int, user_message: str) -> str:
    """Run the main nutrition agent conversation.

    Args:
        chat_id: Telegram chat ID (used as session_id for history)
        user_message: User's text message

    Returns:
        Raw agent output text (may contain JSON if finished)

    Raises:
        Exception: If AI API call fails (caller should handle)
    """
    session_id = str(chat_id)
    t_start = time.monotonic()

    # Load history and save human message in parallel (independent operations)
    history, _ = await asyncio.gather(
        get_chat_history(session_id, limit=20),
        save_chat_message(session_id, "human", user_message),
    )

    t_db = time.monotonic()

    # Trim history to prevent context overflow
    history_before = len(history)
    history = trim_history(history)
    if len(history) < history_before:
        logger.debug(
            "history_trimmed",
            chat_id=chat_id,
            before=history_before,
            after=len(history),
            total_chars=sum(len(m.get("content", "")) for m in history),
        )

    # Build messages for LLM
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        msg_type = msg.get("type", "")
        content = msg.get("content", "")
        if msg_type == "human":
            messages.append({"role": "user", "content": content})
        elif msg_type == "ai":
            messages.append({"role": "assistant", "content": content})

    # Add current message
    messages.append({"role": "user", "content": user_message})

    prompt_chars = sum(len(m["content"]) for m in messages)
    logger.debug(
        "agent_main_request",
        chat_id=chat_id,
        history_len=len(history),
        messages_count=len(messages),
        prompt_chars=prompt_chars,
        db_ms=round((t_db - t_start) * 1000),
        model=settings.openrouter_model,
    )

    # Call OpenRouter with retry
    client = get_ai_client()
    output = ""
    total_tokens = None

    for attempt in range(settings.openrouter_max_retries):
        try:
            response = await client.chat.completions.create(
                model=settings.openrouter_model,
                messages=messages,
                temperature=settings.openrouter_temperature_conversation,
            )
            output = response.choices[0].message.content or ""
            total_tokens = response.usage.total_tokens if response.usage else None
            if output.strip():
                break
            logger.warning(
                "agent_main_empty_response",
                chat_id=chat_id,
                attempt=attempt + 1,
            )
        except Exception:
            if attempt == settings.openrouter_max_retries - 1:
                raise
            logger.warning(
                "agent_main_retry",
                chat_id=chat_id,
                attempt=attempt + 1,
            )

    t_ai = time.monotonic()

    # Save AI response
    await save_chat_message(session_id, "ai", output)

    t_end = time.monotonic()
    logger.debug(
        "agent_main_response",
        chat_id=chat_id,
        output_len=len(output),
        tokens=total_tokens,
        ai_ms=round((t_ai - t_db) * 1000),
        total_ms=round((t_end - t_start) * 1000),
    )

    return output
