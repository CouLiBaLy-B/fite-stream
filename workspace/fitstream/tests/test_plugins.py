"""Tests for plugin system."""

import pytest
from fitstream.core.plugins import PluginRegistry, PluginInfo


class TestPluginRegistry:
    def setup_method(self):
        PluginRegistry.clear()

    def test_register_pipeline(self):
        @PluginRegistry.pipeline("test_pipe", description="Test pipeline")
        class TestPipeline:
            pass

        info = PluginRegistry.get_pipeline("test_pipe")
        assert info is not None
        assert info.name == "test_pipe"
        assert info.type == "pipeline"
        assert info.cls is TestPipeline

    def test_register_model(self):
        @PluginRegistry.model("test_model", description="Test model")
        class TestModel:
            pass

        info = PluginRegistry.get_model("test_model")
        assert info is not None
        assert info.type == "model"

    def test_register_preprocessor(self):
        @PluginRegistry.preprocessor("test_pre", description="Test pre")
        def my_preprocessor(image):
            return image

        info = PluginRegistry.get_preprocessor("test_pre")
        assert info is not None
        assert info.factory is my_preprocessor

    def test_register_exporter(self):
        @PluginRegistry.exporter("test_exp")
        class TestExporter:
            pass

        info = PluginRegistry.get_exporter("test_exp")
        assert info is not None

    def test_list_all(self):
        @PluginRegistry.pipeline("p1")
        class P1:
            pass

        @PluginRegistry.model("m1")
        class M1:
            pass

        result = PluginRegistry.list_all()
        assert len(result["pipelines"]) == 1
        assert len(result["models"]) == 1
        assert result["pipelines"][0]["name"] == "p1"

    def test_count(self):
        PluginRegistry.clear()

        @PluginRegistry.pipeline("a")
        class A:
            pass

        @PluginRegistry.pipeline("b")
        class B:
            pass

        assert PluginRegistry.count() == 2

    def test_get_nonexistent(self):
        assert PluginRegistry.get_pipeline("nonexistent") is None

    def test_clear(self):
        @PluginRegistry.pipeline("temp")
        class Temp:
            pass

        PluginRegistry.clear()
        assert PluginRegistry.count() == 0

    def test_plugin_info_to_dict(self):
        info = PluginInfo(name="test", type="pipeline", description="desc", version="1.0")
        d = info.to_dict()
        assert d["name"] == "test"
        assert d["type"] == "pipeline"
        assert "cls" not in d  # cls should not be in dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
