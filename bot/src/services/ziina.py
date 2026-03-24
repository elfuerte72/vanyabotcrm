"""Ziina Payment Intent API client.

Creates payment intents for EN/AR users. Returns (intent_id, redirect_url)
so the bot can send users a checkout link and track the payment via webhook.
"""

from __future__ import annotations

import aiohttp
import structlog

from config.settings import settings

logger = structlog.get_logger()

ZIINA_API_URL = "https://api-v2.ziina.com/api"


async def create_payment_intent(
    amount_aed: int,
    message: str = "",
) -> tuple[str, str]:
    """Create a Ziina payment intent.

    Args:
        amount_aed: Amount in AED (e.g. 49). Converted to fils internally.
        message: Message displayed on the Ziina checkout page.

    Returns:
        Tuple of (payment_intent_id, redirect_url).

    Raises:
        ZiinaAPIError: If the API call fails.
    """
    amount_fils = amount_aed * 100
    payload = {
        "amount": amount_fils,
        "currency_code": "AED",
    }
    if message:
        payload["message"] = message

    headers = {
        "Authorization": f"Bearer {settings.ziina_api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{ZIINA_API_URL}/payment_intent",
            json=payload,
            headers=headers,
        ) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                logger.error(
                    "ziina_create_intent_failed",
                    status=resp.status,
                    body=body[:200],
                )
                raise ZiinaAPIError(f"Ziina API returned {resp.status}: {body[:200]}")

            data = await resp.json()
            intent_id = data["id"]
            redirect_url = data["redirect_url"]

            logger.info(
                "ziina_payment_intent_created",
                intent_id=intent_id,
                amount_aed=amount_aed,
            )
            return intent_id, redirect_url


class ZiinaAPIError(Exception):
    """Raised when Ziina API call fails."""
