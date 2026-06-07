"""Tests for real-time pipeline — no GPU needed."""

import pytest
from fitstream.core.pipelines.realtime import RealTimePipeline, RealTimeConfig, RealTimeResult


class TestRealTimeConfig:
    def test_defaults(self):
        c = RealTimeConfig()
        assert c.target_fps == 24.0
        assert c.fallback_steps == 8
        assert c.fallback_width == 512

    def test_kv_cache_settings(self):
        c = RealTimeConfig()
        assert c.kv_cache_size == 128
        assert c.garment_switch_frames == 4


class TestRealTimePipeline:
    def test_init(self):
        p = RealTimePipeline()
        assert p is not None

    def test_mode_fallback(self):
        p = RealTimePipeline()
        assert p.mode == "fast_fallback"
        assert p.is_realtime is False

    def test_expected_fps(self):
        p = RealTimePipeline()
        assert p.expected_fps == 3.0  # fallback mode

    def test_status(self):
        p = RealTimePipeline()
        status = p.get_status()
        assert status["mode"] == "fast_fallback"
        assert status["is_realtime"] is False
        assert "fallback_config" in status
        assert status["fallback_config"]["steps"] == 8

    def test_switch_garment_noop_in_fallback(self):
        p = RealTimePipeline()
        # Should not raise, just warn
        p.switch_garment("garment.jpg", "red dress")


class TestRealTimeResult:
    def test_success(self):
        r = RealTimeResult(
            video_path="/out.mp4", fps_achieved=3.2, num_frames=17,
            duration_seconds=1.0, generation_time=5.3,
            is_realtime=False, latency_ms=312, seed=42, success=True,
        )
        assert r.success is True
        assert r.fps_achieved == 3.2

    def test_failure(self):
        r = RealTimeResult(
            video_path="", fps_achieved=0, num_frames=0,
            duration_seconds=0, generation_time=0,
            is_realtime=False, latency_ms=0, seed=0,
            success=False, error="OOM",
        )
        assert r.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
