"""Funnel message definitions for all stages and languages.

Maps funnel_stage → (text, buttons) per language.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import media_config
from src.i18n import get_strings


@dataclass
class FunnelMessage:
    text: str
    buttons: list[tuple[str, str]]  # [(label, callback_data), ...]
    has_url_button: bool = False
    url: str = ""


def get_funnel_message(stage: int, language: str) -> FunnelMessage | None:
    """Get funnel message for a given stage and language.

    Returns None if stage is out of range (0-5).
    """
    s = get_strings(language)

    if stage == 0:
        # Day 1: free workout video link
        workout_url = media_config["videos"].get("workout_url", "")
        return FunnelMessage(
            text=s.FUNNEL_DAY_0,
            buttons=[(s.FUNNEL_DAY_0_BUTTON, "video_workout")],
            has_url_button=True,
            url=workout_url,
        )
    elif stage == 1:
        # Day video_workout: buy offer after free video
        return FunnelMessage(
            text=s.FUNNEL_DAY_1,
            buttons=[(s.FUNNEL_DAY_1_BUTTON, "buy_now")],
        )
    elif stage == 2:
        return FunnelMessage(text=s.FUNNEL_DAY_2, buttons=s.FUNNEL_DAY_2_BUTTONS)
    elif stage == 3:
        return FunnelMessage(text=s.FUNNEL_DAY_3, buttons=s.FUNNEL_DAY_3_BUTTONS)
    elif stage == 4:
        return FunnelMessage(text=s.FUNNEL_DAY_4, buttons=s.FUNNEL_DAY_4_BUTTONS)
    elif stage == 5:
        return FunnelMessage(text=s.FUNNEL_DAY_5, buttons=s.FUNNEL_DAY_5_BUTTONS)

    return None
