"""Tests for structured error hierarchy."""

import pytest

from fitstream.core.errors import (
    ConfigError,
    ExternalError,
    FitStreamError,
    GPUError,
    InternalError,
    ModelError,
    NotFoundError,
    PipelineError,
    RateLimitedError,
    StorageError,
    UserError,
    ValidationError,
)


class TestErrorHierarchy:
    """All custom errors must be FitStreamError subclasses."""

    def test_base_is_exception(self):
        assert issubclass(FitStreamError, Exception)

    @pytest.mark.parametrize(
        "cls,code,status,retryable",
        [
            (UserError, "bad_request", 400, False),
            (ValidationError, "validation_error", 422, False),
            (NotFoundError, "not_found", 404, False),
            (RateLimitedError, "rate_limited", 429, True),
            (ModelError, "model_error", 500, True),
            (GPUError, "gpu_error", 503, True),
            (StorageError, "storage_error", 500, True),
            (ExternalError, "external_error", 502, True),
            (InternalError, "internal_error", 500, False),
            (PipelineError, "pipeline_error", 500, True),
            (ConfigError, "config_error", 500, False),
        ],
    )
    def test_error_attributes(self, cls, code, status, retryable):
        err = cls("test message")
        assert isinstance(err, FitStreamError)
        assert err.error_code == code
        assert err.status_code == status
        assert err.retryable == retryable
        assert err.message == "test message"
        assert str(err) == "test message"


class TestErrorSerialization:
    def test_to_dict_basic(self):
        err = UserError("bad input")
        d = err.to_dict()
        assert d["error"] == "bad_request"
        assert d["message"] == "bad input"
        assert d["status_code"] == 400
        assert d["retryable"] is False
        assert "details" not in d  # empty details omitted

    def test_to_dict_with_details(self):
        err = ValidationError("invalid", details={"field": "prompt", "reason": "too short"})
        d = err.to_dict()
        assert d["details"]["field"] == "prompt"

    def test_pipeline_error_includes_pipeline(self):
        err = PipelineError("OOM", pipeline="animate")
        assert err.pipeline == "animate"
        d = err.to_dict()
        assert d["details"]["pipeline"] == "animate"

    def test_cause_preserved(self):
        original = ValueError("original cause")
        err = ModelError("model failed", cause=original)
        assert err.cause is original

    def test_gpu_error_retryable(self):
        err = GPUError("CUDA OOM")
        assert err.retryable is True
        assert err.status_code == 503


class TestErrorInPractice:
    def test_raise_and_catch_specific(self):
        with pytest.raises(GPUError) as exc_info:
            raise GPUError("out of memory")
        assert "memory" in str(exc_info.value)

    def test_catch_as_base(self):
        """All FitStreamError subclasses caught by the base class."""
        with pytest.raises(FitStreamError):
            raise PipelineError("failed", pipeline="tryon")

    def test_not_caught_by_unrelated(self):
        """FitStreamError is NOT a ValueError."""
        with pytest.raises(GPUError):
            try:
                raise GPUError("oom")
            except ValueError:
                pytest.fail("Should not catch as ValueError")


class TestErrorHandlerIntegration:
    """Test that the error handler returns proper JSON responses."""

    def test_fitstream_error_returns_json(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from fitstream.api.app_factory import create_app
        from fitstream.core.errors import UserError

        app = create_app()

        @app.get("/test-error")
        async def trigger_error():
            raise UserError("test user error", details={"field": "prompt"})

        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.get("/test-error")
            assert r.status_code == 400
            body = r.json()
            assert body["error"] == "bad_request"
            assert body["message"] == "test user error"
            assert body["retryable"] is False

    def test_unhandled_error_returns_500(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from fitstream.api.app_factory import create_app

        app = create_app()

        @app.get("/test-crash")
        async def trigger_crash():
            raise RuntimeError("unexpected bug")

        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.get("/test-crash")
            assert r.status_code == 500
            body = r.json()
            assert body["error"] == "internal_error"
            # Must NOT leak the original error message to the client
            assert "bug" not in body["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
