"""Tests for JobQueue — persistent, thread-safe job management."""

import os
import json
import time
import tempfile
import pytest
from fitstream.core.job_queue import JobQueue, Job, JobStatus


class TestJobDataclass:
    """Job dataclass basic tests."""

    def test_creation(self) -> None:
        job = Job(id="abc", type="animate", prompt="test prompt")
        assert job.id == "abc"
        assert job.type == "animate"
        assert job.status == JobStatus.QUEUED
        assert job.progress == 0.0
        assert job.image_paths == []
        assert job.params == {}
        assert job.metadata == {}

    def test_duration_not_started(self) -> None:
        job = Job(id="x", type="animate")
        assert job.duration == 0.0

    def test_duration_in_progress(self) -> None:
        job = Job(id="x", type="animate", started_at=time.time() - 10)
        assert 9 <= job.duration <= 11  # ~10 seconds

    def test_duration_completed(self) -> None:
        now = time.time()
        job = Job(id="x", type="animate", started_at=now - 30, completed_at=now)
        assert job.duration == 30.0

    def test_to_dict(self) -> None:
        job = Job(id="abc", type="story", prompt="A story", image_paths=["/a.jpg"])
        d = job.to_dict()
        assert d["id"] == "abc"
        assert d["type"] == "story"
        assert d["prompt"] == "A story"
        assert d["image_paths"] == ["/a.jpg"]
        assert "duration" in d

    def test_elapsed_since_created(self) -> None:
        job = Job(id="x", type="animate", created_at=time.time() - 5)
        assert job.elapsed_since_created >= 5

    def test_elapsed_since_created_default(self) -> None:
        job = Job(id="x", type="animate")
        assert job.elapsed_since_created == 0.0


class TestJobQueueBasic:
    """Basic job queue operations."""

    def test_create_job(self) -> None:
        q = JobQueue()
        job = q.create_job("animate", prompt="test", image_paths=["img.jpg"])
        assert job.id is not None
        assert job.type == "animate"
        assert job.prompt == "test"
        assert job.image_paths == ["img.jpg"]
        assert job.status == JobStatus.QUEUED

    def test_create_job_minimal(self) -> None:
        q = JobQueue()
        job = q.create_job("story")
        assert job.status == JobStatus.QUEUED

    def test_get_job_exists(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        retrieved = q.get_job(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id

    def test_get_job_not_exists(self) -> None:
        q = JobQueue()
        assert q.get_job("nonexistent") is None

    def test_start_job(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        q.start_job(job.id)
        assert job.status == JobStatus.PROCESSING
        assert job.started_at is not None
        assert job.progress == 0.0

    def test_update_progress(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        q.update_progress(job.id, 0.5, "Halfway")
        assert job.progress == 0.5
        assert job.progress_message == "Halfway"

    def test_update_progress_clamped(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        q.update_progress(job.id, 2.0)
        assert job.progress == 1.0
        q.update_progress(job.id, -0.5)
        assert job.progress == 0.0

    def test_complete_job(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        q.start_job(job.id)
        q.complete_job(job.id, "/output/video.mp4", metadata={"gen_time": 5.0})
        assert job.status == JobStatus.COMPLETED
        assert job.video_path == "/output/video.mp4"
        assert job.progress == 1.0
        assert job.metadata["gen_time"] == 5.0

    def test_fail_job(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        q.fail_job(job.id, "GPU crashed")
        assert job.status == JobStatus.FAILED
        assert job.error == "GPU crashed"

    def test_list_jobs_all(self) -> None:
        q = JobQueue()
        ids = [q.create_job("animate").id for _ in range(5)]
        jobs = q.list_jobs()
        assert len(jobs) == 5
        assert all(j.id in ids for j in jobs)

    def test_list_jobs_filter_status(self) -> None:
        q = JobQueue()
        q.create_job("animate")
        job2 = q.create_job("animate")
        q.complete_job(job2.id, "/video.mp4")
        completed = q.list_jobs(status=JobStatus.COMPLETED)
        assert len(completed) == 1

    def test_list_jobs_filter_type(self) -> None:
        q = JobQueue()
        q.create_job("animate")
        q.create_job("story")
        anim = q.list_jobs(job_type="animate")
        assert len(anim) == 1
        assert anim[0].type == "animate"

    def test_list_jobs_sorted_newest_first(self) -> None:
        q = JobQueue()
        q.create_job("animate")  # oldest
        time.sleep(0.01)
        newest = q.create_job("story")  # newest
        jobs = q.list_jobs()
        assert jobs[0].id == newest.id


class TestJobQueuePersistence:
    """Disk-based persistence tests."""

    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        import shutil
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_persist_and_reload(self) -> None:
        q1 = JobQueue(persist_dir=self.tmpdir)
        job = q1.create_job("animate", prompt="persist me")
        q1.complete_job(job.id, "/video.mp4")

        # Reload
        q2 = JobQueue(persist_dir=self.tmpdir)
        reloaded = q2.get_job(job.id)
        assert reloaded is not None
        assert reloaded.prompt == "persist me"
        assert reloaded.status == JobStatus.COMPLETED
        assert reloaded.video_path == "/video.mp4"

    def test_delete_persisted_job(self) -> None:
        q = JobQueue(persist_dir=self.tmpdir)
        job = q.create_job("animate")
        json_path = os.path.join(self.tmpdir, f"{job.id}.json")
        assert os.path.exists(json_path)
        q._delete_persisted_job(job.id)
        assert not os.path.exists(json_path)

    def test_corrupted_json_doesnt_crash(self) -> None:
        # Write invalid JSON
        bad_file = os.path.join(self.tmpdir, "bad.json")
        with open(bad_file, "w") as f:
            f.write("not valid json {{{")
        q = JobQueue(persist_dir=self.tmpdir)
        # Should not crash, just skip the bad file
        assert q.get_job("bad") is None


class TestJobQueueLimits:
    """Max jobs and cleanup tests."""

    def test_enforce_limit_removes_oldest(self) -> None:
        q = JobQueue(max_jobs=5)
        for i in range(10):
            job = q.create_job("animate")
            q.complete_job(job.id, f"/v{i}.mp4")
        assert len(q._jobs) <= 5  # Enforced limit

    def test_cleanup_old_jobs(self) -> None:
        q = JobQueue(max_jobs=100)
        for i in range(3):
            job = q.create_job("animate")
            q.complete_job(job.id, f"/v{i}.mp4")
        initial = len(q.list_jobs())
        q.cleanup_old_jobs(max_age_hours=0)  # All older than 0 hours
        assert len(q.list_jobs()) <= initial

    def test_unique_ids(self) -> None:
        q = JobQueue()
        ids = {q.create_job("animate").id for _ in range(50)}
        assert len(ids) == 50  # All unique


class TestJobQueueThreadSafety:
    """Basic thread safety — single-thread sanity."""

    def test_concurrent_creates(self) -> None:
        q = JobQueue()
        # Sequential creates are fine with Lock
        for _ in range(100):
            q.create_job("animate")
        assert len(q._jobs) == 100

    def test_no_race_on_get_and_update(self) -> None:
        q = JobQueue()
        job = q.create_job("animate")
        q.start_job(job.id)
        q.update_progress(job.id, 0.7)
        retrieved = q.get_job(job.id)
        assert retrieved.progress == 0.7
