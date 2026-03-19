"""Tests for ai_agent module — history trimming and message building."""

from __future__ import annotations

from src.services.ai_agent import trim_history, MAX_HISTORY_CHARS, MIN_HISTORY_MESSAGES


class TestTrimHistory:
    """Test history trimming logic."""

    def test_empty_history(self) -> None:
        assert trim_history([]) == []

    def test_short_history_unchanged(self) -> None:
        history = [
            {"type": "human", "content": "hello"},
            {"type": "ai", "content": "hi there"},
        ]
        result = trim_history(history)
        assert result == history

    def test_long_history_trimmed(self) -> None:
        # Create history that exceeds MAX_HISTORY_CHARS
        history = [
            {"type": "human", "content": "x" * 3000},
            {"type": "ai", "content": "y" * 3000},
            {"type": "human", "content": "z" * 3000},
            {"type": "ai", "content": "w" * 3000},
        ]
        result = trim_history(history)
        total_chars = sum(len(m.get("content", "")) for m in result)
        assert total_chars <= MAX_HISTORY_CHARS
        assert len(result) < len(history)

    def test_keeps_minimum_messages(self) -> None:
        # Even if messages are huge, keep at least MIN_HISTORY_MESSAGES
        history = [
            {"type": "human", "content": "x" * 50000},
            {"type": "ai", "content": "y" * 50000},
        ]
        result = trim_history(history)
        assert len(result) == MIN_HISTORY_MESSAGES

    def test_removes_oldest_first(self) -> None:
        history = [
            {"type": "human", "content": "first " + "x" * 4000},
            {"type": "ai", "content": "second " + "y" * 4000},
            {"type": "human", "content": "third"},
            {"type": "ai", "content": "fourth"},
        ]
        result = trim_history(history)
        # Oldest messages should be removed first
        assert result[-1]["content"] == "fourth"
        assert result[-2]["content"] == "third"

    def test_custom_max_chars(self) -> None:
        history = [
            {"type": "human", "content": "a" * 100},
            {"type": "ai", "content": "b" * 100},
            {"type": "human", "content": "c" * 50},
            {"type": "ai", "content": "d" * 50},
        ]
        # 300 total, limit 150 — should trim to last 2 (100 chars)
        result = trim_history(history, max_chars=150)
        assert len(result) == 2
        total = sum(len(m["content"]) for m in result)
        assert total <= 150

    def test_exact_limit_not_trimmed(self) -> None:
        history = [
            {"type": "human", "content": "a" * 4000},
            {"type": "ai", "content": "b" * 4000},
        ]
        result = trim_history(history, max_chars=8000)
        assert len(result) == 2

    def test_single_message(self) -> None:
        history = [{"type": "human", "content": "hello"}]
        result = trim_history(history)
        assert result == history

    def test_missing_content_key(self) -> None:
        history = [
            {"type": "human"},
            {"type": "ai", "content": "response"},
        ]
        result = trim_history(history)
        assert len(result) == 2
