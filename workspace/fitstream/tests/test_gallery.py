"""Tests for gallery manager — no GPU needed."""

import tempfile

import pytest

from fitstream.core.gallery import GalleryItem, GalleryManager


@pytest.fixture
def gallery():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield GalleryManager(gallery_dir=tmpdir)


class TestGalleryManager:
    def test_add_item(self, gallery):
        item = gallery.add_from_job(
            job_id="test001",
            video_path="/fake/video.mp4",
            type="animate",
            prompt="A person walking",
            style="cinematic",
            generation_time=42.5,
            duration_seconds=3.0,
            seed=123,
        )
        assert item.id == "test001"
        assert item.type == "animate"
        assert item.prompt == "A person walking"
        assert "animate" in item.tags
        assert "cinematic" in item.tags

    def test_get_item(self, gallery):
        gallery.add_from_job(job_id="abc", video_path="/v.mp4", prompt="test")
        item = gallery.get_item("abc")
        assert item is not None
        assert item.id == "abc"

    def test_get_nonexistent(self, gallery):
        assert gallery.get_item("nope") is None

    def test_remove_item(self, gallery):
        gallery.add_from_job(job_id="rm1", video_path="/v.mp4")
        assert gallery.remove_item("rm1") is True
        assert gallery.get_item("rm1") is None

    def test_remove_nonexistent(self, gallery):
        assert gallery.remove_item("nope") is False

    def test_toggle_favorite(self, gallery):
        gallery.add_from_job(job_id="fav1", video_path="/v.mp4")
        assert gallery.toggle_favorite("fav1") is True
        assert gallery.get_item("fav1").favorite is True
        assert gallery.toggle_favorite("fav1") is False

    def test_add_tags(self, gallery):
        gallery.add_from_job(job_id="tag1", video_path="/v.mp4")
        gallery.add_tags("tag1", ["portrait", "outdoor"])
        item = gallery.get_item("tag1")
        assert "portrait" in item.tags
        assert "outdoor" in item.tags

    def test_set_collection(self, gallery):
        gallery.add_from_job(job_id="col1", video_path="/v.mp4")
        gallery.set_collection("col1", "Paris Trip")
        assert gallery.get_item("col1").collection == "Paris Trip"

    def test_list_items(self, gallery):
        for i in range(5):
            gallery.add_from_job(
                job_id=f"list{i}",
                video_path=f"/v{i}.mp4",
                type="animate" if i % 2 == 0 else "story",
            )

        result = gallery.list_items()
        assert result["total"] == 5
        assert len(result["items"]) == 5

    def test_list_with_filter(self, gallery):
        gallery.add_from_job(job_id="a1", video_path="/v.mp4", type="animate")
        gallery.add_from_job(job_id="s1", video_path="/v.mp4", type="story")
        gallery.add_from_job(job_id="a2", video_path="/v.mp4", type="animate")

        result = gallery.list_items(type_filter="animate")
        assert result["total"] == 2

    def test_list_pagination(self, gallery):
        for i in range(10):
            gallery.add_from_job(job_id=f"p{i}", video_path=f"/v{i}.mp4")

        page1 = gallery.list_items(offset=0, limit=3)
        page2 = gallery.list_items(offset=3, limit=3)

        assert len(page1["items"]) == 3
        assert len(page2["items"]) == 3
        assert page1["has_more"] is True

    def test_list_favorites_only(self, gallery):
        gallery.add_from_job(job_id="f1", video_path="/v.mp4")
        gallery.add_from_job(job_id="f2", video_path="/v.mp4")
        gallery.toggle_favorite("f1")

        result = gallery.list_items(favorites_only=True)
        assert result["total"] == 1
        assert result["items"][0]["id"] == "f1"

    def test_search(self, gallery):
        gallery.add_from_job(job_id="s1", video_path="/v.mp4", prompt="Person in Paris garden")
        gallery.add_from_job(job_id="s2", video_path="/v.mp4", prompt="Cat on a sofa")
        gallery.add_from_job(job_id="s3", video_path="/v.mp4", prompt="Person on a Paris bridge")

        results = gallery.search("paris")
        assert len(results) == 2

    def test_search_by_tag(self, gallery):
        gallery.add_from_job(job_id="st1", video_path="/v.mp4", prompt="test")
        gallery.add_tags("st1", ["sunset", "romantic"])

        results = gallery.search("sunset")
        assert len(results) == 1

    def test_stats(self, gallery):
        gallery.add_from_job(
            job_id="x1",
            video_path="/v.mp4",
            type="animate",
            duration_seconds=3.0,
            generation_time=40.0,
        )
        gallery.add_from_job(
            job_id="x2",
            video_path="/v.mp4",
            type="story",
            duration_seconds=10.0,
            generation_time=120.0,
        )
        gallery.toggle_favorite("x1")

        stats = gallery.get_stats()
        assert stats["total_items"] == 2
        assert stats["favorites"] == 1
        assert stats["total_duration"] == 13.0
        assert stats["by_type"]["animate"] == 1
        assert stats["by_type"]["story"] == 1


class TestGalleryPersistence:
    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            g1 = GalleryManager(gallery_dir=tmpdir)
            g1.add_from_job(
                job_id="persist1", video_path="/v.mp4", prompt="Persistent item", style="anime"
            )
            g1.toggle_favorite("persist1")

            g2 = GalleryManager(gallery_dir=tmpdir)
            item = g2.get_item("persist1")
            assert item is not None
            assert item.prompt == "Persistent item"
            assert item.favorite is True
            assert item.style == "anime"


class TestGalleryItem:
    def test_matches_search(self):
        item = GalleryItem(
            id="t1",
            video_path="/v.mp4",
            prompt="sunset over the ocean",
            style="cinematic",
            tags=["romantic", "beach"],
        )
        assert item.matches_search("sunset") is True
        assert item.matches_search("OCEAN") is True  # case insensitive
        assert item.matches_search("beach") is True
        assert item.matches_search("cinematic") is True
        assert item.matches_search("mountain") is False

    def test_to_dict(self):
        item = GalleryItem(id="t2", video_path="/v.mp4")
        d = item.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == "t2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
