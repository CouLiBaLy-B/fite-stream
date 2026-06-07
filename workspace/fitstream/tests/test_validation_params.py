"""Tests for validation helpers in interfaces.py."""

from fitstream.core.interfaces import (
    MAX_IMAGE_DIMENSION,
    MAX_PROMPT_LENGTH,
    MIN_IMAGE_DIMENSION,
    validate_generation_params,
    validate_prompt,
)


class TestPromptValidation:
    """Validate prompt text input."""

    def test_valid_prompt(self) -> None:
        assert validate_prompt("A person walking in Paris") == []

    def test_empty_prompt(self) -> None:
        errors = validate_prompt("")
        assert len(errors) == 1
        assert errors[0].code == "required"

    def test_whitespace_only(self) -> None:
        errors = validate_prompt("   ")
        assert len(errors) == 1
        assert errors[0].code == "required"

    def test_too_long_prompt(self) -> None:
        long_prompt = "x" * (MAX_PROMPT_LENGTH + 100)
        errors = validate_prompt(long_prompt)
        assert len(errors) == 1
        assert errors[0].code == "too_long"

    def test_valid_with_unicode(self) -> None:
        assert validate_prompt("Une personne marche dans Paris 🎬") == []

    def test_custom_field_name(self) -> None:
        errors = validate_prompt("", field_name="story")
        assert errors[0].field == "story"


class TestGenerationParamsValidation:
    """Validate generation parameters."""

    def test_defaults_valid(self) -> None:
        assert validate_generation_params() == []

    def test_valid_custom_params(self) -> None:
        assert (
            validate_generation_params(
                width=832,
                height=480,
                num_frames=49,
                num_inference_steps=30,
                guidance_scale=5.0,
            )
            == []
        )

    def test_invalid_width(self) -> None:
        errors = validate_generation_params(width=10)
        assert any(e.field == "width" for e in errors)

    def test_invalid_height(self) -> None:
        errors = validate_generation_params(height=10)
        assert any(e.field == "height" for e in errors)

    def test_width_too_large(self) -> None:
        errors = validate_generation_params(width=10000)
        assert any(e.field == "width" for e in errors)

    def test_invalid_num_frames(self) -> None:
        errors = validate_generation_params(num_frames=0)
        assert any(e.field == "num_frames" for e in errors)

    def test_num_frames_too_high(self) -> None:
        errors = validate_generation_params(num_frames=300)
        assert any(e.field == "num_frames" for e in errors)

    def test_invalid_steps(self) -> None:
        errors = validate_generation_params(num_inference_steps=0)
        assert any(e.field == "num_inference_steps" for e in errors)

    def test_steps_too_high(self) -> None:
        errors = validate_generation_params(num_inference_steps=500)
        assert any(e.field == "num_inference_steps" for e in errors)

    def test_invalid_guidance(self) -> None:
        errors = validate_generation_params(guidance_scale=-1)
        assert any(e.field == "guidance_scale" for e in errors)

    def test_guidance_too_high(self) -> None:
        errors = validate_generation_params(guidance_scale=100)
        assert any(e.field == "guidance_scale" for e in errors)

    def test_multiple_errors(self) -> None:
        errors = validate_generation_params(
            width=10,
            height=10000,
            num_frames=500,
            num_inference_steps=300,
            guidance_scale=100,
        )
        assert len(errors) >= 3  # At least 3 invalid fields

    def test_boundary_values(self) -> None:
        # Min boundary
        assert (
            validate_generation_params(
                width=MIN_IMAGE_DIMENSION,
                height=MIN_IMAGE_DIMENSION,
                num_frames=1,
                num_inference_steps=1,
                guidance_scale=0,
            )
            == []
        )
        # Max boundary
        assert (
            validate_generation_params(
                width=MAX_IMAGE_DIMENSION,
                height=MAX_IMAGE_DIMENSION,
                num_frames=256,
                num_inference_steps=200,
                guidance_scale=50,
            )
            == []
        )
