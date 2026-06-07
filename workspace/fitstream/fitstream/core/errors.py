"""
FitStream Error Hierarchy
Structured, classifiable errors for production-grade error handling.

Error categories:
  - UserError:   Bad input from the user (400) — not retryable
  - NotFound:    Resource not found (404)
  - RateLimited: Too many requests (429) — retryable after delay
  - ModelError:  AI model failure (500) — may be retryable
  - GPUError:    GPU out of memory / unavailable (503) — retryable
  - StorageError: File system / storage failure (500) — retryable
  - ExternalError: Third-party service failure (502) — retryable
  - InternalError: Unexpected bug (500) — not retryable, needs investigation

Usage:
    from fitstream.core.errors import GPUError, UserError

    try:
        result = model.generate(...)
    except torch.cuda.OutOfMemoryError:
        raise GPUError("GPU out of memory. Try a lower resolution or fewer frames.")
    except ValueError as e:
        raise UserError(f"Invalid parameter: {e}")
"""

from typing import Any


class FitStreamError(Exception):
    """Base exception for all FitStream errors."""

    status_code: int = 500
    error_code: str = "internal_error"
    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """To dict."""
        d = {
            "error": self.error_code,
            "message": self.message,
            "retryable": self.retryable,
            "status_code": self.status_code,
        }
        if self.details:
            d["details"] = self.details
        return d


# ── User errors (client-side, not retryable) ──


class UserError(FitStreamError):
    """Bad input from the user."""

    status_code = 400
    error_code = "bad_request"
    retryable = False


class ValidationError(FitStreamError):
    """Input validation failure."""

    status_code = 422
    error_code = "validation_error"
    retryable = False


class NotFoundError(FitStreamError):
    """Resource not found."""

    status_code = 404
    error_code = "not_found"
    retryable = False


class RateLimitedError(FitStreamError):
    """Too many requests."""

    status_code = 429
    error_code = "rate_limited"
    retryable = True


# ── Server errors (retryable) ──


class ModelError(FitStreamError):
    """AI model loading or inference failure."""

    status_code = 500
    error_code = "model_error"
    retryable = True


class GPUError(FitStreamError):
    """GPU out of memory or unavailable."""

    status_code = 503
    error_code = "gpu_error"
    retryable = True


class StorageError(FitStreamError):
    """File system or storage failure."""

    status_code = 500
    error_code = "storage_error"
    retryable = True


class ExternalError(FitStreamError):
    """Third-party service failure (webhooks, external APIs)."""

    status_code = 502
    error_code = "external_error"
    retryable = True


# ── Server errors (not retryable — bugs) ──


class InternalError(FitStreamError):
    """Unexpected internal error (bug)."""

    status_code = 500
    error_code = "internal_error"
    retryable = False


class PipelineError(FitStreamError):
    """Error within a generation pipeline."""

    status_code = 500
    error_code = "pipeline_error"
    retryable = True

    def __init__(
        self,
        message: str,
        pipeline: str = "",
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.pipeline = pipeline
        self.details["pipeline"] = pipeline


class ConfigError(FitStreamError):
    """Invalid configuration."""

    status_code = 500
    error_code = "config_error"
    retryable = False
