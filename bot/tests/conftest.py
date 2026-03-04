"""Shared fixtures for tests."""

from __future__ import annotations

import os
from typing import Any

import pytest

# Set fake env vars before any config import
os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

from tests.helpers import (  # noqa: E402
    AGENT_RESPONSES,
    MEAL_PLANS,
    make_bot,
    make_callback,
    make_message,
    make_user,
    make_user_dict,
)


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data as returned from AI agent."""
    return {
        "is_finished": True,
        "sex": "male",
        "weight": 80,
        "height": 180,
        "age": 30,
        "activity_level": "moderate",
        "goal": "weight_loss",
        "allergies": "none",
        "excluded_foods": "none",
    }


@pytest.fixture
def sample_meal_plan() -> dict:
    """Sample meal plan as returned from AGENT FOOD."""
    return MEAL_PLANS["ru"]


# ─── Multilingual user fixtures ─────────────────────────────────────────

@pytest.fixture(params=["ru", "en", "ar"])
def lang(request: pytest.FixtureRequest) -> str:
    """Parametrized language fixture — yields ru, en, ar."""
    return request.param


@pytest.fixture
def user_ru():
    return make_user("ru")


@pytest.fixture
def user_en():
    return make_user("en")


@pytest.fixture
def user_ar():
    return make_user("ar")


@pytest.fixture
def mock_bot():
    return make_bot()


@pytest.fixture
def agent_response_ru() -> str:
    return AGENT_RESPONSES["ru"]


@pytest.fixture
def agent_response_en() -> str:
    return AGENT_RESPONSES["en"]


@pytest.fixture
def agent_response_ar() -> str:
    return AGENT_RESPONSES["ar"]


@pytest.fixture
def meal_plan_ru() -> dict:
    return MEAL_PLANS["ru"]


@pytest.fixture
def meal_plan_en() -> dict:
    return MEAL_PLANS["en"]


@pytest.fixture
def meal_plan_ar() -> dict:
    return MEAL_PLANS["ar"]
