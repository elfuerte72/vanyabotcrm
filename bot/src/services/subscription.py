"""Telegram channel subscription check.

Used to gate KBJU generation for Russian-speaking users behind a channel
subscription. The bot must be added as an administrator of the target channel
for ``get_chat_member`` to return the user's status.
"""

from __future__ import annotations

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.settings import settings

logger = structlog.get_logger()

_SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Return True if the user is a member of the configured channel.

    Returns False on any API error so the caller can fall through to the
    "please subscribe" path rather than crashing the conversation.
    """
    channel_id = settings.telegram_channel_id
    if not channel_id:
        # Subscription gating disabled by configuration.
        return True

    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
    except TelegramAPIError as e:
        logger.warning(
            "subscription_check_failed",
            user_id=user_id,
            channel=channel_id,
            error=str(e),
        )
        return False

    return member.status in _SUBSCRIBED_STATUSES
