"""Tests for style transfer pipeline — no GPU needed."""

import pytest
from fitstream.core.pipelines.style_transfer import (
    STYLE_PRESETS,
    get_style_prompt,
    StyleTransferPipeline,
)


class TestStylePresets:
    def test_all_presets_have_required_fields(self):
        for name, preset in STYLE_PRESETS.items():
            assert "label" in preset, f"{name} missing label"
            assert "prefix" in preset, f"{name} missing prefix"
            assert "suffix" in preset, f"{name} missing suffix"
            assert "negative" in preset, f"{name} missing negative"
    
    def test_preset_count(self):
        assert len(STYLE_PRESETS) >= 10

    def test_list_styles(self):
        styles = StyleTransferPipeline.list_styles()
        assert isinstance(styles, dict)
        assert "ghibli" in styles
        assert "cyberpunk" in styles
        assert styles["ghibli"] == "Studio Ghibli"


class TestGetStylePrompt:
    def test_preset_style(self):
        result = get_style_prompt("A woman walks in a garden", "ghibli")
        assert "Ghibli" in result
        assert "woman walks" in result
        assert "Miyazaki" in result
    
    def test_custom_style(self):
        result = get_style_prompt(
            "A person smiling",
            "custom",
            "Dark gothic Victorian painting",
        )
        assert "gothic" in result.lower()
        assert "person smiling" in result
    
    def test_unknown_style_treated_as_modifier(self):
        result = get_style_prompt("A person", "retro vaporwave")
        assert "retro vaporwave" in result
    
    def test_all_presets_produce_output(self):
        for style_name in STYLE_PRESETS:
            result = get_style_prompt("test scene", style_name)
            assert len(result) > len("test scene")
    
    def test_noir_style(self):
        result = get_style_prompt("A detective walks into a bar", "noir")
        assert "noir" in result.lower()
        assert "shadow" in result.lower()
    
    def test_cyberpunk_style(self):
        result = get_style_prompt("City at night", "cyberpunk")
        assert "neon" in result.lower()


class TestStyleTransferPipeline:
    def test_pipeline_init(self):
        # Should init without GPU
        pipeline = StyleTransferPipeline()
        assert pipeline is not None
    
    def test_list_styles_static(self):
        styles = StyleTransferPipeline.list_styles()
        assert len(styles) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
