"""
FitStream Job Queue
Persistent job management with progress tracking.

Features:
  - Job creation, tracking, and completion
  - Progress updates with percentage
  - Job history with metadata
  - Disk-based persistence (survives restarts)
  - Automatic cleanup of old jobs
"""

import os
import json
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from loguru import logger
from threading import Lock


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    ANIMATE = "animate"
    STORY = "story"
    TRYON = "tryon"
    COMPOSE = "compose"
    EXTEND = "extend"


@dataclass
class Job:
    """A single generation job."""
    id: str
    type: str
    status: str = JobStatus.QUEUED
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0          # 0.0 to 1.0
    progress_message: str = ""
    
    # Input
    prompt: str = ""
    image_paths: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Output
    video_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Job duration in seconds."""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return 0.0
    
    @property
    def elapsed_since_created(self) -> float:
        """Elapsed since created."""
        return time.time() - self.created_at if self.created_at else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """To dict."""
        d = asdict(self)
        d["duration"] = self.duration
        return d


class JobQueue:
    """
    Thread-safe job queue with optional disk persistence.
    
    Usage:
        queue = JobQueue(persist_dir="./jobs")
        
        # Create a job
        job = queue.create_job(JobType.ANIMATE, prompt="...", image_paths=["photo.jpg"])
        
        # Update progress
        queue.update_progress(job.id, 0.5, "Generating frames...")
        
        # Complete
        queue.complete_job(job.id, video_path="output.mp4", metadata={...})
    """
    
    def __init__(self, persist_dir: Optional[str] = None, max_jobs: int = 1000) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = Lock()
        self._persist_dir = persist_dir
        self._max_jobs = max_jobs
        
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
            self._load_persisted_jobs()
    
    def create_job(
        self,
        job_type: str,
        prompt: str = "",
        image_paths: Optional[List[str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """Create a new job and add it to the queue."""
        job = Job(
            id=str(uuid.uuid4())[:8],
            type=job_type,
            status=JobStatus.QUEUED,
            created_at=time.time(),
            prompt=prompt,
            image_paths=image_paths or [],
            params=params or {},
        )
        
        with self._lock:
            self._jobs[job.id] = job
            self._enforce_limit()
            self._persist_job(job)
        
        logger.info(f"📋 Job {job.id} created: {job_type} — '{prompt[:50]}...'")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)
    
    def start_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.PROCESSING
                job.started_at = time.time()
                job.progress = 0.0
                job.progress_message = "Starting..."
                self._persist_job(job)
    
    def update_progress(self, job_id: str, progress: float, message: str = "") -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.progress = min(1.0, max(0.0, progress))
                if message:
                    job.progress_message = message
                # Don't persist every progress update (too many writes)
    
    def complete_job(
        self,
        job_id: str,
        video_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update job progress (0.0 to 1.0)."""
        """Mark a job as completed."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = time.time()
                job.progress = 1.0
                job.progress_message = "Done"
                job.video_path = video_path
                if metadata:
                    job.metadata.update(metadata)
                self._persist_job(job)
                logger.success(f"✅ Job {job_id} completed in {job.duration:.1f}s")
    
    def fail_job(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = time.time()
                job.progress_message = f"Failed: {error}"
                job.error = error
                self._persist_job(job)
                logger.error(f"❌ Job {job_id} failed: {error}")
    
    def list_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Job]:
        """Mark a job as failed."""
        """List jobs with optional filters."""
        with self._lock:
            jobs = list(self._jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        if job_type:
            jobs = [j for j in jobs if j.type == job_type]
        
        # Sort by creation time, newest first
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: float = 24) -> None:
        cutoff = time.time() - (max_age_hours * 3600)
        
        with self._lock:
            to_remove = [
                jid for jid, j in self._jobs.items()
                if j.created_at < cutoff and j.status in (JobStatus.COMPLETED, JobStatus.FAILED)
            ]
            for jid in to_remove:
                del self._jobs[jid]
                self._delete_persisted_job(jid)
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old jobs")
    
    def _enforce_limit(self) -> None:
        """Remove jobs older than max_age_hours."""
        """Remove oldest completed/failed jobs if over limit."""
        if len(self._jobs) <= self._max_jobs:
            return
        
        # Get completed/failed jobs sorted by age
        removable = sorted(
            [(jid, j) for jid, j in self._jobs.items()
             if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)],
            key=lambda x: x[1].created_at,
        )
        
        while len(self._jobs) > self._max_jobs and removable:
            jid, _ = removable.pop(0)
            del self._jobs[jid]
            self._delete_persisted_job(jid)
    
    def _persist_job(self, job: Job) -> None:
        if not self._persist_dir:
            return
        try:
            path = Path(self._persist_dir) / f"{job.id}.json"
            with open(path, 'w') as f:
                json.dump(job.to_dict(), f, indent=2, default=str)
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Failed to persist job {job.id}: {e}")
    
    def _delete_persisted_job(self, job_id: str) -> None:
        if not self._persist_dir:
            return
        path = Path(self._persist_dir) / f"{job_id}.json"
        if path.exists():
            path.unlink()
    
    def _load_persisted_jobs(self) -> None:
        """Load previously persisted jobs."""
        if not self._persist_dir:
            return
        
        persist_path = Path(self._persist_dir)
        loaded = 0
        
        for json_file in persist_path.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                
                job = Job(
                    id=data["id"],
                    type=data.get("type", "unknown"),
                    status=data.get("status", JobStatus.FAILED),
                    created_at=data.get("created_at", 0),
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                    progress=data.get("progress", 0),
                    progress_message=data.get("progress_message", ""),
                    prompt=data.get("prompt", ""),
                    image_paths=data.get("image_paths", []),
                    params=data.get("params", {}),
                    video_path=data.get("video_path"),
                    error=data.get("error"),
                    metadata=data.get("metadata", {}),
                )
                
                self._jobs[job.id] = job
                loaded += 1
            except (OSError, ValueError, KeyError) as e:
                logger.warning(f"Failed to load job from {json_file}: {e}")
        
        if loaded > 0:
            logger.info(f"📂 Loaded {loaded} persisted jobs")
