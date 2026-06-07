"""Tests for the try-on pipeline utilities — no GPU needed."""

import pytest
from fitstream.core.pipelines.tryon import (
    detect_garment_category,
    build_tryon_prompt,
    GARMENT_CATEGORIES,
)


class TestDetectCategory:
    def test_upper_body(self):
        assert detect_garment_category("a blue cotton t-shirt") == "upper"
        assert detect_garment_category("elegant silk blouse") == "upper"
        assert detect_garment_category("warm winter jacket") == "upper"
    
    def test_lower_body(self):
        assert detect_garment_category("dark blue jeans") == "lower"
        assert detect_garment_category("pleated skirt") == "lower"
        assert detect_garment_category("cargo shorts") == "lower"
    
    def test_dress(self):
        assert detect_garment_category("a red evening dress") == "dress"
        assert detect_garment_category("casual jumpsuit") == "dress"
    
    def test_shoes(self):
        assert detect_garment_category("white sneakers") == "shoes"
        assert detect_garment_category("leather boots") == "shoes"
    
    def test_accessories(self):
        assert detect_garment_category("straw hat") == "accessories"
        assert detect_garment_category("gold necklace") == "accessories"
        assert detect_garment_category("leather bag") == "accessories"
    
    def test_fallback(self):
        assert detect_garment_category("something unknown") == "upper"


class TestBuildTryonPrompt:
    def test_basic_prompt(self):
        result = build_tryon_prompt("a red silk dress", category="dress")
        assert "red silk dress" in result
        assert "wearing" in result.lower()
    
    def test_with_action(self):
        result = build_tryon_prompt(
            "leather jacket", category="upper",
            action="riding a motorcycle"
        )
        assert "riding a motorcycle" in result
    
    def test_auto_category(self):
        result = build_tryon_prompt("white sneakers", category="auto")
        assert "sneakers" in result.lower()
    
    def test_style_applied(self):
        result = build_tryon_prompt("blue jeans", style="anime")
        assert "Anime" in result or "anime" in result


class TestGarmentCategories:
    def test_all_categories_have_fields(self):
        for key, cat in GARMENT_CATEGORIES.items():
            assert "label" in cat
            assert "keywords" in cat
            assert "mask_hint" in cat
            assert len(cat["keywords"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
