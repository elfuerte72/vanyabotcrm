from __future__ import annotations

import json
from typing import Any

import asyncpg
import structlog

from src.db.pool import get_pool
from src.models.user import User

logger = structlog.get_logger()


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


async def set_food_received(chat_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users_nutrition
        SET get_food = TRUE, funnel_stage = 0, last_funnel_msg_at = NOW()
        WHERE chat_id = $1
        """,
        chat_id,
    )
    logger.info("food_received_flag_set", chat_id=chat_id)


async def get_funnel_targets() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT chat_id, funnel_stage, language
        FROM users_nutrition
        WHERE (is_buyer IS FALSE OR is_buyer IS NULL)
          AND get_food = TRUE
          AND funnel_stage >= 0
          AND funnel_stage < 5
        """
    )
    return [dict(row) for row in rows]


async def update_funnel_stage(chat_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users_nutrition
        SET funnel_stage = funnel_stage + 1, last_funnel_msg_at = NOW()
        WHERE chat_id = $1
        """,
        chat_id,
    )
    logger.debug("funnel_stage_updated", chat_id=chat_id)


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


# --- Chat history (compatible with n8n_chat_histories) ---

async def get_chat_history(session_id: str, limit: int = 20) -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT message FROM n8n_chat_histories
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
        INSERT INTO n8n_chat_histories (session_id, message)
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
