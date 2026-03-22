"""Tests for funnel message definitions."""

from src.funnel.messages import FunnelMessage, get_funnel_message


class TestGetFunnelMessageEN:
    """EN/AR funnel: 6 stages (0-5)."""

    def test_stage_0_en(self):
        msg = get_funnel_message(0, "en")
        assert msg is not None
        assert isinstance(msg, FunnelMessage)
        assert len(msg.buttons) > 0
        assert msg.buttons[0][1] == "video_workout"

    def test_stage_0_ar(self):
        msg = get_funnel_message(0, "ar")
        assert msg is not None
        assert msg.buttons[0][1] == "video_workout"

    def test_all_en_stages_exist(self):
        for lang in ("en", "ar"):
            for stage in range(6):
                msg = get_funnel_message(stage, lang)
                assert msg is not None, f"Missing message for stage={stage}, lang={lang}"
                assert msg.text, f"Empty text for stage={stage}, lang={lang}"
                assert len(msg.buttons) > 0, f"No buttons for stage={stage}, lang={lang}"

    def test_en_stage_out_of_range_returns_none(self):
        assert get_funnel_message(6, "en") is None
        assert get_funnel_message(-1, "en") is None
        assert get_funnel_message(100, "ar") is None

    def test_en_stage_1_is_buy(self):
        msg = get_funnel_message(1, "en")
        assert msg is not None
        _, callback = msg.buttons[0]
        assert callback == "buy_now"

    def test_buttons_are_tuples(self):
        for stage in range(6):
            msg = get_funnel_message(stage, "en")
            for btn in msg.buttons:
                assert isinstance(btn, tuple), f"Button is not tuple at stage {stage}"
                assert len(btn) == 2, f"Button tuple wrong length at stage {stage}"

    def test_unknown_language_uses_en(self):
        msg = get_funnel_message(0, "fr")
        assert msg is not None


class TestGetFunnelMessageRU:
    """RU funnel: 8 stages (0-7) with photos and video notes."""

    def test_all_ru_stages_exist(self):
        for stage in range(8):
            msg = get_funnel_message(stage, "ru")
            assert msg is not None, f"Missing RU message for stage={stage}"
            assert msg.text, f"Empty text for RU stage={stage}"

    def test_ru_stage_out_of_range(self):
        assert get_funnel_message(8, "ru") is None
        assert get_funnel_message(-1, "ru") is None

    def test_stage_0_video_workout(self):
        msg = get_funnel_message(0, "ru")
        assert msg.buttons[0][1] == "video_workout"

    def test_stage_1_learn_workout_with_photo(self):
        msg = get_funnel_message(1, "ru")
        assert msg.buttons[0][1] == "learn_workout"
        assert msg.photo_name, "Stage 1 should have a photo"

    def test_stage_2_has_photo_no_buttons(self):
        msg = get_funnel_message(2, "ru")
        assert msg.photo_name, "Stage 2 should have a photo"
        assert len(msg.buttons) == 0, "Stage 2 should have no buttons"

    def test_stage_3_video_circle(self):
        msg = get_funnel_message(3, "ru")
        assert msg.buttons[0][1] == "video_circle"
        assert msg.video_note_id, "Stage 3 should have a video note"

    def test_stage_4_text_only(self):
        msg = get_funnel_message(4, "ru")
        assert len(msg.buttons) == 0, "Stage 4 should have no buttons"
        assert not msg.photo_name
        assert not msg.video_note_id

    def test_stage_5_buy_with_video_note(self):
        msg = get_funnel_message(5, "ru")
        assert msg.buttons[0][1] == "buy_now"
        assert msg.video_note_id, "Stage 5 should have a video note"

    def test_stage_6_buy(self):
        msg = get_funnel_message(6, "ru")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_7_channel_url_button(self):
        msg = get_funnel_message(7, "ru")
        assert msg.has_url_button
        assert "ivanfit_health" in msg.url

    def test_ru_price_690(self):
        """New RU funnel uses 690₽ price."""
        msg = get_funnel_message(5, "ru")
        assert "690" in msg.text, "Stage 5 should mention 690₽ price"

    def test_no_emojis_in_ru_texts(self):
        """New RU funnel texts should not contain emojis."""
        emoji_chars = set("🤍✨🙈📅👉💳✅▶️🔥💪🏻😊🌸😌😄💬🎥🌬📋🎓")
        for stage in range(8):
            msg = get_funnel_message(stage, "ru")
            text_chars = set(msg.text)
            found = text_chars & emoji_chars
            assert not found, f"Stage {stage} has emojis: {found}"
