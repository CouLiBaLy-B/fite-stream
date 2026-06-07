"""Shared pytest fixtures for FitStream tests."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory, clean up after test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_config(temp_dir):
    """Create a minimal config with temp output dir."""
    from fitstream.config import AnimateConfig, APIConfig, FitStreamConfig, ModelConfig

    return FitStreamConfig(
        output_dir=temp_dir,
        models_dir=temp_dir,
        animate=AnimateConfig(width=480, height=320, num_frames=33),
        model=ModelConfig(device="cpu"),
        api=APIConfig(max_concurrent_jobs=1, job_timeout=30),
    )


@pytest.fixture
def mock_model_manager():
    """ModelManager without GPU dependencies."""
    from fitstream.config import FitStreamConfig
    from fitstream.core.models.model_manager import ModelManager

    config = FitStreamConfig()
    config.model.device = "cpu"
    return ModelManager(config)


@pytest.fixture
def job_queue(temp_dir):
    """JobQueue with temp persistence."""
    from fitstream.core.job_queue import JobQueue

    return JobQueue(persist_dir=temp_dir)


@pytest.fixture
def rate_limiter():
    """Default rate limiter."""
    from fitstream.api.middleware import RateLimiter

    return RateLimiter(requests_per_minute=30, burst=50, generation_per_minute=5)


@pytest.fixture
def api_metrics():
    """Fresh API metrics collector."""
    from fitstream.api.middleware import APIMetrics

    return APIMetrics()


@pytest.fixture(autouse=True)
def reset_trace_context():
    """Reset tracing context variables between tests."""
    from fitstream.api.tracing import _request_start, _trace_id

    token_trace = _trace_id.set("")
    token_start = _request_start.set(0.0)
    yield
    _trace_id.reset(token_trace)
    _request_start.reset(token_start)


@pytest.fixture
def sample_image():
    """Generate a simple test image in memory (PIL)."""
    import numpy as np
    from PIL import Image

    img = Image.fromarray((np.random.rand(480, 640, 3) * 255).astype(np.uint8))
    return img


@pytest.fixture
def sample_image_path(temp_dir):
    """Save a test image to disk and return path."""
    import numpy as np
    from PIL import Image

    path = os.path.join(temp_dir, "test_image.jpg")
    img = Image.fromarray((np.random.rand(480, 640, 3) * 255).astype(np.uint8))
    img.save(path)
    return path
