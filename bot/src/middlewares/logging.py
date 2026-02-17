"""Structured logging middleware for all incoming events."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            logger.info(
                "incoming_message",
                chat_id=event.chat.id,
                user_id=event.from_user.id if event.from_user else None,
                username=event.from_user.username if event.from_user else None,
                text=(event.text or "")[:100],
                content_type=event.content_type,
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "incoming_callback",
                user_id=event.from_user.id if event.from_user else None,
                data=event.data,
                chat_id=event.message.chat.id if event.message else None,
            )

        return await handler(event, data)
