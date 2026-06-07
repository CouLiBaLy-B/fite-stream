"""Tests for analytics engine."""

import time
import pytest
from fitstream.core.analytics import AnalyticsEngine, GenerationEvent


class TestAnalyticsEngine:
    def setup_method(self):
        self.engine = AnalyticsEngine()

    def test_record(self):
        self.engine.record(type="animate", style="cinematic", generation_time=42.0)
        assert self.engine.total_events == 1

    def test_empty_report(self):
        report = self.engine.get_report(hours=24)
        assert report["total_generations"] == 0

    def test_report_with_data(self):
        self.engine.record(type="animate", style="cinematic", generation_time=40.0,
                           num_frames=49, success=True, prompt="test prompt")
        self.engine.record(type="story", style="anime", generation_time=120.0,
                           num_frames=147, success=True, prompt="story test")
        self.engine.record(type="animate", style="cinematic", generation_time=45.0,
                           num_frames=49, success=False, prompt="failed test")

        report = self.engine.get_report(hours=1)
        assert report["total_generations"] == 3
        assert report["successful"] == 2
        assert report["failed"] == 1
        assert report["by_type"]["animate"] == 2
        assert report["by_type"]["story"] == 1
        assert report["by_style"]["cinematic"] == 2
        assert report["generation_time"]["average"] > 0

    def test_top_styles(self):
        for _ in range(5):
            self.engine.record(type="animate", style="cinematic")
        for _ in range(3):
            self.engine.record(type="animate", style="ghibli")
        for _ in range(1):
            self.engine.record(type="animate", style="noir")

        top = self.engine.get_top_styles(limit=2)
        assert len(top) == 2
        assert top[0]["style"] == "cinematic"
        assert top[0]["count"] == 5

    def test_top_types(self):
        self.engine.record(type="animate")
        self.engine.record(type="animate")
        self.engine.record(type="story")

        top = self.engine.get_top_types()
        assert top[0]["type"] == "animate"
        assert top[0]["count"] == 2

    def test_eviction(self):
        engine = AnalyticsEngine(max_events=5)
        for i in range(10):
            engine.record(type="animate", prompt=f"prompt {i}")
        assert engine.total_events == 5

    def test_time_stats(self):
        for t in [10.0, 20.0, 30.0, 40.0, 50.0]:
            self.engine.record(type="animate", generation_time=t, success=True)

        report = self.engine.get_report(hours=1)
        assert report["generation_time"]["average"] == 30.0
        assert report["generation_time"]["min"] == 10.0
        assert report["generation_time"]["max"] == 50.0
        assert report["generation_time"]["p50"] == 30.0

    def test_garment_category(self):
        self.engine.record(type="tryon", garment_category="dress")
        self.engine.record(type="tryon", garment_category="dress")
        self.engine.record(type="tryon", garment_category="shoes")

        report = self.engine.get_report(hours=1)
        assert report["by_garment_category"]["dress"] == 2

    def test_hourly_distribution(self):
        self.engine.record(type="animate")
        report = self.engine.get_report(hours=1)
        assert len(report["hourly_distribution"]) >= 1

    def test_success_rate(self):
        self.engine.record(type="animate", success=True)
        self.engine.record(type="animate", success=True)
        self.engine.record(type="animate", success=False)

        report = self.engine.get_report(hours=1)
        assert abs(report["success_rate"] - 2/3) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
