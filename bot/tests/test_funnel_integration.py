"""Funnel integration tests — message content, sender logic, full 6-day cycle.

Part 1: Content verification (18 tests: 6 stages × 3 languages)
Part 2: Sender integration with real DB
Part 3: Full 6-day cycle simulation
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
# Part 1: Message content verification (6 stages × 3 languages = 18 tests)
# ═══════════════════════════════════════════════════════════════════════════


LANGUAGES = ["ru", "en", "ar"]

# Expected buttons mapping: stage → list of callback_data values
EXPECTED_BUTTONS = {
    0: ["video_workout"],
    1: ["buy_now"],
    2: ["buy_now", "check_suitability"],
    3: ["buy_now", "show_info"],
    4: ["buy_now", "none"],
    5: ["buy_now", "remind_later"],
}


class TestFunnelMessageContent:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_0_has_url_button(self, language):
        """Stage 0 has a URL button (workout video link)."""
        msg = get_funnel_message(0, language)
        assert msg is not None
        assert msg.has_url_button is True
        assert len(msg.buttons) >= 1
        assert msg.buttons[0][1] == "video_workout"

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_1_buy_button(self, language):
        """Stage 1 has a single buy_now button."""
        msg = get_funnel_message(1, language)
        assert msg is not None
        assert len(msg.buttons) == 1
        assert msg.buttons[0][1] == "buy_now"

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_2_buttons(self, language):
        """Stage 2 has buy_now + check_suitability buttons."""
        msg = get_funnel_message(2, language)
        assert msg is not None
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "check_suitability" in callbacks

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_3_buttons(self, language):
        """Stage 3 has buy_now + show_info buttons."""
        msg = get_funnel_message(3, language)
        assert msg is not None
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "show_info" in callbacks

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_4_buttons(self, language):
        """Stage 4 has buy_now + none buttons."""
        msg = get_funnel_message(4, language)
        assert msg is not None
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "none" in callbacks

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_5_buttons(self, language):
        """Stage 5 has buy_now + remind_later buttons."""
        msg = get_funnel_message(5, language)
        assert msg is not None
        callbacks = [b[1] for b in msg.buttons]
        assert "buy_now" in callbacks
        assert "remind_later" in callbacks


class TestFunnelMessageText:
    @pytest.mark.parametrize("stage", range(6))
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_message_text_not_empty(self, stage, language):
        """Every stage/language combination has non-empty text."""
        msg = get_funnel_message(stage, language)
        assert msg is not None, f"Stage {stage}, lang {language} returned None"
        assert len(msg.text) > 50, f"Message text too short for stage {stage}, {language}"

    @pytest.mark.parametrize("stage", range(6))
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_button_labels_not_empty(self, stage, language):
        """All button labels are non-empty strings."""
        msg = get_funnel_message(stage, language)
        assert msg is not None
        for label, callback in msg.buttons:
            assert len(label) > 0, f"Empty label for {callback} at stage {stage}, {language}"

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_stage_0_mentions_7_minutes(self, language):
        """Stage 0 text mentions the 7-minute workout."""
        msg = get_funnel_message(0, language)
        assert "7" in msg.text, f"Stage 0 should mention 7 minutes ({language})"


class TestFunnelMessageEdgeCases:
    def test_stage_out_of_range_returns_none(self):
        """Stages outside 0-5 return None."""
        assert get_funnel_message(6, "ru") is None
        assert get_funnel_message(-1, "en") is None
        assert get_funnel_message(100, "ar") is None

    def test_unknown_language_falls_back_to_english(self):
        """Unknown language code uses English strings."""
        msg_unknown = get_funnel_message(1, "fr")
        msg_en = get_funnel_message(1, "en")
        assert msg_unknown.text == msg_en.text

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_buttons_are_tuple_pairs(self, language):
        """All buttons are (label, callback_data) tuples."""
        for stage in range(6):
            msg = get_funnel_message(stage, language)
            for btn in msg.buttons:
                assert isinstance(btn, tuple), f"Button is not a tuple at stage {stage}"
                assert len(btn) == 2, f"Button should have 2 elements at stage {stage}"


# ═══════════════════════════════════════════════════════════════════════════
# Part 2: Sender logic with mocked DB and Bot
# ═══════════════════════════════════════════════════════════════════════════


class TestFunnelSender:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_sends_to_non_buyers(self, mock_targets, mock_update):
        """Sender sends messages to all returned targets."""
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 0, "language": "ru"},
            {"chat_id": 222, "funnel_stage": 2, "language": "en"},
            {"chat_id": 333, "funnel_stage": 4, "language": "ar"},
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
        """Sender picks message in target's language."""
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 1, "language": "ru"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)

        call_kwargs = bot.send_message.call_args
        sent_text = call_kwargs.kwargs.get("text") or call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs["text"]
        expected_msg = get_funnel_message(1, "ru")
        assert sent_text == expected_msg.text

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_skips_invalid_stage(self, mock_targets, mock_update):
        """Sender skips targets with out-of-range stage."""
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
        """If one message fails, sender continues to next user."""
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 0, "language": "ru"},
            {"chat_id": 222, "funnel_stage": 1, "language": "en"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=[Exception("Blocked"), None])

        await send_funnel_messages(bot)

        # First fails, second succeeds
        assert bot.send_message.call_count == 2
        # Only the successful one should update stage
        assert mock_update.call_count == 1
        mock_update.assert_called_with(222)

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_sender_no_targets(self, mock_targets, mock_update):
        """No targets → no messages sent."""
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = []
        bot = AsyncMock()

        await send_funnel_messages(bot)

        bot.send_message.assert_not_called()
        mock_update.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# Part 3: Full 6-day cycle simulation (mocked)
# ═══════════════════════════════════════════════════════════════════════════


class TestFullFunnelCycle:
    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_6_day_cycle_russian(self, mock_targets, mock_update):
        """Simulate 6 days of funnel for a Russian user."""
        from src.funnel.sender import send_funnel_messages

        bot = AsyncMock()
        bot.send_message = AsyncMock()

        for day in range(6):
            mock_targets.return_value = [
                {"chat_id": 555, "funnel_stage": day, "language": "ru"},
            ]
            bot.send_message.reset_mock()
            mock_update.reset_mock()

            await send_funnel_messages(bot)

            expected = get_funnel_message(day, "ru")
            call_kwargs = bot.send_message.call_args.kwargs
            assert call_kwargs["text"] == expected.text, f"Day {day}: wrong text"
            assert call_kwargs["chat_id"] == 555
            mock_update.assert_called_once_with(555)

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_after_stage_5_no_messages(self, mock_targets, mock_update):
        """After completing all 6 stages, user gets no more messages."""
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 555, "funnel_stage": 5, "language": "en"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)
        bot.send_message.assert_called_once()  # Stage 5 still sends

        # Stage 6 — should not send
        mock_targets.return_value = [
            {"chat_id": 555, "funnel_stage": 6, "language": "en"},
        ]
        bot.send_message.reset_mock()

        await send_funnel_messages(bot)
        bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.funnel.sender.update_funnel_stage", new_callable=AsyncMock)
    @patch("src.funnel.sender.get_funnel_targets", new_callable=AsyncMock)
    async def test_multilingual_funnel(self, mock_targets, mock_update):
        """Three users with different languages get correct messages."""
        from src.funnel.sender import send_funnel_messages

        mock_targets.return_value = [
            {"chat_id": 111, "funnel_stage": 0, "language": "ru"},
            {"chat_id": 222, "funnel_stage": 0, "language": "en"},
            {"chat_id": 333, "funnel_stage": 0, "language": "ar"},
        ]
        bot = AsyncMock()
        bot.send_message = AsyncMock()

        await send_funnel_messages(bot)

        calls = bot.send_message.call_args_list
        assert len(calls) == 3

        for call, lang, cid in zip(calls, ["ru", "en", "ar"], [111, 222, 333]):
            expected = get_funnel_message(0, lang)
            assert call.kwargs["text"] == expected.text, f"Wrong text for {lang}"
            assert call.kwargs["chat_id"] == cid
