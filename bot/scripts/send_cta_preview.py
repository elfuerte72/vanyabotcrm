"""One-off: send the new RU meal-plan CTA message to a chat for visual review.

Uses the exact strings from src/i18n/ru.py so the preview matches what RU users
receive right after the meal plan.

Usage: uv run python -m scripts.send_cta_preview <chat_id>
"""

import json
import sys
import urllib.request
from pathlib import Path

from src.i18n import ru as ru_strings
from src.services.tracking import build_cta_url


def _load_token() -> str:
    env = Path(__file__).resolve().parent.parent / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("BOT_TOKEN not found in .env")


def main() -> None:
    chat_id = int(sys.argv[1]) if len(sys.argv) > 1 else 379336096
    token = _load_token()

    # Route the button through the /go tracking endpoint (signed) so the preview
    # exercises the real click-through tracking, not the bare results-site link.
    cta_url = build_cta_url(chat_id)
    print("cta_url:", cta_url)

    payload = {
        "chat_id": chat_id,
        "text": ru_strings.MEAL_PLAN_CTA,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": ru_strings.MEAL_PLAN_CTA_BUTTON,
                    "url": cta_url,
                }
            ]]
        },
    }

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    print("ok:", body.get("ok"), "| message_id:", body.get("result", {}).get("message_id"))


if __name__ == "__main__":
    main()
