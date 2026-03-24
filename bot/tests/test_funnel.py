"""Tests for funnel message definitions."""

from src.funnel.messages import FunnelMessage, get_funnel_message


class TestGetFunnelMessageEN:
    """EN funnel: 9 stages (0-8) + 2 upsells (9-10)."""

    def test_all_en_stages_exist(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "en")
            assert msg is not None, f"Missing message for stage={stage}"
            assert msg.text, f"Empty text for stage={stage}"
            assert len(msg.buttons) > 0, f"No buttons for stage={stage}"

    def test_en_stage_out_of_range_returns_none(self):
        assert get_funnel_message(11, "en") is None
        assert get_funnel_message(-1, "en") is None

    def test_stages_0_to_8_have_buy_and_question(self):
        for stage in range(9):
            msg = get_funnel_message(stage, "en")
            assert len(msg.buttons) == 2, f"Stage {stage} should have 2 buttons"
            assert msg.buttons[0][1] == "buy_now", f"Stage {stage} first button should be buy_now"
            assert msg.buttons[1][1] == f"en_funnel_q_{stage}", f"Stage {stage} second button should be question"

    def test_stage_0_has_photo(self):
        msg = get_funnel_message(0, "en")
        assert msg.photo_name, "Stage 0 should have a photo"
        assert "en_funnel_stage_0" in msg.photo_name

    def test_stage_6_has_photo(self):
        msg = get_funnel_message(6, "en")
        assert msg.photo_name, "Stage 6 should have a photo"
        assert "en_funnel_stage_6" in msg.photo_name

    def test_stages_without_photos(self):
        for stage in [1, 2, 3, 4, 5, 7, 8]:
            msg = get_funnel_message(stage, "en")
            assert not msg.photo_name, f"Stage {stage} should not have a photo"

    def test_upsell_stages_have_buy_and_decline(self):
        for stage in (9, 10):
            msg = get_funnel_message(stage, "en")
            assert len(msg.buttons) == 2
            assert msg.buttons[0][1] == "buy_now"
            assert msg.buttons[1][1] == "upsell_decline"

    def test_stage_0_mentions_49_aed(self):
        msg = get_funnel_message(0, "en")
        assert "49 AED" in msg.text

    def test_upsell_1_mentions_79_aed(self):
        msg = get_funnel_message(9, "en")
        assert "79 AED" in msg.buttons[0][0]

    def test_upsell_2_mentions_129_aed(self):
        msg = get_funnel_message(10, "en")
        assert "129 AED" in msg.buttons[0][0]

    def test_buttons_are_tuples(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "en")
            for btn in msg.buttons:
                assert isinstance(btn, tuple), f"Button is not tuple at stage {stage}"
                assert len(btn) == 2, f"Button tuple wrong length at stage {stage}"


class TestGetFunnelMessageAR:
    """AR funnel: 9 stages (0-8) + 2 upsells (9-10)."""

    def test_all_ar_stages_exist(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "ar")
            assert msg is not None, f"Missing AR message for stage={stage}"
            assert msg.text, f"Empty text for AR stage={stage}"
            assert len(msg.buttons) > 0, f"No buttons for AR stage={stage}"

    def test_ar_stage_out_of_range(self):
        assert get_funnel_message(11, "ar") is None
        assert get_funnel_message(-1, "ar") is None

    def test_stages_0_to_8_have_buy_and_question(self):
        for stage in range(9):
            msg = get_funnel_message(stage, "ar")
            assert len(msg.buttons) == 2, f"AR stage {stage} should have 2 buttons"
            assert msg.buttons[0][1] == "buy_now", f"AR stage {stage} first button should be buy_now"
            assert msg.buttons[1][1] == f"ar_funnel_q_{stage}", f"AR stage {stage} second button should be question"

    def test_stage_0_has_photo(self):
        msg = get_funnel_message(0, "ar")
        assert msg.photo_name, "AR stage 0 should have a photo"

    def test_stage_6_has_photo(self):
        msg = get_funnel_message(6, "ar")
        assert msg.photo_name, "AR stage 6 should have a photo"

    def test_stages_without_photos(self):
        for stage in [1, 2, 3, 4, 5, 7, 8]:
            msg = get_funnel_message(stage, "ar")
            assert not msg.photo_name, f"AR stage {stage} should not have a photo"

    def test_upsell_stages_have_buy_and_decline(self):
        for stage in (9, 10):
            msg = get_funnel_message(stage, "ar")
            assert len(msg.buttons) == 2
            assert msg.buttons[0][1] == "buy_now"
            assert msg.buttons[1][1] == "upsell_decline"

    def test_stage_0_mentions_49_aed(self):
        msg = get_funnel_message(0, "ar")
        assert "49" in msg.text

    def test_upsell_1_mentions_79_aed(self):
        msg = get_funnel_message(9, "ar")
        assert "79" in msg.buttons[0][0]

    def test_upsell_2_mentions_129_aed(self):
        msg = get_funnel_message(10, "ar")
        assert "129" in msg.buttons[0][0]

    def test_buttons_are_tuples(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "ar")
            for btn in msg.buttons:
                assert isinstance(btn, tuple), f"Button is not tuple at AR stage {stage}"
                assert len(btn) == 2, f"Button tuple wrong length at AR stage {stage}"

    def test_unknown_language_uses_ar_default(self):
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
