"""Tests for language detection."""

from src.services.language import detect_language


class TestDetectLanguage:
    def test_english_text(self):
        assert detect_language("Hello, how are you?") == "en"

    def test_russian_text(self):
        assert detect_language("Привет, как дела?") == "ru"

    def test_arabic_text(self):
        assert detect_language("مرحبا كيف حالك") == "ar"

    def test_arabic_priority_over_russian(self):
        # Arabic takes priority even if mixed
        assert detect_language("Привет مرحبا") == "ar"

    def test_russian_priority_over_english(self):
        assert detect_language("Hello привет world") == "ru"

    def test_numbers_default_to_english(self):
        assert detect_language("123 456") == "en"

    def test_empty_string(self):
        assert detect_language("") == "en"

    def test_mixed_latin_only(self):
        assert detect_language("male 80 kg 180 cm") == "en"

    def test_cyrillic_single_char(self):
        assert detect_language("д") == "ru"

    def test_arabic_single_char(self):
        assert detect_language("م") == "ar"
