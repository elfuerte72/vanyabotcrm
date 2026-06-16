"""CTA click tracking — signed redirect links.

The RU meal-plan CTA button can't be a plain URL button if we want to know who
actually opens the results site: Telegram opens URL buttons directly and never
notifies the bot. Instead the button points at our own ``/go`` endpoint
(``handlers/tracking.py``), which records a ``cta_click`` event and 302-redirects
to the real site.

To stop anyone from forging or enumerating ``chat_id`` values in that public URL,
each link carries an HMAC signature derived from the bot token. The site owner
needs no changes — the redirect lives entirely on our side.
"""

from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlencode

from config.settings import settings

# HMAC length in hex chars kept in the URL — 16 chars (64 bits) is plenty to make
# brute-forcing a valid signature for a chosen chat_id infeasible.
_SIG_LEN = 16


def sign_chat_id(chat_id: int) -> str:
    """Return a short HMAC-SHA256 signature for ``chat_id`` keyed by the bot token."""
    digest = hmac.new(
        settings.bot_token.encode(),
        f"cta:{chat_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return digest[:_SIG_LEN]


def verify_signature(chat_id: int, signature: str) -> bool:
    """Constant-time check that ``signature`` matches ``chat_id``."""
    return hmac.compare_digest(sign_chat_id(chat_id), signature or "")


def build_cta_url(chat_id: int) -> str:
    """Build the signed CTA redirect URL pointing at our ``/go`` endpoint."""
    base = settings.public_base_url.rstrip("/")
    query = urlencode({"u": chat_id, "sig": sign_chat_id(chat_id)})
    return f"{base}/go?{query}"
