"""Tests for callback query handlers — all 7 callbacks × 3 languages.

Mocks: CallbackQuery, Bot, DB queries, media services.
Uses db_user from UserDataMiddleware instead of get_user_language mock.
"""

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
    handle_show_info,
    handle_show_results,
    handle_check_suitability,
    handle_remind_later,
    handle_none,
    handle_video_workout,
)
from src.i18n import get_strings
from tests.helpers import make_bot, make_callback, make_user


def _make_callback(chat_id: int = 12345, user_id: int = 12345, data: str = "buy_now"):
    """Create a mock CallbackQuery."""
    callback = AsyncMock()
    callback.data = data
    callback.from_user = MagicMock()
    callback.from_user.id = user_id
    callback.message = MagicMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = chat_id
    callback.answer = AsyncMock()
    return callback


def _make_bot():
    """Create a mock Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


# ─── handle_buy_now ──────────────────────────────────────────────────────


class TestHandleBuyNow:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["en", "ar"])
    @patch("src.handlers.callbacks.save_ziina_payment", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.create_payment_intent", new_callable=AsyncMock, return_value=("intent_123", "https://checkout.ziina.com/test"))
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_en_ar_creates_payment_intent(self, mock_mark_buyer, mock_create, mock_save, language):
        """EN/AR: creates Ziina payment intent, does NOT mark buyer immediately."""
        callback = _make_callback(data="buy_now")
        bot = _make_bot()
        strings = get_strings(language)
        db_user = make_user(language)

        await handle_buy_now(callback, bot, db_user=db_user)

        mock_mark_buyer.assert_not_called()
        mock_create.assert_called_once()
        mock_save.assert_called_once()
        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args
        assert call_kwargs.kwargs["text"] == strings.BUY_MESSAGE
        # Button URL should be the redirect_url from Ziina
        markup = call_kwargs.kwargs["reply_markup"]
        assert markup.inline_keyboard[0][0].url == "https://checkout.ziina.com/test"
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_ru_does_not_mark_buyer(self, mock_mark_buyer):
        """RU: two-step confirmation — mark_as_buyer is NOT called on buy_now."""
        callback = _make_callback(data="buy_now")
        bot = _make_bot()
        db_user = make_user("ru")
        strings = get_strings("ru")

        await handle_buy_now(callback, bot, db_user=db_user)

        mock_mark_buyer.assert_not_called()
        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args
        assert call_kwargs.kwargs["text"] == strings.BUY_MESSAGE_WITH_CONFIRM
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_ru_keyboard_has_confirm_button(self, mock_mark_buyer):
        """RU keyboard: row 1 = payment URL, row 2 = confirm_paid_ru callback."""
        callback = _make_callback(data="buy_now")
        bot = _make_bot()
        db_user = make_user("ru")

        await handle_buy_now(callback, bot, db_user=db_user)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 2
        # Row 1: URL button
        assert markup.inline_keyboard[0][0].url is not None
        strings = get_strings("ru")
        assert markup.inline_keyboard[0][0].text == strings.BUY_BUTTON
        # Row 2: confirm callback button
        assert markup.inline_keyboard[1][0].callback_data == "confirm_paid_ru"
        assert markup.inline_keyboard[1][0].text == strings.CONFIRM_PAID_BUTTON

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.create_payment_intent", new_callable=AsyncMock, side_effect=Exception("API down"))
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_en_fallback_on_ziina_error(self, mock_mark_buyer, mock_create):
        """EN/AR: when Ziina API fails, falls back to static link only."""
        callback = _make_callback(data="buy_now")
        bot = _make_bot()
        db_user = make_user("en")

        await handle_buy_now(callback, bot, db_user=db_user)

        mock_mark_buyer.assert_not_called()
        markup = bot.send_message.call_args.kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 1
        assert markup.inline_keyboard[0][0].url is not None

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.save_ziina_payment", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.create_payment_intent", new_callable=AsyncMock, return_value=("intent_456", "https://checkout.ziina.com/test2"))
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_default_language_en(self, mock_mark_buyer, mock_create, mock_save):
        """If db_user is None, defaults to English (creates Ziina intent)."""
        callback = _make_callback(data="buy_now")
        bot = _make_bot()

        await handle_buy_now(callback, bot, db_user=None)

        mock_mark_buyer.assert_not_called()
        mock_create.assert_called_once()
        strings = get_strings("en")
        assert bot.send_message.call_args.kwargs["text"] == strings.BUY_MESSAGE


# ─── handle_confirm_paid_ru ─────────────────────────────────────────────


class TestHandleConfirmPaidRu:
    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_confirm_paid_marks_buyer(self, mock_mark_buyer):
        callback = _make_callback(data="confirm_paid_ru", user_id=55555)
        bot = _make_bot()

        await handle_confirm_paid_ru(callback, bot)

        mock_mark_buyer.assert_called_once_with(55555)
        bot.send_message.assert_called_once()
        strings = get_strings("ru")
        assert bot.send_message.call_args.kwargs["text"] == strings.PAYMENT_CONFIRMED
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_confirm_paid_no_message_returns(self, mock_mark_buyer):
        callback = _make_callback(data="confirm_paid_ru")
        callback.message = None
        bot = _make_bot()

        await handle_confirm_paid_ru(callback, bot)

        mock_mark_buyer.assert_not_called()
        bot.send_message.assert_not_called()


# ─── handle_show_info ────────────────────────────────────────────────────


class TestHandleShowInfo:
    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_info_video", new_callable=AsyncMock)
    async def test_show_info_sends_video(self, mock_send_video):
        callback = _make_callback(data="show_info")
        bot = _make_bot()

        await handle_show_info(callback, bot)

        mock_send_video.assert_called_once_with(bot, callback.message.chat.id)
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.send_info_video", new_callable=AsyncMock)
    async def test_show_info_handles_error(self, mock_send_video, language):
        """On video download error, sends localized fallback text."""
        mock_send_video.side_effect = Exception("Download failed")
        callback = _make_callback(data="show_info")
        bot = _make_bot()
        strings = get_strings(language)
        db_user = make_user(language)

        await handle_show_info(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once()
        assert bot.send_message.call_args.args[1] == strings.VIDEO_UNAVAILABLE
        callback.answer.assert_called_once()


# ─── handle_show_results ─────────────────────────────────────────────────


class TestHandleShowResults:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    async def test_show_results_sends_photo(self, mock_send_photo, language):
        callback = _make_callback(data="show_results")
        bot = _make_bot()
        strings = get_strings(language)
        db_user = make_user(language)

        await handle_show_results(callback, bot, db_user=db_user)

        mock_send_photo.assert_called_once_with(
            bot, callback.message.chat.id, caption=strings.RESULTS_CAPTION
        )
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    async def test_show_results_handles_error(self, mock_send_photo):
        mock_send_photo.side_effect = Exception("Photo error")
        callback = _make_callback(data="show_results")
        bot = _make_bot()
        db_user = make_user("en")

        # Should not raise
        await handle_show_results(callback, bot, db_user=db_user)
        callback.answer.assert_called_once()


# ─── handle_check_suitability ────────────────────────────────────────────


class TestHandleCheckSuitability:
    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_suitability_video", new_callable=AsyncMock)
    async def test_check_suitability_sends_video(self, mock_send_video):
        callback = _make_callback(data="check_suitability")
        bot = _make_bot()

        await handle_check_suitability(callback, bot)

        mock_send_video.assert_called_once_with(bot, callback.message.chat.id)
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_suitability_video", new_callable=AsyncMock)
    async def test_check_suitability_handles_error(self, mock_send_video):
        mock_send_video.side_effect = Exception("Video error")
        callback = _make_callback(data="check_suitability")
        bot = _make_bot()

        await handle_check_suitability(callback, bot)
        callback.answer.assert_called_once()


# ─── handle_remind_later ─────────────────────────────────────────────────


class TestHandleRemindLater:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    async def test_remind_later_sends_message(self, language):
        callback = _make_callback(data="remind_later")
        bot = _make_bot()
        strings = get_strings(language)
        db_user = make_user(language)

        await handle_remind_later(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once_with(
            callback.message.chat.id, strings.REMIND_LATER, parse_mode="HTML"
        )
        callback.answer.assert_called_once()


# ─── handle_none ─────────────────────────────────────────────────────────


class TestHandleNone:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    async def test_none_sends_response(self, language):
        callback = _make_callback(data="none")
        bot = _make_bot()
        strings = get_strings(language)
        db_user = make_user(language)

        await handle_none(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once_with(
            callback.message.chat.id, strings.NONE_RESPONSE, parse_mode="HTML"
        )
        callback.answer.assert_called_once()


# ─── handle_video_workout ────────────────────────────────────────────────


class TestHandleVideoWorkout:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    async def test_video_workout_sends_prompt_with_video_button(self, language):
        callback = _make_callback(data="video_workout")
        bot = _make_bot()
        strings = get_strings(language)
        db_user = make_user(language)

        await handle_video_workout(callback, bot, db_user=db_user)

        callback.answer.assert_called_once()
        assert bot.send_message.call_count == 1

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.WATCH_VIDEO_PROMPT

        markup = call_kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 1
        video_btn = markup.inline_keyboard[0][0]
        assert video_btn.url is not None
        assert video_btn.text == strings.WATCH_VIDEO_BUTTON
