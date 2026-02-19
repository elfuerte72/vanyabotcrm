"""Tests for message handler flow — guard, routes, error handling.

Mocks: Bot, Message, run_agent_main, run_agent_food, DB queries.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.message import handle_text, _process_text_message
from src.models.user import User
from src.i18n import get_strings


def _make_message(chat_id: int = 12345, text: str = "Hello", username: str = "testuser"):
    """Create a mock Message."""
    msg = AsyncMock()
    msg.chat = MagicMock()
    msg.chat.id = chat_id
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.username = username
    msg.answer = AsyncMock()
    return msg


def _make_user(chat_id: int = 12345, get_food: bool = False, language: str = "en") -> User:
    return User(chat_id=chat_id, get_food=get_food, language=language)


# ─── Guard: get_food ─────────────────────────────────────────────────────


class TestGetFoodGuard:
    @pytest.mark.asyncio
    async def test_already_calculated_ru(self):
        """User with get_food=True gets ALREADY_CALCULATED in Russian."""
        msg = _make_message(text="Привет")
        bot = AsyncMock()
        db_user = _make_user(get_food=True, language="ru")

        await handle_text(msg, bot, db_user)

        msg.answer.assert_called_once()
        sent_text = msg.answer.call_args.args[0]
        assert sent_text == get_strings("ru").ALREADY_CALCULATED

    @pytest.mark.asyncio
    async def test_already_calculated_en(self):
        """User with get_food=True gets ALREADY_CALCULATED in English."""
        msg = _make_message(text="Hello")
        bot = AsyncMock()
        db_user = _make_user(get_food=True, language="en")

        await handle_text(msg, bot, db_user)

        sent_text = msg.answer.call_args.args[0]
        assert sent_text == get_strings("en").ALREADY_CALCULATED

    @pytest.mark.asyncio
    async def test_already_calculated_ar(self):
        """User with get_food=True gets ALREADY_CALCULATED in Arabic."""
        msg = _make_message(text="مرحبا")
        bot = AsyncMock()
        db_user = _make_user(get_food=True, language="ar")

        await handle_text(msg, bot, db_user)

        sent_text = msg.answer.call_args.args[0]
        assert sent_text == get_strings("ar").ALREADY_CALCULATED

    @pytest.mark.asyncio
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_no_guard_when_get_food_false(self, mock_agent):
        """User with get_food=False passes guard and reaches agent."""
        mock_agent.return_value = "Hi! Tell me about yourself."
        msg = _make_message(text="Hello")
        bot = AsyncMock()
        db_user = _make_user(get_food=False)

        await handle_text(msg, bot, db_user)

        mock_agent.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_no_guard_when_db_user_none(self, mock_agent):
        """New user (db_user=None) passes guard."""
        mock_agent.return_value = "Welcome! Let me help."
        msg = _make_message(text="Hello")
        bot = AsyncMock()

        await handle_text(msg, bot, None)

        mock_agent.assert_called_once()


# ─── Route: conversation ─────────────────────────────────────────────────


class TestConversationRoute:
    @pytest.mark.asyncio
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_conversation_sends_text(self, mock_agent):
        """Plain text response from agent → sent to user as conversation."""
        mock_agent.return_value = "What is your weight?"
        msg = _make_message(text="Hello", chat_id=1001)
        bot = AsyncMock()

        await _process_text_message(msg, bot, None, "Hello")

        msg.answer.assert_called_once()
        sent_text = msg.answer.call_args.args[0]
        assert "weight" in sent_text.lower()

    @pytest.mark.asyncio
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_conversation_empty_response(self, mock_agent):
        """Empty agent response → no message sent, no crash."""
        mock_agent.return_value = ""
        msg = _make_message(text="Hello", chat_id=1001)
        bot = AsyncMock()

        await _process_text_message(msg, bot, None, "Hello")

        # answer should NOT be called for empty response
        msg.answer.assert_not_called()


# ─── Route: generate ─────────────────────────────────────────────────────


class TestGenerateRoute:
    @pytest.mark.asyncio
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_generate_full_flow(self, mock_agent_main, mock_agent_food, mock_save, mock_set_food):
        """Agent returns is_finished=true → calculates macros → generates food → sends."""
        agent_json = json.dumps({
            "is_finished": True,
            "sex": "male",
            "weight": 80,
            "height": 180,
            "age": 30,
            "activity_level": "moderate",
            "goal": "weight_loss",
            "allergies": "none",
            "excluded_foods": "none",
        })
        mock_agent_main.return_value = f"```json\n{agent_json}\n```"
        mock_agent_food.return_value = {
            "meals": [
                {
                    "name": "Завтрак",
                    "dish": "Овсянка",
                    "total_cals": 400,
                    "ingredients": [
                        {"name": "Овсянка", "weight_g": 80, "cals": 400, "p": 10, "f": 5, "c": 70},
                    ],
                },
            ]
        }

        msg = _make_message(text="Да, всё верно", chat_id=2001, username="test_gen")
        bot = AsyncMock()

        await _process_text_message(msg, bot, None, "Да, всё верно")

        # save_user_data called with calculated macros
        mock_save.assert_called_once()
        save_kwargs = mock_save.call_args.kwargs
        assert save_kwargs["chat_id"] == 2001
        assert save_kwargs["sex"] == "male"
        assert save_kwargs["calories"] > 0
        assert save_kwargs["protein"] > 0

        # agent_food called with macros
        mock_agent_food.assert_called_once()
        food_kwargs = mock_agent_food.call_args.kwargs
        assert food_kwargs["calories"] > 0

        # set_food_received called
        mock_set_food.assert_called_once_with(2001)

        # Two calls to answer: 1) "calculating..." 2) meal plan HTML
        assert msg.answer.call_count == 2

    @pytest.mark.asyncio
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_generate_calculates_correct_macros(
        self, mock_agent_main, mock_agent_food, mock_save, mock_set_food
    ):
        """Check that calculator is called with correct params from agent data."""
        agent_json = json.dumps({
            "is_finished": True,
            "sex": "female",
            "weight": 60,
            "height": 165,
            "age": 25,
            "activity_level": "light",
            "goal": "maintenance",
            "allergies": "nuts",
            "excluded_foods": "fish",
        })
        mock_agent_main.return_value = f"```json\n{agent_json}\n```"
        mock_agent_food.return_value = {"meals": []}

        msg = _make_message(text="Yes", chat_id=2002)
        bot = AsyncMock()

        await _process_text_message(msg, bot, None, "Yes")

        save_kwargs = mock_save.call_args.kwargs
        # Female, 60kg, 165cm, 25y, light, maintenance
        # BMR = 600 + 1031.25 - 125 - 161 = 1345.25
        # TDEE = 1345.25 * 1.375 = 1849.72 → 1850
        assert save_kwargs["calories"] == 1850
        assert save_kwargs["protein"] == 84  # 60 * 1.4
        assert save_kwargs["fats"] == 60  # 60 * 1.0
        assert save_kwargs["allergies"] == "nuts"
        assert save_kwargs["excluded_foods"] == "fish"

    @pytest.mark.asyncio
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_generate_no_data_no_crash(self, mock_agent_main):
        """If parse returns generate but no data, handler doesn't crash."""
        # Agent returns JSON without is_finished
        mock_agent_main.return_value = '{"some_field": "value"}'
        msg = _make_message(text="test", chat_id=2003)
        bot = AsyncMock()

        # Should not raise
        await _process_text_message(msg, bot, None, "test")


# ─── Language detection in message flow ──────────────────────────────────


class TestLanguageDetection:
    @pytest.mark.asyncio
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_russian_text_detected(self, mock_agent_main, mock_agent_food, mock_save, mock_set_food):
        """Russian text is detected and saved to DB."""
        agent_json = json.dumps({
            "is_finished": True, "sex": "male", "weight": 80, "height": 180,
            "age": 30, "activity_level": "moderate", "goal": "weight_loss",
            "allergies": "none", "excluded_foods": "none",
        })
        mock_agent_main.return_value = f"```json\n{agent_json}\n```"
        mock_agent_food.return_value = {"meals": []}

        msg = _make_message(text="Да, всё верно", chat_id=3001)
        bot = AsyncMock()

        await _process_text_message(msg, bot, None, "Да, всё верно")

        assert mock_save.call_args.kwargs["language"] == "ru"

    @pytest.mark.asyncio
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_arabic_text_detected(self, mock_agent_main, mock_agent_food, mock_save, mock_set_food):
        """Arabic text is detected and saved to DB."""
        agent_json = json.dumps({
            "is_finished": True, "sex": "female", "weight": 60, "height": 165,
            "age": 25, "activity_level": "moderate", "goal": "maintenance",
            "allergies": "none", "excluded_foods": "none",
        })
        mock_agent_main.return_value = f"```json\n{agent_json}\n```"
        mock_agent_food.return_value = {"meals": []}

        msg = _make_message(text="نعم، كل شيء صحيح", chat_id=3002)
        bot = AsyncMock()

        await _process_text_message(msg, bot, None, "نعم، كل شيء صحيح")

        assert mock_save.call_args.kwargs["language"] == "ar"
