"""Tests for FitStream error hierarchy — structured, classifiable errors."""

import pytest
from fitstream.core.errors import (
    FitStreamError,
    UserError,
    ValidationError,
    NotFoundError,
    RateLimitedError,
    ModelError,
    GPUError,
    StorageError,
    ExternalError,
    InternalError,
    PipelineError,
    ConfigError,
)


class TestErrorHierarchy:
    """Verify the error hierarchy structure and properties."""

    def test_all_errors_inherit_from_fitstream_error(self) -> None:
        classes = [
            UserError, ValidationError, NotFoundError, RateLimitedError,
            ModelError, GPUError, StorageError, ExternalError,
            InternalError, PipelineError, ConfigError,
        ]
        for cls in classes:
            assert issubclass(cls, FitStreamError), f"{cls.__name__} must inherit FitStreamError"

    def test_user_errors_not_retryable(self) -> None:
        for cls in [UserError, ValidationError, NotFoundError]:
            err = cls("test")
            assert err.retryable is False, f"{cls.__name__} should not be retryable"

    def test_server_errors_retryable(self) -> None:
        for cls in [ModelError, GPUError, StorageError, ExternalError, PipelineError]:
            err = cls("test")
            assert err.retryable is True, f"{cls.__name__} should be retryable"

    def test_internal_errors_not_retryable(self) -> None:
        for cls in [InternalError, ConfigError]:
            err = cls("test")
            assert err.retryable is False, f"{cls.__name__} should not be retryable"

    def test_rate_limited_is_retryable(self) -> None:
        assert RateLimitedError("test").retryable is True

    def test_status_codes(self) -> None:
        assert UserError("test").status_code == 400
        assert ValidationError("test").status_code == 422
        assert NotFoundError("test").status_code == 404
        assert RateLimitedError("test").status_code == 429
        assert ModelError("test").status_code == 500
        assert GPUError("test").status_code == 503
        assert StorageError("test").status_code == 500
        assert ExternalError("test").status_code == 502
        assert InternalError("test").status_code == 500
        assert PipelineError("test").status_code == 500
        assert ConfigError("test").status_code == 500

    def test_error_codes(self) -> None:
        assert UserError("test").error_code == "bad_request"
        assert ValidationError("test").error_code == "validation_error"
        assert NotFoundError("test").error_code == "not_found"
        assert RateLimitedError("test").error_code == "rate_limited"
        assert ModelError("test").error_code == "model_error"
        assert GPUError("test").error_code == "gpu_error"
        assert StorageError("test").error_code == "storage_error"
        assert ExternalError("test").error_code == "external_error"
        assert InternalError("test").error_code == "internal_error"
        assert PipelineError("test").error_code == "pipeline_error"
        assert ConfigError("test").error_code == "config_error"


class TestFitStreamErrorFeatures:
    """Test the base error features."""

    def test_to_dict_basic(self) -> None:
        err = UserError("Bad input")
        d = err.to_dict()
        assert d == {
            "error": "bad_request",
            "message": "Bad input",
            "retryable": False,
            "status_code": 400,
        }

    def test_to_dict_with_details(self) -> None:
        err = ValidationError("Invalid field", details={"field": "email", "reason": "required"})
        d = err.to_dict()
        assert d["error"] == "validation_error"
        assert d["message"] == "Invalid field"
        assert d["details"] == {"field": "email", "reason": "required"}

    def test_with_cause(self) -> None:
        original = ValueError("root cause")
        err = ModelError("GPU crash", cause=original)
        assert err.cause is original
        assert err.message == "GPU crash"

    def test_pipeline_error_has_pipeline_name(self) -> None:
        err = PipelineError("Failed", pipeline="animate")
        assert err.pipeline == "animate"
        assert err.details["pipeline"] == "animate"
        assert err.retryable is True

    def test_http_exception_compatible(self) -> None:
        """FitStreamError should be catchable as Exception for HTTP handlers."""
        err = NotFoundError("Not found")
        try:
            raise err
        except Exception as e:
            assert isinstance(e, FitStreamError)
            assert str(e) == "Not found"

    def test_serialization_roundtrip(self) -> None:
        import json
        err = GPUError("OOM", details={"gpu": "RTX 4090", "vram_gb": 24})
        d = err.to_dict()
        serialized = json.dumps(d)
        reloaded = json.loads(serialized)
        assert reloaded["error"] == "gpu_error"
        assert reloaded["retryable"] is True
        assert reloaded["status_code"] == 503
        assert reloaded["details"]["gpu"] == "RTX 4090"


class TestErrorPropagation:
    """Test that errors propagate correctly through the chain."""

    def test_can_raise_and_catch_by_base(self) -> None:
        try:
            raise GPUError("Out of memory")
        except FitStreamError as e:
            assert e.error_code == "gpu_error"
            assert e.status_code == 503

    def test_can_catch_multiple_types(self) -> None:
        caught = []
        for err_cls, msg in [
            (UserError, "bad"),
            (GPUError, "oom"),
            (InternalError, "bug"),
        ]:
            try:
                raise err_cls(msg)
            except FitStreamError as e:
                caught.append(e.error_code)
        assert "bad_request" in caught
        assert "gpu_error" in caught
        assert "internal_error" in caught
