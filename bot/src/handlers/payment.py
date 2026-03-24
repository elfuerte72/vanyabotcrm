"""Ziina payment webhook handler.

Receives payment status updates from Ziina via webhook:
- Event: payment_intent.status.updated
- Header: X-Hmac-Signature (HMAC-SHA256 of body)
- Looks up chat_id via payment_intent_id stored in users_nutrition.id_ziina
- On "completed": marks user as buyer and sends confirmation
- On "failed": sends failure notification
"""

from __future__ import annotations

import hmac
import hashlib
import json

import structlog
from aiohttp import web

from config.settings import settings
from src.db.queries import get_chat_id_by_ziina_payment, get_user, mark_as_buyer
from src.i18n import get_strings

logger = structlog.get_logger()


async def handle_ziina_webhook(request: web.Request) -> web.Response:
    """Handle incoming Ziina payment webhook."""
    # Reject webhooks if secret is not configured
    if not settings.ziina_webhook_secret:
        logger.error("ziina_webhook_secret_not_configured")
        return web.Response(status=503, text="Webhook secret not configured")

    # Validate HMAC-SHA256 signature (Ziina uses X-Hmac-Signature header)
    signature = request.headers.get("X-Hmac-Signature", "")
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
        payload = json.loads(body)
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    # Ziina webhook format: {event: "payment_intent.status.updated", data: PaymentIntentDto}
    event = payload.get("event", "")
    intent_data = payload.get("data", {})
    payment_intent_id = intent_data.get("id")
    payment_status = intent_data.get("status")

    logger.info(
        "ziina_webhook_received",
        event=event,
        intent_id=payment_intent_id,
        status=payment_status,
    )

    if not payment_intent_id:
        logger.warning("ziina_webhook_no_intent_id")
        return web.Response(status=200, text="OK")

    # Look up chat_id from payment_intent_id stored in users_nutrition.id_ziina
    chat_id = await get_chat_id_by_ziina_payment(payment_intent_id)
    if not chat_id:
        logger.warning("ziina_webhook_unknown_intent", intent_id=payment_intent_id)
        return web.Response(status=200, text="OK")

    bot = request.app.get("bot")
    user = await get_user(chat_id)
    language = user.language if user else "en"
    strings = get_strings(language)

    if payment_status == "completed":
        await mark_as_buyer(chat_id)
        logger.info("ziina_payment_completed", chat_id=chat_id, intent_id=payment_intent_id)

        if bot:
            await bot.send_message(
                chat_id=chat_id,
                text=strings.PAYMENT_CONFIRMED,
            )

    elif payment_status == "failed":
        logger.warning("ziina_payment_failed", chat_id=chat_id, intent_id=payment_intent_id)

        if bot and hasattr(strings, "PAYMENT_FAILED"):
            await bot.send_message(
                chat_id=chat_id,
                text=strings.PAYMENT_FAILED,
            )

    return web.Response(status=200, text="OK")


def setup_payment_routes(app: web.Application) -> None:
    """Register payment webhook routes."""
    app.router.add_post("/webhook/ziina", handle_ziina_webhook)
