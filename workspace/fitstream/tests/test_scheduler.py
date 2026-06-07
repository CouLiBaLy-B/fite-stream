"""Tests for scheduler."""

import time
from datetime import datetime, timedelta

import pytest

from fitstream.core.scheduler import ScheduledJob, Scheduler


class TestScheduledJob:
    def test_one_shot(self):
        j = ScheduledJob(
            id="j1", name="test", job_type="animate", params={}, run_at=time.time() - 10
        )
        assert j.is_due is True
        assert j.is_recurring is False

    def test_not_yet_due(self):
        j = ScheduledJob(
            id="j2", name="test", job_type="animate", params={}, run_at=time.time() + 3600
        )
        assert j.is_due is False

    def test_inactive_not_due(self):
        j = ScheduledJob(
            id="j3",
            name="test",
            job_type="animate",
            params={},
            run_at=time.time() - 10,
            active=False,
        )
        assert j.is_due is False

    def test_recurring(self):
        j = ScheduledJob(
            id="j4",
            name="test",
            job_type="animate",
            params={},
            run_at=time.time(),
            interval_seconds=3600,
        )
        assert j.is_recurring is True

    def test_advance_oneshot(self):
        j = ScheduledJob(id="j5", name="test", job_type="animate", params={}, run_at=time.time())
        j.advance()
        assert j.active is False
        assert j.runs_completed == 1

    def test_advance_recurring(self):
        j = ScheduledJob(
            id="j6",
            name="test",
            job_type="animate",
            params={},
            run_at=time.time(),
            interval_seconds=3600,
        )
        old_run_at = j.run_at
        j.advance()
        assert j.active is True
        assert j.run_at > old_run_at
        assert j.runs_completed == 1

    def test_max_runs(self):
        j = ScheduledJob(
            id="j7",
            name="test",
            job_type="animate",
            params={},
            run_at=time.time(),
            interval_seconds=3600,
            max_runs=2,
        )
        j.advance()
        assert j.active is True
        j.advance()
        assert j.active is False  # max_runs reached

    def test_to_dict(self):
        j = ScheduledJob(id="j8", name="Test", job_type="animate", params={}, run_at=time.time())
        d = j.to_dict()
        assert d["id"] == "j8"
        assert d["name"] == "Test"
        assert "next_run" in d


class TestScheduler:
    def test_schedule_once(self):
        s = Scheduler()
        jid = s.schedule_once(
            run_at=datetime.now() + timedelta(hours=1),
            job_type="animate",
            params={"prompt": "test"},
        )
        assert jid is not None
        assert s.total_count == 1

    def test_schedule_recurring(self):
        s = Scheduler()
        s.schedule_recurring(
            interval_hours=24,
            job_type="story",
            params={"story": "test"},
            name="daily-story",
        )
        schedules = s.list_schedules()
        assert len(schedules) == 1
        assert schedules[0]["is_recurring"] is True
        assert schedules[0]["name"] == "daily-story"

    def test_cancel(self):
        s = Scheduler()
        jid = s.schedule_once(datetime.now() + timedelta(hours=1), "animate", {})
        assert s.cancel(jid) is True
        assert s.active_count == 0

    def test_remove(self):
        s = Scheduler()
        jid = s.schedule_once(datetime.now() + timedelta(hours=1), "animate", {})
        assert s.remove(jid) is True
        assert s.total_count == 0

    def test_list_active_only(self):
        s = Scheduler()
        s.schedule_once(datetime.now() + timedelta(hours=1), "animate", {})
        jid2 = s.schedule_once(datetime.now() + timedelta(hours=2), "story", {})
        s.cancel(jid2)

        active = s.list_schedules(active_only=True)
        assert len(active) == 1

    def test_executor_callback(self):
        s = Scheduler()
        executed = []
        s.set_executor(lambda jtype, params: executed.append(jtype) or True)

        # Create a job that's already due
        s.schedule_once(
            run_at=datetime.now() - timedelta(seconds=10),
            job_type="animate",
            params={},
        )

        s._check_due_jobs()
        assert "animate" in executed

    def test_get_schedule(self):
        s = Scheduler()
        jid = s.schedule_once(datetime.now() + timedelta(hours=1), "animate", {}, name="my-job")
        info = s.get_schedule(jid)
        assert info is not None
        assert info["name"] == "my-job"

    def test_get_nonexistent(self):
        s = Scheduler()
        assert s.get_schedule("nonexistent") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
