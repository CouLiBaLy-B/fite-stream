"""Tests for image dimension validation."""

from fitstream.core.interfaces import (
    MAX_UPLOAD_SIZE_MB,
    ValidationError,
    validate_image_dimensions,
    validate_image_upload,
)


class TestImageDimensionValidation:
    """Validate image dimensions against limits."""

    def test_valid_dimensions(self) -> None:
        assert validate_image_dimensions(800, 600) == []

    def test_too_small_width(self) -> None:
        errors = validate_image_dimensions(32, 480)
        assert len(errors) == 1
        assert errors[0].code == "too_small_dimensions"

    def test_too_small_height(self) -> None:
        errors = validate_image_dimensions(800, 32)
        assert len(errors) >= 1  # too_small_dimensions, possibly also suspicious_aspect

    def test_too_large(self) -> None:
        errors = validate_image_dimensions(10000, 10000)
        assert len(errors) >= 1
        assert any(e.code == "too_large_dimensions" for e in errors)

    def test_suspicious_aspect_ratio(self) -> None:
        errors = validate_image_dimensions(10000, 100)
        assert any(e.code == "suspicious_aspect" for e in errors)

    def test_aspect_ratio_ok(self) -> None:
        errors = validate_image_dimensions(1920, 1080)
        assert all(e.code != "suspicious_aspect" for e in errors)

    def test_all_errors_combined(self) -> None:
        errors = validate_image_dimensions(10, 10000)
        assert len(errors) >= 2


class TestImageUploadValidation:
    """Validate uploaded images (extension + size)."""

    def test_valid_jpg(self) -> None:
        assert validate_image_upload("photo.jpg", 1024 * 1024) == []

    def test_valid_png(self) -> None:
        assert validate_image_upload("photo.png", 500 * 1024) == []

    def test_valid_webp(self) -> None:
        assert validate_image_upload("photo.webp", 2048 * 1024) == []

    def test_invalid_extension(self) -> None:
        errors = validate_image_upload("file.pdf", 1024 * 1024)
        assert len(errors) == 1
        assert errors[0].code == "invalid_type"

    def test_no_extension(self) -> None:
        errors = validate_image_upload("file", 1024 * 1024)
        assert len(errors) == 1

    def test_too_large(self) -> None:
        size = int((MAX_UPLOAD_SIZE_MB + 10) * 1024 * 1024)
        errors = validate_image_upload("photo.jpg", size)
        assert any(e.code == "too_large" for e in errors)

    def test_too_small(self) -> None:
        errors = validate_image_upload("photo.jpg", 50)
        assert any(e.code == "too_small" for e in errors)

    def test_multiple_errors(self) -> None:
        size = int((MAX_UPLOAD_SIZE_MB + 10) * 1024 * 1024)
        errors = validate_image_upload("file.exe", size)
        assert len(errors) >= 2


class TestValidationError:
    """ValidationError dataclass."""

    def test_creation(self) -> None:
        err = ValidationError("field", "msg", "code")
        assert err.field == "field"
        assert err.message == "msg"
        assert err.code == "code"
