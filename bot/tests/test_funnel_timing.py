"""Tests for funnel timing — calculate_next_send_time."""

from datetime import datetime, time, timedelta, timezone

from src.db.queries import calculate_next_send_time


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
    """RU no longer has a scheduled funnel — always returns None."""

    def test_all_ru_stages_return_none(self):
        for stage in range(0, 16):
            assert calculate_next_send_time(stage, "ru") is None, f"Stage {stage} should be None for RU"

    def test_ru_ignores_variant_and_has_variant(self):
        assert calculate_next_send_time(0, "ru", has_variant=True) is None
        assert calculate_next_send_time(1, "ru", variant="belly") is None
        assert calculate_next_send_time(5, "ru", variant="glutes") is None
