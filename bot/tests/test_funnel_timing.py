"""Tests for funnel timing — calculate_next_send_time."""

from datetime import datetime, time, timedelta, timezone

from src.db.queries import calculate_next_send_time, _MSK


class TestCalculateNextSendTimeEN:
    """EN: 5min first, 24h for stages 1-8, 24h for upsell."""

    def test_after_stage_0_is_5min(self):
        result = calculate_next_send_time(0, "en")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(minutes=4, seconds=58) < diff < timedelta(minutes=5, seconds=2)

    def test_after_stage_1_is_24h(self):
        result = calculate_next_send_time(1, "en")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)

    def test_after_stages_2_to_8_are_24h(self):
        for stage in range(2, 9):
            result = calculate_next_send_time(stage, "en")
            assert result is not None, f"Stage {stage} should have next send time"
            diff = result - datetime.now(timezone.utc)
            assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1), f"Stage {stage} should be ~24h"

    def test_after_stage_9_is_24h(self):
        result = calculate_next_send_time(9, "en")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)

    def test_after_last_stage_is_none(self):
        assert calculate_next_send_time(10, "en") is None

    def test_beyond_last_stage_is_none(self):
        assert calculate_next_send_time(11, "en") is None
        assert calculate_next_send_time(15, "en") is None

    def test_all_en_results_are_utc(self):
        for stage in range(10):
            result = calculate_next_send_time(stage, "en")
            assert result is not None
            assert result.tzinfo == timezone.utc

    def test_all_en_results_are_in_future(self):
        now = datetime.now(timezone.utc)
        for stage in range(10):
            result = calculate_next_send_time(stage, "en")
            assert result > now, f"Stage {stage} result is not in the future"


class TestCalculateNextSendTimeAR:
    """AR: same timing as EN (5min/24h/24h), 11 stages (0-10)."""

    def test_after_stage_0_is_5min(self):
        result = calculate_next_send_time(0, "ar")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(minutes=4, seconds=58) < diff < timedelta(minutes=5, seconds=2)

    def test_after_stage_1_is_24h(self):
        result = calculate_next_send_time(1, "ar")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)

    def test_after_stages_2_to_8_are_24h(self):
        for stage in range(2, 9):
            result = calculate_next_send_time(stage, "ar")
            assert result is not None, f"Stage {stage} should have next send time"
            diff = result - datetime.now(timezone.utc)
            assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1), f"Stage {stage} should be ~24h"

    def test_after_stage_9_is_24h(self):
        result = calculate_next_send_time(9, "ar")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)

    def test_after_last_stage_is_none(self):
        assert calculate_next_send_time(10, "ar") is None

    def test_beyond_last_stage_is_none(self):
        assert calculate_next_send_time(11, "ar") is None
        assert calculate_next_send_time(15, "ar") is None

    def test_all_ar_results_are_utc(self):
        for stage in range(10):
            result = calculate_next_send_time(stage, "ar")
            assert result is not None
            assert result.tzinfo == timezone.utc

    def test_all_ar_results_are_in_future(self):
        now = datetime.now(timezone.utc)
        for stage in range(10):
            result = calculate_next_send_time(stage, "ar")
            assert result > now, f"Stage {stage} result is not in the future"


class TestCalculateNextSendTimeRU:
    """RU: 13 stages (0-12) with zone branching timing."""

    def test_stage_0_no_variant_is_24h(self):
        result = calculate_next_send_time(0, "ru", has_variant=False)
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)

    def test_stage_0_with_variant_is_1h(self):
        result = calculate_next_send_time(0, "ru", has_variant=True)
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(minutes=59) < diff < timedelta(hours=1, minutes=1)

    def test_after_stage_1_is_next_day_10am_msk(self):
        result = calculate_next_send_time(1, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_stage_2_is_19pm_msk(self):
        result = calculate_next_send_time(2, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 19
        assert result_msk.minute == 0

    def test_after_stage_3_is_next_day_10am_msk(self):
        result = calculate_next_send_time(3, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_stage_4_is_next_day_10am_msk(self):
        result = calculate_next_send_time(4, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_stage_5_is_19pm_msk(self):
        """Default (non-glutes): stage 5 → same day 19:00 MSK."""
        result = calculate_next_send_time(5, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 19
        assert result_msk.minute == 0

    def test_after_stage_5_glutes_is_next_day_10am_msk(self):
        """Glutes variant: stage 5 → next day 10:00 MSK (no same-day 19:00)."""
        result = calculate_next_send_time(5, "ru", variant="glutes")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_stages_6_to_13_is_next_day_10am_msk(self):
        # Stages 6-13 schedule next at 10:00 MSK the following day
        # (belly extends to stage 14; thighs/arms/glutes cap at 11 and return None earlier)
        for stage in range(6, 14):
            result = calculate_next_send_time(stage, "ru", variant="belly")
            assert result is not None, f"Stage {stage} should have next send time"
            result_msk = result.astimezone(_MSK)
            assert result_msk.hour == 10, f"Stage {stage} should be at 10:00 MSK, got {result_msk.hour}"
            assert result_msk.minute == 0

    def test_after_last_stage_belly_is_none(self):
        assert calculate_next_send_time(14, "ru", variant="belly") is None

    def test_after_last_stage_thighs_is_none(self):
        assert calculate_next_send_time(11, "ru", variant="thighs") is None

    def test_after_last_stage_arms_is_none(self):
        assert calculate_next_send_time(11, "ru", variant="arms") is None

    def test_after_last_stage_glutes_is_none(self):
        assert calculate_next_send_time(12, "ru", variant="glutes") is None

    def test_beyond_last_stage_is_none(self):
        assert calculate_next_send_time(15, "ru") is None
        assert calculate_next_send_time(20, "ru") is None
        assert calculate_next_send_time(12, "ru", variant="thighs") is None
        assert calculate_next_send_time(12, "ru", variant="arms") is None
        assert calculate_next_send_time(13, "ru", variant="glutes") is None

    def test_all_results_are_utc(self):
        for stage in range(12):
            result = calculate_next_send_time(stage, "ru")
            assert result is not None
            assert result.tzinfo == timezone.utc

    def test_all_results_are_in_future(self):
        now = datetime.now(timezone.utc)
        for stage in range(12):
            result = calculate_next_send_time(stage, "ru")
            assert result is not None
            assert result > now, f"Stage {stage} result is not in the future"
