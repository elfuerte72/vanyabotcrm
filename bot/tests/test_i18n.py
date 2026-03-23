"""Tests for i18n string modules."""

from src.i18n import get_strings


# Common attrs across all languages
COMMON_ATTRS = [
    "SUBSCRIBE_MESSAGE",
    "ALREADY_CALCULATED",
    "CALCULATING_MENU",
    "BUY_MESSAGE",
    "BUY_BUTTON",
    "RESULTS_CAPTION",
    "REMIND_LATER",
    "NONE_RESPONSE",
    "VIDEO_WORKOUT_RESPONSE",
]

# AR (and RU) still use FUNNEL_DAY_* pattern
AR_FUNNEL_ATTRS = [
    "FUNNEL_DAY_0", "FUNNEL_DAY_0_BUTTON",
    "FUNNEL_DAY_1", "FUNNEL_DAY_1_BUTTON",
    "FUNNEL_DAY_2", "FUNNEL_DAY_2_BUTTONS",
    "FUNNEL_DAY_3", "FUNNEL_DAY_3_BUTTONS",
    "FUNNEL_DAY_4", "FUNNEL_DAY_4_BUTTONS",
    "FUNNEL_DAY_5", "FUNNEL_DAY_5_BUTTONS",
]

# EN uses FUNNEL_STAGE_* pattern (9 stages + 2 upsells)
EN_FUNNEL_ATTRS = [
    *[f"FUNNEL_STAGE_{i}" for i in range(9)],
    *[f"FUNNEL_STAGE_{i}_BUY" for i in range(9)],
    *[f"FUNNEL_STAGE_{i}_QUESTION" for i in range(9)],
    "UPSELL_1", "UPSELL_1_BUY", "UPSELL_1_DECLINE",
    "UPSELL_2", "UPSELL_2_BUY", "UPSELL_2_DECLINE",
]


class TestI18n:
    def test_common_attrs_in_all_languages(self):
        for lang in ("ru", "en", "ar"):
            strings = get_strings(lang)
            for attr in COMMON_ATTRS:
                assert hasattr(strings, attr), f"Missing {attr} in {lang}"
                assert getattr(strings, attr) is not None, f"{attr} is None in {lang}"

    def test_ar_has_funnel_day_attrs(self):
        strings = get_strings("ar")
        for attr in AR_FUNNEL_ATTRS:
            assert hasattr(strings, attr), f"Missing {attr} in ar"

    def test_en_has_funnel_stage_attrs(self):
        strings = get_strings("en")
        for attr in EN_FUNNEL_ATTRS:
            assert hasattr(strings, attr), f"Missing {attr} in en"

    def test_unknown_language_returns_english(self):
        strings = get_strings("fr")
        en_strings = get_strings("en")
        assert strings is en_strings

    def test_ar_button_lists_are_tuple_lists(self):
        strings = get_strings("ar")
        for attr in ("FUNNEL_DAY_2_BUTTONS", "FUNNEL_DAY_3_BUTTONS",
                      "FUNNEL_DAY_4_BUTTONS", "FUNNEL_DAY_5_BUTTONS"):
            buttons = getattr(strings, attr)
            assert isinstance(buttons, list), f"{attr} not list in ar"
            for btn in buttons:
                assert isinstance(btn, tuple), f"Button not tuple in {attr} ar"
                assert len(btn) == 2
