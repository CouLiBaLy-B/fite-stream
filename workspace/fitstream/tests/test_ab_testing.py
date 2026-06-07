"""Tests for A/B testing pipeline — no GPU needed."""

import pytest

from fitstream.core.ab_testing import ABTestingPipeline, ABTestResult, Variant


class TestVariant:
    def test_success(self):
        v = Variant(id="v1", label="Test", video_path="/v.mp4", success=True)
        assert v.success is True

    def test_failed(self):
        v = Variant(id="v2", label="Test", success=False, error="OOM")
        assert v.error == "OOM"


class TestABTestResult:
    def test_to_dict(self):
        result = ABTestResult(
            test_id="t1",
            test_type="styles",
            variants=[
                Variant(id="v1", label="Style A", success=True, style="ghibli"),
                Variant(id="v2", label="Style B", success=False, style="noir", error="OOM"),
            ],
            total_time=60.0,
            num_successful=1,
            output_dir="/out",
        )
        d = result.to_dict()
        assert d["test_id"] == "t1"
        assert d["test_type"] == "styles"
        assert d["num_successful"] == 1
        assert d["num_total"] == 2
        assert len(d["variants"]) == 2

    def test_empty(self):
        result = ABTestResult(
            test_id="t2",
            test_type="prompts",
            variants=[],
            total_time=0,
            num_successful=0,
            output_dir="/out",
        )
        assert result.to_dict()["num_total"] == 0


class TestABTestingPipeline:
    def test_init(self):
        ab = ABTestingPipeline()
        assert ab is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
