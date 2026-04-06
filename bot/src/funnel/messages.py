"""Funnel message definitions for all stages and languages.

Maps funnel_stage → (text, buttons, media) per language.
RU: 13 stages (0-12) with zone branching. Stage 0 common, 1-12 zone-specific.
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


def _get_ru_funnel_message(stage: int, s, variant: str | None = None) -> FunnelMessage | None:
    """RU funnel: 13 stages (0-12) with zone branching.

    Stage 0 is common (zone selection). Stages 1-12 are zone-specific.
    Currently only 'belly' variant is implemented.
    """
    video_notes = media_config.get("video_notes", {})
    funnel_photos = media_config.get("photos", {}).get("funnel", {})

    if stage == 0:
        # Zone selection only (4 buttons). Wakeup message is sent separately first.
        return FunnelMessage(
            text=s.FUNNEL_STAGE_0,
            buttons=[
                (s.ZONE_BELLY, "zone_belly"),
                (s.ZONE_THIGHS, "zone_thighs"),
                (s.ZONE_ARMS, "zone_arms"),
                (s.ZONE_GLUTES, "zone_glutes"),
            ],
        )

    # Stages 1+ require variant
    if not variant:
        logger.warning("ru_funnel_no_variant", stage=stage, variant=variant)
        return None

    if variant == "thighs":
        return _get_ru_thighs_message(stage, s, video_notes, funnel_photos)

    if variant != "belly":
        logger.warning("ru_funnel_unknown_variant", stage=stage, variant=variant)
        return None

    # --- Belly zone stages ---
    if stage == 1:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_1,
            buttons=[(s.FUNNEL_BUY_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_belly_stage_1", ""),
        )
    elif stage == 2:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_2,
            buttons=[(s.FUNNEL_GET_ACCESS_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_belly_stage_2a", ""),
            extra_photos=[funnel_photos.get("ru_belly_stage_2b", "")],
        )
    elif stage == 3:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_3,
            buttons=[],
            video_note_id=video_notes.get("how_it_works", ""),
        )
    elif stage == 4:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_4,
            buttons=[(s.FUNNEL_TAKE_WORKOUT_BUTTON, "buy_now")],
        )
    elif stage == 5:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_5,
            buttons=[],
            video_note_id=video_notes.get("will_it_suit", ""),
        )
    elif stage == 6:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_6,
            buttons=[(s.FUNNEL_HARD_SELL_BUTTON, "buy_now")],
        )
    elif stage == 7:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_7,
            buttons=[],
        )
    elif stage == 8:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_8,
            buttons=[],
        )
    elif stage == 9:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_9,
            buttons=[(s.FUNNEL_READY_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_belly_stage_9a", ""),
            extra_photos=[funnel_photos.get("ru_belly_stage_9b", "")],
        )
    elif stage == 10:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_10,
            buttons=[(s.FUNNEL_CHECKOUT_BUTTON, "buy_now")],
        )
    elif stage == 11:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_11,
            buttons=[(s.FUNNEL_LAST_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_belly_stage_11", ""),
        )
    elif stage == 12:
        return FunnelMessage(
            text=s.FUNNEL_BELLY_STAGE_12,
            buttons=[(s.FUNNEL_CHANNEL_BUTTON, "")],
            has_url_button=True,
            url="https://t.me/ivanfit_health",
        )

    return None


def _get_ru_thighs_message(stage: int, s, video_notes: dict, funnel_photos: dict) -> FunnelMessage | None:
    """RU thighs zone: 11 stages (1-11)."""
    if stage == 1:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_1,
            buttons=[(s.FUNNEL_BUY_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_thighs_stage_1", ""),
        )
    elif stage == 2:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_2,
            buttons=[(s.FUNNEL_GET_ACCESS_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_thighs_stage_2a", ""),
            extra_photos=[funnel_photos.get("ru_thighs_stage_2b", "")],
        )
    elif stage == 3:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_3,
            buttons=[],
            video_note_id=video_notes.get("how_it_works", ""),
        )
    elif stage == 4:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_4,
            buttons=[(s.FUNNEL_TAKE_WORKOUT_BUTTON, "buy_now")],
        )
    elif stage == 5:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_5,
            buttons=[],
            video_note_id=video_notes.get("will_it_suit", ""),
        )
    elif stage == 6:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_6,
            buttons=[(s.FUNNEL_HARD_SELL_BUTTON, "buy_now")],
        )
    elif stage == 7:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_7,
            buttons=[],
        )
    elif stage == 8:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_8,
            buttons=[],
        )
    elif stage == 9:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_9,
            buttons=[(s.FUNNEL_CHECKOUT_BUTTON, "buy_now")],
        )
    elif stage == 10:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_10,
            buttons=[(s.FUNNEL_LAST_BUTTON, "buy_now")],
            photo_name=funnel_photos.get("ru_thighs_stage_10", ""),
        )
    elif stage == 11:
        return FunnelMessage(
            text=s.FUNNEL_THIGHS_STAGE_11,
            buttons=[(s.FUNNEL_CHANNEL_BUTTON, "")],
            has_url_button=True,
            url="https://t.me/ivanfit_health",
        )

    return None


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

    RU: 13 stages (0-12) with zone branching (variant required for stages 1+).
    EN: 9 stages (0-8) + 2 upsells (9-10).
    AR: 9 stages (0-8) + 2 upsells (9-10).
    Returns None if stage is out of range.
    """
    s = get_strings(language)

    if language == "ru":
        msg = _get_ru_funnel_message(stage, s, variant=variant)
    elif language == "en":
        msg = _get_en_funnel_message(stage, s)
    elif language == "ar":
        msg = _get_ar_funnel_message(stage, s)
    else:
        msg = _get_ar_funnel_message(stage, get_strings("ar"))

    if msg:
        logger.debug("funnel_message_resolved", stage=stage, language=language, variant=variant, has_photo=bool(msg.photo_name), has_video_note=bool(msg.video_note_id), num_buttons=len(msg.buttons))
    return msg
