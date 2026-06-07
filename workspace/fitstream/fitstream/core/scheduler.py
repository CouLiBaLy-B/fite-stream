"""
FitStream Scheduler
Schedule and automate recurring video generation jobs.

Use cases:
  - Daily fashion lookbook generation (new outfit every morning)
  - Scheduled content for social media calendars
  - Batch processing at off-peak hours
  - Recurring story series ("Episode 1, 2, 3...")

Usage:
    scheduler = Scheduler()
    
    # One-time scheduled job
    scheduler.schedule_once(
        run_at=datetime(2026, 6, 8, 9, 0),
        job_type="animate",
        params={"image": "model.jpg", "prompt": "Morning walk in Paris"},
    )
    
    # Recurring daily job
    scheduler.schedule_recurring(
        interval_hours=24,
        job_type="story",
        params={"image": "model.jpg", "story": "Daily adventure..."},
        name="daily-lookbook",
    )
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from loguru import logger
import uuid


@dataclass
class ScheduledJob:
    """A job scheduled for future execution."""
    id: str
    name: str
    job_type: str              # animate, story, tryon, style, etc.
    params: Dict[str, Any]
    
    # Schedule
    run_at: float              # Unix timestamp of next run
    interval_seconds: float = 0  # 0 = one-shot, >0 = recurring
    
    # State
    active: bool = True
    runs_completed: int = 0
    max_runs: int = 0          # 0 = unlimited
    last_run_at: Optional[float] = None
    last_result: Optional[str] = None  # "success" / "failed"
    last_error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    @property
    def is_recurring(self) -> bool:
        """Is recurring."""
        return self.interval_seconds > 0
    
    @property
    def is_due(self) -> bool:
        """Is due."""
        return self.active and time.time() >= self.run_at
    
    @property
    def next_run_human(self) -> str:
        """Next run human."""
        return datetime.fromtimestamp(self.run_at).strftime("%Y-%m-%d %H:%M:%S")
    
    def advance(self) -> None:
        """Move to next run time for recurring jobs."""
        self.runs_completed += 1
        self.last_run_at = time.time()
        
        if self.is_recurring:
            if self.max_runs > 0 and self.runs_completed >= self.max_runs:
                self.active = False
                logger.info(f"📅 Schedule '{self.name}' completed {self.max_runs} runs — deactivated")
            else:
                self.run_at = time.time() + self.interval_seconds
        else:
            self.active = False  # one-shot
    
    def to_dict(self) -> dict:
        """To dict."""
        return {
            "id": self.id,
            "name": self.name,
            "job_type": self.job_type,
            "active": self.active,
            "is_recurring": self.is_recurring,
            "interval_hours": self.interval_seconds / 3600 if self.interval_seconds else 0,
            "next_run": self.next_run_human,
            "runs_completed": self.runs_completed,
            "max_runs": self.max_runs,
            "last_result": self.last_result,
            "last_error": self.last_error,
        }


class Scheduler:
    """
    Job scheduler for automated video generation.
    
    Runs a background thread that checks for due jobs every `check_interval` seconds.
    When a job is due, it calls the `executor` callback.
    """
    
    def __init__(self, check_interval: float = 30.0) -> None:
        self._schedules: Dict[str, ScheduledJob] = {}
        self._executor: Optional[Callable] = None
        self._check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def set_executor(self, executor: Callable) -> None:
        """Set the callback that runs scheduled jobs.
        
        executor(job_type: str, params: dict) -> bool (success)
        """
        self._executor = executor
    
    def schedule_once(
        self,
        run_at: datetime,
        job_type: str,
        params: Dict[str, Any],
        name: str = "",
    ) -> str:
        """Schedule a one-time job."""
        job_id = str(uuid.uuid4())[:8]
        
        job = ScheduledJob(
            id=job_id,
            name=name or f"{job_type}-{job_id}",
            job_type=job_type,
            params=params,
            run_at=run_at.timestamp(),
        )
        
        self._schedules[job_id] = job
        logger.info(f"📅 Scheduled one-time: '{job.name}' at {job.next_run_human}")
        return job_id
    
    def schedule_recurring(
        self,
        interval_hours: float,
        job_type: str,
        params: Dict[str, Any],
        name: str = "",
        max_runs: int = 0,
        start_at: Optional[datetime] = None,
    ) -> str:
        """Schedule a recurring job."""
        job_id = str(uuid.uuid4())[:8]
        
        if start_at:
            first_run = start_at.timestamp()
        else:
            first_run = time.time() + (interval_hours * 3600)
        
        job = ScheduledJob(
            id=job_id,
            name=name or f"{job_type}-recurring-{job_id}",
            job_type=job_type,
            params=params,
            run_at=first_run,
            interval_seconds=interval_hours * 3600,
            max_runs=max_runs,
        )
        
        self._schedules[job_id] = job
        
        recurrence = f"every {interval_hours}h"
        if max_runs:
            recurrence += f" (max {max_runs} runs)"
        logger.info(f"📅 Scheduled recurring: '{job.name}' — {recurrence}, first at {job.next_run_human}")
        return job_id
    
    def cancel(self, job_id: str) -> bool:
        if job_id in self._schedules:
            self._schedules[job_id].active = False
            logger.info(f"📅 Cancelled: {job_id}")
            return True
        return False
    
    def remove(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        if job_id in self._schedules:
            del self._schedules[job_id]
            return True
        return False
    
    def list_schedules(self, active_only: bool = False) -> List[dict]:
        """Remove a scheduled job entirely."""
        jobs = list(self._schedules.values())
        if active_only:
            jobs = [j for j in jobs if j.active]
        jobs.sort(key=lambda j: j.run_at)
        return [j.to_dict() for j in jobs]
    
    def get_schedule(self, job_id: str) -> Optional[dict]:
        """List all scheduled jobs."""
        job = self._schedules.get(job_id)
        return job.to_dict() if job else None
    
    def start(self) -> None:
        """Get schedule."""
        """Start the scheduler background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"📅 Scheduler started (checking every {self._check_interval}s)")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("📅 Scheduler stopped")
    
    def _run_loop(self) -> None:
        """Background loop that checks for due jobs."""
        while self._running:
            try:
                self._check_due_jobs()
            except (RuntimeError, OSError, ValueError) as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(self._check_interval)
    
    def _check_due_jobs(self) -> None:
        """Check all schedules and execute due jobs."""
        for job in list(self._schedules.values()):
            if not job.is_due:
                continue
            
            logger.info(f"📅 Executing scheduled job: '{job.name}' ({job.job_type})")
            
            if self._executor:
                try:
                    success = self._executor(job.job_type, job.params)
                    job.last_result = "success" if success else "failed"
                    job.last_error = None
                except (RuntimeError, OSError, ValueError) as e:
                    job.last_result = "failed"
                    job.last_error = str(e)
                    logger.error(f"📅 Scheduled job '{job.name}' failed: {e}")
            else:
                logger.warning("No executor set — cannot run scheduled jobs")
                job.last_result = "skipped"
            
            job.advance()
    
    @property
    def active_count(self) -> int:
        """Active count."""
        return sum(1 for j in self._schedules.values() if j.active)
    
    @property
    def total_count(self) -> int:
        """Total count."""
        return len(self._schedules)
