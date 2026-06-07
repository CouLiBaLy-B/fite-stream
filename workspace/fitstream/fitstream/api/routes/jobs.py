"""Job management endpoints — /api/v1/jobs/*"""

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from fitstream.api.dependencies import get_job_queue, require_rate_limit
from fitstream.core.job_queue import JobQueue

router = APIRouter(prefix="/api/v1", tags=["Jobs"], dependencies=[Depends(require_rate_limit)])


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, jobs: JobQueue = Depends(get_job_queue)):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    d = job.to_dict()
    d["video_url"] = f"/api/v1/jobs/{job_id}/video" if job.video_path else None
    return d


@router.get("/jobs/{job_id}/video")
async def get_video(job_id: str, jobs: JobQueue = Depends(get_job_queue)):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    if not job.video_path or not os.path.exists(job.video_path):
        raise HTTPException(404, "Video not ready or not found")

    return FileResponse(
        job.video_path,
        media_type="video/mp4",
        filename=f"fitstream_{job_id}.mp4",
    )


@router.get("/jobs")
async def list_jobs(jobs: JobQueue = Depends(get_job_queue)) -> dict:
    all_jobs = jobs.list_jobs(limit=100)
    return {
        "jobs": [
            {
                "job_id": j.id,
                "type": j.type,
                "status": j.status,
                "created_at": j.created_at,
                "prompt": j.prompt[:100] if j.prompt else "",
                "progress": j.progress,
            }
            for j in all_jobs
        ],
        "total": len(all_jobs),
    }


@router.get("/gallery")
async def gallery(
    limit: int = 20,
    offset: int = 0,
    jobs: JobQueue = Depends(get_job_queue),
):
    """List all jobs."""
    """📸 Paginated gallery of completed generations."""
    completed = [j for j in jobs.list_jobs(limit=500) if j.status == "completed" and j.video_path]

    total = len(completed)
    page = completed[offset : offset + limit]

    return {
        "items": [
            {
                "job_id": j.id,
                "type": j.type,
                "prompt": j.prompt[:100] if j.prompt else "",
                "video_url": f"/api/v1/jobs/{j.id}/video",
                "generation_time": j.metadata.get("generation_time"),
                "resolution": j.metadata.get("resolution", ""),
                "duration_seconds": j.metadata.get("duration_seconds", 0),
                "seed": j.metadata.get("seed", 0),
                "created_at": j.created_at,
            }
            for j in page
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }
