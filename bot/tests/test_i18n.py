"""Tests for i18n string modules."""

from src.i18n import get_strings


REQUIRED_ATTRS = [
    "SUBSCRIBE_MESSAGE",
    "ALREADY_CALCULATED",
    "CALCULATING_MENU",
    "BUY_MESSAGE",
    "BUY_BUTTON",
    "RESULTS_CAPTION",
    "REMIND_LATER",
    "NONE_RESPONSE",
    "VIDEO_WORKOUT_RESPONSE",
    "FUNNEL_DAY_0",
    "FUNNEL_DAY_0_BUTTON",
    "FUNNEL_DAY_1",
    "FUNNEL_DAY_1_BUTTON",
    "FUNNEL_DAY_2",
    "FUNNEL_DAY_2_BUTTONS",
    "FUNNEL_DAY_3",
    "FUNNEL_DAY_3_BUTTONS",
    "FUNNEL_DAY_4",
    "FUNNEL_DAY_4_BUTTONS",
    "FUNNEL_DAY_5",
    "FUNNEL_DAY_5_BUTTONS",
]


class TestI18n:
    def test_all_languages_have_required_strings(self):
        for lang in ("ru", "en", "ar"):
            strings = get_strings(lang)
            for attr in REQUIRED_ATTRS:
                assert hasattr(strings, attr), f"Missing {attr} in {lang}"
                val = getattr(strings, attr)
                assert val is not None, f"{attr} is None in {lang}"

    def test_unknown_language_returns_english(self):
        strings = get_strings("fr")
        en_strings = get_strings("en")
        assert strings is en_strings

    def test_button_lists_are_tuple_lists(self):
        for lang in ("ru", "en", "ar"):
            strings = get_strings(lang)
            for attr in ("FUNNEL_DAY_2_BUTTONS", "FUNNEL_DAY_3_BUTTONS",
                          "FUNNEL_DAY_4_BUTTONS", "FUNNEL_DAY_5_BUTTONS"):
                buttons = getattr(strings, attr)
                assert isinstance(buttons, list), f"{attr} not list in {lang}"
                for btn in buttons:
                    assert isinstance(btn, tuple), f"Button not tuple in {attr} {lang}"
                    assert len(btn) == 2
