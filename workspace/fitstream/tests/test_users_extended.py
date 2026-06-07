"""Tests for the multi-user system."""

import tempfile, os, pytest
from fitstream.core.users import UserManager


class TestUserRegistration:
    """User registration and auth tests."""

    def test_register(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            user, api_key = users.register("alice", email="alice@test.com")
            assert user.username == "alice"
            assert user.email == "alice@test.com"
            assert api_key.startswith("fs_")

    def test_register_daily_limit(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            user, _ = users.register("bob", daily_limit=25)
            assert user.daily_limit == 25

    def test_authenticate_valid(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            _, api_key = users.register("carol")
            user = users.authenticate(api_key)
            assert user is not None
            assert user.username == "carol"

    def test_authenticate_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            assert users.authenticate("bad_key") is None

    def test_duplicate_username(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            users.register("frank")
            with pytest.raises(ValueError):
                users.register("frank")


class TestUserPersistence:
    """Disk persistence for user data."""

    def test_persist_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            u1 = UserManager(data_dir=tmpdir)
            _, api_key = u1.register("persist_user")
            del u1
            u2 = UserManager(data_dir=tmpdir)
            user = u2.authenticate(api_key)
            assert user is not None
            assert user.username == "persist_user"


class TestSharing:
    """Video sharing."""

    def test_create_share(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            user, _ = users.register("sharer")
            share = users.create_share(user.id, "job_abc", "/video.mp4")
            assert share.share_id is not None
            assert share.share_url.startswith("/shared/")

    def test_get_share_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            user, _ = users.register("sharer2")
            share = users.create_share(user.id, "job_xyz", "/video.mp4")
            result = users.get_share(share.share_id)
            assert result is not None

    def test_get_share_by_url(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            user, _ = users.register("sharer3")
            share = users.create_share(user.id, "job", "/video.mp4")
            # get_share expects share_id, not URL — extract from share_url
            share_id = share.share_url.replace("/shared/", "")
            result = users.get_share(share_id)
            assert result is not None

    def test_expired_share(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            user, _ = users.register("sharer4")
            import time
            share = users.create_share(user.id, "job", "/video.mp4")
            share.expires_at = time.time() - 1
            assert share.is_expired is True

    def test_nonexistent_share(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            users = UserManager(data_dir=d)
            assert users.get_share("/shared/nonexistent") is None
