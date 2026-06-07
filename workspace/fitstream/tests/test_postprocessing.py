"""Tests for video post-processing — no video files needed for these tests."""

import pytest

from fitstream.core.postprocessing import COLOR_GRADE_PRESETS, PostProcessor


class TestColorPresets:
    def test_all_presets_defined(self):
        expected = [
            "warm",
            "cool",
            "vintage",
            "cinematic",
            "vibrant",
            "desaturated",
            "sepia",
            "noir",
        ]
        for name in expected:
            assert name in COLOR_GRADE_PRESETS, f"Missing preset: {name}"

    def test_preset_count(self):
        assert len(COLOR_GRADE_PRESETS) >= 8

    def test_list_presets(self):
        presets = PostProcessor.list_color_presets()
        assert isinstance(presets, dict)
        assert "cinematic" in presets
        assert presets["cinematic"] == "Cinematic"


class TestPostProcessorInit:
    def test_init(self):
        pp = PostProcessor()
        assert pp is not None

    def test_missing_input_upscale(self):
        pp = PostProcessor()
        result = pp.upscale("/nonexistent.mp4", "/tmp/out.mp4")
        assert result.success is False

    def test_missing_input_color_grade(self):
        pp = PostProcessor()
        result = pp.color_grade("/nonexistent.mp4", "/tmp/out.mp4", "cinematic")
        assert result.success is False

    def test_invalid_preset(self):
        pp = PostProcessor()
        result = pp.color_grade("/nonexistent.mp4", "/tmp/out.mp4", "nonexistent_preset")
        assert result.success is False
        assert "Unknown preset" in result.error

    def test_missing_input_slow_motion(self):
        pp = PostProcessor()
        result = pp.slow_motion("/nonexistent.mp4", "/tmp/out.mp4")
        assert result.success is False

    def test_missing_input_stabilize(self):
        pp = PostProcessor()
        result = pp.stabilize("/nonexistent.mp4", "/tmp/out.mp4")
        # stabilize uses two-pass ffmpeg — may fail differently if ffmpeg not found
        assert result.success is False or result.error is not None

    def test_missing_input_watermark(self):
        pp = PostProcessor()
        result = pp.add_watermark("/nonexistent.mp4", "/tmp/out.mp4")
        assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
