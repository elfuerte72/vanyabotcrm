"""Middleware to load user data from DB and inject into handler context."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from src.db.queries import get_user

logger = structlog.get_logger()


class UserDataMiddleware(BaseMiddleware):
    """Load user from database and inject as 'db_user' into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat_id: int | None = None

        if isinstance(event, Message) and event.from_user:
            chat_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            chat_id = event.from_user.id

        if chat_id is not None:
            user = await get_user(chat_id)
            data["db_user"] = user
            logger.debug("user_loaded", chat_id=chat_id, found=user is not None)
        else:
            data["db_user"] = None

        return await handler(event, data)
