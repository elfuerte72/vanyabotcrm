"""Handler for /start and /language commands — language selection for new users."""

import structlog
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.db.queries import save_user_language, update_user_language
from src.i18n import get_strings
from src.models.user import User

logger = structlog.get_logger()

router = Router()

# Multilingual message — shown before user has a language preference
LANGUAGE_CHOOSE_MESSAGE = (
    "🌍 Choose your language:\n"
    "Выберите язык:\n"
    "اختر لغتك:"
)


def _make_language_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with language selection buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="English", callback_data="lang_en"),
            InlineKeyboardButton(text="العربية", callback_data="lang_ar"),
            InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
        ]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User | None) -> None:
    chat_id = message.chat.id

    if db_user is None:
        # New user — ask to choose language
        logger.info("start_new_user", chat_id=chat_id)
        await message.answer(
            LANGUAGE_CHOOSE_MESSAGE,
            reply_markup=_make_language_keyboard(),
        )
        return

    # Existing user — greet in their language
    lang = db_user.language or "en"
    logger.info("start_existing_user", chat_id=chat_id, lang=lang)
    strings = get_strings(lang)
    await message.answer(strings.START_MESSAGE, parse_mode="HTML")


@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(callback: CallbackQuery, db_user: User | None) -> None:
    """User picked a language from inline keyboard."""
    await callback.answer()
    if not callback.message or not callback.from_user:
        return

    lang = callback.data.removeprefix("lang_")  # "en", "ar", "ru"
    chat_id = callback.from_user.id
    username = callback.from_user.username or ""
    first_name = callback.from_user.first_name or ""

    logger.info("language_selected", chat_id=chat_id, lang=lang)

    if db_user is None:
        # New user — create minimal record
        await save_user_language(chat_id, lang, username, first_name)
    else:
        # Existing user — just update language
        await update_user_language(chat_id, lang)

    # Remove language buttons
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Send welcome message in chosen language
    strings = get_strings(lang)
    await callback.message.answer(strings.START_MESSAGE, parse_mode="HTML")


@router.message(Command("language"))
async def cmd_language(message: Message, db_user: User | None) -> None:
    """Show language selection keyboard (works for both new and existing users)."""
    logger.info("language_command", chat_id=message.chat.id)
    await message.answer(
        LANGUAGE_CHOOSE_MESSAGE,
        reply_markup=_make_language_keyboard(),
    )
