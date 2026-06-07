"""
FitStream API — Pydantic Schemas
"""

from enum import Enum

from pydantic import BaseModel, Field


class StyleEnum(str, Enum):
    cinematic = "cinematic"
    photorealistic = "photorealistic"
    anime = "anime"
    artistic = "artistic"
    documentary = "documentary"
    dreamy = "dreamy"
    warm = "warm"


class PresetEnum(str, Enum):
    draft = "draft"
    standard = "standard"
    high = "high"


class TransitionEnum(str, Enum):
    none = "none"
    crossfade = "crossfade"


class AnimateRequest(BaseModel):
    """Request for single-scene animation."""

    prompt: str = Field(..., description="Text prompt for the animation", min_length=5)
    style: StyleEnum = StyleEnum.cinematic
    preset: PresetEnum = PresetEnum.standard
    seed: int = Field(-1, description="Random seed (-1 for random)")
    num_frames: int | None = Field(None, ge=16, le=128)
    num_inference_steps: int | None = Field(None, ge=5, le=100)
    guidance_scale: float | None = Field(None, ge=1.0, le=20.0)


class StoryRequest(BaseModel):
    """Request for multi-scene story generation."""

    story: str = Field(..., description="Story text to animate", min_length=10)
    style: StyleEnum = StyleEnum.cinematic
    preset: PresetEnum = PresetEnum.standard
    max_scenes: int = Field(5, ge=1, le=8)
    transition: TransitionEnum = TransitionEnum.crossfade


class GenerationResponse(BaseModel):
    """Response for generation requests."""

    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    video_url: str | None = None
    progress: float = 0.0  # 0.0 to 1.0
    generation_time: float | None = None
    error: str | None = None

    # Metadata
    num_frames: int = 0
    duration_seconds: float = 0.0
    resolution: str = ""
    seed: int = 0
    prompt_used: str = ""


class StoryResponse(BaseModel):
    """Response for story generation."""

    job_id: str
    status: str
    video_url: str | None = None
    scenes_completed: int = 0
    scenes_total: int = 0
    progress: float = 0.0
    total_duration: float = 0.0
    generation_time: float | None = None
    error: str | None = None


class GPUStatus(BaseModel):
    """GPU status information."""

    available: bool
    gpu_name: str | None = None
    total_gb: float = 0.0
    free_gb: float = 0.0
    used_gb: float = 0.0
    utilization_pct: float = 0.0
    loaded_model: str | None = None


class TryOnResponse(BaseModel):
    """Response for try-on requests."""

    job_id: str
    status: str
    video_url: str | None = None
    garment_category: str = ""
    generation_time: float | None = None
    error: str | None = None
    num_frames: int = 0
    duration_seconds: float = 0.0
    resolution: str = ""
    seed: int = 0
    prompt_used: str = ""


class LoomResponse(BaseModel):
    """Response for LoomVideo multi-image generation."""

    job_id: str
    status: str
    video_url: str | None = None
    task: str = ""
    num_reference_images: int = 0
    generation_time: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
    gpu: GPUStatus
