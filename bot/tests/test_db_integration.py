"""Integration tests for database queries with real PostgreSQL.

These tests create temporary records (chat_id 99990001-99990010),
verify query behavior, and clean up after themselves.

Requires DATABASE_URL env var pointing to a real PostgreSQL instance.
"""

from __future__ import annotations

import os
import ssl
import json

import asyncpg
import pytest
import pytest_asyncio

# Use DATABASE_URL from environment for integration tests
if not os.environ.get("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set — skipping integration tests", allow_module_level=True)
os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

from src.db.queries import (
    advance_funnel_if_at_stage,
    get_user,
    save_user_data,
    mark_as_buyer,
    set_food_received,
    get_funnel_targets,
    update_funnel_stage,
    get_chat_history,
    save_chat_message,
    get_user_language,
)
import src.db.pool as pool_module
from src.db.pool import get_pool, close_pool

# Test chat_ids to avoid collision with real users
TEST_CHAT_IDS = [99990001, 99990002, 99990003, 99990004, 99990005]
TEST_SESSION_ID = "99990001"


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data():
    """Clean up test records before and after each test."""
    # Reset pool singleton so it creates a new pool on the current event loop
    if pool_module._pool is not None:
        try:
            await pool_module._pool.close()
        except Exception:
            pass
    pool_module._pool = None

    pool = await get_pool()
    # Pre-cleanup
    for cid in TEST_CHAT_IDS:
        await pool.execute("DELETE FROM users_nutrition WHERE chat_id = $1", cid)
        await pool.execute(
            "DELETE FROM n8n_chat_histories WHERE session_id = $1", str(cid)
        )
    yield
    # Post-cleanup (reuse same pool)
    for cid in TEST_CHAT_IDS:
        await pool.execute("DELETE FROM users_nutrition WHERE chat_id = $1", cid)
        await pool.execute(
            "DELETE FROM n8n_chat_histories WHERE session_id = $1", str(cid)
        )


@pytest.fixture
def chat_id() -> int:
    return TEST_CHAT_IDS[0]


# ─── save_user_data & get_user ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_and_get_user(chat_id: int):
    """save_user_data inserts a new user; get_user retrieves it correctly."""
    await save_user_data(
        chat_id=chat_id,
        username="testuser",
        sex="male",
        age=30,
        weight=80.0,
        height=180.0,
        activity_level="moderate",
        goal="weight_loss",
        allergies="none",
        excluded_foods="none",
        calories=2000,
        protein=120,
        fats=80,
        carbs=200,
        language="ru",
    )

    user = await get_user(chat_id)
    assert user is not None, f"User {chat_id} not found after insert"
    assert user.chat_id == chat_id
    assert user.username == "testuser"
    assert user.sex == "male"
    assert user.age == 30
    assert user.weight == 80.0
    assert user.height == 180.0
    assert user.activity_level == "moderate"
    assert user.goal == "weight_loss"
    assert user.calories == 2000
    assert user.protein == 120
    assert user.fats == 80
    assert user.carbs == 200
    assert user.language == "ru"
    assert user.get_food is False  # default
    assert user.is_buyer is False  # default


@pytest.mark.asyncio
async def test_save_user_data_upsert(chat_id: int):
    """save_user_data updates existing user on conflict (UPSERT)."""
    # Insert
    await save_user_data(
        chat_id=chat_id, username="user1", sex="male", age=25,
        weight=70.0, height=175.0, activity_level="light", goal="maintenance",
        allergies="none", excluded_foods="none",
        calories=1800, protein=100, fats=70, carbs=220, language="en",
    )
    # Update same chat_id
    await save_user_data(
        chat_id=chat_id, username="user1_updated", sex="female", age=28,
        weight=60.0, height=165.0, activity_level="high", goal="muscle_gain",
        allergies="nuts", excluded_foods="fish",
        calories=2200, protein=130, fats=60, carbs=280, language="ru",
    )

    user = await get_user(chat_id)
    assert user is not None
    assert user.sex == "female"
    assert user.age == 28
    assert user.weight == 60.0
    assert user.goal == "muscle_gain"
    assert user.calories == 2200
    assert user.language == "ru"
    assert user.allergies == "nuts"


@pytest.mark.asyncio
async def test_save_user_data_resets_get_food(chat_id: int):
    """save_user_data sets get_food=FALSE on upsert (re-calculation resets funnel)."""
    # Insert and set food received
    await save_user_data(
        chat_id=chat_id, username="u", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(chat_id)

    user = await get_user(chat_id)
    assert user.get_food is True

    # Re-save → get_food should reset to FALSE
    await save_user_data(
        chat_id=chat_id, username="u", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2100, protein=125, fats=80, carbs=210, language="ru",
    )

    user = await get_user(chat_id)
    assert user.get_food is False, "get_food should be reset to FALSE on re-save"


@pytest.mark.asyncio
async def test_get_user_not_found():
    """get_user returns None for non-existent chat_id."""
    user = await get_user(999999999)
    assert user is None


# ─── mark_as_buyer ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_as_buyer(chat_id: int):
    """mark_as_buyer sets is_buyer=TRUE."""
    await save_user_data(
        chat_id=chat_id, username="buyer", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="en",
    )

    user = await get_user(chat_id)
    assert user.is_buyer is False

    await mark_as_buyer(chat_id)

    user = await get_user(chat_id)
    assert user.is_buyer is True


# ─── set_food_received ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_food_received(chat_id: int):
    """set_food_received sets get_food=TRUE, funnel_stage=0, last_funnel_msg_at."""
    await save_user_data(
        chat_id=chat_id, username="food", sex="female", age=25,
        weight=60.0, height=165.0, activity_level="light", goal="maintenance",
        allergies="none", excluded_foods="none",
        calories=1600, protein=90, fats=60, carbs=190, language="en",
    )

    await set_food_received(chat_id)

    user = await get_user(chat_id)
    assert user.get_food is True
    assert user.funnel_stage == 0
    assert user.last_funnel_msg_at is not None


# ─── get_funnel_targets ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_funnel_targets():
    """get_funnel_targets returns only non-buyers with funnel_stage 0-4."""
    # user_A: non-buyer, stage 0 → included
    await save_user_data(
        chat_id=TEST_CHAT_IDS[0], username="a", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(TEST_CHAT_IDS[0])

    # user_B: non-buyer, stage 4 → included
    await save_user_data(
        chat_id=TEST_CHAT_IDS[1], username="b", sex="female", age=25,
        weight=60.0, height=165.0, activity_level="light", goal="maintenance",
        allergies="none", excluded_foods="none",
        calories=1600, protein=90, fats=60, carbs=190, language="en",
    )
    await set_food_received(TEST_CHAT_IDS[1])
    # Advance to stage 4
    for _ in range(4):
        await update_funnel_stage(TEST_CHAT_IDS[1])

    # user_C: buyer → excluded
    await save_user_data(
        chat_id=TEST_CHAT_IDS[2], username="c", sex="male", age=35,
        weight=90.0, height=185.0, activity_level="high", goal="muscle_gain",
        allergies="none", excluded_foods="none",
        calories=2500, protein=135, fats=90, carbs=280, language="ar",
    )
    await set_food_received(TEST_CHAT_IDS[2])
    await mark_as_buyer(TEST_CHAT_IDS[2])

    # user_D: non-buyer, stage 5 → excluded (>= 5)
    await save_user_data(
        chat_id=TEST_CHAT_IDS[3], username="d", sex="female", age=28,
        weight=55.0, height=160.0, activity_level="sedentary", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=1400, protein=83, fats=55, carbs=155, language="ru",
    )
    await set_food_received(TEST_CHAT_IDS[3])
    for _ in range(5):
        await update_funnel_stage(TEST_CHAT_IDS[3])

    targets = await get_funnel_targets()
    target_ids = {t["chat_id"] for t in targets}

    assert TEST_CHAT_IDS[0] in target_ids, "Non-buyer stage 0 should be included"
    assert TEST_CHAT_IDS[1] in target_ids, "Non-buyer stage 4 should be included"
    assert TEST_CHAT_IDS[2] not in target_ids, "Buyer should be excluded"
    assert TEST_CHAT_IDS[3] not in target_ids, "Stage 5 should be excluded"


@pytest.mark.asyncio
async def test_get_funnel_targets_returns_language():
    """get_funnel_targets returns language for each target."""
    await save_user_data(
        chat_id=TEST_CHAT_IDS[0], username="lang", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ar",
    )
    await set_food_received(TEST_CHAT_IDS[0])

    targets = await get_funnel_targets()
    target = next(t for t in targets if t["chat_id"] == TEST_CHAT_IDS[0])
    assert target["language"] == "ar"
    assert target["funnel_stage"] == 0


# ─── update_funnel_stage ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_funnel_stage(chat_id: int):
    """update_funnel_stage increments funnel_stage by 1 and updates timestamp."""
    await save_user_data(
        chat_id=chat_id, username="stage", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(chat_id)

    user = await get_user(chat_id)
    assert user.funnel_stage == 0

    await update_funnel_stage(chat_id)
    user = await get_user(chat_id)
    assert user.funnel_stage == 1

    await update_funnel_stage(chat_id)
    user = await get_user(chat_id)
    assert user.funnel_stage == 2


# ─── advance_funnel_if_at_stage ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_advance_funnel_if_at_stage_matches(chat_id: int):
    """advance_funnel_if_at_stage increments when current stage matches expected."""
    await save_user_data(
        chat_id=chat_id, username="adv", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(chat_id)
    # Stage is 0 after set_food_received
    await update_funnel_stage(chat_id)
    # Now stage is 1

    result = await advance_funnel_if_at_stage(chat_id, expected_stage=1)
    assert result is True, "Should advance when stage matches"

    user = await get_user(chat_id)
    assert user.funnel_stage == 2


@pytest.mark.asyncio
async def test_advance_funnel_if_at_stage_no_match(chat_id: int):
    """advance_funnel_if_at_stage does NOT increment when stage doesn't match."""
    await save_user_data(
        chat_id=chat_id, username="noadv", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(chat_id)
    # Stage is 0

    result = await advance_funnel_if_at_stage(chat_id, expected_stage=3)
    assert result is False, "Should NOT advance when stage doesn't match"

    user = await get_user(chat_id)
    assert user.funnel_stage == 0, "Stage should remain unchanged"


@pytest.mark.asyncio
async def test_advance_funnel_if_at_stage_idempotent(chat_id: int):
    """advance_funnel_if_at_stage is idempotent — second call returns False."""
    await save_user_data(
        chat_id=chat_id, username="idem", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(chat_id)
    await update_funnel_stage(chat_id)  # stage → 1

    first = await advance_funnel_if_at_stage(chat_id, expected_stage=1)
    assert first is True

    second = await advance_funnel_if_at_stage(chat_id, expected_stage=1)
    assert second is False, "Second call should return False (already at stage 2)"

    user = await get_user(chat_id)
    assert user.funnel_stage == 2, "Stage should only increment once"


@pytest.mark.asyncio
async def test_update_funnel_stage_updates_timestamp(chat_id: int):
    """update_funnel_stage sets last_funnel_msg_at."""
    await save_user_data(
        chat_id=chat_id, username="ts", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ru",
    )
    await set_food_received(chat_id)

    user_before = await get_user(chat_id)
    ts_before = user_before.last_funnel_msg_at

    await update_funnel_stage(chat_id)

    user_after = await get_user(chat_id)
    assert user_after.last_funnel_msg_at is not None
    assert user_after.last_funnel_msg_at >= ts_before


# ─── Chat history ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_and_get_chat_history():
    """save_chat_message stores JSONB; get_chat_history returns oldest-first."""
    session_id = TEST_SESSION_ID

    await save_chat_message(session_id, "human", "Hello, I want to calculate KBJU")
    await save_chat_message(session_id, "ai", "Hi! Let me help you with that.")
    await save_chat_message(session_id, "human", "I'm male, 80 kg, 180 cm")
    await save_chat_message(session_id, "ai", "Great! And your age?")
    await save_chat_message(session_id, "human", "30 years old")

    messages = await get_chat_history(session_id)

    assert len(messages) == 5
    # Oldest first
    assert messages[0]["type"] == "human"
    assert messages[0]["content"] == "Hello, I want to calculate KBJU"
    assert messages[1]["type"] == "ai"
    assert messages[4]["type"] == "human"
    assert messages[4]["content"] == "30 years old"


@pytest.mark.asyncio
async def test_get_chat_history_limit():
    """get_chat_history respects limit parameter."""
    session_id = TEST_SESSION_ID

    for i in range(10):
        await save_chat_message(session_id, "human", f"Message {i}")

    messages = await get_chat_history(session_id, limit=3)
    assert len(messages) == 3
    # Should be the 3 MOST RECENT, returned oldest-first
    assert messages[0]["content"] == "Message 7"
    assert messages[2]["content"] == "Message 9"


@pytest.mark.asyncio
async def test_get_chat_history_empty():
    """get_chat_history returns empty list for non-existent session."""
    messages = await get_chat_history("nonexistent_session_99999")
    assert messages == []


@pytest.mark.asyncio
async def test_chat_message_jsonb_format():
    """Messages stored in JSONB format with type and content."""
    session_id = TEST_SESSION_ID
    await save_chat_message(session_id, "human", "Test content")

    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT message FROM n8n_chat_histories WHERE session_id = $1 ORDER BY id DESC LIMIT 1",
        session_id,
    )
    msg = row["message"]
    # asyncpg auto-parses JSONB
    if isinstance(msg, str):
        msg = json.loads(msg)
    assert msg["type"] == "human"
    assert msg["content"] == "Test content"


# ─── get_user_language ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_language(chat_id: int):
    """get_user_language returns correct language."""
    await save_user_data(
        chat_id=chat_id, username="lang", sex="male", age=30,
        weight=80.0, height=180.0, activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="ar",
    )

    lang = await get_user_language(chat_id)
    assert lang == "ar"


@pytest.mark.asyncio
async def test_get_user_language_not_found():
    """get_user_language returns None for non-existent user."""
    lang = await get_user_language(999999999)
    assert lang is None
