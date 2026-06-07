"""Tests for the GalleryManager and GalleryItem."""

import tempfile

from fitstream.core.gallery import GalleryItem, GalleryManager


class TestGalleryItem:
    def test_creation(self):
        e = GalleryItem(id="abc", video_path="/v.mp4", prompt="test", type="animate")
        assert e.id == "abc"
        assert e.prompt == "test"
        assert e.favorite is False

    def test_to_dict(self):
        e = GalleryItem(id="x", video_path="/v.mp4", prompt="p", type="story", tags=["tag1"])
        d = e.to_dict()
        assert d["id"] == "x"
        assert d["tags"] == ["tag1"]

    def test_matches_search(self):
        e = GalleryItem(
            id="s", video_path="/v.mp4", prompt="walking in paris", type="animate", tags=["fashion"]
        )
        assert e.matches_search("paris") is True
        assert e.matches_search("fashion") is True
        assert e.matches_search("tokyo") is False


class TestGalleryManager:
    def test_add_and_get(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("job1", "/v.mp4", type="animate", prompt="test prompt")
            result = g.list_items()
            items = result["items"] if isinstance(result, dict) else result
            assert len(items) == 1
            assert items[0]["id"] == "job1"

    def test_add_with_tags(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("job2", "/v.mp4", type="story", prompt="test", tags=["fashion"])
            assert g.get_item("job2") is not None
            assert "fashion" in g.get_item("job2").tags

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as d:
            assert GalleryManager(gallery_dir=d).get_item("nope") is None

    def test_toggle_favorite(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("job3", "/v.mp4", type="animate", prompt="t")
            g.toggle_favorite("job3")
            assert g.get_item("job3").favorite is True
            g.toggle_favorite("job3")
            assert g.get_item("job3").favorite is False

    def test_search(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("a", "/v.mp4", type="animate", prompt="walking in paris")
            g.add_from_job("b", "/v.mp4", type="story", prompt="dancing in tokyo")
            assert len(g.search("paris")) == 1

    def test_remove_item(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("rx", "/v.mp4", type="animate", prompt="p")
            assert g.remove_item("rx") is True
            assert g.get_item("rx") is None

    def test_add_tags(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("tx", "/v.mp4", type="story", prompt="p")
            g.add_tags("tx", ["new_tag"])
            assert "new_tag" in g.get_item("tx").tags

    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as d:
            g1 = GalleryManager(gallery_dir=d)
            g1.add_from_job("pjob", "/v.mp4", type="animate", prompt="persist")
            del g1
            g2 = GalleryManager(gallery_dir=d)
            e = g2.get_item("pjob")
            assert e is not None
            assert e.prompt == "persist"

    def test_get_stats(self):
        with tempfile.TemporaryDirectory() as d:
            g = GalleryManager(gallery_dir=d)
            g.add_from_job("a", "/v.mp4", type="animate", prompt="p1")
            g.add_from_job("b", "/v.mp4", type="story", prompt="p2")
            stats = g.get_stats()
            assert stats.get("total_items", 0) == 2
