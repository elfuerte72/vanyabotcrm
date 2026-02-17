"""Shared fixtures for tests."""

import os

import pytest

# Set fake env vars before any config import
os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")


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
    return {
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
    }
