from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from typing import Any

import asyncpg
import structlog

from src.db.pool import get_pool
from src.models.user import User

logger = structlog.get_logger()

# Moscow timezone: UTC+3
_MSK = timezone(timedelta(hours=3))

# Max funnel stage per language
_MAX_STAGE = {"ru": 7, "en": 5, "ar": 5}


def calculate_next_send_time(current_stage: int, language: str) -> datetime | None:
    """Calculate absolute UTC time for the NEXT funnel message after current_stage is sent.

    RU has 8 stages (0-7) with specific MSK times.
    EN/AR have 6 stages (0-5) with simple interval delays.
    Returns None if current_stage is the last stage.
    """
    now = datetime.now(timezone.utc)
    max_stage = _MAX_STAGE.get(language, 5)

    if current_stage >= max_stage:
        return None

    if language != "ru":
        # EN/AR: 2h after stage 0, 23h after stages 1-4
        if current_stage == 0:
            return now + timedelta(hours=2)
        return now + timedelta(hours=23)

    # RU stage timing map: after sending stage N, next message at:
    msk_now = now.astimezone(_MSK)
    tomorrow = msk_now.date() + timedelta(days=1)

    if current_stage == 0:
        # Stage 1: +2.5h from now
        return now + timedelta(hours=2, minutes=30)
    elif current_stage == 1:
        # Stage 2: tomorrow 10:00 MSK
        return datetime.combine(tomorrow, time(10, 0), tzinfo=_MSK).astimezone(timezone.utc)
    elif current_stage == 2:
        # Stage 3: tomorrow 10:00 MSK
        return datetime.combine(tomorrow, time(10, 0), tzinfo=_MSK).astimezone(timezone.utc)
    elif current_stage == 3:
        # Stage 4: today 19:00 MSK (same day, +9h)
        target = datetime.combine(msk_now.date(), time(19, 0), tzinfo=_MSK)
        if target <= msk_now:
            target = datetime.combine(tomorrow, time(19, 0), tzinfo=_MSK)
        return target.astimezone(timezone.utc)
    elif current_stage == 4:
        # Stage 5: tomorrow 19:00 MSK
        return datetime.combine(tomorrow, time(19, 0), tzinfo=_MSK).astimezone(timezone.utc)
    elif current_stage == 5:
        # Stage 6: tomorrow 11:00 MSK
        return datetime.combine(tomorrow, time(11, 0), tzinfo=_MSK).astimezone(timezone.utc)
    elif current_stage == 6:
        # Stage 7: tomorrow 10:00 MSK
        return datetime.combine(tomorrow, time(10, 0), tzinfo=_MSK).astimezone(timezone.utc)

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


async def set_food_received(chat_id: int, language: str = "ru") -> None:
    next_send = datetime.now(timezone.utc) + timedelta(minutes=30)
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
    logger.info("food_received_flag_set", chat_id=chat_id, next_send=next_send.isoformat())


async def get_funnel_targets() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT chat_id, funnel_stage, language
        FROM users_nutrition
        WHERE (is_buyer IS FALSE OR is_buyer IS NULL)
          AND get_food = TRUE
          AND funnel_stage >= 0
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
    chat_id: int, language: str = "ru", current_stage: int = 0
) -> None:
    next_send = calculate_next_send_time(current_stage, language)
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


async def clear_chat_history(session_id: str) -> None:
    """Delete all chat history for a given session."""
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM chat_histories WHERE session_id = $1", session_id
    )
    logger.info("chat_history_cleared", session_id=session_id)
