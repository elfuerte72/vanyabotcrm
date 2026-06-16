"""CTA redirect endpoint — tracks who opens the results site after KBJU.

The RU meal-plan CTA button links here instead of straight to the results site.
When a user taps it we record a ``cta_click`` event (so the CRM timeline shows the
click-through) and then 302-redirect to the real site. The link is HMAC-signed
(see ``services/tracking.py``) so chat_ids can't be forged or enumerated.

The redirect always happens, even on a bad/missing signature, so a tampered link
never leaves the user stuck — we just don't record an event in that case.
"""

from __future__ import annotations

import structlog
from aiohttp import web

from src.db.queries import save_user_event
from src.i18n import ru as ru_strings
from src.services.tracking import verify_signature

logger = structlog.get_logger()


async def handle_cta_redirect(request: web.Request) -> web.Response:
    """Log a CTA click (when the signature is valid) and redirect to the site."""
    destination = ru_strings.MEAL_PLAN_CTA_URL

    raw_chat_id = request.query.get("u", "")
    signature = request.query.get("sig", "")

    try:
        chat_id = int(raw_chat_id)
    except (TypeError, ValueError):
        logger.warning("cta_redirect_bad_chat_id", raw=raw_chat_id)
        raise web.HTTPFound(location=destination)

    if verify_signature(chat_id, signature):
        try:
            await save_user_event(
                chat_id,
                "cta_click",
                "meal_plan_cta",
                language="ru",
                workflow_name="funnel",
            )
            logger.info("cta_click_tracked", chat_id=chat_id)
        except Exception as e:  # never block the redirect on a DB hiccup
            logger.error("cta_click_save_failed", chat_id=chat_id, error=str(e))
    else:
        logger.warning("cta_redirect_invalid_signature", chat_id=chat_id)

    raise web.HTTPFound(location=destination)


def setup_tracking_routes(app: web.Application) -> None:
    """Register the CTA click-tracking redirect route."""
    app.router.add_get("/go", handle_cta_redirect)
