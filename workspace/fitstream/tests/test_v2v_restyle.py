"""Tests for V2V restyling pipeline — no GPU needed."""

import pytest

from fitstream.core.pipelines.v2v_restyle import V2VRestylePipeline, V2VResult


class TestV2VRestylePipeline:
    def test_init(self):
        pipeline = V2VRestylePipeline()
        assert pipeline is not None

    def test_recommended_strengths(self):
        s = V2VRestylePipeline.RECOMMENDED_STRENGTHS
        assert "ghibli" in s
        assert "cyberpunk" in s
        assert 0 < s["ghibli"] < 1
        # Stronger styles should have higher strength
        assert s["cyberpunk"] > s["warm"]

    def test_result_dataclass(self):
        r = V2VResult(
            video_path="/out.mp4",
            source_path="/in.mp4",
            style="Ghibli",
            strength=0.7,
            num_frames=49,
            duration_seconds=3.0,
            resolution="832x480",
            generation_time=42.0,
            seed=123,
            prompt_used="test",
            success=True,
        )
        assert r.success is True
        assert r.strength == 0.7

    def test_failed_result(self):
        r = V2VResult(
            video_path="",
            source_path="/in.mp4",
            style="Noir",
            strength=0.7,
            num_frames=0,
            duration_seconds=0,
            resolution="",
            generation_time=0,
            seed=0,
            prompt_used="",
            success=False,
            error="OOM",
        )
        assert r.success is False
        assert r.error == "OOM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
