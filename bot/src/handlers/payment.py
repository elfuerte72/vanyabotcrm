"""Ziina payment webhook handler.

Receives payment confirmation from Ziina and:
1. Updates user as buyer in DB
2. Sends confirmation + content to user via Telegram
"""

from __future__ import annotations

import structlog
from aiohttp import web

from src.db.queries import mark_as_buyer, get_user
from src.i18n import get_strings

logger = structlog.get_logger()


async def handle_ziina_webhook(request: web.Request) -> web.Response:
    """Handle incoming Ziina payment webhook."""
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    logger.info("ziina_webhook_received", data=data)

    # Extract payment info (adjust based on actual Ziina webhook format)
    payment_status = data.get("status")
    chat_id = data.get("metadata", {}).get("chat_id")

    if not chat_id:
        logger.warning("ziina_webhook_no_chat_id", data=data)
        return web.Response(status=200, text="OK")

    chat_id = int(chat_id)

    if payment_status == "completed":
        await mark_as_buyer(chat_id)
        logger.info("ziina_payment_completed", chat_id=chat_id)

        # Send confirmation via bot (bot instance passed via app context)
        bot = request.app.get("bot")
        if bot:
            user = await get_user(chat_id)
            language = user.language if user else "en"
            strings = get_strings(language)
            await bot.send_message(
                chat_id=chat_id,
                text="Payment received! Your workout access is now active. Check your messages.",
            )

    return web.Response(status=200, text="OK")


def setup_payment_routes(app: web.Application) -> None:
    """Register payment webhook routes."""
    app.router.add_post("/webhook/ziina", handle_ziina_webhook)
