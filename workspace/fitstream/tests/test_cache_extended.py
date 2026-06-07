"""Tests for GenerationCache."""

import os
import tempfile
import time

from fitstream.core.cache import CacheEntry, GenerationCache


class TestCacheEntry:
    def test_creation(self):
        e = CacheEntry(
            key="abc", video_path="/v.mp4", created_at=time.time(), last_accessed=time.time()
        )
        assert e.key == "abc"
        assert e.video_path == "/v.mp4"

    def test_is_expired(self):
        now = time.time()
        e = CacheEntry(key="k", video_path="/v.mp4", created_at=now - 2, last_accessed=now, ttl=1)
        assert e.is_expired is True
        e2 = CacheEntry(key="k2", video_path="/v.mp4", created_at=now, last_accessed=now, ttl=86400)
        assert e2.is_expired is False

    def test_age_hours(self):
        now = time.time()
        e = CacheEntry(key="k", video_path="/v.mp4", created_at=now - 3600, last_accessed=now)
        assert abs(e.age_hours - 1.0) < 0.1


class TestGenerationCache:
    def _make_video(self, d):
        p = os.path.join(d, "test.mp4")
        with open(p, "w") as f:
            f.write("fake video data")
        return p

    def test_put_and_get(self):
        with tempfile.TemporaryDirectory() as d:
            c = GenerationCache(cache_dir=d)
            vp = self._make_video(d)
            c.put("key1", vp, metadata={"gen": 5.0})
            entry = c.get("key1")
            assert entry is not None
            assert entry.video_path == vp

    def test_get_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            c = GenerationCache(cache_dir=d)
            c.put("key1", "/nonexistent/video.mp4")
            assert c.get("key1") is None

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as d:
            assert GenerationCache(cache_dir=d).get("nope") is None

    def test_get_stats(self):
        with tempfile.TemporaryDirectory() as d:
            c = GenerationCache(cache_dir=d)
            vp = self._make_video(d)
            c.put("a", vp)
            c.put("b", vp)
            s = c.get_stats()
            assert s.get("entries", 0) >= 2

    def test_invalidate(self):
        with tempfile.TemporaryDirectory() as d:
            c = GenerationCache(cache_dir=d)
            vp = self._make_video(d)
            c.put("key", vp)
            assert c.invalidate("key") is True
            assert c.get("key") is None

    def test_invalidate_nonexistent(self):
        with tempfile.TemporaryDirectory() as d:
            assert GenerationCache(cache_dir=d).invalidate("nope") is False

    def test_clear(self):
        with tempfile.TemporaryDirectory() as d:
            c = GenerationCache(cache_dir=d)
            vp = self._make_video(d)
            c.put("a", vp)
            c.put("b", vp)
            c.clear()
            assert c.get("a") is None
            assert c.get("b") is None

    def test_make_key_deterministic(self):
        k1 = GenerationCache.make_key("prompt", "style")
        k2 = GenerationCache.make_key("prompt", "style")
        assert k1 == k2

    def test_make_key_different(self):
        k1 = GenerationCache.make_key("prompt1", "style1")
        k2 = GenerationCache.make_key("prompt2", "style2")
        assert k1 != k2

    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as d:
            vp = self._make_video(d)
            c1 = GenerationCache(cache_dir=d)
            c1.put("pk", vp, metadata={"type": "persist"})
            del c1
            c2 = GenerationCache(cache_dir=d)
            entry = c2.get("pk")
            assert entry is not None
