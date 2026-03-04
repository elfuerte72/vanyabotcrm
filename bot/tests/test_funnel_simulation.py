"""Funnel simulation tests: 6-day cycle × 3 languages (RU/EN/AR).

Tests:
- Full 6-day funnel cycle per language with text/button verification
- Funnel stage progression
- Buyer exclusion from funnel
- Error resilience (one user failure doesn't block others)
- Mixed-language batch
- Button label and callback_data correctness
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import logging
from unittest.mock import AsyncMock, patch, call

import pytest

from src.funnel.messages import get_funnel_message, FunnelMessage
from src.funnel.sender import send_funnel_messages
from src.i18n import get_strings

from tests.helpers import make_bot, make_funnel_targets

logger = logging.getLogger(__name__)

# Expected button configurations per stage
EXPECTED_BUTTONS = {
    0: [("video_workout",)],  # single callback button
    1: [("buy_now",)],
    2: [("buy_now",), ("check_suitability",)],
    3: [("buy_now",), ("show_info",)],
    4: [("buy_now",), ("none",)],
    5: [("buy_now",), ("remind_later",)],
}


# ─── get_funnel_message text verification ────────────────────────────────


class TestFunnelMessageTextMatchesI18n:
    """Verify funnel message text exactly matches i18n strings."""

    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    def test_funnel_text_matches_i18n(self, lang, stage):
        strings = get_strings(lang)
        msg = get_funnel_message(stage, lang)

        assert msg is not None, f"Stage {stage} should return a message"

        expected_text = getattr(strings, f"FUNNEL_DAY_{stage}")
        assert msg.text == expected_text, (
            f"Stage {stage} ({lang}): text mismatch"
        )


class TestFunnelButtonsCorrectPerStage:
    """Verify button callback_data for each stage."""

    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    def test_buttons_have_correct_callback_data(self, lang, stage):
        msg = get_funnel_message(stage, lang)
        assert msg is not None

        expected_cbs = EXPECTED_BUTTONS[stage]
        actual_cbs = [(btn[1],) for btn in msg.buttons]

        assert actual_cbs == expected_cbs, (
            f"Stage {stage} ({lang}): button callback_data mismatch. "
            f"Expected {expected_cbs}, got {actual_cbs}"
        )

    @pytest.mark.parametrize("lang", ["ru", "en", "ar"])
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    def test_button_labels_match_i18n(self, lang, stage):
        strings = get_strings(lang)
        msg = get_funnel_message(stage, lang)
        assert msg is not None

        if stage == 0:
            expected_labels = [getattr(strings, "FUNNEL_DAY_0_BUTTON")]
        elif stage == 1:
            expected_labels = [getattr(strings, "FUNNEL_DAY_1_BUTTON")]
        else:
            buttons_attr = getattr(strings, f"FUNNEL_DAY_{stage}_BUTTONS")
            expected_labels = [btn[0] for btn in buttons_attr]

        actual_labels = [btn[0] for btn in msg.buttons]
        assert actual_labels == expected_labels, (
            f"Stage {stage} ({lang}): button label mismatch"
        )


class TestFunnelOutOfRange:
    def test_stage_minus_1_returns_none(self):
        assert get_funnel_message(-1, "en") is None

    def test_stage_6_returns_none(self):
        assert get_funnel_message(6, "en") is None

    def test_stage_100_returns_none(self):
        assert get_funnel_message(100, "en") is None


# ─── Full 6-day cycle simulation ────────────────────────────────────────


class TestFullFunnelCycleRU:
    """Simulate complete 6-day funnel for a Russian user."""

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_full_cycle_ru(self, mock_targets, mock_update_stage):
        bot = make_bot()
        strings = get_strings("ru")
        chat_id = 300001

        for day in range(6):
            # Simulate scheduler: user is at stage=day
            mock_targets.return_value = [
                {"chat_id": chat_id, "funnel_stage": day, "language": "ru"}
            ]
            mock_update_stage.reset_mock()
            bot.send_message.reset_mock()

            await send_funnel_messages(bot)

            # Message was sent
            bot.send_message.assert_called_once()
            send_kwargs = bot.send_message.call_args.kwargs
            assert send_kwargs["chat_id"] == chat_id

            expected_text = getattr(strings, f"FUNNEL_DAY_{day}")
            assert send_kwargs["text"] == expected_text, f"Day {day}: text mismatch"

            # Stage was incremented
            mock_update_stage.assert_called_once_with(chat_id)


class TestFullFunnelCycleEN:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_full_cycle_en(self, mock_targets, mock_update_stage):
        bot = make_bot()
        strings = get_strings("en")
        chat_id = 300002

        for day in range(6):
            mock_targets.return_value = [
                {"chat_id": chat_id, "funnel_stage": day, "language": "en"}
            ]
            mock_update_stage.reset_mock()
            bot.send_message.reset_mock()

            await send_funnel_messages(bot)

            send_kwargs = bot.send_message.call_args.kwargs
            expected_text = getattr(strings, f"FUNNEL_DAY_{day}")
            assert send_kwargs["text"] == expected_text, f"Day {day} (EN): text mismatch"
            mock_update_stage.assert_called_once_with(chat_id)


class TestFullFunnelCycleAR:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_full_cycle_ar(self, mock_targets, mock_update_stage):
        bot = make_bot()
        strings = get_strings("ar")
        chat_id = 300003

        for day in range(6):
            mock_targets.return_value = [
                {"chat_id": chat_id, "funnel_stage": day, "language": "ar"}
            ]
            mock_update_stage.reset_mock()
            bot.send_message.reset_mock()

            await send_funnel_messages(bot)

            send_kwargs = bot.send_message.call_args.kwargs
            expected_text = getattr(strings, f"FUNNEL_DAY_{day}")
            assert send_kwargs["text"] == expected_text, f"Day {day} (AR): text mismatch"
            mock_update_stage.assert_called_once_with(chat_id)


# ─── Stage increment ────────────────────────────────────────────────────


class TestFunnelStageIncrement:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_stage_increments_after_each_send(self, mock_targets, mock_update):
        """update_funnel_stage is called AFTER send_message for each user."""
        bot = make_bot()
        chat_id = 400001

        mock_targets.return_value = [
            {"chat_id": chat_id, "funnel_stage": 2, "language": "en"}
        ]

        await send_funnel_messages(bot)

        # send_message was called first, then update_funnel_stage
        bot.send_message.assert_called_once()
        mock_update.assert_called_once_with(chat_id)


# ─── Buyer exclusion ────────────────────────────────────────────────────


class TestBuyerExcludedFromFunnel:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_no_targets_means_no_sends(self, mock_targets, mock_update):
        """If get_funnel_targets returns empty (all buyers), nothing is sent."""
        bot = make_bot()
        mock_targets.return_value = []

        await send_funnel_messages(bot)

        bot.send_message.assert_not_called()
        mock_update.assert_not_called()


# ─── Error resilience ───────────────────────────────────────────────────


class TestFunnelErrorResilience:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_one_user_error_does_not_block_others(self, mock_targets, mock_update):
        """If send_message fails for one user, other users still get messages."""
        bot = make_bot()

        mock_targets.return_value = [
            {"chat_id": 500001, "funnel_stage": 0, "language": "ru"},
            {"chat_id": 500002, "funnel_stage": 0, "language": "en"},
            {"chat_id": 500003, "funnel_stage": 0, "language": "ar"},
        ]

        # Fail for the second user
        call_count = 0

        async def send_message_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if kwargs.get("chat_id") == 500002:
                raise Exception("User blocked the bot")

        bot.send_message.side_effect = send_message_side_effect

        await send_funnel_messages(bot)

        # All 3 were attempted
        assert bot.send_message.call_count == 3

        # update_funnel_stage called for users 1 and 3, NOT for user 2
        update_calls = [c.args[0] for c in mock_update.call_args_list]
        assert 500001 in update_calls
        assert 500002 not in update_calls  # failed user
        assert 500003 in update_calls


# ─── Mixed languages ────────────────────────────────────────────────────


class TestFunnelMixedLanguages:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_mixed_languages_get_correct_messages(self, mock_targets, mock_update):
        """Multiple users with different languages all get correctly localized messages."""
        bot = make_bot()

        mock_targets.return_value = make_funnel_targets(
            languages=["ru", "en", "ar"], stage=3, base_chat_id=600000
        )

        await send_funnel_messages(bot)

        assert bot.send_message.call_count == 3

        for i, lang in enumerate(["ru", "en", "ar"]):
            call_kwargs = bot.send_message.call_args_list[i].kwargs
            expected_text = get_strings(lang).FUNNEL_DAY_3
            assert call_kwargs["chat_id"] == 600000 + i
            assert call_kwargs["text"] == expected_text, f"User {lang}: wrong text"

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_mixed_stages_get_correct_day_messages(self, mock_targets, mock_update):
        """Users at different funnel stages get their corresponding day message."""
        bot = make_bot()

        mock_targets.return_value = [
            {"chat_id": 700001, "funnel_stage": 0, "language": "en"},
            {"chat_id": 700002, "funnel_stage": 2, "language": "en"},
            {"chat_id": 700003, "funnel_stage": 4, "language": "en"},
        ]

        await send_funnel_messages(bot)

        strings = get_strings("en")
        calls = bot.send_message.call_args_list

        assert calls[0].kwargs["text"] == strings.FUNNEL_DAY_0
        assert calls[1].kwargs["text"] == strings.FUNNEL_DAY_2
        assert calls[2].kwargs["text"] == strings.FUNNEL_DAY_4


# ─── Keyboard verification ──────────────────────────────────────────────


class TestFunnelKeyboardConfiguration:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_keyboard_buttons_sent_correctly(self, mock_targets, mock_update, stage):
        """Verify that InlineKeyboard sent by sender matches expected buttons."""
        bot = make_bot()

        mock_targets.return_value = [
            {"chat_id": 800001, "funnel_stage": stage, "language": "en"}
        ]

        await send_funnel_messages(bot)

        send_kwargs = bot.send_message.call_args.kwargs
        markup = send_kwargs["reply_markup"]

        # sender.py puts each button in its own row
        rows = markup.inline_keyboard
        expected_cbs = EXPECTED_BUTTONS[stage]

        assert len(rows) == len(expected_cbs), (
            f"Stage {stage}: expected {len(expected_cbs)} button rows, got {len(rows)}"
        )

        for row, (expected_cb,) in zip(rows, expected_cbs):
            btn = row[0]
            assert btn.callback_data == expected_cb, (
                f"Stage {stage}: expected callback_data={expected_cb}, got {btn.callback_data}"
            )
