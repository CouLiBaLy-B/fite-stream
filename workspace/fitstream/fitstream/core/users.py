"""
FitStream Multi-User System
User accounts, profiles, quotas, and sharing.

Features:
  - User registration and authentication (API key based)
  - Per-user generation quotas (daily limits)
  - User galleries (private by default)
  - Video sharing (public links)
  - Usage tracking per user

Usage:
    users = UserManager()

    # Register
    user = users.register("alice", email="alice@example.com")
    # → user.api_key = "fs_abc123..."

    # Authenticate
    user = users.authenticate("fs_abc123...")

    # Check quota
    if users.check_quota(user.id):
        # proceed with generation
        users.record_usage(user.id, "animate", generation_time=42.0)
"""

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


@dataclass
class User:
    """A FitStream user."""

    id: str
    username: str
    email: str = ""
    api_key_hash: str = ""  # SHA-256 of API key

    # Quota
    daily_limit: int = 50  # Max generations per day
    monthly_limit: int = 1000

    # Stats
    total_generations: int = 0
    today_generations: int = 0
    last_generation_date: str = ""
    total_generation_time: float = 0.0

    # Account
    created_at: float = field(default_factory=time.time)
    active: bool = True
    role: str = "user"  # user, admin, premium

    def to_dict(self) -> dict:
        """To dict."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "daily_limit": self.daily_limit,
            "today_generations": self.today_generations,
            "total_generations": self.total_generations,
            "created_at": self.created_at,
        }


@dataclass
class SharedVideo:
    """A publicly shared video."""

    share_id: str
    job_id: str
    user_id: str
    video_path: str
    prompt: str = ""
    created_at: float = field(default_factory=time.time)
    views: int = 0
    expires_at: float | None = None  # None = never expires

    @property
    def is_expired(self) -> bool:
        """Is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    @property
    def share_url(self) -> str:
        """Share url."""
        return f"/shared/{self.share_id}"


class UserManager:
    """
    Multi-user management system with quotas and sharing.
    """

    def __init__(self, data_dir: str = "./data/users") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._users: dict[str, User] = {}
        self._key_to_user: dict[str, str] = {}  # api_key_hash → user_id
        self._shares: dict[str, SharedVideo] = {}

        self._load()

    def register(
        self,
        username: str,
        email: str = "",
        role: str = "user",
        daily_limit: int = 50,
    ) -> tuple:
        """
        Register a new user.
        Returns (User, api_key) — the API key is shown only once!
        """
        # Check username uniqueness
        for u in self._users.values():
            if u.username == username:
                raise ValueError(f"Username '{username}' already taken")

        user_id = secrets.token_hex(8)
        api_key = f"fs_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        user = User(
            id=user_id,
            username=username,
            email=email,
            api_key_hash=api_key_hash,
            role=role,
            daily_limit=daily_limit,
        )

        self._users[user_id] = user
        self._key_to_user[api_key_hash] = user_id
        self._save()

        logger.info(f"👤 User registered: {username} (id={user_id})")
        return user, api_key

    def authenticate(self, api_key: str) -> User | None:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        user_id = self._key_to_user.get(key_hash)

        if user_id:
            user = self._users.get(user_id)
            if user and user.active:
                return user
        return None

    def get_user(self, user_id: str) -> User | None:
        """Authenticate a user by API key."""
        return self._users.get(user_id)

    def list_users(self) -> list[dict]:
        """Get user."""
        """List users."""
        return [u.to_dict() for u in self._users.values()]

    def check_quota(self, user_id: str) -> bool:
        user = self._users.get(user_id)
        if not user:
            return False

        today = time.strftime("%Y-%m-%d")
        if user.last_generation_date != today:
            user.today_generations = 0
            user.last_generation_date = today

        return user.today_generations < user.daily_limit

    def get_remaining_quota(self, user_id: str) -> dict[str, int]:
        """Check if user has remaining quota for today."""
        user = self._users.get(user_id)
        if not user:
            return {"daily_remaining": 0, "daily_limit": 0}

        today = time.strftime("%Y-%m-%d")
        if user.last_generation_date != today:
            user.today_generations = 0

        return {
            "daily_remaining": max(0, user.daily_limit - user.today_generations),
            "daily_limit": user.daily_limit,
            "today_used": user.today_generations,
            "total_generations": user.total_generations,
        }

    def record_usage(self, user_id: str, gen_type: str, generation_time: float = 0.0) -> None:
        """Get remaining quota for a user."""
        user = self._users.get(user_id)
        if not user:
            return

        today = time.strftime("%Y-%m-%d")
        if user.last_generation_date != today:
            user.today_generations = 0
            user.last_generation_date = today

        user.today_generations += 1
        user.total_generations += 1
        user.total_generation_time += generation_time

        self._save()

    def create_share(
        self,
        user_id: str,
        job_id: str,
        video_path: str,
        prompt: str = "",
        expires_hours: float | None = None,
    ) -> SharedVideo:
        """Record a generation for quota tracking."""
        """Create a public share link for a video."""
        share_id = secrets.token_urlsafe(12)

        share = SharedVideo(
            share_id=share_id,
            job_id=job_id,
            user_id=user_id,
            video_path=video_path,
            prompt=prompt,
            expires_at=time.time() + (expires_hours * 3600) if expires_hours else None,
        )

        self._shares[share_id] = share
        self._save()

        logger.info(f"🔗 Share created: {share.share_url}")
        return share

    def get_share(self, share_id: str) -> SharedVideo | None:
        share = self._shares.get(share_id)
        if share and not share.is_expired:
            share.views += 1
            return share
        return None

    def revoke_api_key(self, user_id: str) -> str | None:
        """Get a shared video. Returns None if expired."""
        user = self._users.get(user_id)
        if not user:
            return None

        # Remove old key mapping
        self._key_to_user = {k: v for k, v in self._key_to_user.items() if v != user_id}

        # Generate new key
        new_key = f"fs_{secrets.token_urlsafe(32)}"
        new_hash = hashlib.sha256(new_key.encode()).hexdigest()
        user.api_key_hash = new_hash
        self._key_to_user[new_hash] = user_id

        self._save()
        return new_key

    def _save(self) -> None:
        """Revoke current API key and generate a new one."""
        try:
            data = {
                "users": {
                    uid: {
                        "id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "api_key_hash": u.api_key_hash,
                        "role": u.role,
                        "daily_limit": u.daily_limit,
                        "active": u.active,
                        "total_generations": u.total_generations,
                        "today_generations": u.today_generations,
                        "last_generation_date": u.last_generation_date,
                        "total_generation_time": u.total_generation_time,
                        "created_at": u.created_at,
                    }
                    for uid, u in self._users.items()
                },
                "shares": {
                    sid: {
                        "share_id": s.share_id,
                        "job_id": s.job_id,
                        "user_id": s.user_id,
                        "video_path": s.video_path,
                        "prompt": s.prompt,
                        "created_at": s.created_at,
                        "views": s.views,
                        "expires_at": s.expires_at,
                    }
                    for sid, s in self._shares.items()
                },
            }
            with open(self.data_dir / "users.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Failed to save user data: {e}")

    def _load(self) -> None:
        path = self.data_dir / "users.json"
        if not path.exists():
            return
        try:
            with open(path) as f:
                data = json.load(f)

            for uid, ud in data.get("users", {}).items():
                user = User(**{k: v for k, v in ud.items() if k in User.__dataclass_fields__})
                self._users[uid] = user
                if user.api_key_hash:
                    self._key_to_user[user.api_key_hash] = uid

            for sid, sd in data.get("shares", {}).items():
                self._shares[sid] = SharedVideo(
                    **{k: v for k, v in sd.items() if k in SharedVideo.__dataclass_fields__}
                )

            if self._users:
                logger.info(f"👤 Loaded {len(self._users)} users, {len(self._shares)} shares")
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Failed to load user data: {e}")
