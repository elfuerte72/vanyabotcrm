"""Tests for user events — save_user_event() and callback handler integration."""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.callbacks import (
    handle_buy_now,
    handle_confirm_paid_ru,
    handle_remind_later,
    handle_none,
    handle_video_workout,
    handle_en_funnel_question,
    handle_ar_funnel_question,
    handle_upsell_decline,
)
from tests.helpers import make_bot, make_user


def _make_callback(chat_id: int = 12345, user_id: int = 12345, data: str = "buy_now"):
    callback = AsyncMock()
    callback.data = data
    callback.from_user = MagicMock()
    callback.from_user.id = user_id
    callback.message = MagicMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = chat_id
    callback.answer = AsyncMock()
    return callback


def _make_bot_mock():
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


# ─── save_user_event unit test ───────────────────────────────────────────


class TestSaveUserEvent:
    @pytest.mark.asyncio
    @patch("src.db.queries.get_pool")
    async def test_save_user_event_inserts_correctly(self, mock_get_pool):
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_get_pool.return_value = mock_pool

        from src.db.queries import save_user_event

        await save_user_event(12345, "button_click", "buy_now", "ru", "funnel")

        mock_pool.execute.assert_called_once()
        args = mock_pool.execute.call_args
        query = args[0][0]
        params = args[0][1:]
        assert "INSERT INTO user_events" in query
        assert params == (12345, "button_click", "buy_now", "ru", "funnel")

    @pytest.mark.asyncio
    @patch("src.db.queries.get_pool")
    async def test_save_user_event_optional_fields(self, mock_get_pool):
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_get_pool.return_value = mock_pool

        from src.db.queries import save_user_event

        await save_user_event(99999, "funnel_message", "stage_3")

        args = mock_pool.execute.call_args
        params = args[0][1:]
        assert params == (99999, "funnel_message", "stage_3", None, None)


# ─── Callback handlers save events ──────────────────────────────────────


class TestCallbacksSaveEvents:
    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.save_ziina_payment", new_callable=AsyncMock)
    @patch(
        "src.handlers.callbacks.create_payment_intent",
        new_callable=AsyncMock,
        return_value=("intent_123", "https://checkout.ziina.com/test"),
    )
    async def test_buy_now_saves_event(self, mock_create, mock_save_ziina, mock_save_event):
        callback = _make_callback(data="buy_now")
        bot = _make_bot_mock()
        db_user = make_user("en")

        await handle_buy_now(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "buy_now", "en", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_confirm_paid_ru_saves_event(self, mock_mark, mock_save_event):
        callback = _make_callback(data="confirm_paid_ru")
        bot = _make_bot_mock()

        await handle_confirm_paid_ru(callback, bot)

        mock_save_event.assert_called_once_with(12345, "button_click", "confirm_paid_ru", "ru", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    async def test_remind_later_saves_event(self, mock_save_event):
        callback = _make_callback(data="remind_later")
        bot = _make_bot_mock()
        db_user = make_user("ru")

        await handle_remind_later(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "remind_later", "ru", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    async def test_none_saves_event(self, mock_save_event):
        callback = _make_callback(data="none")
        bot = _make_bot_mock()
        db_user = make_user("en")

        await handle_none(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "none", "en", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    async def test_video_workout_saves_event(self, mock_save_event):
        callback = _make_callback(data="video_workout")
        bot = _make_bot_mock()
        db_user = make_user("ru")

        await handle_video_workout(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "video_workout", "ru", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    async def test_upsell_decline_saves_event(self, mock_save_event):
        callback = _make_callback(data="upsell_decline")
        bot = _make_bot_mock()
        db_user = make_user("en")

        await handle_upsell_decline(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "upsell_decline", "en", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks._send_single_funnel_message", new_callable=AsyncMock)
    @patch("src.handlers.callbacks._build_keyboard", return_value=None)
    @patch("src.handlers.callbacks.get_funnel_message")
    @patch("src.handlers.callbacks.get_user", new_callable=AsyncMock)
    async def test_en_funnel_question_saves_event(
        self, mock_get_user, mock_get_msg, mock_kbd, mock_send, mock_stage, mock_save_event
    ):
        db_user = make_user("en")
        db_user.funnel_stage = 2
        db_user.is_buyer = False
        mock_get_msg.return_value = MagicMock(text="Next", buttons=[], photo_name=None, video_note_id=None)

        callback = _make_callback(data="en_funnel_q_2")
        bot = _make_bot_mock()

        await handle_en_funnel_question(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "en_funnel_q_2", "en", "funnel")

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_user_event", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks._send_single_funnel_message", new_callable=AsyncMock)
    @patch("src.handlers.callbacks._build_keyboard", return_value=None)
    @patch("src.handlers.callbacks.get_funnel_message")
    @patch("src.handlers.callbacks.get_user", new_callable=AsyncMock)
    async def test_ar_funnel_question_saves_event(
        self, mock_get_user, mock_get_msg, mock_kbd, mock_send, mock_stage, mock_save_event
    ):
        db_user = make_user("ar")
        db_user.funnel_stage = 5
        db_user.is_buyer = False
        mock_get_msg.return_value = MagicMock(text="Next", buttons=[], photo_name=None, video_note_id=None)

        callback = _make_callback(data="ar_funnel_q_5")
        bot = _make_bot_mock()

        await handle_ar_funnel_question(callback, bot, db_user=db_user)

        mock_save_event.assert_called_once_with(12345, "button_click", "ar_funnel_q_5", "ar", "funnel")
