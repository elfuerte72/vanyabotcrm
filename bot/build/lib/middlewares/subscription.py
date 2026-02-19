"""Middleware to check Telegram channel subscription."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message

from config.settings import settings
from src.i18n import get_strings
from src.services.language import detect_language

logger = structlog.get_logger()

ALLOWED_STATUSES = {"member", "administrator", "creator"}


class SubscriptionMiddleware(BaseMiddleware):
    """Check if user is subscribed to the required channel.

    Skips callback queries (they are handled separately).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Only check for messages, not callbacks
        if not isinstance(event, Message):
            return await handler(event, data)

        message: Message = event
        user_id = message.from_user.id if message.from_user else None
        if user_id is None:
            return await handler(event, data)

        bot: Bot = data["bot"]

        try:
            # Use @username if numeric ID fails (bot must be channel admin)
            channel = f"@{settings.channel_username}" if settings.channel_username else settings.channel_id
            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=user_id,
            )
            is_subscribed = member.status in ALLOWED_STATUSES
            logger.debug(
                "subscription_check",
                user_id=user_id,
                channel=channel,
                status=member.status,
                is_subscribed=is_subscribed,
            )
        except Exception as e:
            logger.warning(
                "subscription_check_failed",
                user_id=user_id,
                channel=channel,
                error=str(e),
                error_type=type(e).__name__,
            )
            is_subscribed = False

        if not is_subscribed:
            lang = detect_language(message.text or "")
            strings = get_strings(lang)
            await message.answer(
                f"<b>RU:</b>\n{get_strings('ru').SUBSCRIBE_MESSAGE}\n\n"
                f"<b>EN:</b>\n{get_strings('en').SUBSCRIBE_MESSAGE}\n\n"
                f"<b>AR:</b>\n{get_strings('ar').SUBSCRIBE_MESSAGE}",
                parse_mode="HTML",
            )
            logger.info("user_not_subscribed", user_id=user_id)
            return  # Block handler

        data["is_subscribed"] = True
        return await handler(event, data)
