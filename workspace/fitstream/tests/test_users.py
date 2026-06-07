"""Tests for multi-user system."""

import os
import time
import tempfile
import pytest
from fitstream.core.users import UserManager, User, SharedVideo


@pytest.fixture
def mgr():
    with tempfile.TemporaryDirectory() as d:
        yield UserManager(data_dir=d)


class TestUserRegistration:
    def test_register(self, mgr):
        user, key = mgr.register("alice", email="alice@test.com")
        assert user.username == "alice"
        assert key.startswith("fs_")
        assert len(key) > 20

    def test_duplicate_username(self, mgr):
        mgr.register("bob")
        with pytest.raises(ValueError, match="already taken"):
            mgr.register("bob")

    def test_get_user(self, mgr):
        user, _ = mgr.register("charlie")
        fetched = mgr.get_user(user.id)
        assert fetched.username == "charlie"

    def test_list_users(self, mgr):
        mgr.register("a")
        mgr.register("b")
        assert len(mgr.list_users()) == 2


class TestAuthentication:
    def test_auth_valid_key(self, mgr):
        _, key = mgr.register("dave")
        user = mgr.authenticate(key)
        assert user is not None
        assert user.username == "dave"

    def test_auth_invalid_key(self, mgr):
        assert mgr.authenticate("fs_invalid_key_12345") is None

    def test_revoke_key(self, mgr):
        user, old_key = mgr.register("eve")
        new_key = mgr.revoke_api_key(user.id)
        assert new_key != old_key
        assert mgr.authenticate(old_key) is None
        assert mgr.authenticate(new_key) is not None


class TestQuota:
    def test_initial_quota(self, mgr):
        user, _ = mgr.register("fay", daily_limit=10)
        assert mgr.check_quota(user.id) is True
        q = mgr.get_remaining_quota(user.id)
        assert q["daily_remaining"] == 10

    def test_record_usage(self, mgr):
        user, _ = mgr.register("gus", daily_limit=3)
        mgr.record_usage(user.id, "animate", 10.0)
        mgr.record_usage(user.id, "animate", 20.0)
        q = mgr.get_remaining_quota(user.id)
        assert q["daily_remaining"] == 1
        assert q["today_used"] == 2

    def test_quota_exhausted(self, mgr):
        user, _ = mgr.register("hal", daily_limit=2)
        mgr.record_usage(user.id, "animate")
        mgr.record_usage(user.id, "animate")
        assert mgr.check_quota(user.id) is False

    def test_nonexistent_user_quota(self, mgr):
        assert mgr.check_quota("fake_id") is False


class TestSharing:
    def test_create_share(self, mgr):
        user, _ = mgr.register("ivy")
        share = mgr.create_share(user.id, "job123", "/v.mp4", prompt="test")
        assert share.share_id is not None
        assert share.share_url.startswith("/shared/")

    def test_get_share(self, mgr):
        user, _ = mgr.register("jay")
        share = mgr.create_share(user.id, "job456", "/v.mp4")
        fetched = mgr.get_share(share.share_id)
        assert fetched is not None
        assert fetched.views == 1

    def test_expired_share(self, mgr):
        user, _ = mgr.register("kay")
        share = mgr.create_share(user.id, "job789", "/v.mp4", expires_hours=0.0001)
        time.sleep(0.5)
        assert mgr.get_share(share.share_id) is None

    def test_nonexistent_share(self, mgr):
        assert mgr.get_share("nonexistent") is None


class TestPersistence:
    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as d:
            m1 = UserManager(data_dir=d)
            user, key = m1.register("persist_user", email="p@test.com")
            m1.record_usage(user.id, "animate", 50.0)

            m2 = UserManager(data_dir=d)
            loaded = m2.get_user(user.id)
            assert loaded is not None
            assert loaded.username == "persist_user"
            assert loaded.total_generations == 1
            assert m2.authenticate(key) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
