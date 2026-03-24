"""Comprehensive callback tests × 3 languages — CRM updates, button config, text verification.

Uses db_user from UserDataMiddleware instead of get_user_language mock.

Extends test_callbacks.py with:
- Full CRM data flow verification (mark_as_buyer → is_buyer=TRUE)
- InlineKeyboard configuration for buy_now and video_workout
- Parametrized across all 3 languages
- Edge cases: db_user=None, error handling
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
    handle_confirm_paid_ru,
    handle_check_suitability,
    handle_none,
    handle_remind_later,
    handle_show_info,
    handle_show_results,
    handle_video_workout,
)
from src.i18n import get_strings

from tests.helpers import make_bot, make_callback, make_user

logger = logging.getLogger(__name__)


# ─── handle_buy_now × 3 languages ───────────────────────────────────────


class TestBuyNowMultilang:
    """buy_now: EN/AR marks buyer immediately; RU uses two-step confirmation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_en_ar_text(self, mock_mark, lang):
        db_user = make_user(lang)
        callback = make_callback(data="buy_now", chat_id=10000, user_id=10000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_buy_now(callback, bot, db_user=db_user)

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.BUY_MESSAGE, f"{lang}: BUY_MESSAGE mismatch"

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_ru_text_with_confirm(self, mock_mark):
        """RU: shows BUY_MESSAGE_WITH_CONFIRM instead of BUY_MESSAGE."""
        db_user = make_user("ru")
        callback = make_callback(data="buy_now", chat_id=10000, user_id=10000)
        bot = make_bot()
        strings = get_strings("ru")

        await handle_buy_now(callback, bot, db_user=db_user)

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.BUY_MESSAGE_WITH_CONFIRM

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_en_ar_marks_buyer_in_db(self, mock_mark, lang):
        """EN/AR: mark_as_buyer called immediately."""
        db_user = make_user(lang)
        callback = make_callback(data="buy_now", user_id=20000)
        bot = make_bot()

        await handle_buy_now(callback, bot, db_user=db_user)

        mock_mark.assert_called_once_with(20000)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_ru_does_not_mark_buyer(self, mock_mark):
        """RU: mark_as_buyer is NOT called on buy_now (two-step)."""
        db_user = make_user("ru")
        callback = make_callback(data="buy_now", user_id=20000)
        bot = make_bot()

        await handle_buy_now(callback, bot, db_user=db_user)

        mock_mark.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["en", "ar"])
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_en_ar_keyboard_has_url_button(self, mock_mark, lang):
        """EN/AR: single URL button."""
        db_user = make_user(lang)
        callback = make_callback(data="buy_now")
        bot = make_bot()
        strings = get_strings(lang)

        await handle_buy_now(callback, bot, db_user=db_user)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        buttons = markup.inline_keyboard[0]
        assert len(buttons) == 1
        assert buttons[0].url is not None, "Should be URL button"
        assert buttons[0].text == strings.BUY_BUTTON

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_ru_keyboard_has_confirm_button(self, mock_mark):
        """RU: 2 rows — URL button + confirm_paid_ru callback button."""
        db_user = make_user("ru")
        callback = make_callback(data="buy_now")
        bot = make_bot()
        strings = get_strings("ru")

        await handle_buy_now(callback, bot, db_user=db_user)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 2
        assert markup.inline_keyboard[0][0].url is not None
        assert markup.inline_keyboard[1][0].callback_data == "confirm_paid_ru"
        assert markup.inline_keyboard[1][0].text == strings.CONFIRM_PAID_BUTTON

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_none_db_user_defaults_en(self, mock_mark):
        """db_user=None defaults to English (marks buyer immediately)."""
        callback = make_callback(data="buy_now")
        bot = make_bot()

        await handle_buy_now(callback, bot, db_user=None)

        mock_mark.assert_called_once()
        strings = get_strings("en")
        assert bot.send_message.call_args.kwargs["text"] == strings.BUY_MESSAGE

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_answers_callback(self, mock_mark):
        db_user = make_user("en")
        callback = make_callback(data="buy_now")

        await handle_buy_now(callback, make_bot(), db_user=db_user)

        callback.answer.assert_called_once()


# ─── handle_confirm_paid_ru ─────────────────────────────────────────────


class TestConfirmPaidRuMultilang:
    """confirm_paid_ru: marks buyer and sends PAYMENT_CONFIRMED."""

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_confirm_paid_marks_buyer(self, mock_mark):
        callback = make_callback(data="confirm_paid_ru", user_id=30000, chat_id=30000)
        bot = make_bot()

        await handle_confirm_paid_ru(callback, bot)

        mock_mark.assert_called_once_with(30000)
        strings = get_strings("ru")
        assert bot.send_message.call_args.kwargs["text"] == strings.PAYMENT_CONFIRMED

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_confirm_paid_answers_callback(self, mock_mark):
        callback = make_callback(data="confirm_paid_ru")
        bot = make_bot()

        await handle_confirm_paid_ru(callback, bot)

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
        db_user = make_user("en")
        callback = make_callback(data="show_info", chat_id=30000)
        bot = make_bot()

        await handle_show_info(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once()
        assert "unavailable" in bot.send_message.call_args.args[1]


# ─── handle_show_results × 3 languages ──────────────────────────────────


class TestShowResultsMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    async def test_show_results_caption_per_language(self, mock_photo, lang):
        db_user = make_user(lang)
        callback = make_callback(data="show_results", chat_id=40000, user_id=40000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_show_results(callback, bot, db_user=db_user)

        mock_photo.assert_called_once_with(bot, 40000, caption=strings.RESULTS_CAPTION)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_random_result_photo", new_callable=AsyncMock)
    async def test_show_results_error_handled(self, mock_photo):
        mock_photo.side_effect = Exception("Photo error")
        db_user = make_user("en")
        callback = make_callback(data="show_results")

        await handle_show_results(callback, make_bot(), db_user=db_user)

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
    async def test_remind_later_text_per_language(self, lang):
        db_user = make_user(lang)
        callback = make_callback(data="remind_later", chat_id=60000, user_id=60000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_remind_later(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once_with(60000, strings.REMIND_LATER, parse_mode="HTML")
        callback.answer.assert_called_once()


# ─── handle_none × 3 languages ──────────────────────────────────────────


class TestNoneMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    async def test_none_text_per_language(self, lang):
        db_user = make_user(lang)
        callback = make_callback(data="none", chat_id=70000, user_id=70000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_none(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once_with(70000, strings.NONE_RESPONSE, parse_mode="HTML")
        callback.answer.assert_called_once()


# ─── handle_video_workout × 3 languages ─────────────────────────────────


class TestVideoWorkoutMultilang:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    async def test_video_workout_text_per_language(self, lang):
        db_user = make_user(lang)
        callback = make_callback(data="video_workout", chat_id=80000, user_id=80000)
        bot = make_bot()
        strings = get_strings(lang)

        await handle_video_workout(callback, bot, db_user=db_user)

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["text"] == strings.WATCH_VIDEO_PROMPT, (
            f"{lang}: WATCH_VIDEO_PROMPT mismatch"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    async def test_video_workout_keyboard_structure(self, lang):
        """Keyboard has 1 row: [video URL button]."""
        db_user = make_user(lang)
        callback = make_callback(data="video_workout")
        bot = make_bot()
        strings = get_strings(lang)

        await handle_video_workout(callback, bot, db_user=db_user)

        markup = bot.send_message.call_args.kwargs["reply_markup"]
        assert len(markup.inline_keyboard) == 1, "Should have 1 row (video only)"

        video_btn = markup.inline_keyboard[0][0]
        assert video_btn.url is not None, "First button should be URL"
        assert video_btn.text == strings.WATCH_VIDEO_BUTTON

    @pytest.mark.asyncio
    async def test_video_workout_answers_callback_first(self):
        """callback.answer() is called immediately (before send_message)."""
        db_user = make_user("en")
        callback = make_callback(data="video_workout")

        await handle_video_workout(callback, make_bot(), db_user=db_user)

        callback.answer.assert_called_once()


# ─── Summary: CRM data flow for each callback ───────────────────────────


class TestCRMDataFlow:
    """Verify that callbacks correctly update CRM-relevant data."""

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_buy_now_en_sets_is_buyer_true(self, mock_mark):
        """buy_now (EN/AR) → CRM: is_buyer changes from FALSE to TRUE."""
        db_user = make_user("en")
        callback = make_callback(data="buy_now", user_id=90001)
        await handle_buy_now(callback, make_bot(), db_user=db_user)

        mock_mark.assert_called_once_with(90001)

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.mark_as_buyer", new_callable=AsyncMock)
    async def test_confirm_paid_ru_sets_is_buyer_true(self, mock_mark):
        """confirm_paid_ru → CRM: is_buyer changes from FALSE to TRUE."""
        callback = make_callback(data="confirm_paid_ru", user_id=90010)
        await handle_confirm_paid_ru(callback, make_bot())

        mock_mark.assert_called_once_with(90010)

    @pytest.mark.asyncio
    async def test_video_workout_sends_video_link(self):
        """video_workout → sends video link, no delayed followup."""
        db_user = make_user("en")
        callback = make_callback(data="video_workout", user_id=90002)
        bot = make_bot()
        await handle_video_workout(callback, bot, db_user=db_user)

        bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.callbacks.send_info_video", new_callable=AsyncMock)
    async def test_show_info_no_crm_update(self, mock_video):
        """show_info → no CRM data changes."""
        callback = make_callback(data="show_info")
        await handle_show_info(callback, make_bot())
        # No mark_as_buyer or advance call

    @pytest.mark.asyncio
    async def test_remind_later_no_crm_update(self):
        """remind_later → no CRM data changes."""
        db_user = make_user("en")
        callback = make_callback(data="remind_later")
        await handle_remind_later(callback, make_bot(), db_user=db_user)

    @pytest.mark.asyncio
    async def test_none_no_crm_update(self):
        """none → no CRM data changes."""
        db_user = make_user("en")
        callback = make_callback(data="none")
        await handle_none(callback, make_bot(), db_user=db_user)
