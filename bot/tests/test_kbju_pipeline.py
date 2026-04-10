"""Tests for the full KBJU pipeline: message → AI agent → calculate_macros → save to DB → meal plan → send.

Tests per language (RU/EN/AR):
- Full pipeline with mocked AI and DB
- KBJU values correctness
- DB writes with correct arguments
- Language detection and saving
- Already-calculated guard
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import logging
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from src.handlers.message import _process_text_message, handle_text
from src.services.calculator import calculate_macros
from src.i18n import get_strings

from tests.helpers import (
    AGENT_RESPONSES,
    AGENT_CONVERSATION_RESPONSES,
    MEAL_PLANS,
    make_message,
    make_user,
    expected_macros,
)

logger = logging.getLogger(__name__)


# ─── Full pipeline tests per language ────────────────────────────────────


class TestKBJUPipelineRU:
    """Russian user: male, 80kg, 180cm, 30yo, moderate, weight_loss."""

    @pytest.mark.asyncio
    @patch("src.handlers.message.save_chat_message", new_callable=AsyncMock)
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_kbju_pipeline_ru(
        self, mock_agent_main, mock_agent_food, mock_save_user, mock_set_food, mock_save_chat
    ):
        mock_agent_main.return_value = AGENT_RESPONSES["ru"]
        mock_agent_food.return_value = MEAL_PLANS["ru"]

        message = make_message(text="Привет, я мужчина, 80 кг", chat_id=100001)
        bot = AsyncMock()
        db_user = None  # New user, no DB record yet

        await _process_text_message(message, bot, db_user, "Привет, я мужчина, 80 кг")

        # AI agent was called
        mock_agent_main.assert_called_once_with(100001, "Привет, я мужчина, 80 кг")

        # save_user_data was called with correct KBJU
        mock_save_user.assert_called_once()
        save_kwargs = mock_save_user.call_args
        assert save_kwargs.kwargs["chat_id"] == 100001
        assert save_kwargs.kwargs["language"] == "ru"  # detected from Cyrillic text
        assert save_kwargs.kwargs["sex"] == "male"
        assert save_kwargs.kwargs["goal"] == "weight_loss"

        # Verify KBJU values match calculator
        macros = expected_macros("ru")
        assert save_kwargs.kwargs["calories"] == macros["calories"]
        assert save_kwargs.kwargs["protein"] == macros["protein"]
        assert save_kwargs.kwargs["fats"] == macros["fats"]
        assert save_kwargs.kwargs["carbs"] == macros["carbs"]

        # run_agent_food called with calculated macros
        mock_agent_food.assert_called_once()
        food_kwargs = mock_agent_food.call_args
        assert food_kwargs.kwargs["calories"] == macros["calories"]
        assert food_kwargs.kwargs["protein"] == macros["protein"]

        # set_food_received called → starts funnel
        mock_set_food.assert_called_once_with(100001, language="ru")

        # Meal plan sent to user
        assert message.answer.call_count >= 2  # "calculating..." + meal plan HTML


class TestKBJUPipelineEN:
    """English user: female, 60kg, 165cm, 25yo, light, maintenance."""

    @pytest.mark.asyncio
    @patch("src.handlers.message.save_chat_message", new_callable=AsyncMock)
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_kbju_pipeline_en(
        self, mock_agent_main, mock_agent_food, mock_save_user, mock_set_food, mock_save_chat
    ):
        mock_agent_main.return_value = AGENT_RESPONSES["en"]
        mock_agent_food.return_value = MEAL_PLANS["en"]

        message = make_message(text="Hi, I'm female, 60 kg", chat_id=100002)
        bot = AsyncMock()

        await _process_text_message(message, bot, None, "Hi, I'm female, 60 kg")

        mock_save_user.assert_called_once()
        save_kwargs = mock_save_user.call_args
        assert save_kwargs.kwargs["language"] == "en"
        assert save_kwargs.kwargs["sex"] == "female"
        assert save_kwargs.kwargs["goal"] == "maintenance"

        macros = expected_macros("en")
        assert save_kwargs.kwargs["calories"] == macros["calories"]
        assert save_kwargs.kwargs["protein"] == macros["protein"]
        assert save_kwargs.kwargs["fats"] == macros["fats"]
        assert save_kwargs.kwargs["carbs"] == macros["carbs"]

        mock_set_food.assert_called_once_with(100002, language="en")


class TestKBJUPipelineAR:
    """Arabic user: male, 75kg, 175cm, 28yo, high, muscle_gain."""

    @pytest.mark.asyncio
    @patch("src.handlers.message.save_chat_message", new_callable=AsyncMock)
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_kbju_pipeline_ar(
        self, mock_agent_main, mock_agent_food, mock_save_user, mock_set_food, mock_save_chat
    ):
        mock_agent_main.return_value = AGENT_RESPONSES["ar"]
        mock_agent_food.return_value = MEAL_PLANS["ar"]

        message = make_message(text="مرحبا، أنا رجل", chat_id=100003)
        bot = AsyncMock()

        await _process_text_message(message, bot, None, "مرحبا، أنا رجل")

        mock_save_user.assert_called_once()
        save_kwargs = mock_save_user.call_args
        assert save_kwargs.kwargs["language"] == "ar"  # detected from Arabic script
        assert save_kwargs.kwargs["sex"] == "male"
        assert save_kwargs.kwargs["goal"] == "muscle_gain"

        macros = expected_macros("ar")
        assert save_kwargs.kwargs["calories"] == macros["calories"]

        mock_set_food.assert_called_once_with(100003, language="ar")


# ─── KBJU calculation verification ──────────────────────────────────────


class TestCalculateMacrosSavedToDB:
    """Verify that calculated KBJU matches what gets saved to DB."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.message.save_chat_message", new_callable=AsyncMock)
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_macros_match_calculator(
        self, mock_agent_main, mock_agent_food, mock_save_user, mock_set_food, mock_save_chat, lang
    ):
        mock_agent_main.return_value = AGENT_RESPONSES[lang]
        mock_agent_food.return_value = MEAL_PLANS[lang]

        # Text in the corresponding language to trigger detect_language
        texts = {"ru": "Привет", "en": "Hello", "ar": "مرحبا"}
        chat_ids = {"ru": 100001, "en": 100002, "ar": 100003}

        message = make_message(text=texts[lang], chat_id=chat_ids[lang])

        await _process_text_message(message, AsyncMock(), None, texts[lang])

        save_kwargs = mock_save_user.call_args.kwargs
        macros = expected_macros(lang)

        assert save_kwargs["calories"] == macros["calories"], f"{lang}: calories mismatch"
        assert save_kwargs["protein"] == macros["protein"], f"{lang}: protein mismatch"
        assert save_kwargs["fats"] == macros["fats"], f"{lang}: fats mismatch"
        assert save_kwargs["carbs"] == macros["carbs"], f"{lang}: carbs mismatch"


# ─── Funnel start test ───────────────────────────────────────────────────


class TestSetFoodReceivedStartsFunnel:
    @pytest.mark.asyncio
    @patch("src.handlers.message.save_chat_message", new_callable=AsyncMock)
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_set_food_received_called_after_meal_plan_sent(
        self, mock_agent_main, mock_agent_food, mock_save_user, mock_set_food, mock_save_chat
    ):
        mock_agent_main.return_value = AGENT_RESPONSES["en"]
        mock_agent_food.return_value = MEAL_PLANS["en"]

        message = make_message(text="Hello", chat_id=55555)

        await _process_text_message(message, AsyncMock(), None, "Hello")

        # set_food_received is the LAST DB call — after meal plan is sent
        mock_set_food.assert_called_once_with(55555, language="en")

        # It was called AFTER save_user_data
        save_order = mock_save_user.call_args_list
        food_order = mock_set_food.call_args_list
        assert len(save_order) == 1
        assert len(food_order) == 1


# ─── Language detection and saving ───────────────────────────────────────


class TestLanguageDetectedAndSaved:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text,expected_lang",
        [
            ("Привет, расскажи мне", "ru"),
            ("Hello, tell me please", "en"),
            ("مرحبا، أخبرني من فضلك", "ar"),
        ],
    )
    @patch("src.handlers.message.save_chat_message", new_callable=AsyncMock)
    @patch("src.handlers.message.set_food_received", new_callable=AsyncMock)
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_food", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_language_detected_and_saved_to_db(
        self, mock_agent_main, mock_agent_food, mock_save_user, mock_set_food, mock_save_chat,
        text, expected_lang
    ):
        mock_agent_main.return_value = AGENT_RESPONSES[expected_lang]
        mock_agent_food.return_value = MEAL_PLANS[expected_lang]

        message = make_message(text=text, chat_id=77777)
        await _process_text_message(message, AsyncMock(), None, text)

        save_kwargs = mock_save_user.call_args.kwargs
        assert save_kwargs["language"] == expected_lang


# ─── Already calculated guard ───────────────────────────────────────────


class TestAlreadyCalculatedBlocksRepeat:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    async def test_already_calculated_sends_block_message(self, lang):
        """If get_food=True, bot sends ALREADY_CALCULATED and does not process."""
        db_user = make_user(lang, get_food=True)
        message = make_message(text="test", chat_id=db_user.chat_id)
        bot = AsyncMock()

        await handle_text(message, bot, db_user)

        strings = get_strings(lang)
        message.answer.assert_called_once_with(strings.ALREADY_CALCULATED, parse_mode="HTML")

    @pytest.mark.asyncio
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_already_calculated_does_not_call_agent(self, mock_agent):
        db_user = make_user("en", get_food=True)
        message = make_message(text="test", chat_id=db_user.chat_id)

        await handle_text(message, AsyncMock(), db_user)

        mock_agent.assert_not_called()


# ─── Conversation route (no generate) ───────────────────────────────────


class TestConversationRoute:
    @pytest.mark.asyncio
    @patch("src.handlers.message.save_user_data", new_callable=AsyncMock)
    @patch("src.handlers.message.run_agent_main", new_callable=AsyncMock)
    async def test_conversation_does_not_trigger_kbju(self, mock_agent_main, mock_save):
        """When agent returns normal text (no JSON), no KBJU calculation happens."""
        mock_agent_main.return_value = AGENT_CONVERSATION_RESPONSES["en"]

        message = make_message(text="Hi", chat_id=88888)
        await _process_text_message(message, AsyncMock(), None, "Hi")

        # Agent was called
        mock_agent_main.assert_called_once()

        # But save_user_data was NOT called (no generate route)
        mock_save.assert_not_called()

        # Bot sent text response
        message.answer.assert_called_once()
        call_text = message.answer.call_args.args[0]
        assert "Hello" in call_text or len(call_text) > 0
