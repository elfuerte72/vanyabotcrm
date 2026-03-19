import re

# Arabic script range (standard + extensions)
_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")

# Cyrillic script range
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def detect_language(text: str) -> str:
    """Detect language from text using script detection.

    Priority: Arabic > Russian > English (default).
    """
    if _ARABIC_RE.search(text):
        return "ar"
    if _CYRILLIC_RE.search(text):
        return "ru"
    return "en"
