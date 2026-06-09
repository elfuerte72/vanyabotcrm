from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg
import structlog

from src.db.pool import get_pool
from src.models.user import User

logger = structlog.get_logger()

# Max funnel stage per language (RU has no scheduled funnel anymore)
_MAX_STAGE = {"en": 10, "ar": 10}


def calculate_next_send_time(
    current_stage: int, language: str, has_variant: bool = False, variant: str | None = None,
) -> datetime | None:
    """Calculate absolute UTC time for the NEXT funnel message after current_stage is sent.

    Only EN/AR have a scheduled funnel: 11 stages (0-10), 5 min after stage 0,
    24h for stages 1-9. RU no longer has a scheduled funnel (a single CTA message
    is sent inline right after the meal plan), so this returns None for RU.
    Returns None if current_stage is the last stage.
    """
    now = datetime.now(timezone.utc)
    if language not in ("en", "ar"):
        return None

    max_stage = _MAX_STAGE.get(language, 10)
    if current_stage >= max_stage:
        return None

    # EN/AR: 5 min after stage 0, 24h for stages 1-9 (incl. upsell)
    if current_stage == 0:
        return now + timedelta(minutes=5)
    if current_stage <= 9:
        return now + timedelta(hours=24)
    return None


async def get_user(chat_id: int) -> User | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM users_nutrition WHERE chat_id = $1", chat_id
    )
    if row is None:
        return None
    return User.from_row(row)


async def save_user_data(
    chat_id: int,
    username: str,
    sex: str,
    age: int,
    weight: float,
    height: float,
    activity_level: str,
    goal: str,
    allergies: str,
    excluded_foods: str,
    calories: int,
    protein: int,
    fats: int,
    carbs: int,
    language: str,
    first_name: str = "",
) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO users_nutrition (
            chat_id, username, first_name, sex, age, weight, height,
            activity_level, goal, allergies, excluded_foods,
            calories, protein, fats, carbs, language, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW())
        ON CONFLICT (chat_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            sex = EXCLUDED.sex,
            age = EXCLUDED.age,
            weight = EXCLUDED.weight,
            height = EXCLUDED.height,
            activity_level = EXCLUDED.activity_level,
            goal = EXCLUDED.goal,
            allergies = EXCLUDED.allergies,
            excluded_foods = EXCLUDED.excluded_foods,
            calories = EXCLUDED.calories,
            protein = EXCLUDED.protein,
            fats = EXCLUDED.fats,
            carbs = EXCLUDED.carbs,
            language = EXCLUDED.language,
            get_food = FALSE,
            updated_at = NOW()
        """,
        chat_id, username, first_name, sex, age, weight, height,
        activity_level, goal, allergies, excluded_foods,
        calories, protein, fats, carbs, language,
    )
    logger.info("user_data_saved", chat_id=chat_id, calories=calories)


async def mark_as_buyer(chat_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE users_nutrition SET is_buyer = TRUE WHERE chat_id = $1",
        chat_id,
    )
    logger.info("user_marked_as_buyer", chat_id=chat_id)


async def save_ziina_payment(chat_id: int, payment_intent_id: str, amount_aed: int) -> None:
    """Store Ziina payment intent ID for later webhook lookup."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE users_nutrition SET id_ziina = $1, type_ziina = $2 WHERE chat_id = $3",
        payment_intent_id,
        amount_aed,
        chat_id,
    )
    logger.info("ziina_payment_saved", chat_id=chat_id, intent_id=payment_intent_id, amount=amount_aed)


async def get_chat_id_by_ziina_payment(payment_intent_id: str) -> int | None:
    """Look up chat_id by Ziina payment intent ID."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT chat_id FROM users_nutrition WHERE id_ziina = $1",
        payment_intent_id,
    )
    return int(row["chat_id"]) if row else None


async def set_food_received(chat_id: int, language: str = "ru") -> None:
    # RU: a single CTA message is sent inline from the handler — no scheduled funnel,
    #     so next_funnel_msg_at stays NULL and the scheduler never picks RU up.
    # EN/AR: first funnel message in 5 min.
    next_send = (
        None if language == "ru"
        else datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users_nutrition
        SET get_food = TRUE, funnel_stage = 0,
            last_funnel_msg_at = NOW(), next_funnel_msg_at = $2
        WHERE chat_id = $1
        """,
        chat_id, next_send,
    )
    logger.info(
        "food_received_flag_set",
        chat_id=chat_id,
        next_send=next_send.isoformat() if next_send else None,
    )


async def get_funnel_targets() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT chat_id, funnel_stage, language, funnel_variant
        FROM users_nutrition
        WHERE get_food = TRUE
          AND funnel_stage >= 0
          AND language IN ('en', 'ar')
          AND (
            -- New: use next_funnel_msg_at if set
            (next_funnel_msg_at IS NOT NULL AND next_funnel_msg_at <= NOW())
            OR
            -- Fallback for old records without next_funnel_msg_at
            (next_funnel_msg_at IS NULL AND funnel_stage <= 5 AND (
              (funnel_stage = 0 AND last_funnel_msg_at + interval '2 hours' <= NOW())
              OR
              (funnel_stage > 0 AND last_funnel_msg_at + interval '23 hours' <= NOW())
            ))
          )
        """
    )
    return [dict(row) for row in rows]


async def update_funnel_stage(
    chat_id: int, language: str = "ru", current_stage: int = 0,
    has_variant: bool = True, variant: str | None = None,
) -> None:
    next_send = calculate_next_send_time(current_stage, language, has_variant=has_variant, variant=variant)
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = funnel_stage + 1,
            last_funnel_msg_at = NOW(),
            next_funnel_msg_at = $2
        WHERE chat_id = $1
        """,
        chat_id, next_send,
    )
    logger.debug(
        "funnel_stage_updated",
        chat_id=chat_id,
        from_stage=current_stage,
        next_send=next_send.isoformat() if next_send else None,
    )


async def advance_funnel_if_at_stage(chat_id: int, expected_stage: int) -> bool:
    """Advance funnel only if user is at the expected stage. Returns True if updated."""
    pool = await get_pool()
    result = await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = funnel_stage + 1, last_funnel_msg_at = NOW()
        WHERE chat_id = $1 AND funnel_stage = $2
        """,
        chat_id, expected_stage,
    )
    updated = result == "UPDATE 1"
    if updated:
        logger.debug("funnel_stage_advanced", chat_id=chat_id, from_stage=expected_stage)
    return updated


# --- Chat history (compatible with chat_histories) ---

async def get_chat_history(session_id: str, limit: int = 20) -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT message FROM chat_histories
        WHERE session_id = $1
        ORDER BY id DESC
        LIMIT $2
        """,
        session_id, limit,
    )
    messages = []
    for row in reversed(rows):
        msg = row["message"]
        if isinstance(msg, str):
            msg = json.loads(msg)
        messages.append(msg)
    return messages


async def save_chat_message(session_id: str, role: str, content: str) -> None:
    pool = await get_pool()
    message = json.dumps({"type": role, "content": content})
    await pool.execute(
        """
        INSERT INTO chat_histories (session_id, message)
        VALUES ($1, $2::jsonb)
        """,
        session_id, message,
    )
    logger.debug("chat_message_saved", session_id=session_id, role=role)


async def get_user_language(chat_id: int) -> str | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT language FROM users_nutrition WHERE chat_id = $1", chat_id
    )
    return row["language"] if row else None


async def save_user_language(
    chat_id: int, language: str, username: str = "", first_name: str = ""
) -> None:
    """UPSERT minimal user record with language. Used when new user picks language at /start."""
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO users_nutrition (chat_id, username, first_name, language, updated_at)
        VALUES ($1, $2, $3, $4, NOW())
        ON CONFLICT (chat_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            language = EXCLUDED.language,
            updated_at = NOW()
        """,
        chat_id, username, first_name, language,
    )
    logger.info("user_language_saved", chat_id=chat_id, language=language)


async def update_user_language(chat_id: int, language: str) -> None:
    """Update language for an existing user. Used by /language command."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE users_nutrition SET language = $1, updated_at = NOW() WHERE chat_id = $2",
        language, chat_id,
    )
    logger.info("user_language_updated", chat_id=chat_id, language=language)


async def save_user_event(
    chat_id: int,
    event_type: str,
    event_data: str,
    language: str | None = None,
    workflow_name: str | None = None,
    message_text: str | None = None,
    media: dict | None = None,
) -> None:
    """Save a user interaction event (button click, funnel message, etc.) to user_events.

    `media` holds funnel attachments as {"photos": [...], "video_note": bool} so the
    CRM can render images; stored as JSONB (NULL when the message has no media).
    """
    pool = await get_pool()
    media_json = json.dumps(media) if media else None
    await pool.execute(
        """
        INSERT INTO user_events (chat_id, event_type, event_data, language, workflow_name, message_text, media)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
        """,
        chat_id, event_type, event_data, language, workflow_name, message_text, media_json,
    )
    logger.debug(
        "user_event_saved",
        chat_id=chat_id,
        event_type=event_type,
        event_data=event_data,
        language=language,
        workflow_name=workflow_name,
    )


async def clear_chat_history(session_id: str) -> None:
    """Delete all chat history for a given session."""
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM chat_histories WHERE session_id = $1", session_id
    )
    logger.info("chat_history_cleared", session_id=session_id)
