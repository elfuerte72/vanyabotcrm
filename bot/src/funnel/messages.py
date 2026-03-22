"""Funnel message definitions for all stages and languages.

Maps funnel_stage → (text, buttons, media) per language.
RU: 8 stages (0-7) with photos and video notes.
EN/AR: 6 stages (0-5) with text + buttons only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from config.settings import media_config
from src.i18n import get_strings

logger = structlog.get_logger()


@dataclass
class FunnelMessage:
    text: str
    buttons: list[tuple[str, str]]  # [(label, callback_data), ...]
    has_url_button: bool = False
    url: str = ""
    photo_name: str = ""  # Local photo filename (bot/media/photos/)
    video_note_id: str = ""  # Google Drive file ID for video note (circle)


def _get_ru_funnel_message(stage: int, s) -> FunnelMessage | None:
    """RU funnel: 8 stages (0-7) with photos and video notes."""
    workout_url = media_config["videos"].get("workout_url", "")
    video_notes = media_config.get("video_notes", {})
    funnel_photos = media_config.get("photos", {}).get("funnel", {})

    if stage == 0:
        # Gift: morning activation video link
        return FunnelMessage(
            text=s.FUNNEL_STAGE_0,
            buttons=[(s.FUNNEL_STAGE_0_BUTTON, "video_workout")],
        )
    elif stage == 1:
        # Before/after photo + learn_workout button
        return FunnelMessage(
            text=s.FUNNEL_STAGE_1,
            buttons=[(s.FUNNEL_STAGE_1_BUTTON, "learn_workout")],
            photo_name=funnel_photos.get("stage_1", ""),
        )
    elif stage == 2:
        # Masha's story + before/after photo (no buttons)
        return FunnelMessage(
            text=s.FUNNEL_STAGE_2,
            buttons=[],
            photo_name=funnel_photos.get("stage_2", ""),
        )
    elif stage == 3:
        # "How it works" — video note (circle)
        return FunnelMessage(
            text=s.FUNNEL_STAGE_3,
            buttons=[(s.FUNNEL_STAGE_3_BUTTON, "video_circle")],
            video_note_id=video_notes.get("how_it_works", ""),
        )
    elif stage == 4:
        # Detailed workout description (text only, no buttons)
        return FunnelMessage(
            text=s.FUNNEL_STAGE_4,
            buttons=[],
        )
    elif stage == 5:
        # Sales pitch: 690₽ + buy button + video note
        return FunnelMessage(
            text=s.FUNNEL_STAGE_5,
            buttons=[(s.FUNNEL_STAGE_5_BUTTON, "buy_now")],
            video_note_id=video_notes.get("will_it_suit", ""),
        )
    elif stage == 6:
        # Soft reminder: 690₽ + buy button
        return FunnelMessage(
            text=s.FUNNEL_STAGE_6,
            buttons=[(s.FUNNEL_STAGE_6_BUTTON, "buy_now")],
        )
    elif stage == 7:
        # Thank you + channel subscription (URL button)
        return FunnelMessage(
            text=s.FUNNEL_STAGE_7,
            buttons=[(s.FUNNEL_STAGE_7_BUTTON, "")],
            has_url_button=True,
            url="https://t.me/ivanfit_health",
        )

    return None


def _get_default_funnel_message(stage: int, s) -> FunnelMessage | None:
    """EN/AR funnel: 6 stages (0-5), text + buttons only."""
    if stage == 0:
        return FunnelMessage(
            text=s.FUNNEL_DAY_0,
            buttons=[(s.FUNNEL_DAY_0_BUTTON, "video_workout")],
        )
    elif stage == 1:
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


def get_funnel_message(stage: int, language: str) -> FunnelMessage | None:
    """Get funnel message for a given stage and language.

    RU: 8 stages (0-7).
    EN/AR: 6 stages (0-5).
    Returns None if stage is out of range.
    """
    s = get_strings(language)

    if language == "ru":
        msg = _get_ru_funnel_message(stage, s)
    else:
        msg = _get_default_funnel_message(stage, s)

    if msg:
        logger.debug("funnel_message_resolved", stage=stage, language=language, has_photo=bool(msg.photo_name), has_video_note=bool(msg.video_note_id))
    return msg
