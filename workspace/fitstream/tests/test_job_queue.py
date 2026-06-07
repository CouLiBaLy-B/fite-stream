"""Tests for the job queue — no GPU needed."""

import os
import time
import tempfile
import pytest
from fitstream.core.job_queue import JobQueue, Job, JobStatus, JobType


class TestJobQueue:
    def setup_method(self):
        self.queue = JobQueue()  # in-memory only
    
    def test_create_job(self):
        job = self.queue.create_job(
            JobType.ANIMATE, prompt="Test prompt",
            image_paths=["test.jpg"],
        )
        assert job.id is not None
        assert len(job.id) == 8
        assert job.status == JobStatus.QUEUED
        assert job.prompt == "Test prompt"
    
    def test_get_job(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        retrieved = self.queue.get_job(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id
    
    def test_get_nonexistent_job(self):
        assert self.queue.get_job("nonexistent") is None
    
    def test_start_job(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        self.queue.start_job(job.id)
        updated = self.queue.get_job(job.id)
        assert updated.status == JobStatus.PROCESSING
        assert updated.started_at is not None
    
    def test_update_progress(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        self.queue.start_job(job.id)
        self.queue.update_progress(job.id, 0.5, "Half done")
        updated = self.queue.get_job(job.id)
        assert updated.progress == 0.5
        assert updated.progress_message == "Half done"
    
    def test_progress_clamped(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        self.queue.update_progress(job.id, 1.5, "Over 100%")
        assert self.queue.get_job(job.id).progress == 1.0
        self.queue.update_progress(job.id, -0.5, "Negative")
        assert self.queue.get_job(job.id).progress == 0.0
    
    def test_complete_job(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        self.queue.start_job(job.id)
        self.queue.complete_job(job.id, video_path="/output.mp4", metadata={"seed": 42})
        
        updated = self.queue.get_job(job.id)
        assert updated.status == JobStatus.COMPLETED
        assert updated.video_path == "/output.mp4"
        assert updated.metadata["seed"] == 42
        assert updated.progress == 1.0
        assert updated.completed_at is not None
    
    def test_fail_job(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        self.queue.start_job(job.id)
        self.queue.fail_job(job.id, "Out of memory")
        
        updated = self.queue.get_job(job.id)
        assert updated.status == JobStatus.FAILED
        assert updated.error == "Out of memory"
    
    def test_list_jobs(self):
        self.queue.create_job(JobType.ANIMATE, prompt="animate 1")
        self.queue.create_job(JobType.STORY, prompt="story 1")
        self.queue.create_job(JobType.TRYON, prompt="tryon 1")
        
        all_jobs = self.queue.list_jobs()
        assert len(all_jobs) == 3
        
        # Filter by type
        animate_jobs = self.queue.list_jobs(job_type=JobType.ANIMATE)
        assert len(animate_jobs) == 1
    
    def test_list_jobs_sorted_newest_first(self):
        j1 = self.queue.create_job(JobType.ANIMATE, prompt="first")
        time.sleep(0.01)
        j2 = self.queue.create_job(JobType.ANIMATE, prompt="second")
        
        jobs = self.queue.list_jobs()
        assert jobs[0].id == j2.id  # newest first
    
    def test_job_duration(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        assert job.duration == 0.0
        
        self.queue.start_job(job.id)
        time.sleep(0.05)
        assert self.queue.get_job(job.id).duration > 0
    
    def test_job_to_dict(self):
        job = self.queue.create_job(JobType.ANIMATE, prompt="test")
        d = job.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == job.id
        assert "duration" in d


class TestJobQueuePersistence:
    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create queue with persistence
            queue1 = JobQueue(persist_dir=tmpdir)
            job = queue1.create_job(JobType.ANIMATE, prompt="persistent job")
            queue1.complete_job(job.id, video_path="/test.mp4")
            
            # Create new queue from same directory
            queue2 = JobQueue(persist_dir=tmpdir)
            loaded = queue2.get_job(job.id)
            
            assert loaded is not None
            assert loaded.prompt == "persistent job"
            assert loaded.status == JobStatus.COMPLETED
            assert loaded.video_path == "/test.mp4"
    
    def test_cleanup_old_jobs(self):
        queue = JobQueue()
        
        # Create an "old" job
        job = queue.create_job(JobType.ANIMATE, prompt="old")
        job.created_at = time.time() - 100000  # very old
        queue.complete_job(job.id, video_path="/old.mp4")
        
        # Create a "new" job
        new_job = queue.create_job(JobType.ANIMATE, prompt="new")
        queue.complete_job(new_job.id, video_path="/new.mp4")
        
        queue.cleanup_old_jobs(max_age_hours=1)
        
        assert queue.get_job(job.id) is None  # old job removed
        assert queue.get_job(new_job.id) is not None  # new job kept


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
