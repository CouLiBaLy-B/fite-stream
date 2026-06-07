"""Tests for GenerationRequest and GenerationResult dataclasses."""

import pytest
from fitstream.core.interfaces import GenerationRequest, GenerationResult


class TestGenerationRequest:
    """GenerationRequest — unified input for all pipelines."""

    def test_default_values(self) -> None:
        req = GenerationRequest()
        assert req.job_id == ""
        assert req.pipeline == ""
        assert req.image_paths == []
        assert req.prompt == ""
        assert req.width == 832
        assert req.height == 480
        assert req.num_frames == 49
        assert req.num_inference_steps == 30
        assert req.guidance_scale == 5.0
        assert req.fps == 16
        assert req.seed == -1
        assert req.style == "cinematic"
        assert req.preset == "standard"
        assert req.extra == {}

    def test_custom_values(self) -> None:
        req = GenerationRequest(
            job_id="job-123",
            pipeline="animate",
            image_paths=["/path/1.jpg", "/path/2.jpg"],
            prompt="A person walking",
            width=1024,
            height=576,
            num_frames=97,
            num_inference_steps=50,
            guidance_scale=7.0,
            fps=24,
            seed=42,
            style="ghibli",
            preset="high",
            extra={"custom_field": "value"},
        )
        assert req.job_id == "job-123"
        assert req.pipeline == "animate"
        assert req.image_paths == ["/path/1.jpg", "/path/2.jpg"]
        assert req.prompt == "A person walking"
        assert req.width == 1024
        assert req.seed == 42
        assert req.style == "ghibli"
        assert req.extra == {"custom_field": "value"}

    def test_image_paths_default_factory(self) -> None:
        req1 = GenerationRequest()
        req2 = GenerationRequest()
        req1.image_paths.append("test.jpg")
        assert req2.image_paths == []  # Separate instances

    def test_extra_default_factory(self) -> None:
        req1 = GenerationRequest()
        req2 = GenerationRequest()
        req1.extra["key"] = "val"
        assert req2.extra == {}


class TestGenerationResult:
    """GenerationResult — unified output from all pipelines."""

    def test_success_result(self) -> None:
        result = GenerationResult(
            success=True,
            video_path="/output/test.mp4",
            num_frames=49,
            duration_seconds=3.0,
            resolution="832x480",
            generation_time=12.5,
            seed=42,
            prompt_used="A person walking",
            pipeline="animate",
        )
        assert result.success is True
        assert result.video_path == "/output/test.mp4"
        assert result.error is None
        assert result.num_frames == 49
        assert result.generation_time == 12.5
        assert result.pipeline == "animate"

    def test_failure_result(self) -> None:
        result = GenerationResult(
            success=False,
            error="GPU out of memory",
            generation_time=1.2,
            pipeline="animate",
        )
        assert result.success is False
        assert result.video_path == ""
        assert result.error == "GPU out of memory"

    def test_default_values(self) -> None:
        result = GenerationResult(success=True)
        assert result.video_path == ""
        assert result.num_frames == 0
        assert result.duration_seconds == 0.0
        assert result.resolution == ""
        assert result.generation_time == 0.0
        assert result.seed == 0
        assert result.prompt_used == ""
        assert result.pipeline == ""

    def test_metadata(self) -> None:
        result = GenerationResult(
            success=True,
            metadata={"fps": 16, "model": "vace-1.3b"},
        )
        assert result.metadata == {"fps": 16, "model": "vace-1.3b"}

    def test_metadata_default_factory(self) -> None:
        r1 = GenerationResult(success=True)
        r2 = GenerationResult(success=True)
        r1.metadata["key"] = "val"
        assert r2.metadata == {}
