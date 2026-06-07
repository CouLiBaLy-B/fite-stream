"""
FitStream API — Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


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
    num_frames: Optional[int] = Field(None, ge=16, le=128)
    num_inference_steps: Optional[int] = Field(None, ge=5, le=100)
    guidance_scale: Optional[float] = Field(None, ge=1.0, le=20.0)


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
    video_url: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    generation_time: Optional[float] = None
    error: Optional[str] = None
    
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
    video_url: Optional[str] = None
    scenes_completed: int = 0
    scenes_total: int = 0
    progress: float = 0.0
    total_duration: float = 0.0
    generation_time: Optional[float] = None
    error: Optional[str] = None


class GPUStatus(BaseModel):
    """GPU status information."""
    available: bool
    gpu_name: Optional[str] = None
    total_gb: float = 0.0
    free_gb: float = 0.0
    used_gb: float = 0.0
    utilization_pct: float = 0.0
    loaded_model: Optional[str] = None


class TryOnResponse(BaseModel):
    """Response for try-on requests."""
    job_id: str
    status: str
    video_url: Optional[str] = None
    garment_category: str = ""
    generation_time: Optional[float] = None
    error: Optional[str] = None
    num_frames: int = 0
    duration_seconds: float = 0.0
    resolution: str = ""
    seed: int = 0
    prompt_used: str = ""


class LoomResponse(BaseModel):
    """Response for LoomVideo multi-image generation."""
    job_id: str
    status: str
    video_url: Optional[str] = None
    task: str = ""
    num_reference_images: int = 0
    generation_time: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str
    gpu: GPUStatus
