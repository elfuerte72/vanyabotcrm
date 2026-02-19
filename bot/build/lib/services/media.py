"""Google Drive media download and Telegram sending."""

from __future__ import annotations

import random
from io import BytesIO

import httpx
import structlog
from aiogram import Bot
from aiogram.types import BufferedInputFile

from config.settings import media_config

logger = structlog.get_logger()


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
    file_id = media_config["videos"]["info"]
    logger.debug("downloading_info_video", file_id=file_id)
    data = await _download_file(file_id)
    await bot.send_video(
        chat_id=chat_id,
        video=BufferedInputFile(data, filename="info.mp4"),
    )


async def send_suitability_video(bot: Bot, chat_id: int) -> None:
    """Send 'will this workout suit me' video."""
    file_id = media_config["videos"]["suitability"]
    logger.debug("downloading_suitability_video", file_id=file_id)
    data = await _download_file(file_id)
    await bot.send_video(
        chat_id=chat_id,
        video=BufferedInputFile(data, filename="suitability.mp4"),
    )


async def send_random_result_photo(bot: Bot, chat_id: int, caption: str = "") -> None:
    """Send a random result photo."""
    photo_ids = media_config["photos"]["results"]
    file_id = random.choice(photo_ids)
    logger.debug("downloading_result_photo", file_id=file_id)
    data = await _download_file(file_id)
    await bot.send_photo(
        chat_id=chat_id,
        photo=BufferedInputFile(data, filename="result.jpg"),
        caption=caption,
        parse_mode="HTML",
    )
