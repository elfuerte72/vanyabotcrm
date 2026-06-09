"""Funnel message definitions for all stages and languages.

Maps funnel_stage → (text, buttons, media) per language.
RU has no scheduled funnel — after the meal plan the handler sends a single CTA
message inline (see handlers/message.py), so only EN/AR are defined here.
EN: 9 stages (0-8) + 2 upsells (9-10) with photos and question buttons.
AR: 9 stages (0-8) + 2 upsells (9-10) with photos and question buttons.
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
    extra_photos: list[str] = field(default_factory=list)  # Additional photos for media group
    video_note_id: str = ""  # Google Drive file ID for video note (circle)
    photo_first: bool = False  # Send photo before text (default: text first)
    text_after: str = ""  # Text sent after photo (text → photo → text_after+keyboard)


def _get_en_funnel_message(stage: int, s) -> FunnelMessage | None:
    """EN funnel: 9 stages (0-8) + 2 upsells (9-10), with photos and question buttons."""
    funnel_photos = media_config.get("photos", {}).get("funnel", {})

    # Stages 0-8: buy button + question button (question triggers next stage instantly)
    stage_map = {
        0: (s.FUNNEL_STAGE_0, s.FUNNEL_STAGE_0_BUY, s.FUNNEL_STAGE_0_QUESTION),
        1: (s.FUNNEL_STAGE_1, s.FUNNEL_STAGE_1_BUY, s.FUNNEL_STAGE_1_QUESTION),
        2: (s.FUNNEL_STAGE_2, s.FUNNEL_STAGE_2_BUY, s.FUNNEL_STAGE_2_QUESTION),
        3: (s.FUNNEL_STAGE_3, s.FUNNEL_STAGE_3_BUY, s.FUNNEL_STAGE_3_QUESTION),
        4: (s.FUNNEL_STAGE_4, s.FUNNEL_STAGE_4_BUY, s.FUNNEL_STAGE_4_QUESTION),
        5: (s.FUNNEL_STAGE_5, s.FUNNEL_STAGE_5_BUY, s.FUNNEL_STAGE_5_QUESTION),
        6: (s.FUNNEL_STAGE_6, s.FUNNEL_STAGE_6_BUY, s.FUNNEL_STAGE_6_QUESTION),
        7: (s.FUNNEL_STAGE_7, s.FUNNEL_STAGE_7_BUY, s.FUNNEL_STAGE_7_QUESTION),
        8: (s.FUNNEL_STAGE_8, s.FUNNEL_STAGE_8_BUY, s.FUNNEL_STAGE_8_QUESTION),
    }

    if stage in stage_map:
        text, buy_label, question_label = stage_map[stage]
        photo_name = ""
        if stage == 0:
            photo_name = funnel_photos.get("en_stage_0", "")
        elif stage == 5:
            photo_name = funnel_photos.get("en_stage_5", "")
        elif stage == 6:
            photo_name = funnel_photos.get("en_stage_6", "")

        return FunnelMessage(
            text=text,
            buttons=[
                (buy_label, "buy_now"),
                (question_label, f"en_funnel_q_{stage}"),
            ],
            photo_name=photo_name,
        )

    # Upsell stages (after purchase)
    if stage == 9:
        return FunnelMessage(
            text=s.UPSELL_1,
            buttons=[
                (s.UPSELL_1_BUY, "buy_now"),
                (s.UPSELL_1_DECLINE, "upsell_decline"),
            ],
        )
    elif stage == 10:
        return FunnelMessage(
            text=s.UPSELL_2,
            buttons=[
                (s.UPSELL_2_BUY, "buy_now"),
                (s.UPSELL_2_DECLINE, "upsell_decline"),
            ],
        )

    return None


def _get_ar_funnel_message(stage: int, s) -> FunnelMessage | None:
    """AR funnel: 9 stages (0-8) + 2 upsells (9-10), with photos and question buttons."""
    funnel_photos = media_config.get("photos", {}).get("funnel", {})

    # Stages 0-8: buy button + question button (question triggers next stage instantly)
    stage_map = {
        0: (s.FUNNEL_STAGE_0, s.FUNNEL_STAGE_0_BUY, s.FUNNEL_STAGE_0_QUESTION),
        1: (s.FUNNEL_STAGE_1, s.FUNNEL_STAGE_1_BUY, s.FUNNEL_STAGE_1_QUESTION),
        2: (s.FUNNEL_STAGE_2, s.FUNNEL_STAGE_2_BUY, s.FUNNEL_STAGE_2_QUESTION),
        3: (s.FUNNEL_STAGE_3, s.FUNNEL_STAGE_3_BUY, s.FUNNEL_STAGE_3_QUESTION),
        4: (s.FUNNEL_STAGE_4, s.FUNNEL_STAGE_4_BUY, s.FUNNEL_STAGE_4_QUESTION),
        5: (s.FUNNEL_STAGE_5, s.FUNNEL_STAGE_5_BUY, s.FUNNEL_STAGE_5_QUESTION),
        6: (s.FUNNEL_STAGE_6, s.FUNNEL_STAGE_6_BUY, s.FUNNEL_STAGE_6_QUESTION),
        7: (s.FUNNEL_STAGE_7, s.FUNNEL_STAGE_7_BUY, s.FUNNEL_STAGE_7_QUESTION),
        8: (s.FUNNEL_STAGE_8, s.FUNNEL_STAGE_8_BUY, s.FUNNEL_STAGE_8_QUESTION),
    }

    if stage in stage_map:
        text, buy_label, question_label = stage_map[stage]
        photo_name = ""
        if stage == 0:
            photo_name = funnel_photos.get("en_stage_0", "")
        elif stage == 5:
            photo_name = funnel_photos.get("en_stage_5", "")
        elif stage == 6:
            photo_name = funnel_photos.get("en_stage_6", "")

        return FunnelMessage(
            text=text,
            buttons=[
                (buy_label, "buy_now"),
                (question_label, f"ar_funnel_q_{stage}"),
            ],
            photo_name=photo_name,
        )

    # Upsell stages (after purchase)
    if stage == 9:
        return FunnelMessage(
            text=s.UPSELL_1,
            buttons=[
                (s.UPSELL_1_BUY, "buy_now"),
                (s.UPSELL_1_DECLINE, "upsell_decline"),
            ],
        )
    elif stage == 10:
        return FunnelMessage(
            text=s.UPSELL_2,
            buttons=[
                (s.UPSELL_2_BUY, "buy_now"),
                (s.UPSELL_2_DECLINE, "upsell_decline"),
            ],
        )

    return None


def get_funnel_message(stage: int, language: str, variant: str | None = None) -> FunnelMessage | None:
    """Get funnel message for a given stage and language.

    EN: 9 stages (0-8) + 2 upsells (9-10).
    AR: 9 stages (0-8) + 2 upsells (9-10).
    RU has no scheduled funnel (single CTA sent inline) → always None.
    Returns None if stage is out of range.
    """
    s = get_strings(language)

    if language == "en":
        msg = _get_en_funnel_message(stage, s)
    elif language == "ar":
        msg = _get_ar_funnel_message(stage, s)
    elif language == "ru":
        msg = None
    else:
        msg = _get_ar_funnel_message(stage, get_strings("ar"))

    if msg:
        logger.debug("funnel_message_resolved", stage=stage, language=language, variant=variant, has_photo=bool(msg.photo_name), has_video_note=bool(msg.video_note_id), num_buttons=len(msg.buttons))
    return msg
