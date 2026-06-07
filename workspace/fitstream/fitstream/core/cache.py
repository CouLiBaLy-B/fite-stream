"""
FitStream Cache Layer
Intelligent caching to avoid re-generating identical results.

Cache key = hash(image + prompt + params).
If the same generation was already done, return the cached result instantly.

Features:
  - Content-addressable caching (hash-based keys)
  - Configurable max cache size (LRU eviction)
  - Disk-backed persistence
  - TTL (time-to-live) for auto-expiration
  - Cache stats and hit-rate monitoring
"""

import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class CacheEntry:
    """A single cache entry."""

    key: str
    video_path: str
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: float = 86400.0  # 24 hours default
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Is expired."""
        return time.time() - self.created_at > self.ttl

    @property
    def age_hours(self) -> float:
        """Age hours."""
        return (time.time() - self.created_at) / 3600


class GenerationCache:
    """
    LRU cache for generated videos with disk persistence.

    Usage:
        cache = GenerationCache("./cache", max_size_gb=10)

        # Check cache before generating
        key = cache.make_key(image_path, prompt, preset="standard", seed=42)
        cached = cache.get(key)
        if cached:
            return cached.video_path  # instant result!

        # After generating, store in cache
        cache.put(key, video_path="output.mp4", metadata={"seed": 42})
    """

    def __init__(
        self,
        cache_dir: str = "./cache",
        max_size_gb: float = 10.0,
        default_ttl: float = 86400.0,  # 24 hours
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.default_ttl = default_ttl

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.cache_dir / "index.json"

        # LRU ordered dict: oldest first
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

        # Stats
        self._hits = 0
        self._misses = 0

        self._load_index()

    @staticmethod
    def make_key(
        image_path: str,
        prompt: str,
        **params,
    ) -> str:
        """
        Generate a deterministic cache key from inputs.

        The key is a SHA-256 hash of:
        - Image file content (or path if content unavailable)
        - Prompt text
        - Sorted generation parameters

        Same inputs → same key → cache hit.
        """
        hasher = hashlib.sha256()

        # Hash image content
        image_path_obj = Path(image_path)
        if image_path_obj.exists():
            hasher.update(image_path_obj.read_bytes())
        else:
            hasher.update(str(image_path).encode())

        # Hash prompt
        hasher.update(prompt.encode())

        # Hash sorted params
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        hasher.update(sorted_params.encode())

        return hasher.hexdigest()[:24]  # 24 chars is enough

    def get(self, key: str) -> CacheEntry | None:
        """
        Look up a cached result.
        Returns the CacheEntry if found and valid, None otherwise.
        """
        entry = self._entries.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Check expiration
        if entry.is_expired:
            self._remove(key)
            self._misses += 1
            return None

        # Check if video file still exists
        if not os.path.exists(entry.video_path):
            self._remove(key)
            self._misses += 1
            return None

        # Cache hit — update access stats
        entry.last_accessed = time.time()
        entry.access_count += 1

        # Move to end (most recently used)
        self._entries.move_to_end(key)

        self._hits += 1
        logger.debug(f"📦 Cache HIT: {key[:12]}... (accessed {entry.access_count}x)")
        return entry

    def put(
        self,
        key: str,
        video_path: str,
        metadata: dict[str, Any] | None = None,
        ttl: float | None = None,
    ) -> CacheEntry:
        """Store a generated result in the cache."""
        # Evict if over size limit
        self._evict_if_needed()

        entry = CacheEntry(
            key=key,
            video_path=video_path,
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=ttl or self.default_ttl,
            metadata=metadata or {},
        )

        self._entries[key] = entry
        self._entries.move_to_end(key)

        self._save_index()
        logger.debug(f"📦 Cache PUT: {key[:12]}... → {video_path}")
        return entry

    def invalidate(self, key: str) -> bool:
        if key in self._entries:
            self._remove(key)
            return True
        return False

    def clear(self) -> None:
        """Remove a specific entry from cache."""
        """Clear the entire cache."""
        self._entries.clear()
        self._save_index()
        logger.info("📦 Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total = self._hits + self._misses
        entries = list(self._entries.values())

        # Calculate total cached size
        total_bytes = 0
        for entry in entries:
            if os.path.exists(entry.video_path):
                total_bytes += os.path.getsize(entry.video_path)

        return {
            "entries": len(entries),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(1, total),
            "total_size_mb": total_bytes / (1024 * 1024),
            "max_size_gb": self.max_size_bytes / (1024**3),
            "oldest_hours": max((e.age_hours for e in entries), default=0),
            "most_accessed": max((e.access_count for e in entries), default=0),
        }

    def _remove(self, key: str) -> None:
        if key in self._entries:
            del self._entries[key]
            self._save_index()

    def _evict_if_needed(self) -> None:
        """Remove an entry."""
        """Evict oldest entries if cache exceeds max size."""
        total_bytes = 0
        for entry in self._entries.values():
            if os.path.exists(entry.video_path):
                total_bytes += os.path.getsize(entry.video_path)

        while total_bytes > self.max_size_bytes and self._entries:
            # Remove oldest (first item in OrderedDict)
            oldest_key, oldest_entry = next(iter(self._entries.items()))
            if os.path.exists(oldest_entry.video_path):
                total_bytes -= os.path.getsize(oldest_entry.video_path)
            del self._entries[oldest_key]
            logger.debug(f"📦 Cache evicted: {oldest_key[:12]}...")

    def _save_index(self) -> None:
        """Persist cache index to disk."""
        try:
            data = {
                "entries": [
                    {
                        "key": e.key,
                        "video_path": e.video_path,
                        "created_at": e.created_at,
                        "last_accessed": e.last_accessed,
                        "access_count": e.access_count,
                        "ttl": e.ttl,
                        "metadata": e.metadata,
                    }
                    for e in self._entries.values()
                ],
                "stats": {"hits": self._hits, "misses": self._misses},
            }
            with open(self._index_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Cache index save failed: {e}")

    def _load_index(self) -> None:
        """Load cache index from disk."""
        if not self._index_path.exists():
            return
        try:
            with open(self._index_path) as f:
                data = json.load(f)

            for entry_data in data.get("entries", []):
                entry = CacheEntry(
                    key=entry_data["key"],
                    video_path=entry_data["video_path"],
                    created_at=entry_data.get("created_at", 0),
                    last_accessed=entry_data.get("last_accessed", 0),
                    access_count=entry_data.get("access_count", 0),
                    ttl=entry_data.get("ttl", self.default_ttl),
                    metadata=entry_data.get("metadata", {}),
                )
                if not entry.is_expired and os.path.exists(entry.video_path):
                    self._entries[entry.key] = entry

            stats = data.get("stats", {})
            self._hits = stats.get("hits", 0)
            self._misses = stats.get("misses", 0)

            if self._entries:
                logger.info(f"📦 Cache loaded: {len(self._entries)} entries")
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Cache index load failed: {e}")
