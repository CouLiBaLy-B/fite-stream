"""Tests for the PluginRegistry and plugin system."""

from fitstream.core.plugins import PluginInfo, PluginRegistry


class TestPluginInfo:
    """PluginInfo dataclass tests."""

    def test_creation(self) -> None:
        info = PluginInfo(name="test", type="pipeline")
        assert info.name == "test"
        assert info.type == "pipeline"
        assert info.description == ""

    def test_to_dict(self) -> None:
        info = PluginInfo(
            name="mypipe", type="pipeline", description="My pipeline", version="2.0", author="Test"
        )
        d = info.to_dict()
        assert d["name"] == "mypipe"
        assert d["type"] == "pipeline"
        assert d["version"] == "2.0"
        assert d["author"] == "Test"
        assert d["description"] == "My pipeline"


class TestPluginRegistryClassMethods:
    """All registry methods are classmethods on PluginRegistry."""

    def setup_method(self) -> None:
        PluginRegistry.clear()

    def teardown_method(self) -> None:
        PluginRegistry.clear()

    def _find(self, items, name):
        return next((p for p in items if p["name"] == name), None)

    def test_register_pipeline_decorator(self) -> None:
        @PluginRegistry.pipeline("my_pipeline", description="Test pipeline")
        class MyPipeline:
            pass

        plugins = PluginRegistry.list_all()
        assert self._find(plugins["pipelines"], "my_pipeline") is not None

    def test_register_exporter_decorator(self) -> None:
        @PluginRegistry.exporter("my_exporter", description="Test exporter")
        class MyExporter:
            pass

        plugins = PluginRegistry.list_all()
        assert self._find(plugins["exporters"], "my_exporter") is not None

    def test_register_model_decorator(self) -> None:
        @PluginRegistry.model("my_model", description="Test model")
        class MyModel:
            pass

        plugins = PluginRegistry.list_all()
        assert self._find(plugins["models"], "my_model") is not None

    def test_register_multiple_pipelines(self) -> None:
        @PluginRegistry.pipeline("p1")
        class P1:
            pass

        @PluginRegistry.pipeline("p2")
        class P2:
            pass

        assert PluginRegistry.count() >= 2

    def test_list_all_structure(self) -> None:
        plugins = PluginRegistry.list_all()
        assert "pipelines" in plugins
        assert "models" in plugins
        assert "preprocessors" in plugins
        assert "exporters" in plugins

    def test_get_pipeline(self) -> None:
        @PluginRegistry.pipeline("find_me", description="Found")
        class FindMe:
            pass

        info = PluginRegistry.get_pipeline("find_me")
        assert info is not None
        assert info.description == "Found"

    def test_get_pipeline_not_found(self) -> None:
        assert PluginRegistry.get_pipeline("nonexistent") is None

    def test_get_exporter(self) -> None:
        @PluginRegistry.exporter("myexp", description="Export")
        class MyExp:
            pass

        info = PluginRegistry.get_exporter("myexp")
        assert info is not None
        assert info.type == "exporter"
        assert info.description == "Export"

    def test_duplicate_registration(self) -> None:
        @PluginRegistry.pipeline("dup")
        class First:
            pass

        @PluginRegistry.pipeline("dup", description="overwritten")
        class Second:
            pass

        info = PluginRegistry.get_pipeline("dup")
        assert info is not None
        assert info.description == "overwritten"

    def test_count_and_clear(self) -> None:
        @PluginRegistry.pipeline("temp")
        class Temp:
            pass

        assert PluginRegistry.count() > 0
        PluginRegistry.clear()
        assert PluginRegistry.count() == 0
