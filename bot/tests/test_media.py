"""Tests for media.py file_id cache — cache miss/hit, local photo cache, cache reset."""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services import media
from src.services.media import (
    send_info_video,
    send_suitability_video,
    send_random_result_photo,
    send_video_note_from_drive,
    send_local_photo,
    _tg_file_id_cache,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear file_id cache before each test."""
    _tg_file_id_cache.clear()
    yield
    _tg_file_id_cache.clear()


def _make_bot_with_video(file_id: str = "tg_video_123") -> AsyncMock:
    bot = AsyncMock()
    msg = MagicMock()
    msg.video = MagicMock()
    msg.video.file_id = file_id
    msg.photo = None
    msg.video_note = None
    bot.send_video.return_value = msg
    return bot


def _make_bot_with_photo(file_id: str = "tg_photo_123") -> AsyncMock:
    bot = AsyncMock()
    msg = MagicMock()
    msg.video = None
    photo = MagicMock()
    photo.file_id = file_id
    msg.photo = [photo]
    msg.video_note = None
    bot.send_photo.return_value = msg
    return bot


def _make_bot_with_video_note(file_id: str = "tg_vnote_123") -> AsyncMock:
    bot = AsyncMock()
    msg = MagicMock()
    msg.video = None
    msg.photo = None
    msg.video_note = MagicMock()
    msg.video_note.file_id = file_id
    bot.send_video_note.return_value = msg
    return bot


# ─── send_info_video ─────────────────────────────────────────────────────


class TestInfoVideoCache:
    @pytest.mark.asyncio
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    @patch("src.services.media.media_config", {"videos": {"info": "gdrive_info_id"}})
    async def test_cache_miss_downloads(self, mock_download):
        mock_download.return_value = b"fake_video_data"
        bot = _make_bot_with_video("tg_info_file_id")

        await send_info_video(bot, 12345)

        mock_download.assert_called_once_with("gdrive_info_id")
        bot.send_video.assert_called_once()
        assert _tg_file_id_cache["video:gdrive_info_id"] == "tg_info_file_id"

    @pytest.mark.asyncio
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    @patch("src.services.media.media_config", {"videos": {"info": "gdrive_info_id"}})
    async def test_cache_hit_no_download(self, mock_download):
        _tg_file_id_cache["video:gdrive_info_id"] = "cached_file_id"
        bot = AsyncMock()

        await send_info_video(bot, 12345)

        mock_download.assert_not_called()
        bot.send_video.assert_called_once_with(chat_id=12345, video="cached_file_id")


# ─── send_suitability_video ──────────────────────────────────────────────


class TestSuitabilityVideoCache:
    @pytest.mark.asyncio
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    @patch("src.services.media.media_config", {"videos": {"suitability": "gdrive_suit_id"}})
    async def test_cache_miss_downloads(self, mock_download):
        mock_download.return_value = b"fake_video"
        bot = _make_bot_with_video("tg_suit_file_id")

        await send_suitability_video(bot, 12345)

        mock_download.assert_called_once_with("gdrive_suit_id")
        assert _tg_file_id_cache["video:gdrive_suit_id"] == "tg_suit_file_id"

    @pytest.mark.asyncio
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    @patch("src.services.media.media_config", {"videos": {"suitability": "gdrive_suit_id"}})
    async def test_cache_hit_no_download(self, mock_download):
        _tg_file_id_cache["video:gdrive_suit_id"] = "cached_suit"
        bot = AsyncMock()

        await send_suitability_video(bot, 12345)

        mock_download.assert_not_called()
        bot.send_video.assert_called_once_with(chat_id=12345, video="cached_suit")


# ─── send_random_result_photo ────────────────────────────────────────────


class TestResultPhotoCache:
    @pytest.mark.asyncio
    @patch("src.services.media.random.choice", return_value="gdrive_photo_id")
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    @patch("src.services.media.media_config", {"photos": {"results": ["gdrive_photo_id"]}})
    async def test_cache_miss_downloads(self, mock_download, mock_choice):
        mock_download.return_value = b"fake_photo"
        bot = _make_bot_with_photo("tg_photo_file_id")

        await send_random_result_photo(bot, 12345, caption="Results")

        mock_download.assert_called_once_with("gdrive_photo_id")
        assert _tg_file_id_cache["photo:gdrive_photo_id"] == "tg_photo_file_id"

    @pytest.mark.asyncio
    @patch("src.services.media.random.choice", return_value="gdrive_photo_id")
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    @patch("src.services.media.media_config", {"photos": {"results": ["gdrive_photo_id"]}})
    async def test_cache_hit_no_download(self, mock_download, mock_choice):
        _tg_file_id_cache["photo:gdrive_photo_id"] = "cached_photo"
        bot = AsyncMock()

        await send_random_result_photo(bot, 12345, caption="Cap")

        mock_download.assert_not_called()
        bot.send_photo.assert_called_once_with(
            chat_id=12345, photo="cached_photo", caption="Cap", parse_mode="HTML",
        )


# ─── send_video_note_from_drive ──────────────────────────────────────────


class TestVideoNoteCache:
    @pytest.mark.asyncio
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    async def test_cache_miss_downloads(self, mock_download):
        mock_download.return_value = b"fake_note"
        bot = _make_bot_with_video_note("tg_vnote_file_id")

        await send_video_note_from_drive(bot, 12345, "gdrive_note_id")

        mock_download.assert_called_once_with("gdrive_note_id")
        assert _tg_file_id_cache["video_note:gdrive_note_id"] == "tg_vnote_file_id"

    @pytest.mark.asyncio
    @patch("src.services.media._download_file", new_callable=AsyncMock)
    async def test_cache_hit_no_download(self, mock_download):
        _tg_file_id_cache["video_note:gdrive_note_id"] = "cached_vnote"
        bot = AsyncMock()

        await send_video_note_from_drive(bot, 12345, "gdrive_note_id")

        mock_download.assert_not_called()
        bot.send_video_note.assert_called_once_with(chat_id=12345, video_note="cached_vnote")


# ─── send_local_photo ────────────────────────────────────────────────────


class TestLocalPhotoCache:
    @pytest.mark.asyncio
    @patch("src.services.media._MEDIA_DIR")
    async def test_cache_miss_sends_file(self, mock_media_dir):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_media_dir.__truediv__ = MagicMock(return_value=MagicMock(__truediv__=MagicMock(return_value=mock_path)))

        bot = _make_bot_with_photo("tg_local_photo_id")

        with patch("src.services.media.FSInputFile"):
            await send_local_photo(bot, 12345, "test.jpg", caption="Hi")

        assert _tg_file_id_cache["local_photo:test.jpg"] == "tg_local_photo_id"

    @pytest.mark.asyncio
    async def test_cache_hit_no_file_read(self):
        _tg_file_id_cache["local_photo:test.jpg"] = "cached_local"
        bot = AsyncMock()

        await send_local_photo(bot, 12345, "test.jpg", caption="Hi")

        bot.send_photo.assert_called_once_with(
            chat_id=12345, photo="cached_local", caption="Hi",
            parse_mode="HTML", reply_markup=None,
        )


# ─── Cache isolation between tests ──────────────────────────────────────


class TestCacheIsolation:
    @pytest.mark.asyncio
    async def test_cache_empty_at_start(self):
        """Autouse fixture clears cache before each test."""
        assert len(_tg_file_id_cache) == 0
