"""Tests for AR funnel — _MAX_STAGE and callback data format."""

from src.db.queries import _MAX_STAGE
from src.funnel.messages import get_funnel_message


class TestARFunnelConfig:
    """AR funnel configuration."""

    def test_max_stage_ar_is_10(self):
        assert _MAX_STAGE["ar"] == 10

    def test_max_stage_ar_equals_en(self):
        assert _MAX_STAGE["ar"] == _MAX_STAGE["en"]


class TestARCallbackDataFormat:
    """AR funnel callback data format: ar_funnel_q_{0-8}."""

    def test_stages_0_to_8_callback_prefix(self):
        for stage in range(9):
            msg = get_funnel_message(stage, "ar")
            question_btn = msg.buttons[1]
            assert question_btn[1].startswith("ar_funnel_q_"), (
                f"Stage {stage} question callback should start with ar_funnel_q_"
            )

    def test_callback_data_contains_stage_number(self):
        for stage in range(9):
            msg = get_funnel_message(stage, "ar")
            callback_data = msg.buttons[1][1]
            parsed_stage = int(callback_data.split("_")[-1])
            assert parsed_stage == stage, (
                f"Callback data {callback_data} should contain stage {stage}"
            )

    def test_upsell_stages_no_question_callback(self):
        for stage in (9, 10):
            msg = get_funnel_message(stage, "ar")
            for btn in msg.buttons:
                assert not btn[1].startswith("ar_funnel_q_"), (
                    f"Upsell stage {stage} should not have ar_funnel_q_ callback"
                )
