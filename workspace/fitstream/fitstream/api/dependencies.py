"""
FitStream API Dependencies — Dependency Injection via FastAPI Depends().

This replaces global mutable state with proper DI:
  - JobQueue (persistent) replaces the dict global
  - ModelManager is a singleton with proper lifecycle
  - Config is loaded once and injected everywhere
  - Rate limiter and auth are applied per-route

Usage in routes:
    from fitstream.api.dependencies import get_job_queue, get_model_manager

    @router.post("/animate")
    async def animate(
        jobs: JobQueue = Depends(get_job_queue),
        models: ModelManager = Depends(get_model_manager),
    ):
        ...
"""

import os
import shutil
import uuid
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, Request, UploadFile
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.job_queue import JobQueue, JobStatus
from fitstream.core.interfaces import validate_image_upload, validate_image_dimensions
from fitstream.api.middleware import rate_limiter, api_auth, metrics


# ═══════════════════════════════════════════════════════════
# Paths (constants)
# ═══════════════════════════════════════════════════════════

UPLOAD_DIR = "./uploads"
OUTPUT_DIR = "./outputs"


def _ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("./jobs", exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Singleton dependencies — cached via @lru_cache
# No global mutable state — thread-safe and testable
# ═══════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_app_config() -> FitStreamConfig:
    """Get the application config (cached singleton)."""
    return get_config()


@lru_cache(maxsize=1)
def get_model_manager() -> ModelManager:
    """Get the model manager (cached singleton, lazy init)."""
    return ModelManager(get_app_config())


@lru_cache(maxsize=1)
def get_job_queue() -> JobQueue:
    """Get the persistent job queue (cached singleton)."""
    _ensure_dirs()
    return JobQueue(persist_dir="./jobs")


def get_upload_dir() -> str:
    """Get the upload directory, ensuring it exists."""
    _ensure_dirs()
    return UPLOAD_DIR


# ═══════════════════════════════════════════════════════════
# Request-level dependencies (called per request)
# ═══════════════════════════════════════════════════════════

async def require_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
        )


async def require_generation_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_ip):
        raise HTTPException(429, "Rate limit exceeded.")
    if not rate_limiter.allow_generation(client_ip):
        raise HTTPException(429, "Generation rate limit exceeded. Max 5/minute.")


async def optional_auth(request: Request) -> Optional[str]:
    """
    Optional API key auth. Returns the API key or None.
    Does NOT block requests when auth is disabled.
    """
    api_key = request.headers.get("X-API-Key")
    if api_auth.enabled and not api_auth.verify(api_key):
        raise HTTPException(401, "Invalid or missing API key.")
    return api_key


# ═══════════════════════════════════════════════════════════
# Helper: save uploaded file
# ═══════════════════════════════════════════════════════════

async def save_upload(
    file: UploadFile,
    prefix: str = "",
    validate: bool = True,
) -> str:
    """
    Save an uploaded file to the uploads directory.
    Returns the saved file path.
    Validates image type and size before saving.
    """
    upload_dir = get_upload_dir()
    
    # Read content to check size
    content = await file.read()
    await file.seek(0)
    
    # Validate
    if validate:
        errors = validate_image_upload(
            filename=file.filename or "unknown",
            file_size_bytes=len(content),
            content_type=file.content_type or "",
        )
        if errors:
            messages = "; ".join(e.message for e in errors)
            raise HTTPException(400, f"Invalid upload: {messages}")
        
        # Also validate actual image dimensions
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(content))
            dim_errors = validate_image_dimensions(img.width, img.height, file.filename or "")
            if dim_errors:
                messages = "; ".join(e.message for e in dim_errors)
                raise HTTPException(400, f"Invalid image: {messages}")
        except HTTPException:
            raise
        except Exception:
            pass  # If PIL fails, skip dimension validation (binary check already done)
    
    # Save
    job_id = uuid.uuid4().hex[:8]
    safe_name = (file.filename or "upload").replace("/", "_").replace("\\", "_")
    filename = f"{prefix}{job_id}_{safe_name}"
    path = os.path.join(upload_dir, filename)
    
    with open(path, "wb") as f:
        f.write(content)
    
    return path
