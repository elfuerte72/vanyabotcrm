"""Funnel simulation tests.

RU: 8 stages (0-7) with photos, video notes, and specific callbacks.
EN/AR: 6 stages (0-5) with text + buttons only.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import logging
from unittest.mock import AsyncMock, patch

import pytest

from src.funnel.messages import get_funnel_message, FunnelMessage
from src.funnel.sender import send_funnel_messages
from src.i18n import get_strings

from tests.helpers import make_bot, make_funnel_targets

logger = logging.getLogger(__name__)

# Expected button callbacks for EN/AR (6 stages)
EXPECTED_BUTTONS_EN = {
    0: [("video_workout",)],
    1: [("buy_now",)],
    2: [("buy_now",), ("check_suitability",)],
    3: [("buy_now",), ("show_info",)],
    4: [("buy_now",), ("none",)],
    5: [("buy_now",), ("remind_later",)],
}

# Expected button callbacks for RU (8 stages)
EXPECTED_BUTTONS_RU = {
    0: [("video_workout",)],
    1: [("learn_workout",)],
    2: [],  # no buttons, photo only
    3: [("video_circle",)],
    4: [],  # text only
    5: [("buy_now",)],
    6: [("buy_now",)],
    7: [],  # URL button (channel link), tested separately
}


# ─── EN/AR funnel text matches i18n ─────────────────────────────────────


class TestFunnelMessageTextMatchesI18nEN:
    @pytest.mark.parametrize("lang", ["en", "ar"])
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    def test_funnel_text_matches_i18n(self, lang, stage):
        strings = get_strings(lang)
        msg = get_funnel_message(stage, lang)
        assert msg is not None
        expected_text = getattr(strings, f"FUNNEL_DAY_{stage}")
        assert msg.text == expected_text


class TestFunnelMessageTextMatchesI18nRU:
    @pytest.mark.parametrize("stage", range(8))
    def test_funnel_text_matches_i18n_ru(self, stage):
        strings = get_strings("ru")
        msg = get_funnel_message(stage, "ru")
        assert msg is not None
        expected_text = getattr(strings, f"FUNNEL_STAGE_{stage}")
        assert msg.text == expected_text


# ─── Button callback_data verification ──────────────────────────────────


class TestFunnelButtonsEN:
    @pytest.mark.parametrize("lang", ["en", "ar"])
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    def test_buttons_have_correct_callback_data(self, lang, stage):
        msg = get_funnel_message(stage, lang)
        assert msg is not None
        expected_cbs = EXPECTED_BUTTONS_EN[stage]
        actual_cbs = [(btn[1],) for btn in msg.buttons]
        assert actual_cbs == expected_cbs

    @pytest.mark.parametrize("lang", ["en", "ar"])
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    def test_button_labels_match_i18n(self, lang, stage):
        strings = get_strings(lang)
        msg = get_funnel_message(stage, lang)
        assert msg is not None
        if stage == 0:
            expected_labels = [strings.FUNNEL_DAY_0_BUTTON]
        elif stage == 1:
            expected_labels = [strings.FUNNEL_DAY_1_BUTTON]
        else:
            expected_labels = [btn[0] for btn in getattr(strings, f"FUNNEL_DAY_{stage}_BUTTONS")]
        actual_labels = [btn[0] for btn in msg.buttons]
        assert actual_labels == expected_labels


class TestFunnelButtonsRU:
    @pytest.mark.parametrize("stage", range(8))
    def test_ru_buttons_have_correct_callback_data(self, stage):
        msg = get_funnel_message(stage, "ru")
        assert msg is not None
        expected = EXPECTED_BUTTONS_RU[stage]
        actual = [(btn[1],) for btn in msg.buttons]
        if stage == 7:
            # Stage 7 has URL button with empty callback
            assert msg.has_url_button
            assert "ivanfit_health" in msg.url
        else:
            assert actual == expected


# ─── Out of range ───────────────────────────────────────────────────────


class TestFunnelOutOfRange:
    def test_en_stage_6_returns_none(self):
        assert get_funnel_message(6, "en") is None

    def test_ru_stage_8_returns_none(self):
        assert get_funnel_message(8, "ru") is None

    def test_stage_minus_1_returns_none(self):
        assert get_funnel_message(-1, "en") is None

    def test_stage_100_returns_none(self):
        assert get_funnel_message(100, "en") is None


# ─── Full cycle simulation (EN/AR) ──────────────────────────────────────


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
            mock_update_stage.assert_called_once_with(
                chat_id, language="en", current_stage=day
            )


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
            mock_update_stage.assert_called_once_with(
                chat_id, language="ar", current_stage=day
            )


# ─── Stage increment ────────────────────────────────────────────────────


class TestFunnelStageIncrement:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_stage_increments_after_each_send(self, mock_targets, mock_update):
        bot = make_bot()
        chat_id = 400001

        mock_targets.return_value = [
            {"chat_id": chat_id, "funnel_stage": 2, "language": "en"}
        ]

        await send_funnel_messages(bot)

        bot.send_message.assert_called_once()
        mock_update.assert_called_once_with(chat_id, language="en", current_stage=2)


# ─── Buyer exclusion ────────────────────────────────────────────────────


class TestBuyerExcludedFromFunnel:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_no_targets_means_no_sends(self, mock_targets, mock_update):
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
        bot = make_bot()

        mock_targets.return_value = [
            {"chat_id": 500001, "funnel_stage": 0, "language": "en"},
            {"chat_id": 500002, "funnel_stage": 0, "language": "en"},
            {"chat_id": 500003, "funnel_stage": 0, "language": "en"},
        ]

        call_count = 0

        async def send_message_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if kwargs.get("chat_id") == 500002:
                raise Exception("User blocked the bot")

        bot.send_message.side_effect = send_message_side_effect

        await send_funnel_messages(bot)

        assert bot.send_message.call_count == 3
        update_calls = [c.args[0] for c in mock_update.call_args_list]
        assert 500001 in update_calls
        assert 500002 not in update_calls
        assert 500003 in update_calls


# ─── Mixed languages ────────────────────────────────────────────────────


class TestFunnelMixedLanguages:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_mixed_stages_get_correct_day_messages(self, mock_targets, mock_update):
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


# ─── EN keyboard verification ───────────────────────────────────────────


class TestFunnelKeyboardConfigurationEN:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("stage", [0, 1, 2, 3, 4, 5])
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_keyboard_buttons_sent_correctly(self, mock_targets, mock_update, stage):
        bot = make_bot()

        mock_targets.return_value = [
            {"chat_id": 800001, "funnel_stage": stage, "language": "en"}
        ]

        await send_funnel_messages(bot)

        send_kwargs = bot.send_message.call_args.kwargs
        markup = send_kwargs["reply_markup"]
        rows = markup.inline_keyboard
        expected_cbs = EXPECTED_BUTTONS_EN[stage]

        assert len(rows) == len(expected_cbs)
        for row, (expected_cb,) in zip(rows, expected_cbs):
            btn = row[0]
            assert btn.callback_data == expected_cb
