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

from src.db.queries import save_user_event, save_user_language, update_user_language, clear_chat_history
from src.i18n import get_strings
from src.models.user import User

logger = structlog.get_logger()

router = Router()

LANGUAGE_CHOOSE_MESSAGE = "Choose your language:"


def _make_language_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with language selection buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f1ec\U0001f1e7 English", callback_data="lang_en"),
            InlineKeyboardButton(text="\U0001f1e6\U0001f1ea \u0627\u0644\u0639\u0631\u0628\u064a\u0629", callback_data="lang_ar"),
            InlineKeyboardButton(text="\U0001f1f7\U0001f1fa \u0420\u0443\u0441\u0441\u043a\u0438\u0439", callback_data="lang_ru"),
        ]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User | None) -> None:
    logger.info("start_command", chat_id=message.chat.id)
    await message.answer(
        LANGUAGE_CHOOSE_MESSAGE,
        reply_markup=_make_language_keyboard(),
    )


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
    await save_user_event(chat_id, "button_click", f"lang_{lang}", lang, "onboarding")

    if db_user is None:
        await save_user_language(chat_id, lang, username, first_name)
    else:
        await update_user_language(chat_id, lang)

    # Delete the language selection message
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Clear chat history so the agent starts fresh
    await clear_chat_history(str(chat_id))

    strings = get_strings(lang)

    if db_user is not None and db_user.get_food:
        # User already has a meal plan — just confirm language change
        await callback.message.answer(strings.LANGUAGE_CHANGED)
    else:
        # New user or user without meal plan — send welcome with questions
        await callback.message.answer(strings.WELCOME_WITH_QUESTIONS)


@router.message(Command("language"))
async def cmd_language(message: Message, db_user: User | None) -> None:
    """Show language selection keyboard (works for both new and existing users)."""
    logger.info("language_command", chat_id=message.chat.id)
    await message.answer(
        LANGUAGE_CHOOSE_MESSAGE,
        reply_markup=_make_language_keyboard(),
    )
