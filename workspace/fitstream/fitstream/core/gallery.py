"""
FitStream Gallery Manager
Persistent gallery with thumbnails, tags, search, and metadata.

Features:
  - Auto-generate thumbnails from videos
  - Tag-based organization (style, type, garment, etc.)
  - Full-text search over prompts
  - Favorites / collections
  - Export / share
  - Disk-backed persistence (JSON index)
"""

import contextlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class GalleryItem:
    """A single gallery entry."""

    id: str
    video_path: str
    thumbnail_path: str = ""

    # Metadata
    type: str = ""  # animate, story, tryon, compose, style
    prompt: str = ""
    style: str = ""
    created_at: float = 0.0
    generation_time: float = 0.0
    duration_seconds: float = 0.0
    resolution: str = ""
    seed: int = 0
    num_frames: int = 0

    # Organization
    tags: list[str] = field(default_factory=list)
    favorite: bool = False
    collection: str = ""

    # Extra metadata from pipeline
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """To dict."""
        return asdict(self)

    def matches_search(self, query: str) -> bool:
        q = query.lower()
        searchable = f"{self.prompt} {self.type} {self.style} {' '.join(self.tags)} {self.collection}".lower()
        return q in searchable


class GalleryManager:
    """
    Manages the video gallery with persistence and search.

    Usage:
        gallery = GalleryManager("./gallery")

        # Add a completed generation
        gallery.add_from_job(job_id="abc123", video_path="out.mp4",
                             type="animate", prompt="walking in park", ...)

        # Search
        results = gallery.search("park", style="cinematic")

        # Browse
        page = gallery.list_items(offset=0, limit=20, sort="newest")
    """

    def __init__(self, gallery_dir: str = "./gallery") -> None:
        self.gallery_dir = Path(gallery_dir)
        self.thumbnails_dir = self.gallery_dir / "thumbnails"
        self.index_path = self.gallery_dir / "index.json"

        self.gallery_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)

        self._items: dict[str, GalleryItem] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load gallery index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path) as f:
                    data = json.load(f)
                for item_data in data.get("items", []):
                    item = GalleryItem(
                        **{
                            k: v
                            for k, v in item_data.items()
                            if k in GalleryItem.__dataclass_fields__
                        }
                    )
                    self._items[item.id] = item
                logger.info(f"📸 Gallery loaded: {len(self._items)} items")
            except (OSError, ValueError, KeyError) as e:
                logger.warning(f"Failed to load gallery index: {e}")

    def _save_index(self) -> None:
        """Save gallery index to disk."""
        try:
            data = {
                "version": 1,
                "count": len(self._items),
                "items": [item.to_dict() for item in self._items.values()],
            }
            with open(self.index_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Failed to save gallery index: {e}")

    def add_from_job(
        self,
        job_id: str,
        video_path: str,
        type: str = "animate",
        prompt: str = "",
        style: str = "",
        generation_time: float = 0.0,
        duration_seconds: float = 0.0,
        resolution: str = "",
        seed: int = 0,
        num_frames: int = 0,
        tags: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> GalleryItem:
        """Add a completed generation to the gallery."""

        # Generate thumbnail
        thumbnail_path = str(self.thumbnails_dir / f"{job_id}.jpg")
        self._generate_thumbnail(video_path, thumbnail_path)

        # Auto-generate tags from type and prompt
        auto_tags = [type]
        if style:
            auto_tags.append(style)

        item = GalleryItem(
            id=job_id,
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            type=type,
            prompt=prompt,
            style=style,
            created_at=time.time(),
            generation_time=generation_time,
            duration_seconds=duration_seconds,
            resolution=resolution,
            seed=seed,
            num_frames=num_frames,
            tags=auto_tags + (tags or []),
            extra=extra or {},
        )

        self._items[job_id] = item
        self._save_index()

        logger.info(f"📸 Added to gallery: {job_id} ({type})")
        return item

    def get_item(self, item_id: str) -> GalleryItem | None:
        return self._items.get(item_id)

    def remove_item(self, item_id: str) -> bool:
        if item_id in self._items:
            item = self._items.pop(item_id)
            # Clean up thumbnail
            if item.thumbnail_path and os.path.exists(item.thumbnail_path):
                with contextlib.suppress(OSError):
                    os.unlink(item.thumbnail_path)
            self._save_index()
            return True
        return False

    def toggle_favorite(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item:
            item.favorite = not item.favorite
            self._save_index()
            return item.favorite
        return False

    def add_tags(self, item_id: str, tags: list[str]) -> None:
        item = self._items.get(item_id)
        if item:
            for tag in tags:
                if tag not in item.tags:
                    item.tags.append(tag)
            self._save_index()

    def set_collection(self, item_id: str, collection: str) -> None:
        item = self._items.get(item_id)
        if item:
            item.collection = collection
            self._save_index()

    def list_items(
        self,
        offset: int = 0,
        limit: int = 20,
        sort: str = "newest",
        type_filter: str | None = None,
        style_filter: str | None = None,
        tag_filter: str | None = None,
        favorites_only: bool = False,
        collection: str | None = None,
    ) -> dict[str, Any]:
        """Assign an item to a collection."""
        """List gallery items with filtering, sorting, and pagination."""
        items = list(self._items.values())

        # Filters
        if type_filter:
            items = [i for i in items if i.type == type_filter]
        if style_filter:
            items = [i for i in items if i.style == style_filter]
        if tag_filter:
            items = [i for i in items if tag_filter in i.tags]
        if favorites_only:
            items = [i for i in items if i.favorite]
        if collection:
            items = [i for i in items if i.collection == collection]

        # Sort
        if sort == "newest":
            items.sort(key=lambda x: x.created_at, reverse=True)
        elif sort == "oldest":
            items.sort(key=lambda x: x.created_at)
        elif sort == "longest":
            items.sort(key=lambda x: x.duration_seconds, reverse=True)
        elif sort == "fastest":
            items.sort(key=lambda x: x.generation_time)

        total = len(items)
        page = items[offset : offset + limit]

        return {
            "items": [item.to_dict() for item in page],
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total,
        }

    def search(self, query: str, limit: int = 20) -> list[GalleryItem]:
        results = [item for item in self._items.values() if item.matches_search(query)]
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Full-text search over prompts, tags, and styles."""
        """Get gallery statistics."""
        items = list(self._items.values())
        return {
            "total_items": len(items),
            "total_duration": sum(i.duration_seconds for i in items),
            "total_generation_time": sum(i.generation_time for i in items),
            "favorites": sum(1 for i in items if i.favorite),
            "by_type": {
                t: sum(1 for i in items if i.type == t) for t in set(i.type for i in items)
            },
            "by_style": {
                s: sum(1 for i in items if i.style == s) for s in set(i.style for i in items) if s
            },
            "collections": list(set(i.collection for i in items if i.collection)),
        }

    def _generate_thumbnail(self, video_path: str, thumbnail_path: str) -> None:
        try:
            import cv2
            from PIL import Image

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return

            # Get frame from 25% into the video (usually more interesting than first frame)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = max(0, total // 4)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)

                # Resize thumbnail to 320px width
                ratio = 320 / img.width
                thumb_size = (320, int(img.height * ratio))
                img = img.resize(thumb_size, Image.LANCZOS)

                img.save(thumbnail_path, "JPEG", quality=80)
                logger.debug(f"Thumbnail generated: {thumbnail_path}")
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Thumbnail generation failed: {e}")
