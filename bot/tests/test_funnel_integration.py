"""Funnel integration tests — message content, sender logic, full cycle.

RU: 8 stages (0-7), EN/AR: 6 stages (0-5).
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

from unittest.mock import AsyncMock, patch

import pytest

from src.funnel.messages import get_funnel_message, FunnelMessage
from src.i18n import get_strings


# ═══════════════════════════════════════════════════════════════════════════
# Part 1: EN/AR message content verification (6 stages × 2 languages)
# ═══════════════════════════════════════════════════════════════════════════

EN_AR_LANGUAGES = ["en", "ar"]

EXPECTED_EN_BUTTONS = {
    0: ["video_workout"],
    1: ["buy_now"],
    2: ["buy_now", "check_suitability"],
    3: ["buy_now", "show_info"],
    4: ["buy_now", "none"],
    5: ["buy_now", "remind_later"],
}


class TestFunnelMessageContentEN:
    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_stage_0_has_callback_button(self, language):
        msg = get_funnel_message(0, language)
        assert msg is not None
        assert msg.has_url_button is False
        assert msg.buttons[0][1] == "video_workout"

    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_stage_1_buy_button(self, language):
        msg = get_funnel_message(1, language)
        assert msg is not None
        assert len(msg.buttons) == 1
        assert msg.buttons[0][1] == "buy_now"

    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_stage_2_buttons(self, language):
        msg = get_funnel_message(2, language)
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "check_suitability" in callbacks

    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_stage_3_buttons(self, language):
        msg = get_funnel_message(3, language)
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "show_info" in callbacks

    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_stage_4_buttons(self, language):
        msg = get_funnel_message(4, language)
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "none" in callbacks

    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_stage_5_buttons(self, language):
        msg = get_funnel_message(5, language)
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "remind_later" in callbacks


# ═══════════════════════════════════════════════════════════════════════════
# Part 1b: RU message content verification (8 stages)
# ═══════════════════════════════════════════════════════════════════════════


class TestFunnelMessageContentRU:
    def test_stage_0_video_workout(self):
        msg = get_funnel_message(0, "ru")
        assert msg.buttons[0][1] == "video_workout"

    def test_stage_1_learn_workout_with_photo(self):
        msg = get_funnel_message(1, "ru")
        assert msg.buttons[0][1] == "learn_workout"
        assert msg.photo_name

    def test_stage_2_photo_no_buttons(self):
        msg = get_funnel_message(2, "ru")
        assert msg.photo_name
        assert len(msg.buttons) == 0

    def test_stage_3_video_circle(self):
        msg = get_funnel_message(3, "ru")
        assert msg.buttons[0][1] == "video_circle"
        assert msg.video_note_id

    def test_stage_4_text_only(self):
        msg = get_funnel_message(4, "ru")
        assert len(msg.buttons) == 0

    def test_stage_5_buy_now(self):
        msg = get_funnel_message(5, "ru")
        assert msg.buttons[0][1] == "buy_now"
        assert "690" in msg.text

    def test_stage_6_buy_now(self):
        msg = get_funnel_message(6, "ru")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_7_channel_url(self):
        msg = get_funnel_message(7, "ru")
        assert msg.has_url_button
        assert "ivanfit_health" in msg.url


class TestFunnelMessageText:
    @pytest.mark.parametrize("stage", range(6))
    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_en_message_text_not_empty(self, stage, language):
        msg = get_funnel_message(stage, language)
        assert msg is not None
        assert len(msg.text) > 50

    @pytest.mark.parametrize("stage", range(8))
    def test_ru_message_text_not_empty(self, stage):
        msg = get_funnel_message(stage, "ru")
        assert msg is not None
        assert len(msg.text) > 50

    @pytest.mark.parametrize("language", ["ru", "en", "ar"])
    def test_stage_0_mentions_7_minutes(self, language):
        msg = get_funnel_message(0, language)
        assert "7" in msg.text


class TestFunnelMessageEdgeCases:
    def test_en_stage_out_of_range_returns_none(self):
        assert get_funnel_message(6, "en") is None
        assert get_funnel_message(-1, "en") is None

    def test_ru_stage_out_of_range_returns_none(self):
        assert get_funnel_message(8, "ru") is None
        assert get_funnel_message(-1, "ru") is None

    def test_unknown_language_falls_back_to_english(self):
        msg_unknown = get_funnel_message(1, "fr")
        msg_en = get_funnel_message(1, "en")
        assert msg_unknown.text == msg_en.text

    @pytest.mark.parametrize("language", EN_AR_LANGUAGES)
    def test_en_buttons_are_tuple_pairs(self, language):
        for stage in range(6):
            msg = get_funnel_message(stage, language)
            for btn in msg.buttons:
                assert isinstance(btn, tuple)
                assert len(btn) == 2


# ═══════════════════════════════════════════════════════════════════════════
# Part 2: Sender logic with mocked DB and Bot
# ═══════════════════════════════════════════════════════════════════════════


class TestFunnelSender:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_sends_to_non_buyers(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 0, "language": "en"},
            {"chat_id": 222, "funnel_stage": 2, "language": "en"},
            {"chat_id": 333, "funnel_stage": 4, "language": "en"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)

        assert bot.send_message.call_count == 3
        assert mock_update.call_count == 3

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_uses_correct_language(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 0, "language": "en"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)

        call_kwargs = bot.send_message.call_args.kwargs
        expected_msg = get_funnel_message(0, "en")
        assert call_kwargs["text"] == expected_msg.text

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_skips_invalid_stage(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 10, "language": "ru"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)

        bot.send_message.assert_not_called()
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_continues_on_send_failure(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 0, "language": "en"},
            {"chat_id": 222, "funnel_stage": 0, "language": "en"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=[Exception("Blocked"), None])

        await send_funnel_messages(bot)

        assert bot.send_message.call_count == 2
        assert mock_update.call_count == 1
        mock_update.assert_called_with(222, language="en", current_stage=0)

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_no_targets(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = []
        bot = AsyncMock()

        await send_funnel_messages(bot)

        bot.send_message.assert_not_called()
        mock_update.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# Part 3: Full cycle
# ═══════════════════════════════════════════════════════════════════════════


class TestFullFunnelCycle:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_en_6_day_cycle(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        bot = AsyncMock()
        bot.send_message = AsyncMock()

        for day in range(6):
            mock_targets.return_value = [
                {"chat_id": 555, "funnel_stage": day, "language": "en"},
            ]
            bot.send_message.reset_mock()
            mock_update.reset_mock()

            await send_funnel_messages(bot)

            expected = get_funnel_message(day, "en")
            call_kwargs = bot.send_message.call_args.kwargs
            assert call_kwargs["text"] == expected.text, f"Day {day}: wrong text"
            mock_update.assert_called_once_with(555, language="en", current_stage=day)

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_after_last_en_stage_no_messages(self, mock_targets, mock_update):
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 555, "funnel_stage": 6, "language": "en"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)
        bot.send_message.assert_not_called()
