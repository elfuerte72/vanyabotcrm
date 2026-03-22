"""Google Drive media download and Telegram sending with file_id caching."""

from __future__ import annotations

import random
from pathlib import Path

import httpx
import structlog
from aiogram import Bot
from aiogram.types import BufferedInputFile, FSInputFile

from config.settings import media_config

logger = structlog.get_logger()

_MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "media"

# In-memory cache: cache_key → Telegram file_id
# Avoids re-downloading from Google Drive / re-uploading local files after first send.
_tg_file_id_cache: dict[str, str] = {}


def _gdrive_download_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


async def _download_file(file_id: str) -> bytes:
    url = _gdrive_download_url(file_id)
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def send_info_video(bot: Bot, chat_id: int) -> None:
    """Send 'what's in the program' info video."""
    gdrive_id = media_config["videos"]["info"]
    cache_key = f"video:{gdrive_id}"

    cached = _tg_file_id_cache.get(cache_key)
    if cached:
        logger.debug("media_cache_hit", key=cache_key)
        await bot.send_video(chat_id=chat_id, video=cached)
        return

    logger.debug("media_cache_miss", key=cache_key)
    data = await _download_file(gdrive_id)
    msg = await bot.send_video(
        chat_id=chat_id,
        video=BufferedInputFile(data, filename="info.mp4"),
    )
    if msg.video:
        _tg_file_id_cache[cache_key] = msg.video.file_id
        logger.debug("media_cache_stored", key=cache_key, file_id=msg.video.file_id)


async def send_suitability_video(bot: Bot, chat_id: int) -> None:
    """Send 'will this workout suit me' video."""
    gdrive_id = media_config["videos"]["suitability"]
    cache_key = f"video:{gdrive_id}"

    cached = _tg_file_id_cache.get(cache_key)
    if cached:
        logger.debug("media_cache_hit", key=cache_key)
        await bot.send_video(chat_id=chat_id, video=cached)
        return

    logger.debug("media_cache_miss", key=cache_key)
    data = await _download_file(gdrive_id)
    msg = await bot.send_video(
        chat_id=chat_id,
        video=BufferedInputFile(data, filename="suitability.mp4"),
    )
    if msg.video:
        _tg_file_id_cache[cache_key] = msg.video.file_id
        logger.debug("media_cache_stored", key=cache_key, file_id=msg.video.file_id)


async def send_random_result_photo(bot: Bot, chat_id: int, caption: str = "") -> None:
    """Send a random result photo."""
    photo_ids = media_config["photos"]["results"]
    gdrive_id = random.choice(photo_ids)
    cache_key = f"photo:{gdrive_id}"

    cached = _tg_file_id_cache.get(cache_key)
    if cached:
        logger.debug("media_cache_hit", key=cache_key)
        await bot.send_photo(
            chat_id=chat_id, photo=cached, caption=caption, parse_mode="HTML",
        )
        return

    logger.debug("media_cache_miss", key=cache_key)
    data = await _download_file(gdrive_id)
    msg = await bot.send_photo(
        chat_id=chat_id,
        photo=BufferedInputFile(data, filename="result.jpg"),
        caption=caption,
        parse_mode="HTML",
    )
    if msg.photo:
        _tg_file_id_cache[cache_key] = msg.photo[-1].file_id
        logger.debug("media_cache_stored", key=cache_key, file_id=msg.photo[-1].file_id)


async def send_local_photo(
    bot: Bot, chat_id: int, photo_name: str, caption: str = "",
    reply_markup=None,
) -> None:
    """Send a photo from bot/media/photos/ directory."""
    cache_key = f"local_photo:{photo_name}"

    cached = _tg_file_id_cache.get(cache_key)
    if cached:
        logger.debug("media_cache_hit", key=cache_key)
        await bot.send_photo(
            chat_id=chat_id, photo=cached, caption=caption,
            parse_mode="HTML", reply_markup=reply_markup,
        )
        return

    photo_path = _MEDIA_DIR / "photos" / photo_name
    if not photo_path.exists():
        logger.error("local_photo_not_found", path=str(photo_path))
        return
    logger.debug("media_cache_miss", key=cache_key)
    msg = await bot.send_photo(
        chat_id=chat_id,
        photo=FSInputFile(photo_path),
        caption=caption,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    if msg.photo:
        _tg_file_id_cache[cache_key] = msg.photo[-1].file_id
        logger.debug("media_cache_stored", key=cache_key, file_id=msg.photo[-1].file_id)


async def send_video_note_from_drive(bot: Bot, chat_id: int, file_id: str) -> None:
    """Download video from Google Drive and send as video note (circle)."""
    cache_key = f"video_note:{file_id}"

    cached = _tg_file_id_cache.get(cache_key)
    if cached:
        logger.debug("media_cache_hit", key=cache_key)
        await bot.send_video_note(chat_id=chat_id, video_note=cached)
        return

    logger.debug("media_cache_miss", key=cache_key)
    data = await _download_file(file_id)
    msg = await bot.send_video_note(
        chat_id=chat_id,
        video_note=BufferedInputFile(data, filename="circle.mp4"),
    )
    if msg.video_note:
        _tg_file_id_cache[cache_key] = msg.video_note.file_id
        logger.debug("media_cache_stored", key=cache_key, file_id=msg.video_note.file_id)
