#!/usr/bin/env python3
"""One-time script: register Ziina webhook URL.

Usage:
    uv run python scripts/register_ziina_webhook.py https://YOUR_PUBLIC_URL/webhook/ziina
"""

import sys
import os
from pathlib import Path

# Add bot/ to path
_BOT_DIR = Path(__file__).resolve().parent.parent / "bot"
os.chdir(_BOT_DIR)
sys.path.insert(0, str(_BOT_DIR))

import asyncio
import aiohttp
from config.settings import settings


async def register_webhook(webhook_url: str) -> None:
    secret = settings.ziina_webhook_secret
    payload = {"url": webhook_url}
    if secret and secret != "your_ziina_secret":
        payload["secret"] = secret

    headers = {
        "Authorization": f"Bearer {settings.ziina_api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api-v2.ziina.com/api/webhook",
            json=payload,
            headers=headers,
        ) as resp:
            body = await resp.json()
            print(f"Status: {resp.status}")
            print(f"Response: {body}")
            if body.get("success"):
                print(f"\nWebhook registered: {webhook_url}")
                if secret and secret != "your_ziina_secret":
                    print(f"Secret configured for HMAC validation")
            else:
                print(f"\nFailed: {body.get('error', 'unknown error')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/register_ziina_webhook.py https://YOUR_URL/webhook/ziina")
        sys.exit(1)

    asyncio.run(register_webhook(sys.argv[1]))
