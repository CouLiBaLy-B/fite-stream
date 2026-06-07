"""Tests for generation cache."""

import os
import time
import tempfile
import pytest
from fitstream.core.cache import GenerationCache, CacheEntry


@pytest.fixture
def cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield GenerationCache(cache_dir=tmpdir, max_size_gb=0.001)  # 1MB for testing


@pytest.fixture
def dummy_video():
    """Create a small dummy video file."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content " * 100)
        yield f.name
    os.unlink(f.name)


class TestMakeKey:
    def test_deterministic(self):
        """Same inputs → same key."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"image data")
            img_path = f.name

        k1 = GenerationCache.make_key(img_path, "test prompt", seed=42)
        k2 = GenerationCache.make_key(img_path, "test prompt", seed=42)
        assert k1 == k2

        os.unlink(img_path)

    def test_different_prompt_different_key(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"image data")
            img_path = f.name

        k1 = GenerationCache.make_key(img_path, "prompt A", seed=42)
        k2 = GenerationCache.make_key(img_path, "prompt B", seed=42)
        assert k1 != k2

        os.unlink(img_path)

    def test_different_seed_different_key(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"image data")
            img_path = f.name

        k1 = GenerationCache.make_key(img_path, "same prompt", seed=1)
        k2 = GenerationCache.make_key(img_path, "same prompt", seed=2)
        assert k1 != k2

        os.unlink(img_path)


class TestCacheOperations:
    def test_put_and_get(self, cache, dummy_video):
        cache.put("key1", video_path=dummy_video, metadata={"seed": 42})
        entry = cache.get("key1")
        assert entry is not None
        assert entry.video_path == dummy_video
        assert entry.metadata["seed"] == 42

    def test_miss(self, cache):
        assert cache.get("nonexistent") is None

    def test_hit_increments_access_count(self, cache, dummy_video):
        cache.put("key2", video_path=dummy_video)
        cache.get("key2")
        cache.get("key2")
        entry = cache.get("key2")
        assert entry.access_count == 3

    def test_expired_entry_returns_none(self, cache, dummy_video):
        cache.put("expired", video_path=dummy_video, ttl=0.01)
        time.sleep(0.02)
        assert cache.get("expired") is None

    def test_invalidate(self, cache, dummy_video):
        cache.put("inv1", video_path=dummy_video)
        assert cache.invalidate("inv1") is True
        assert cache.get("inv1") is None

    def test_invalidate_nonexistent(self, cache):
        assert cache.invalidate("nope") is False

    def test_clear(self, cache, dummy_video):
        cache.put("c1", video_path=dummy_video)
        cache.put("c2", video_path=dummy_video)
        cache.clear()
        assert cache.get("c1") is None
        assert cache.get("c2") is None


class TestCacheStats:
    def test_stats(self, cache, dummy_video):
        cache.put("s1", video_path=dummy_video)
        cache.get("s1")          # hit
        cache.get("missing")     # miss

        stats = cache.get_stats()
        assert stats["entries"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestCachePersistence:
    def test_persist_and_reload(self, dummy_video):
        with tempfile.TemporaryDirectory() as tmpdir:
            c1 = GenerationCache(cache_dir=tmpdir)
            c1.put("persist_key", video_path=dummy_video, metadata={"test": True})

            c2 = GenerationCache(cache_dir=tmpdir)
            entry = c2.get("persist_key")
            assert entry is not None
            assert entry.metadata["test"] is True


class TestCacheEntry:
    def test_is_expired(self):
        entry = CacheEntry(key="k", video_path="/v", created_at=time.time() - 100, 
                           last_accessed=time.time(), ttl=10)
        assert entry.is_expired is True

    def test_not_expired(self):
        entry = CacheEntry(key="k", video_path="/v", created_at=time.time(),
                           last_accessed=time.time(), ttl=86400)
        assert entry.is_expired is False

    def test_age_hours(self):
        entry = CacheEntry(key="k", video_path="/v", created_at=time.time() - 7200,
                           last_accessed=time.time())
        assert abs(entry.age_hours - 2.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
