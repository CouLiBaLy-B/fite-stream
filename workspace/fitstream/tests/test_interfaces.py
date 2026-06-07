"""Tests for interfaces, protocols, and validation."""

import pytest

from fitstream.core.interfaces import (
    MAX_UPLOAD_SIZE_MB,
    GenerationPipeline,
    GenerationRequest,
    GenerationResult,
    JobManager,
    ValidationError,
    VideoStore,
    validate_generation_params,
    validate_image_upload,
    validate_prompt,
)


class TestGenerationRequest:
    def test_defaults(self):
        r = GenerationRequest()
        assert r.width == 832
        assert r.height == 480
        assert r.num_frames == 49
        assert r.seed == -1

    def test_custom(self):
        r = GenerationRequest(
            job_id="test",
            pipeline="animate",
            image_paths=["a.jpg"],
            prompt="walk in park",
            width=512,
            height=512,
        )
        assert r.pipeline == "animate"
        assert len(r.image_paths) == 1


class TestGenerationResult:
    def test_success(self):
        r = GenerationResult(success=True, video_path="/out.mp4", seed=42)
        assert r.success
        assert r.error is None

    def test_failure(self):
        r = GenerationResult(success=False, error="GPU OOM")
        assert not r.success
        assert r.error == "GPU OOM"


class TestProtocols:
    def test_generation_pipeline_protocol(self):
        """A class with generate(request)->result satisfies the protocol."""

        class FakePipeline:
            def generate(self, request: GenerationRequest) -> GenerationResult:
                return GenerationResult(success=True)

        assert isinstance(FakePipeline(), GenerationPipeline)

    def test_non_pipeline_rejected(self):
        """A class without generate() does NOT satisfy the protocol."""

        class NotAPipeline:
            def run(self):
                pass

        assert not isinstance(NotAPipeline(), GenerationPipeline)

    def test_video_store_protocol(self):
        class FakeStore:
            def save(self, video_path, metadata):
                return "id1"

            def get(self, video_id):
                return None

            def delete(self, video_id):
                return True

            def list(self, limit=20, offset=0):
                return []

        assert isinstance(FakeStore(), VideoStore)

    def test_job_manager_protocol(self):
        class FakeJobs:
            def create(self, job_type, params):
                return "j1"

            def get(self, job_id):
                return None

            def update(self, job_id, **kw):
                pass

            def list_jobs(self, limit=50):
                return []

        assert isinstance(FakeJobs(), JobManager)


class TestValidateImageUpload:
    def test_valid_jpg(self):
        errors = validate_image_upload("photo.jpg", 1_000_000)
        assert len(errors) == 0

    def test_valid_png(self):
        errors = validate_image_upload("image.png", 500_000)
        assert len(errors) == 0

    def test_invalid_extension(self):
        errors = validate_image_upload("virus.exe", 1000)
        assert len(errors) == 1
        assert errors[0].code == "invalid_type"

    def test_too_large(self):
        errors = validate_image_upload("big.jpg", MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        assert any(e.code == "too_large" for e in errors)

    def test_too_small(self):
        errors = validate_image_upload("tiny.jpg", 50)
        assert any(e.code == "too_small" for e in errors)

    def test_webp_allowed(self):
        assert len(validate_image_upload("photo.webp", 10000)) == 0


class TestValidatePrompt:
    def test_valid(self):
        assert len(validate_prompt("A person walking in a park")) == 0

    def test_empty(self):
        errors = validate_prompt("")
        assert len(errors) == 1
        assert errors[0].code == "required"

    def test_whitespace_only(self):
        errors = validate_prompt("   ")
        assert len(errors) == 1

    def test_too_long(self):
        errors = validate_prompt("x" * 5000)
        assert any(e.code == "too_long" for e in errors)


class TestValidateGenerationParams:
    def test_valid_defaults(self):
        assert len(validate_generation_params()) == 0

    def test_invalid_width(self):
        errors = validate_generation_params(width=10)
        assert len(errors) == 1

    def test_invalid_steps(self):
        errors = validate_generation_params(num_inference_steps=500)
        assert len(errors) == 1

    def test_multiple_errors(self):
        errors = validate_generation_params(width=1, height=99999, num_frames=-1)
        assert len(errors) == 3


class TestValidationError:
    def test_fields(self):
        e = ValidationError("image", "Too large", "too_large")
        assert e.field == "image"
        assert e.code == "too_large"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
