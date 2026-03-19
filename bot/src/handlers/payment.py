"""Ziina payment webhook handler.

Receives payment confirmation from Ziina and:
1. Validates webhook secret (required — rejects if not configured)
2. Updates user as buyer in DB
3. Sends confirmation + content to user via Telegram
"""

from __future__ import annotations

import hmac
import hashlib

import structlog
from aiohttp import web

from config.settings import settings
from src.db.queries import mark_as_buyer, get_user
from src.i18n import get_strings

logger = structlog.get_logger()


async def handle_ziina_webhook(request: web.Request) -> web.Response:
    """Handle incoming Ziina payment webhook."""
    # Reject webhooks if secret is not configured
    if not settings.ziina_webhook_secret:
        logger.error("ziina_webhook_secret_not_configured")
        return web.Response(status=503, text="Webhook secret not configured")

    signature = request.headers.get("X-Webhook-Signature", "")
    body = await request.read()
    expected = hmac.new(
        settings.ziina_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        logger.warning("ziina_webhook_invalid_signature")
        return web.Response(status=401, text="Invalid signature")

    try:
        import json
        data = json.loads(body)
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    # Log only safe fields
    logger.info(
        "ziina_webhook_received",
        status=data.get("status"),
        has_chat_id=bool(data.get("metadata", {}).get("chat_id")),
    )

    # Extract payment info
    payment_status = data.get("status")
    chat_id_raw = data.get("metadata", {}).get("chat_id")

    if not chat_id_raw:
        logger.warning("ziina_webhook_no_chat_id")
        return web.Response(status=200, text="OK")

    try:
        chat_id = int(chat_id_raw)
    except (ValueError, TypeError):
        logger.warning("ziina_webhook_invalid_chat_id", chat_id_raw=str(chat_id_raw)[:20])
        return web.Response(status=400, text="Invalid chat_id")

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
                text=strings.PAYMENT_CONFIRMED,
            )

    return web.Response(status=200, text="OK")


def setup_payment_routes(app: web.Application) -> None:
    """Register payment webhook routes."""
    app.router.add_post("/webhook/ziina", handle_ziina_webhook)
