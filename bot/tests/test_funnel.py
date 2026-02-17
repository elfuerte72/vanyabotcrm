"""Tests for funnel message definitions."""

from src.funnel.messages import FunnelMessage, get_funnel_message


class TestGetFunnelMessage:
    def test_stage_0_ru(self):
        msg = get_funnel_message(0, "ru")
        assert msg is not None
        assert isinstance(msg, FunnelMessage)
        assert len(msg.buttons) > 0
        assert msg.has_url_button is True
        assert msg.url != ""

    def test_stage_0_en(self):
        msg = get_funnel_message(0, "en")
        assert msg is not None
        assert msg.has_url_button is True

    def test_stage_0_ar(self):
        msg = get_funnel_message(0, "ar")
        assert msg is not None
        assert msg.has_url_button is True

    def test_all_stages_exist(self):
        for lang in ("ru", "en", "ar"):
            for stage in range(6):
                msg = get_funnel_message(stage, lang)
                assert msg is not None, f"Missing message for stage={stage}, lang={lang}"
                assert msg.text, f"Empty text for stage={stage}, lang={lang}"
                assert len(msg.buttons) > 0, f"No buttons for stage={stage}, lang={lang}"

    def test_stage_out_of_range_returns_none(self):
        assert get_funnel_message(6, "ru") is None
        assert get_funnel_message(-1, "en") is None
        assert get_funnel_message(100, "ar") is None

    def test_stage_1_is_buy(self):
        msg = get_funnel_message(1, "ru")
        assert msg is not None
        # Stage 1 should have buy_now callback
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
        assert msg is not None  # Should fallback to 'en'
