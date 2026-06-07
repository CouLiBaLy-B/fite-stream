"""FitStream Generation Pipelines — lazy imports to avoid torch at import time."""


def __getattr__(name: str):
    _map = {
        "BasePipeline": ".base",
        "AnimatePipeline": ".animate",
        "StoryPipeline": ".story",
        "TryOnPipeline": ".tryon",
        "LoomPipeline": ".loom",
        "LoomNativePipeline": ".loom_native",
        "ExtendPipeline": ".extend",
        "StyleTransferPipeline": ".style_transfer",
        "V2VRestylePipeline": ".v2v_restyle",
        "RealTimePipeline": ".realtime",
    }
    if name in _map:
        import importlib

        module = importlib.import_module(_map[name], package=__name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
