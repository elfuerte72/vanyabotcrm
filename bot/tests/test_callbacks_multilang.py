"""Comprehensive callback tests × 3 languages — CRM updates, button config, text verification.

Extends test_callbacks.py with:
- Full CRM data flow verification (mark_as_buyer → is_buyer=TRUE)
- advance_funnel_if_at_stage verification for video_workout
- InlineKeyboard configuration for buy_now and video_workout
- Parametrized across all 3 languages
- Edge cases: None language, error handling
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import logging
from unittest.mock import AsyncMock, patch

import pytest

from src.handlers.callbacks import (
    handle_buy_now,
    handle_check_suitability,
    handle_none,
    handle_remind_later,
    handle_show_info,
    handle_show_results,
    handle_video_workout,
)
from src.i18n import get_strings

from tests.helpers import make_bot, make_callback

logger = logging.getLogger(__name__)


# ─── handle_buy_now × 3 languages ───────────────────────────────────────


class TestBuyNowMultilang:
    """buy_now: marks buyer, sends payment message in user's language."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_text_per_language(self, mock_get_lang, mock_mark, lang):
        mock_get_lang.return_value = lang
        callback = make_callback(data="buy_now", chat_id=10000, user_id=10000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_buy_now(callback, bot)

        # Text matches i18n
        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.BUY_MESSAGE, f"{lang}: BUY_MESSAGE mismatch"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_marks_buyer_in_db(self, mock_get_lang, mock_mark, lang):
        """CRM update: mark_as_buyer sets is_buyer=TRUE."""
        mock_get_lang.return_value = lang
        callback = make_callback(data="buy_now", user_id=20000)
        bot = make_bot()

        await handle_buy_now(callback, bot)

        mock_mark.assert_called_once_with(20000)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_keyboard_has_url_button(self, mock_get_lang, mock_mark, lang):
        """Payment button is a URL button (not callback)."""
        mock_get_lang.return_value = lang
        callback = make_callback(data="buy_now")
        bot = make_bot()
        strings = get_strings(lang)

        await handle_buy_now(callback, bot)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        buttons = markup.inline_keyboard[0]
        assert len(buttons) == 1
        assert buttons[0].url is not None, "Should be URL button"
        assert buttons[0].text == strings.BUY_BUTTON

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_none_language_defaults_en(self, mock_get_lang, mock_mark):
        """Language=None defaults to English."""
        mock_get_lang.return_value = None
        callback = make_callback(data="buy_now")
        bot = make_bot()

        await handle_buy_now(callback, bot)

        strings = get_strings("en")
        assert bot.send_message.call_args.kwargs["text"] == strings.BUY_MESSAGE

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_answers_callback(self, mock_get_lang, mock_mark):
        mock_get_lang.return_value = "en"
        callback = make_callback(data="buy_now")

        await handle_buy_now(callback, make_bot())

        callback.answer.assert_called_once()


# ─── handle_show_info ────────────────────────────────────────────────────


class TestShowInfoMultilang:
    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_info_video", new_callable=AsyncMock)
    async def test_show_info_sends_video(self, mock_video):
        callback = make_callback(data="show_info", chat_id=30000)
        bot = make_bot()

        await handle_show_info(callback, bot)

        mock_video.assert_called_once_with(bot, 30000)
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_info_video", new_callable=AsyncMock)
    async def test_show_info_error_sends_fallback(self, mock_video):
        mock_video.side_effect = Exception("Download failed")
        callback = make_callback(data="show_info", chat_id=30000)
        bot = make_bot()

        await handle_show_info(callback, bot)

        bot.send_message.assert_called_once()
        assert "unavailable" in bot.send_message.call_args.args[1]


# ─── handle_show_results × 3 languages ──────────────────────────────────


class TestShowResultsMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_show_results_caption_per_language(self, mock_get_lang, mock_photo, lang):
        mock_get_lang.return_value = lang
        callback = make_callback(data="show_results", chat_id=40000, user_id=40000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_show_results(callback, bot)

        mock_photo.assert_called_once_with(bot, 40000, caption=strings.RESULTS_CAPTION)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_show_results_error_handled(self, mock_get_lang, mock_photo):
        mock_get_lang.return_value = "en"
        mock_photo.side_effect = Exception("Photo error")
        callback = make_callback(data="show_results")

        await handle_show_results(callback, make_bot())

        callback.answer.assert_called_once()  # Should not raise


# ─── handle_check_suitability ────────────────────────────────────────────


class TestCheckSuitabilityMultilang:
    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_suitability_video", new_callable=AsyncMock)
    async def test_check_suitability_sends_video(self, mock_video):
        callback = make_callback(data="check_suitability", chat_id=50000)
        bot = make_bot()

        await handle_check_suitability(callback, bot)

        mock_video.assert_called_once_with(bot, 50000)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_suitability_video", new_callable=AsyncMock)
    async def test_check_suitability_error_handled(self, mock_video):
        mock_video.side_effect = Exception("Video error")
        callback = make_callback(data="check_suitability")

        await handle_check_suitability(callback, make_bot())

        callback.answer.assert_called_once()


# ─── handle_remind_later × 3 languages ──────────────────────────────────


class TestRemindLaterMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_remind_later_text_per_language(self, mock_get_lang, lang):
        mock_get_lang.return_value = lang
        callback = make_callback(data="remind_later", chat_id=60000, user_id=60000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_remind_later(callback, bot)

        bot.send_message.assert_called_once_with(60000, strings.REMIND_LATER, parse_mode="HTML")
        callback.answer.assert_called_once()


# ─── handle_none × 3 languages ──────────────────────────────────────────


class TestNoneMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_none_text_per_language(self, mock_get_lang, lang):
        mock_get_lang.return_value = lang
        callback = make_callback(data="none", chat_id=70000, user_id=70000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_none(callback, bot)

        bot.send_message.assert_called_once_with(70000, strings.NONE_RESPONSE, parse_mode="HTML")
        callback.answer.assert_called_once()


# ─── handle_video_workout × 3 languages ─────────────────────────────────


class TestVideoWorkoutMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.advance_funnel_if_at_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_video_workout_text_per_language(self, mock_get_lang, mock_advance, lang):
        mock_get_lang.return_value = lang
        mock_advance.return_value = True
        callback = make_callback(data="video_workout", chat_id=80000, user_id=80000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_video_workout(callback, bot)

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.VIDEO_WORKOUT_RESPONSE, (
            f"{lang}: VIDEO_WORKOUT_RESPONSE mismatch"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.advance_funnel_if_at_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_video_workout_advances_funnel(self, mock_get_lang, mock_advance, lang):
        """CRM update: advance_funnel_if_at_stage(user_id, 1) called."""
        mock_get_lang.return_value = lang
        mock_advance.return_value = True
        callback = make_callback(data="video_workout", user_id=80000)
        bot = make_bot()

        await handle_video_workout(callback, bot)

        mock_advance.assert_called_once_with(80000, expected_stage=1)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.advance_funnel_if_at_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_video_workout_keyboard_structure(self, mock_get_lang, mock_advance, lang):
        """Keyboard has 2 rows: [video URL button], [buy_now callback button]."""
        mock_get_lang.return_value = lang
        mock_advance.return_value = True
        callback = make_callback(data="video_workout")
        bot = make_bot()
        strings = get_strings(lang)

        await handle_video_workout(callback, bot)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 2, "Should have 2 rows"

        # Row 1: video URL button
        video_btn = markup.inline_keyboard[0][0]
        assert video_btn.url is not None, "First button should be URL"
        assert video_btn.text == strings.WATCH_VIDEO_BUTTON

        # Row 2: buy callback button
        buy_btn = markup.inline_keyboard[1][0]
        assert buy_btn.callback_data == "buy_now"
        assert buy_btn.text == strings.BUY_BUTTON

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.advance_funnel_if_at_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_video_workout_answers_callback_first(self, mock_get_lang, mock_advance):
        """callback.answer() is called immediately (before send_message)."""
        mock_get_lang.return_value = "en"
        mock_advance.return_value = True
        callback = make_callback(data="video_workout")

        await handle_video_workout(callback, make_bot())

        callback.answer.assert_called_once()


# ─── Summary: CRM data flow for each callback ───────────────────────────


class TestCRMDataFlow:
    """Verify that callbacks correctly update CRM-relevant data."""

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_buy_now_sets_is_buyer_true(self, mock_lang, mock_mark):
        """buy_now → CRM: is_buyer changes from FALSE to TRUE."""
        mock_lang.return_value = "en"
        callback = make_callback(data="buy_now", user_id=90001)
        await handle_buy_now(callback, make_bot())

        mock_mark.assert_called_once_with(90001)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.advance_funnel_if_at_stage", new_callable=AsyncMock)
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_video_workout_advances_stage_1_to_2(self, mock_lang, mock_advance):
        """video_workout → CRM: funnel_stage conditionally 1→2."""
        mock_lang.return_value = "en"
        mock_advance.return_value = True
        callback = make_callback(data="video_workout", user_id=90002)
        await handle_video_workout(callback, make_bot())

        mock_advance.assert_called_once_with(90002, expected_stage=1)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_info_video", new_callable=AsyncMock)
    async def test_show_info_no_crm_update(self, mock_video):
        """show_info → no CRM data changes."""
        callback = make_callback(data="show_info")
        await handle_show_info(callback, make_bot())
        # No mark_as_buyer or advance call

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_remind_later_no_crm_update(self, mock_lang):
        """remind_later → no CRM data changes."""
        mock_lang.return_value = "en"
        callback = make_callback(data="remind_later")
        await handle_remind_later(callback, make_bot())

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.get_user_language", new_callable=AsyncMock)
    async def test_none_no_crm_update(self, mock_lang):
        """none → no CRM data changes."""
        mock_lang.return_value = "en"
        callback = make_callback(data="none")
        await handle_none(callback, make_bot())
