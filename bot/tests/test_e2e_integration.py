"""End-to-end integration test — full user lifecycle with real PostgreSQL.

Simulates: user creation → KBJU save → food received → 6-day funnel → buy → verify.
Uses test chat_id 99999999.
"""

from __future__ import annotations

import os

# Real database URL for integration tests
REAL_DATABASE_URL = (
    "postgres://railway:y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa"
    "@yamabiko.proxy.rlwy.net:26903/railway"
)

os.environ["DATABASE_URL"] = REAL_DATABASE_URL
os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import pytest
import pytest_asyncio

import src.db.pool as pool_module
from src.db.pool import get_pool, close_pool
from src.db.queries import (
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
from src.services.calculator import calculate_macros
from src.funnel.messages import get_funnel_message

E2E_CHAT_ID = 99999999
E2E_SESSION_ID = "99999999"


@pytest_asyncio.fixture(autouse=True)
async def e2e_cleanup():
    """Clean up before and after each test."""
    if pool_module._pool is not None:
        try:
            await pool_module._pool.close()
        except Exception:
            pass
    pool_module._pool = None

    pool = await get_pool()
    await pool.execute("DELETE FROM users_nutrition WHERE chat_id = $1", E2E_CHAT_ID)
    await pool.execute("DELETE FROM n8n_chat_histories WHERE session_id = $1", E2E_SESSION_ID)
    yield
    pool = await get_pool()
    await pool.execute("DELETE FROM users_nutrition WHERE chat_id = $1", E2E_CHAT_ID)
    await pool.execute("DELETE FROM n8n_chat_histories WHERE session_id = $1", E2E_SESSION_ID)


# ═══════════════════════════════════════════════════════════════════════════
# Full lifecycle test
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_full_user_lifecycle():
    """Complete user journey: register → KBJU → funnel 6 days → buy."""

    # ── Step 1: User doesn't exist yet ────────────────────────────────
    user = await get_user(E2E_CHAT_ID)
    assert user is None, "Test user should not exist before test"

    # ── Step 2: Save user data (simulate data collection) ─────────────
    macros = calculate_macros(
        sex="female", weight=65.0, height=170.0, age=28,
        activity_level="moderate", goal="weight_loss",
    )
    assert macros.calories > 0

    await save_user_data(
        chat_id=E2E_CHAT_ID, username="e2e_test_user",
        sex="female", age=28, weight=65.0, height=170.0,
        activity_level="moderate", goal="weight_loss",
        allergies="nuts", excluded_foods="fish",
        calories=macros.calories, protein=macros.protein,
        fats=macros.fats, carbs=macros.carbs, language="ru",
    )

    user = await get_user(E2E_CHAT_ID)
    assert user is not None
    assert user.calories == macros.calories
    assert user.get_food is False
    assert user.is_buyer is False
    assert user.funnel_stage == 0

    # ── Step 3: Food received → starts funnel ─────────────────────────
    await set_food_received(E2E_CHAT_ID)

    user = await get_user(E2E_CHAT_ID)
    assert user.get_food is True
    assert user.funnel_stage == 0
    assert user.last_funnel_msg_at is not None

    # ── Step 4: Verify user appears in funnel targets ─────────────────
    targets = await get_funnel_targets()
    target_ids = {t["chat_id"] for t in targets}
    assert E2E_CHAT_ID in target_ids

    # ── Step 5: Simulate 6-day funnel ─────────────────────────────────
    for day in range(6):
        user = await get_user(E2E_CHAT_ID)
        assert user.funnel_stage == day, f"Day {day}: wrong funnel_stage"

        # Verify correct message exists for this stage
        msg = get_funnel_message(day, "ru")
        assert msg is not None, f"No message for day {day}"
        assert len(msg.text) > 0

        # Simulate sending (just update stage)
        await update_funnel_stage(E2E_CHAT_ID)

    # After 6 days, stage should be 6
    user = await get_user(E2E_CHAT_ID)
    assert user.funnel_stage == 6, "After 6 days, funnel_stage should be 6"

    # User should NOT appear in funnel targets anymore (stage >= 5)
    targets = await get_funnel_targets()
    target_ids = {t["chat_id"] for t in targets}
    assert E2E_CHAT_ID not in target_ids

    # ── Step 6: Simulate purchase ─────────────────────────────────────
    await mark_as_buyer(E2E_CHAT_ID)

    user = await get_user(E2E_CHAT_ID)
    assert user.is_buyer is True

    # ── Step 7: Verify language ───────────────────────────────────────
    lang = await get_user_language(E2E_CHAT_ID)
    assert lang == "ru"


@pytest.mark.asyncio
async def test_chat_history_lifecycle():
    """Full chat history: save messages → retrieve → verify order."""

    messages_to_save = [
        ("human", "Привет, хочу рассчитать КБЖУ"),
        ("ai", "Привет! Рад помочь. Расскажи о себе."),
        ("human", "Девушка, 65 кг, 170 см, 28 лет"),
        ("ai", "Отлично! Какая у тебя физическая активность?"),
        ("human", "Умеренная, занимаюсь 3 раза в неделю"),
        ("ai", "Понял! Какая цель: похудение, набор массы или поддержание?"),
        ("human", "Похудение"),
        ("ai", '```json\n{"is_finished": true, "sex": "female", "weight": 65}\n```'),
    ]

    for role, content in messages_to_save:
        await save_chat_message(E2E_SESSION_ID, role, content)

    history = await get_chat_history(E2E_SESSION_ID)
    assert len(history) == 8

    # Check order (oldest first)
    assert history[0]["type"] == "human"
    assert "КБЖУ" in history[0]["content"]
    assert history[-1]["type"] == "ai"
    assert "is_finished" in history[-1]["content"]

    # Check alternating pattern
    for i, (expected_role, _) in enumerate(messages_to_save):
        assert history[i]["type"] == expected_role, f"Message {i}: wrong role"


@pytest.mark.asyncio
async def test_funnel_excludes_buyer():
    """A buyer should never appear in funnel targets, regardless of stage."""
    await save_user_data(
        chat_id=E2E_CHAT_ID, username="buyer_test",
        sex="male", age=30, weight=80.0, height=180.0,
        activity_level="moderate", goal="weight_loss",
        allergies="none", excluded_foods="none",
        calories=2000, protein=120, fats=80, carbs=200, language="en",
    )
    await set_food_received(E2E_CHAT_ID)
    await mark_as_buyer(E2E_CHAT_ID)

    targets = await get_funnel_targets()
    target_ids = {t["chat_id"] for t in targets}
    assert E2E_CHAT_ID not in target_ids


@pytest.mark.asyncio
async def test_macros_match_expected_for_e2e_profile():
    """Verify KBJU calculation for the E2E test profile."""
    macros = calculate_macros(
        sex="female", weight=65.0, height=170.0, age=28,
        activity_level="moderate", goal="weight_loss",
    )
    # Manual: BMR = 650 + 1062.5 - 140 - 161 = 1411.5
    # TDEE = 1411.5 * 1.55 = 2187.825
    # Target = 2187.825 * 0.85 = 1859.65 → 1860
    assert macros.calories == 1860
    assert macros.protein == 98   # 65 * 1.5
    assert macros.fats == 65      # 65 * 1.0
    # carbs = (1860 - 98*4 - 65*9) / 4 = (1860 - 392 - 585) / 4 = 883 / 4 = 220.75 → 221
    assert macros.carbs == 221
