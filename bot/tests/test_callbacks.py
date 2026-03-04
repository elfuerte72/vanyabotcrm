"""Tests for callback query handlers — all 7 callbacks × 3 languages.

Mocks: CallbackQuery, Bot, DB queries, media services.
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
    handle_show_info,
    handle_show_results,
    handle_check_suitability,
    handle_remind_later,
    handle_none,
    handle_video_workout,
)
from src.i18n import get_strings


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
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_sends_payment_message(
        self, mock_get_lang, mock_mark_buyer, language
    ):
        mock_get_lang.return_value = language
        callback = _make_callback(data="buy_now")
        bot = _make_bot()
        strings = get_strings(language)

        await handle_buy_now(callback, bot)

        mock_mark_buyer.assert_called_once_with(callback.from_user.id)
        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args
        assert call_kwargs.kwargs["text"] == strings.BUY_MESSAGE
        assert call_kwargs.kwargs["reply_markup"] is not None
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_keyboard_has_url_button(self, mock_get_lang, mock_mark_buyer):
        mock_get_lang.return_value = "ru"
        callback = _make_callback(data="buy_now")
        bot = _make_bot()

        await handle_buy_now(callback, bot)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        buttons = markup.inline_keyboard[0]
        assert len(buttons) == 1
        assert buttons[0].url is not None  # URL button, not callback
        strings = get_strings("ru")
        assert buttons[0].text == strings.BUY_BUTTON

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_default_language_en(self, mock_get_lang, mock_mark_buyer):
        """If user language is None, defaults to English."""
        mock_get_lang.return_value = None
        callback = _make_callback(data="buy_now")
        bot = _make_bot()

        await handle_buy_now(callback, bot)

        strings = get_strings("en")
        assert bot.send_message.call_args.kwargs["text"] == strings.BUY_MESSAGE


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
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_show_info_handles_error(self, mock_get_lang, mock_send_video, language):
        """On video download error, sends localized fallback text."""
        mock_get_lang.return_value = language
        mock_send_video.side_effect = Exception("Download failed")
        callback = _make_callback(data="show_info")
        bot = _make_bot()
        strings = get_strings(language)

        await handle_show_info(callback, bot)

        bot.send_message.assert_called_once()
        assert bot.send_message.call_args.args[1] == strings.VIDEO_UNAVAILABLE
        callback.answer.assert_called_once()


# ─── handle_show_results ─────────────────────────────────────────────────


class TestHandleShowResults:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_show_results_sends_photo(self, mock_get_lang, mock_send_photo, language):
        mock_get_lang.return_value = language
        callback = _make_callback(data="show_results")
        bot = _make_bot()
        strings = get_strings(language)

        await handle_show_results(callback, bot)

        mock_send_photo.assert_called_once_with(
            bot, callback.message.chat.id, caption=strings.RESULTS_CAPTION
        )
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_show_results_handles_error(self, mock_get_lang, mock_send_photo):
        mock_get_lang.return_value = "en"
        mock_send_photo.side_effect = Exception("Photo error")
        callback = _make_callback(data="show_results")
        bot = _make_bot()

        # Should not raise
        await handle_show_results(callback, bot)
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
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_remind_later_sends_message(self, mock_get_lang, language):
        mock_get_lang.return_value = language
        callback = _make_callback(data="remind_later")
        bot = _make_bot()
        strings = get_strings(language)

        await handle_remind_later(callback, bot)

        bot.send_message.assert_called_once_with(
            callback.message.chat.id, strings.REMIND_LATER, parse_mode="HTML"
        )
        callback.answer.assert_called_once()


# ─── handle_none ─────────────────────────────────────────────────────────


class TestHandleNone:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_none_sends_response(self, mock_get_lang, language):
        mock_get_lang.return_value = language
        callback = _make_callback(data="none")
        bot = _make_bot()
        strings = get_strings(language)

        await handle_none(callback, bot)

        bot.send_message.assert_called_once_with(
            callback.message.chat.id, strings.NONE_RESPONSE, parse_mode="HTML"
        )
        callback.answer.assert_called_once()


# ─── handle_video_workout ────────────────────────────────────────────────


class TestHandleVideoWorkout:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.advance_funnel_if_at_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_video_workout_sends_pitch_with_video_and_buy_buttons(self, mock_get_lang, mock_advance, language):
        mock_get_lang.return_value = language
        mock_advance.return_value = True
        callback = _make_callback(data="video_workout")
        bot = _make_bot()
        strings = get_strings(language)

        await handle_video_workout(callback, bot)

        # Answer callback first, then single message
        callback.answer.assert_called_once()
        assert bot.send_message.call_count == 1

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.VIDEO_WORKOUT_RESPONSE

        # Two rows: video URL button + buy callback button
        markup = call_kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 2
        video_btn = markup.inline_keyboard[0][0]
        assert video_btn.url is not None
        assert video_btn.text == strings.WATCH_VIDEO_BUTTON
        buy_btn = markup.inline_keyboard[1][0]
        assert buy_btn.callback_data == "buy_now"
        assert buy_btn.text == strings.BUY_BUTTON

        # Should advance funnel from stage 1→2
        mock_advance.assert_called_once_with(callback.from_user.id, expected_stage=1)
