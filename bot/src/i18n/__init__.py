"""i18n helper — get localized strings by language code."""

from __future__ import annotations

from types import ModuleType

from src.i18n import ar, en, ru

_MODULES: dict[str, ModuleType] = {
    "ru": ru,
    "en": en,
    "ar": ar,
}


def get_strings(language: str) -> ModuleType:
    """Return the i18n module for the given language code."""
    return _MODULES.get(language, en)
