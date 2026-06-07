"""
FitStream Mobile-Optimized API
Lightweight endpoints at /m/ for mobile apps.
Uses proper dependency injection — NO circular imports.
"""

import os
import uuid
import base64
from typing import Optional

from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
from pydantic import BaseModel
from loguru import logger

from fitstream.api.dependencies import (
    get_app_config, get_model_manager, get_job_queue,
    require_rate_limit, save_upload, get_upload_dir,
)
from fitstream.core.job_queue import JobQueue
from fitstream.core.models.model_manager import ModelManager
from fitstream.config import FitStreamConfig

mobile_router = APIRouter(tags=["Mobile"])


class MobileStatus(BaseModel):
    ok: bool
    gpu: bool
    gpu_free_gb: float = 0
    active_jobs: int = 0
    total_jobs: int = 0


class MobileJobStatus(BaseModel):
    id: str
    status: str
    progress: float = 0
    video_url: Optional[str] = None
    seconds: float = 0
    error: Optional[str] = None


@mobile_router.get("/status", dependencies=[Depends(require_rate_limit)])
async def mobile_status(
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
) -> MobileStatus:
    """📱 Quick status check."""
    gpu_info = models.get_gpu_status()
    all_jobs = jobs.list_jobs(limit=500)
    active = sum(1 for j in all_jobs if j.status == "processing")
    
    return MobileStatus(
        ok=True,
        gpu=gpu_info.get("available", False),
        gpu_free_gb=gpu_info.get("free_gb", 0),
        active_jobs=active,
        total_jobs=len(all_jobs),
    )


@mobile_router.post("/generate", dependencies=[Depends(require_rate_limit)])
async def mobile_generate(
    prompt: str = Form(...),
    mode: str = Form("animate"),
    style: str = Form("cinematic"),
    quality: str = Form("draft"),
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    jobs: JobQueue = Depends(get_job_queue),
):
    """📱 Simplified generation endpoint."""
    if image:
        img_path = await save_upload(image, prefix="m_")
    elif image_base64:
        img_path = _save_base64(image_base64)
    else:
        raise HTTPException(400, "Image required")
    
    if quality not in ("draft", "standard"):
        quality = "draft"
    
    job = jobs.create_job(mode, prompt=prompt, image_paths=[img_path],
                          params={"style": style, "quality": quality, "mobile": True})
    
    return {"job_id": job.id, "status": "queued", "mode": mode}


@mobile_router.get("/job/{job_id}", dependencies=[Depends(require_rate_limit)])
async def mobile_job_status(
    job_id: str,
    jobs: JobQueue = Depends(get_job_queue),
) -> MobileJobStatus:
    """📱 Compact job status."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    status_map = {"completed": "done", "failed": "failed", "queued": "queued", "processing": "processing"}
    
    return MobileJobStatus(
        id=job_id,
        status=status_map.get(job.status, job.status),
        progress=job.progress,
        video_url=f"/api/v1/jobs/{job_id}/video" if job.video_path else None,
        seconds=job.metadata.get("generation_time", 0),
        error=job.error,
    )


@mobile_router.get("/gallery", dependencies=[Depends(require_rate_limit)])
async def mobile_gallery(
    page: int = 0,
    size: int = 12,
    jobs: JobQueue = Depends(get_job_queue),
):
    """📱 Lightweight paginated gallery."""
    completed = [
        j for j in jobs.list_jobs(limit=500)
        if j.status == "completed" and j.video_path
    ]
    
    total = len(completed)
    page_items = completed[page * size:(page + 1) * size]
    
    return {
        "items": [
            {"id": j.id, "type": j.type, "prompt": (j.prompt or "")[:60],
             "video": f"/api/v1/jobs/{j.id}/video"}
            for j in page_items
        ],
        "total": total,
        "page": page,
        "has_next": (page + 1) * size < total,
    }


@mobile_router.get("/styles", dependencies=[Depends(require_rate_limit)])
async def mobile_styles() -> list:
    """📱 Flat style list."""
    from fitstream.core.pipelines.style_transfer import STYLE_PRESETS
    return [{"id": k, "name": v["label"]} for k, v in STYLE_PRESETS.items()]


@mobile_router.get("/templates", dependencies=[Depends(require_rate_limit)])
async def mobile_templates(category: Optional[str] = None) -> list:
    from fitstream.core.prompt_templates import PromptTemplateLibrary
    return [{"id": t["id"], "name": t["name"], "category": t["category"]}
            for t in PromptTemplateLibrary().list_templates(category)]


def _save_base64(b64: str) -> str:
    """Decode a base64 image string and save it to the upload directory."""
    try:
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        data = base64.b64decode(b64)
        ext = "png" if data[:4] == b'\x89PNG' else "jpg"
        path = os.path.join(get_upload_dir(), f"m_{uuid.uuid4().hex[:8]}.{ext}")
        with open(path, "wb") as f:
            f.write(data)
        return path
    except (ValueError, OSError) as e:
        raise HTTPException(400, f"Invalid base64: {e}")
