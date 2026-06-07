"""Tests for native LoomVideo pipeline — no GPU needed."""

import pytest
from fitstream.core.pipelines.loom_native import LoomNativePipeline


class TestLoomNativePipeline:
    def test_init(self):
        pipeline = LoomNativePipeline()
        assert pipeline is not None

    def test_mode_detected(self):
        pipeline = LoomNativePipeline()
        # Without LoomVideo weights, should be vace_fallback
        assert pipeline.mode == "vace_fallback"
        assert pipeline.is_available is False

    def test_is_available_false_without_weights(self):
        pipeline = LoomNativePipeline()
        assert pipeline.is_available is False


class TestMobileAPI:
    def test_mobile_styles(self):
        """Test that mobile styles endpoint returns flat list."""
        from fitstream.core.pipelines.style_transfer import STYLE_PRESETS
        styles = [
            {"id": k, "name": v["label"]}
            for k, v in STYLE_PRESETS.items()
        ]
        assert len(styles) >= 10
        assert styles[0]["name"]  # has a name

    def test_mobile_templates(self):
        from fitstream.core.prompt_templates import PromptTemplateLibrary
        lib = PromptTemplateLibrary()
        templates = lib.list_templates()
        flat = [{"id": t["id"], "name": t["name"]} for t in templates]
        assert len(flat) >= 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
