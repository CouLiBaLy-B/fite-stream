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
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, Request
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.job_queue import JobQueue, JobStatus
from fitstream.api.middleware import rate_limiter, api_auth, metrics


# ═══════════════════════════════════════════════════════════
# Singleton instances (created once, injected everywhere)
# ═══════════════════════════════════════════════════════════

_config: Optional[FitStreamConfig] = None
_model_manager: Optional[ModelManager] = None
_job_queue: Optional[JobQueue] = None

UPLOAD_DIR = "./uploads"
OUTPUT_DIR = "./outputs"


def _ensure_dirs() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("./jobs", exist_ok=True)


def get_app_config() -> FitStreamConfig:
    """Get the application config (singleton)."""
    global _config
    if _config is None:
        _config = get_config()
    return _config


def get_model_manager() -> ModelManager:
    """Get the model manager (singleton, lazy init)."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager(get_app_config())
    return _model_manager


def get_job_queue() -> JobQueue:
    """Get the persistent job queue (singleton)."""
    global _job_queue
    if _job_queue is None:
        _ensure_dirs()
        _job_queue = JobQueue(persist_dir="./jobs")
    return _job_queue


def get_upload_dir() -> str:
    """Get upload dir."""
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

import shutil
import uuid
from fastapi import UploadFile

from fitstream.core.interfaces import validate_image_upload


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
    
    # Save
    job_id = uuid.uuid4().hex[:8]
    safe_name = (file.filename or "upload").replace("/", "_").replace("\\", "_")
    filename = f"{prefix}{job_id}_{safe_name}"
    path = os.path.join(upload_dir, filename)
    
    with open(path, "wb") as f:
        f.write(content)
    
    return path
