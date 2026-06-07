"""
FitStream Interfaces (Protocols)
Defines the contracts that all components must follow.

This is the foundation of SOLID compliance:
  - Every pipeline implements GenerationPipeline
  - Every store implements VideoStore
  - Every model loader implements ModelLoader
  - Protocols allow structural subtyping (duck typing with type safety)

Usage:
    class MyPipeline:
        def generate(self, request: GenerationRequest) -> GenerationResult:
            ...

    # Type checker verifies this satisfies GenerationPipeline
    pipeline: GenerationPipeline = MyPipeline()
"""

from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# ═══════════════════════════════════════════════════════════
# Common Data Types
# ═══════════════════════════════════════════════════════════


@dataclass
class GenerationRequest:
    """Unified request for all generation pipelines."""

    # Identity
    job_id: str = ""
    pipeline: str = ""  # animate, story, tryon, compose, style, v2v, realtime

    # Inputs
    image_paths: list[str] = field(default_factory=list)
    prompt: str = ""

    # Generation params
    width: int = 832
    height: int = 480
    num_frames: int = 49
    num_inference_steps: int = 30
    guidance_scale: float = 5.0
    fps: int = 16
    seed: int = -1

    # Style & quality
    style: str = "cinematic"
    preset: str = "standard"

    # Pipeline-specific params
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Unified result from all generation pipelines."""

    success: bool
    video_path: str = ""
    error: str | None = None

    # Metadata
    num_frames: int = 0
    duration_seconds: float = 0.0
    resolution: str = ""
    generation_time: float = 0.0
    seed: int = 0
    prompt_used: str = ""
    pipeline: str = ""

    # Extra
    metadata: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# Protocol Interfaces
# ═══════════════════════════════════════════════════════════


@runtime_checkable
class GenerationPipeline(Protocol):
    """
    Interface for all video generation pipelines.

    Every pipeline (animate, story, tryon, etc.) should satisfy
    this protocol for polymorphic usage.
    """

    def generate(self, request: GenerationRequest) -> GenerationResult: ...


@runtime_checkable
class VideoStore(Protocol):
    """Interface for video storage backends."""

    def save(self, video_path: str, metadata: dict[str, Any]) -> str: ...

    def get(self, video_id: str) -> str | None: ...

    def delete(self, video_id: str) -> bool: ...

    def list(self, limit: int = 20, offset: int = 0) -> builtins.list[dict[str, Any]]: ...


@runtime_checkable
class ModelLoader(Protocol):
    """Interface for AI model loading backends."""

    def load(self, model_key: str) -> Any: ...

    def unload(self) -> None:
        """Unload all models from memory."""
        ...

    def is_loaded(self, model_key: str) -> bool: ...

    def get_status(self) -> dict[str, Any]:
        """Get model/GPU status."""
        ...


@runtime_checkable
class JobManager(Protocol):
    """Interface for job queue backends."""

    def create(self, job_type: str, params: dict[str, Any]) -> str: ...

    def get(self, job_id: str) -> dict[str, Any] | None: ...

    def update(self, job_id: str, **kwargs) -> None: ...

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]: ...


@runtime_checkable
class ImagePreprocessor(Protocol):
    """Interface for image preprocessing."""

    def validate(self, image_path: str) -> list[str]: ...

    def prepare(self, image_path: str, width: int, height: int) -> Any: ...


@runtime_checkable
class Exporter(Protocol):
    """Interface for video export backends."""

    def export(self, video_path: str, output_path: str, format: str, **kwargs) -> bool: ...


# ═══════════════════════════════════════════════════════════
# Input Validation
# ═══════════════════════════════════════════════════════════

MAX_UPLOAD_SIZE_MB = 50
ALLOWED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_TYPES = {".mp4", ".webm", ".mov", ".avi"}
MAX_IMAGE_DIMENSION = 8192
MIN_IMAGE_DIMENSION = 64
MAX_PROMPT_LENGTH = 4000
MAX_STORY_LENGTH = 10000


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    message: str
    code: str = "invalid"


def validate_image_upload(
    filename: str,
    file_size_bytes: int,
    content_type: str = "",
) -> list[ValidationError]:
    """
    Validate an uploaded image file.
    Returns list of errors (empty = valid).
    """
    errors = []

    # File extension
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_TYPES:
        errors.append(
            ValidationError(
                "file",
                f"Invalid image type: {ext}. Allowed: {ALLOWED_IMAGE_TYPES}",
                "invalid_type",
            )
        )

    # File size
    size_mb = file_size_bytes / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        errors.append(
            ValidationError(
                "file",
                f"File too large: {size_mb:.1f}MB. Max: {MAX_UPLOAD_SIZE_MB}MB",
                "too_large",
            )
        )

    if file_size_bytes < 100:
        errors.append(
            ValidationError(
                "file",
                "File too small (likely empty or corrupt)",
                "too_small",
            )
        )

    return errors


def validate_image_dimensions(
    width: int,
    height: int,
    filename: str = "",
) -> list[ValidationError]:
    """
    Validate image dimensions against limits.
    Call AFTER reading actual dimensions with PIL.
    """
    errors = []

    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        errors.append(
            ValidationError(
                "file",
                f"Image too small: {width}x{height}. Min: {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}",
                "too_small_dimensions",
            )
        )

    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        errors.append(
            ValidationError(
                "file",
                f"Image too large: {width}x{height}. Max: {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}",
                "too_large_dimensions",
            )
        )

    # Check aspect ratio sanity
    if width > 0 and height > 0:
        ratio = max(width, height) / min(width, height)
        if ratio > 20:
            errors.append(
                ValidationError(
                    "file",
                    f"Suspicious aspect ratio: {ratio:.1f}:1",
                    "suspicious_aspect",
                )
            )

    return errors


def validate_prompt(prompt: str, field_name: str = "prompt") -> list[ValidationError]:
    errors = []

    if not prompt or not prompt.strip():
        errors.append(ValidationError(field_name, "Prompt is required", "required"))
    elif len(prompt) > MAX_PROMPT_LENGTH:
        errors.append(
            ValidationError(
                field_name,
                f"Prompt too long: {len(prompt)} chars. Max: {MAX_PROMPT_LENGTH}",
                "too_long",
            )
        )

    return errors


def validate_generation_params(
    width: int = 832,
    height: int = 480,
    num_frames: int = 49,
    num_inference_steps: int = 30,
    guidance_scale: float = 5.0,
) -> list[ValidationError]:
    """Validate generation parameters."""
    errors = []

    if width < MIN_IMAGE_DIMENSION or width > MAX_IMAGE_DIMENSION:
        errors.append(
            ValidationError("width", f"Width must be {MIN_IMAGE_DIMENSION}-{MAX_IMAGE_DIMENSION}")
        )
    if height < MIN_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        errors.append(
            ValidationError("height", f"Height must be {MIN_IMAGE_DIMENSION}-{MAX_IMAGE_DIMENSION}")
        )
    if num_frames < 1 or num_frames > 256:
        errors.append(ValidationError("num_frames", "Frames must be 1-256"))
    if num_inference_steps < 1 or num_inference_steps > 200:
        errors.append(ValidationError("num_inference_steps", "Steps must be 1-200"))
    if guidance_scale < 0 or guidance_scale > 50:
        errors.append(ValidationError("guidance_scale", "Guidance must be 0-50"))

    return errors
