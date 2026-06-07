"""Tests for internationalization."""

import pytest

from fitstream.core.i18n import TRANSLATIONS, I18n, translate_prompt


class TestI18n:
    def test_english_default(self):
        i = I18n("en")
        assert i.t("status.processing") == "Generating..."
        assert i.t("btn.generate") == "Generate"

    def test_french(self):
        i = I18n("fr")
        assert i.t("status.processing") == "En cours de génération..."
        assert i.t("btn.generate") == "Générer"
        assert i.t("app.title") == "FitStream — Animation IA"

    def test_chinese(self):
        i = I18n("zh")
        assert i.t("status.processing") == "生成中..."
        assert i.t("btn.generate") == "生成"

    def test_japanese(self):
        i = I18n("ja")
        assert i.t("btn.generate") == "生成する"

    def test_spanish(self):
        i = I18n("es")
        assert i.t("btn.generate") == "Generar"

    def test_fallback_to_english(self):
        i = I18n("ja")
        # Japanese doesn't have all keys → falls back to English
        assert i.t("error.no_image") == "Please upload an image"

    def test_unknown_key_returns_key(self):
        i = I18n("en")
        assert i.t("nonexistent.key") == "nonexistent.key"

    def test_unknown_language_falls_to_english(self):
        i = I18n("xx")
        assert i.lang == "en"

    def test_get_all(self):
        i = I18n("fr")
        all_msgs = i.get_all()
        assert isinstance(all_msgs, dict)
        assert "btn.generate" in all_msgs
        assert all_msgs["btn.generate"] == "Générer"

    def test_supported_languages(self):
        langs = I18n.supported_languages()
        assert "en" in langs
        assert "fr" in langs
        assert "zh" in langs
        assert "ja" in langs
        assert "es" in langs
        assert len(langs) >= 8


class TestTranslatePrompt:
    def test_english_passthrough(self):
        assert translate_prompt("A woman walks in Paris", "en") == "A woman walks in Paris"

    def test_french_to_english(self):
        result = translate_prompt("une femme marche dans une rue", "fr")
        assert "woman" in result.lower()
        assert "walks" in result.lower()
        assert "street" in result.lower()

    def test_french_colors(self):
        result = translate_prompt("une robe rouge", "fr")
        assert "dress" in result.lower()
        assert "red" in result.lower()

    def test_chinese_basic(self):
        result = translate_prompt("一个女人在花园微笑", "zh")
        assert "woman" in result.lower()
        assert "smiles" in result.lower() or "garden" in result.lower()

    def test_unknown_language_passthrough(self):
        original = "something in unknown language"
        result = translate_prompt(original, "xx")
        assert result == original

    def test_capitalizes_first_letter(self):
        result = translate_prompt("une femme", "fr")
        assert result[0].isupper()


class TestSupportedLanguages:
    def test_all_languages_have_essential_keys(self):
        essential_keys = ["status.processing", "btn.generate"]
        for lang_code in ["en", "fr", "zh"]:
            for key in essential_keys:
                assert key in TRANSLATIONS[lang_code], f"{lang_code} missing {key}"

    def test_english_is_complete(self):
        en = TRANSLATIONS["en"]
        assert len(en) >= 20  # English should have all keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
