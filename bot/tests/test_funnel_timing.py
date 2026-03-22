"""Tests for funnel timing — calculate_next_send_time."""

from datetime import datetime, time, timedelta, timezone

from src.db.queries import calculate_next_send_time, _MSK


class TestCalculateNextSendTimeEN:
    """EN/AR: simple interval delays."""

    def test_after_stage_0_is_2h(self):
        result = calculate_next_send_time(0, "en")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=1, minutes=59) < diff < timedelta(hours=2, minutes=1)

    def test_after_stage_1_is_23h(self):
        result = calculate_next_send_time(1, "en")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=22, minutes=59) < diff < timedelta(hours=23, minutes=1)

    def test_after_last_stage_is_none(self):
        assert calculate_next_send_time(5, "en") is None
        assert calculate_next_send_time(5, "ar") is None

    def test_beyond_last_stage_is_none(self):
        assert calculate_next_send_time(6, "en") is None
        assert calculate_next_send_time(10, "ar") is None


class TestCalculateNextSendTimeRU:
    """RU: specific MSK times."""

    def test_after_stage_0_is_2h30m(self):
        result = calculate_next_send_time(0, "ru")
        assert result is not None
        diff = result - datetime.now(timezone.utc)
        assert timedelta(hours=2, minutes=29) < diff < timedelta(hours=2, minutes=31)

    def test_after_stage_1_is_next_day_10am_msk(self):
        result = calculate_next_send_time(1, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_stage_2_is_next_day_10am_msk(self):
        result = calculate_next_send_time(2, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_stage_3_is_19pm_msk(self):
        result = calculate_next_send_time(3, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 19
        assert result_msk.minute == 0

    def test_after_stage_4_is_next_day_19pm_msk(self):
        result = calculate_next_send_time(4, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 19
        assert result_msk.minute == 0

    def test_after_stage_5_is_next_day_11am_msk(self):
        result = calculate_next_send_time(5, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 11
        assert result_msk.minute == 0

    def test_after_stage_6_is_next_day_10am_msk(self):
        result = calculate_next_send_time(6, "ru")
        assert result is not None
        result_msk = result.astimezone(_MSK)
        assert result_msk.hour == 10
        assert result_msk.minute == 0

    def test_after_last_stage_is_none(self):
        assert calculate_next_send_time(7, "ru") is None

    def test_all_results_are_utc(self):
        for stage in range(7):
            result = calculate_next_send_time(stage, "ru")
            assert result is not None
            assert result.tzinfo == timezone.utc

    def test_all_results_are_in_future(self):
        now = datetime.now(timezone.utc)
        for stage in range(7):
            result = calculate_next_send_time(stage, "ru")
            assert result is not None
            assert result > now, f"Stage {stage} result is not in the future"
