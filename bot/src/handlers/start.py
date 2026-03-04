"""Handler for /start command."""

import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.i18n import get_strings

logger = structlog.get_logger()

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    tg_lang = message.from_user.language_code or ""
    if tg_lang.startswith("ar"):
        lang = "ar"
    elif tg_lang.startswith("ru"):
        lang = "ru"
    else:
        lang = "en"

    logger.info("start_command", chat_id=message.chat.id, tg_lang=tg_lang, detected_lang=lang)

    strings = get_strings(lang)
    await message.answer(strings.START_MESSAGE, parse_mode="HTML")
