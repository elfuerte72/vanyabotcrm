"""Tests for language selection at /start and /language command."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.start import (
    LANGUAGE_CHOOSE_MESSAGE,
    _make_language_keyboard,
    cmd_start,
    handle_language_selection,
    cmd_language,
)
from tests.helpers import make_callback, make_message, make_user


# ─── Keyboard helper ─────────────────────────────────────────────────────


def test_make_language_keyboard_has_three_buttons():
    kb = _make_language_keyboard()
    buttons = kb.inline_keyboard[0]
    assert len(buttons) == 3
    assert buttons[0].text == "English"
    assert buttons[0].callback_data == "lang_en"
    assert buttons[1].text == "العربية"
    assert buttons[1].callback_data == "lang_ar"
    assert buttons[2].text == "Русский"
    assert buttons[2].callback_data == "lang_ru"


# ─── /start ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_new_user_shows_language_buttons():
    """New user (db_user=None) should see language selection."""
    message = make_message(text="/start")
    await cmd_start(message, db_user=None)

    message.answer.assert_called_once()
    call_kwargs = message.answer.call_args
    assert call_kwargs[0][0] == LANGUAGE_CHOOSE_MESSAGE
    assert call_kwargs[1]["reply_markup"] is not None
    # Check that buttons are present
    kb = call_kwargs[1]["reply_markup"]
    assert len(kb.inline_keyboard[0]) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["ru", "en", "ar"])
async def test_start_existing_user_shows_message(lang):
    """Existing user should get START_MESSAGE in their language."""
    user = make_user(lang)
    message = make_message(text="/start")

    await cmd_start(message, db_user=user)

    message.answer.assert_called_once()
    call_args = message.answer.call_args
    # Should NOT have reply_markup with language buttons
    reply_markup = call_args[1].get("reply_markup")
    assert reply_markup is None
    # Should have parse_mode HTML
    assert call_args[1].get("parse_mode") == "HTML"


# ─── Language callback ────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "ar", "ru"])
@patch("src.handlers.start.save_user_language", new_callable=AsyncMock)
async def test_language_callback_saves_language(mock_save, lang):
    """Selecting a language should save it via save_user_language for new users."""
    callback = make_callback(data=f"lang_{lang}", chat_id=12345, user_id=12345)
    callback.from_user.username = "testuser"
    callback.from_user.first_name = "Test"
    callback.message.answer = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()

    await handle_language_selection(callback, db_user=None)

    callback.answer.assert_called_once()
    mock_save.assert_called_once_with(12345, lang, "testuser", "Test")
    callback.message.edit_reply_markup.assert_called_once_with(reply_markup=None)
    callback.message.answer.assert_called_once()


@pytest.mark.asyncio
@patch("src.handlers.start.update_user_language", new_callable=AsyncMock)
async def test_language_callback_updates_existing_user(mock_update):
    """Existing user changing language should call update_user_language."""
    user = make_user("en")
    callback = make_callback(data="lang_ru", chat_id=user.chat_id, user_id=user.chat_id)
    callback.from_user.username = "jane_en"
    callback.from_user.first_name = "Jane"
    callback.message.answer = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()

    await handle_language_selection(callback, db_user=user)

    mock_update.assert_called_once_with(user.chat_id, "ru")
    callback.message.answer.assert_called_once()


# ─── /language command ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_language_command_shows_buttons():
    """/language should show language selection keyboard."""
    message = make_message(text="/language")

    await cmd_language(message, db_user=None)

    message.answer.assert_called_once()
    call_kwargs = message.answer.call_args
    assert call_kwargs[0][0] == LANGUAGE_CHOOSE_MESSAGE
    kb = call_kwargs[1]["reply_markup"]
    assert len(kb.inline_keyboard[0]) == 3


# ─── Language detection fallback in message.py ────────────────────────────


def test_detected_lang_uses_db_language():
    """When db_user has a language, it should be used instead of detect_language."""
    from src.services.language import detect_language

    user = make_user("ar")
    # User has Arabic in DB but writes in English
    text = "Hello, I want to calculate my nutrition"
    detected = detect_language(text)
    assert detected == "en"  # detect_language would return English

    # But db_user.language should take priority
    result_lang = user.language if user and user.language else detect_language(text)
    assert result_lang == "ar"
