"""Shared test helpers and factories for multilingual bot tests.

Provides:
- User factories (make_user) for RU/EN/AR profiles
- Mock builders for Bot, CallbackQuery, Message
- Sample AI agent responses per language
- Sample meal plan data per language
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from typing import Any

from src.models.user import User

logger = logging.getLogger(__name__)

# ─── User profiles per language ──────────────────────────────────────────

_USER_PROFILES: dict[str, dict[str, Any]] = {
    "ru": {
        "chat_id": 100001,
        "username": "ivan_ru",
        "first_name": "Иван",
        "sex": "male",
        "age": 30,
        "weight": 80.0,
        "height": 180.0,
        "activity_level": "moderate",
        "goal": "weight_loss",
        "allergies": "нет",
        "excluded_foods": "нет",
        "language": "ru",
    },
    "en": {
        "chat_id": 100002,
        "username": "jane_en",
        "first_name": "Jane",
        "sex": "female",
        "age": 25,
        "weight": 60.0,
        "height": 165.0,
        "activity_level": "light",
        "goal": "maintenance",
        "allergies": "none",
        "excluded_foods": "none",
        "language": "en",
    },
    "ar": {
        "chat_id": 100003,
        "username": "ahmed_ar",
        "first_name": "أحمد",
        "sex": "male",
        "age": 28,
        "weight": 75.0,
        "height": 175.0,
        "activity_level": "high",
        "goal": "muscle_gain",
        "allergies": "لا",
        "excluded_foods": "لا",
        "language": "ar",
    },
}


def make_user(lang: str = "en", **overrides: Any) -> User:
    """Create a User dataclass with realistic data for the given language.

    Args:
        lang: Language code (ru/en/ar).
        **overrides: Any User field to override.

    Returns:
        User dataclass instance.
    """
    profile = {**_USER_PROFILES.get(lang, _USER_PROFILES["en"]), **overrides}
    logger.debug("make_user lang=%s chat_id=%s", lang, profile["chat_id"])
    return User(**profile)


def make_user_dict(lang: str = "en", **overrides: Any) -> dict[str, Any]:
    """Return raw profile dict (for DB target mocking)."""
    profile = {**_USER_PROFILES.get(lang, _USER_PROFILES["en"]), **overrides}
    return profile


# ─── Agent JSON responses (is_finished=True) ────────────────────────────

AGENT_RESPONSES: dict[str, str] = {
    "ru": (
        '```json\n'
        '{\n'
        '  "is_finished": true,\n'
        '  "sex": "male",\n'
        '  "weight": 80,\n'
        '  "height": 180,\n'
        '  "age": 30,\n'
        '  "activity_level": "moderate",\n'
        '  "goal": "weight_loss",\n'
        '  "allergies": "нет",\n'
        '  "excluded_foods": "нет"\n'
        '}\n'
        '```'
    ),
    "en": (
        '```json\n'
        '{\n'
        '  "is_finished": true,\n'
        '  "sex": "female",\n'
        '  "weight": 60,\n'
        '  "height": 165,\n'
        '  "age": 25,\n'
        '  "activity_level": "light",\n'
        '  "goal": "maintenance",\n'
        '  "allergies": "none",\n'
        '  "excluded_foods": "none"\n'
        '}\n'
        '```'
    ),
    "ar": (
        '```json\n'
        '{\n'
        '  "is_finished": true,\n'
        '  "sex": "male",\n'
        '  "weight": 75,\n'
        '  "height": 175,\n'
        '  "age": 28,\n'
        '  "activity_level": "high",\n'
        '  "goal": "muscle_gain",\n'
        '  "allergies": "لا",\n'
        '  "excluded_foods": "لا"\n'
        '}\n'
        '```'
    ),
}

# Conversation (non-finished) responses per language
AGENT_CONVERSATION_RESPONSES: dict[str, str] = {
    "ru": "Привет! Расскажи, какой у тебя рост и вес?",
    "en": "Hello! Tell me your height and weight, please.",
    "ar": "مرحبا! أخبرني عن طولك ووزنك من فضلك.",
}


# ─── Meal plan samples ──────────────────────────────────────────────────

MEAL_PLANS: dict[str, dict] = {
    "ru": {
        "meals": [
            {
                "name": "Завтрак",
                "dish": "Овсянка с ягодами",
                "total_cals": 400,
                "ingredients": [
                    {"name": "Овсяные хлопья", "weight_g": 80, "cals": 280, "p": 10, "f": 5, "c": 50},
                    {"name": "Голубика", "weight_g": 100, "cals": 57, "p": 1, "f": 0, "c": 14},
                    {"name": "Мёд", "weight_g": 15, "cals": 48, "p": 0, "f": 0, "c": 13},
                ],
            },
            {
                "name": "Обед",
                "dish": "Куриная грудка с рисом",
                "total_cals": 550,
                "ingredients": [
                    {"name": "Куриная грудка", "weight_g": 200, "cals": 330, "p": 62, "f": 7, "c": 0},
                    {"name": "Рис", "weight_g": 80, "cals": 280, "p": 5, "f": 1, "c": 62},
                ],
            },
            {
                "name": "Ужин",
                "dish": "Салат с тунцом",
                "total_cals": 350,
                "ingredients": [
                    {"name": "Тунец", "weight_g": 150, "cals": 180, "p": 39, "f": 1, "c": 0},
                    {"name": "Овощи", "weight_g": 200, "cals": 50, "p": 2, "f": 0, "c": 10},
                    {"name": "Оливковое масло", "weight_g": 10, "cals": 88, "p": 0, "f": 10, "c": 0},
                ],
            },
        ]
    },
    "en": {
        "meals": [
            {
                "name": "Breakfast",
                "dish": "Oatmeal with berries",
                "total_cals": 350,
                "ingredients": [
                    {"name": "Oatmeal", "weight_g": 70, "cals": 245, "p": 9, "f": 4, "c": 44},
                    {"name": "Blueberries", "weight_g": 80, "cals": 46, "p": 1, "f": 0, "c": 11},
                    {"name": "Honey", "weight_g": 15, "cals": 48, "p": 0, "f": 0, "c": 13},
                ],
            },
            {
                "name": "Lunch",
                "dish": "Grilled chicken salad",
                "total_cals": 450,
                "ingredients": [
                    {"name": "Chicken breast", "weight_g": 150, "cals": 248, "p": 47, "f": 5, "c": 0},
                    {"name": "Mixed greens", "weight_g": 150, "cals": 30, "p": 2, "f": 0, "c": 5},
                    {"name": "Olive oil", "weight_g": 10, "cals": 88, "p": 0, "f": 10, "c": 0},
                ],
            },
            {
                "name": "Dinner",
                "dish": "Salmon with vegetables",
                "total_cals": 400,
                "ingredients": [
                    {"name": "Salmon fillet", "weight_g": 150, "cals": 280, "p": 30, "f": 17, "c": 0},
                    {"name": "Broccoli", "weight_g": 200, "cals": 68, "p": 6, "f": 1, "c": 13},
                    {"name": "Lemon", "weight_g": 20, "cals": 6, "p": 0, "f": 0, "c": 2},
                ],
            },
        ]
    },
    "ar": {
        "meals": [
            {
                "name": "فطور",
                "dish": "شوفان بالتوت",
                "total_cals": 380,
                "ingredients": [
                    {"name": "شوفان", "weight_g": 80, "cals": 280, "p": 10, "f": 5, "c": 50},
                    {"name": "توت", "weight_g": 80, "cals": 46, "p": 1, "f": 0, "c": 11},
                    {"name": "عسل", "weight_g": 15, "cals": 48, "p": 0, "f": 0, "c": 13},
                ],
            },
            {
                "name": "غداء",
                "dish": "صدر دجاج مع أرز",
                "total_cals": 560,
                "ingredients": [
                    {"name": "صدر دجاج", "weight_g": 200, "cals": 330, "p": 62, "f": 7, "c": 0},
                    {"name": "أرز", "weight_g": 80, "cals": 280, "p": 5, "f": 1, "c": 62},
                ],
            },
            {
                "name": "عشاء",
                "dish": "سلطة تونة",
                "total_cals": 380,
                "ingredients": [
                    {"name": "تونة", "weight_g": 150, "cals": 180, "p": 39, "f": 1, "c": 0},
                    {"name": "خضار", "weight_g": 200, "cals": 50, "p": 2, "f": 0, "c": 10},
                    {"name": "زيت زيتون", "weight_g": 15, "cals": 133, "p": 0, "f": 15, "c": 0},
                ],
            },
        ]
    },
}


# ─── Mock builders ───────────────────────────────────────────────────────

def make_bot() -> AsyncMock:
    """Create a mock Bot with common async methods."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.get_file = AsyncMock()
    bot.download_file = AsyncMock()
    logger.debug("make_bot created")
    return bot


def make_callback(
    data: str = "buy_now",
    chat_id: int = 12345,
    user_id: int = 12345,
) -> AsyncMock:
    """Create a mock CallbackQuery.

    Args:
        data: Callback data string.
        chat_id: Chat ID for the message.
        user_id: User ID for from_user.
    """
    callback = AsyncMock()
    callback.data = data
    callback.from_user = MagicMock()
    callback.from_user.id = user_id
    callback.message = MagicMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = chat_id
    callback.answer = AsyncMock()
    logger.debug("make_callback data=%s chat_id=%s user_id=%s", data, chat_id, user_id)
    return callback


def make_message(
    text: str = "Hello",
    chat_id: int = 12345,
    user_id: int = 12345,
    username: str = "testuser",
) -> AsyncMock:
    """Create a mock Message.

    Args:
        text: Message text.
        chat_id: Chat ID.
        user_id: Sender user ID.
        username: Sender username.
    """
    message = AsyncMock()
    message.text = text
    message.chat = MagicMock()
    message.chat.id = chat_id
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.from_user.username = username
    message.answer = AsyncMock()
    logger.debug("make_message chat_id=%s text=%s", chat_id, text[:50])
    return message


# ─── Expected KBJU values per language profile ──────────────────────────

def expected_macros(lang: str) -> dict[str, int]:
    """Return expected MacroResult values for the given language profile.

    Pre-computed using calculate_macros with the profile data.
    """
    from src.services.calculator import calculate_macros

    profile = _USER_PROFILES[lang]
    result = calculate_macros(
        sex=profile["sex"],
        weight=profile["weight"],
        height=profile["height"],
        age=profile["age"],
        activity_level=profile["activity_level"],
        goal=profile["goal"],
    )
    return {
        "calories": result.calories,
        "protein": result.protein,
        "fats": result.fats,
        "carbs": result.carbs,
    }


# ─── Funnel target dicts (simulating DB rows) ───────────────────────────

def make_funnel_targets(
    languages: list[str] | None = None,
    stage: int = 0,
    base_chat_id: int = 200000,
) -> list[dict[str, Any]]:
    """Create a list of funnel target dicts as returned by get_funnel_targets.

    Args:
        languages: List of language codes. Defaults to ["ru", "en", "ar"].
        stage: Funnel stage for all targets.
        base_chat_id: Starting chat_id (incremented per target).
    """
    if languages is None:
        languages = ["ru", "en", "ar"]

    targets = []
    for i, lang in enumerate(languages):
        targets.append({
            "chat_id": base_chat_id + i,
            "funnel_stage": stage,
            "language": lang,
        })
    logger.debug("make_funnel_targets count=%d stage=%d", len(targets), stage)
    return targets
