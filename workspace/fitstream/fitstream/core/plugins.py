"""
FitStream Plugin System
Extensible architecture for registering custom pipelines, models, and processors.

A plugin is a Python module/class that registers capabilities with FitStream:
  - Custom pipelines (new generation modes)
  - Custom model loaders (new AI models)
  - Custom preprocessors (new image/video transforms)
  - Custom exporters (new output formats)

Usage:
    # Register a plugin
    from fitstream.core.plugins import PluginRegistry

    @PluginRegistry.pipeline("my_pipeline")
    class MyCustomPipeline:
        def generate(self, **kwargs) -> None:
            ...

    # Discover and use
    registry = PluginRegistry()
    registry.load_plugins("./plugins/")
    pipeline = registry.get_pipeline("my_pipeline")
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Type
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class PluginInfo:
    """Metadata about a registered plugin."""
    name: str
    type: str          # "pipeline", "model", "preprocessor", "exporter"
    description: str = ""
    version: str = "0.1.0"
    author: str = ""
    cls: Optional[Type] = None
    factory: Optional[Callable] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """To dict."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "version": self.version,
            "author": self.author,
        }


class PluginRegistry:
    """
    Central registry for FitStream plugins.

    Supports:
    - Decorator-based registration (@PluginRegistry.pipeline("name"))
    - Auto-discovery from a plugins directory
    - Plugin listing and introspection
    """

    _pipelines: Dict[str, PluginInfo] = {}
    _models: Dict[str, PluginInfo] = {}
    _preprocessors: Dict[str, PluginInfo] = {}
    _exporters: Dict[str, PluginInfo] = {}

    # ---------- Decorator-based registration ----------

    @classmethod
    def pipeline(cls, name: str, description: str = "", version: str = "0.1.0", author: str = ""):
        """Decorator to register a pipeline plugin."""
        def decorator(pipeline_cls):
            cls._pipelines[name] = PluginInfo(
                name=name, type="pipeline", description=description,
                version=version, author=author, cls=pipeline_cls,
            )
            logger.debug(f"Plugin registered: pipeline '{name}'")
            return pipeline_cls
        return decorator

    @classmethod
    def model(cls, name: str, description: str = "", version: str = "0.1.0", author: str = ""):
        """Decorator to register a model loader plugin."""
        def decorator(model_cls):
            cls._models[name] = PluginInfo(
                name=name, type="model", description=description,
                version=version, author=author, cls=model_cls,
            )
            logger.debug(f"Plugin registered: model '{name}'")
            return model_cls
        return decorator

    @classmethod
    def preprocessor(cls, name: str, description: str = ""):
        """Decorator to register a preprocessor plugin."""
        def decorator(func_or_cls):
            cls._preprocessors[name] = PluginInfo(
                name=name, type="preprocessor", description=description,
                cls=func_or_cls if isinstance(func_or_cls, type) else None,
                factory=func_or_cls if not isinstance(func_or_cls, type) else None,
            )
            return func_or_cls
        return decorator

    @classmethod
    def exporter(cls, name: str, description: str = ""):
        """Decorator to register an exporter plugin."""
        def decorator(func_or_cls):
            cls._exporters[name] = PluginInfo(
                name=name, type="exporter", description=description,
                cls=func_or_cls if isinstance(func_or_cls, type) else None,
                factory=func_or_cls if not isinstance(func_or_cls, type) else None,
            )
            return func_or_cls
        return decorator

    # ---------- Getters ----------

    @classmethod
    def get_pipeline(cls, name: str) -> Optional[PluginInfo]:
        return cls._pipelines.get(name)

    @classmethod
    def get_model(cls, name: str) -> Optional[PluginInfo]:
        return cls._models.get(name)

    @classmethod
    def get_preprocessor(cls, name: str) -> Optional[PluginInfo]:
        return cls._preprocessors.get(name)

    @classmethod
    def get_exporter(cls, name: str) -> Optional[PluginInfo]:
        return cls._exporters.get(name)

    # ---------- Discovery ----------

    @classmethod
    def load_plugins(cls, plugins_dir: str = "./plugins"):
        """
        Auto-discover and load plugins from a directory.
        Each .py file in the directory is imported; any decorators
        inside will self-register.
        """
        plugins_path = Path(plugins_dir)
        if not plugins_path.exists():
            logger.debug(f"No plugins directory at {plugins_dir}")
            return 0

        # Add to Python path
        sys.path.insert(0, str(plugins_path.parent))

        loaded = 0
        for py_file in sorted(plugins_path.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"plugins.{py_file.stem}"
            try:
                importlib.import_module(module_name)
                loaded += 1
                logger.info(f"🔌 Plugin loaded: {py_file.name}")
            except (ImportError, AttributeError, OSError) as e:
                logger.warning(f"⚠️ Failed to load plugin {py_file.name}: {e}")

        return loaded

    # ---------- Listing ----------

    @classmethod
    def list_all(cls) -> Dict[str, List[dict]]:
        """List all registered plugins by type."""
        return {
            "pipelines": [p.to_dict() for p in cls._pipelines.values()],
            "models": [p.to_dict() for p in cls._models.values()],
            "preprocessors": [p.to_dict() for p in cls._preprocessors.values()],
            "exporters": [p.to_dict() for p in cls._exporters.values()],
        }

    @classmethod
    def count(cls) -> int:
        """Count."""
        return (len(cls._pipelines) + len(cls._models) +
                len(cls._preprocessors) + len(cls._exporters))

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (mainly for testing)."""
        cls._pipelines.clear()
        cls._models.clear()
        cls._preprocessors.clear()
        cls._exporters.clear()
