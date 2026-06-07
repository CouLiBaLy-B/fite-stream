"""Tests for ModelManager — the critical component that was missing."""

import pytest
from fitstream.config import FitStreamConfig
from fitstream.core.models.model_manager import ModelManager, _MockPipeline, _MockVAE


class TestModelManagerInit:
    """ModelManager initialization tests."""

    def test_default_init(self) -> None:
        mm = ModelManager()
        assert mm._loaded_model is None
        assert mm._loaded_model_key == ""

    def test_init_with_config(self) -> None:
        config = FitStreamConfig()
        mm = ModelManager(config)
        assert mm.config is config

    def test_init_custom_config(self) -> None:
        config = FitStreamConfig(output_dir="/custom/output")
        mm = ModelManager(config)
        assert mm.config.output_dir == "/custom/output"


class TestModelManagerLoad:
    """Model loading tests — uses MockPipeline when no GPU."""

    def test_load_returns_mock(self) -> None:
        mm = ModelManager()
        pipe = mm.load_vace_diffusers()
        assert pipe is not None
        # Should return the mock pipeline when torch is unavailable
        assert mm.is_loaded()

    def test_load_is_cached(self) -> None:
        mm = ModelManager()
        pipe1 = mm.load_vace_diffusers()
        pipe2 = mm.load_vace_diffusers()
        assert pipe1 is pipe2  # Same cached instance

    def test_load_different_key_reloads(self) -> None:
        mm = ModelManager()
        pipe1 = mm.load_vace_diffusers()
        pipe2 = mm.load_vace_diffusers("loomvideo")
        assert pipe1 is not pipe2  # Different model key → reload

    def test_is_loaded_after_load(self) -> None:
        mm = ModelManager()
        assert not mm.is_loaded()
        mm.load_vace_diffusers()
        assert mm.is_loaded()

    def test_is_loaded_specific_key(self) -> None:
        mm = ModelManager()
        mm.load_vace_diffusers("loomvideo")
        assert mm.is_loaded("loomvideo")
        assert not mm.is_loaded("vace")


class TestModelManagerUnload:
    """Unload behavior tests."""

    def test_unload_clears_model(self) -> None:
        mm = ModelManager()
        mm.load_vace_diffusers()
        assert mm.is_loaded()
        mm.unload()
        assert not mm.is_loaded()
        assert mm._loaded_model is None
        assert mm._loaded_model_key == ""

    def test_unload_idempotent(self) -> None:
        mm = ModelManager()
        mm.unload()  # Should not crash
        mm.unload()  # Should not crash
        assert not mm.is_loaded()

    def test_load_after_unload(self) -> None:
        mm = ModelManager()
        pipe1 = mm.load_vace_diffusers()
        mm.unload()
        pipe2 = mm.load_vace_diffusers()
        assert pipe1 is not pipe2  # New instance after reload


class TestGPUStatus:
    """GPU status reporting tests."""

    def test_get_gpu_status_structure(self) -> None:
        mm = ModelManager()
        status = mm.get_gpu_status()
        assert "available" in status
        assert "gpu_name" in status
        assert "total_gb" in status
        assert "free_gb" in status
        assert "used_gb" in status
        assert "utilization_pct" in status
        assert "loaded_model" in status

    def test_gpu_status_not_available_by_default(self) -> None:
        mm = ModelManager()
        status = mm.get_gpu_status()
        assert status["available"] is False  # No GPU in test env

    def test_gpu_status_shows_loaded_model(self) -> None:
        mm = ModelManager()
        status = mm.get_gpu_status()
        assert status["loaded_model"] is None
        mm.load_vace_diffusers()
        status = mm.get_gpu_status()
        assert status["loaded_model"] is not None


class TestMockPipeline:
    """MockPipeline for GPU-less environments."""

    def test_mock_pipeline_callable(self) -> None:
        pipe = _MockPipeline()
        result = pipe(prompt="test", width=512, height=256, num_frames=16)
        assert hasattr(result, "frames")
        assert len(result.frames) == 16

    def test_mock_pipeline_to_device(self) -> None:
        pipe = _MockPipeline()
        result = pipe.to("cuda")
        assert result is pipe  # Same instance returned

    def test_mock_pipeline_vae(self) -> None:
        pipe = _MockPipeline()
        vae = pipe.vae
        assert isinstance(vae, _MockVAE)

    def test_mock_pipeline_enable_slicing(self) -> None:
        pipe = _MockPipeline()
        pipe.enable_vae_slicing()  # Should not crash

    def test_mock_pipeline_cpu_offload(self) -> None:
        pipe = _MockPipeline()
        pipe.enable_model_cpu_offload()  # Should not crash

    def test_mock_generates_correct_frame_count(self) -> None:
        pipe = _MockPipeline()
        result = pipe(prompt="test", width=100, height=100, num_frames=7)
        assert len(result.frames) == 7

    def test_mock_generates_correct_dimensions(self) -> None:
        pipe = _MockPipeline()
        result = pipe(prompt="test", width=200, height=150, num_frames=3)
        for frame in result.frames:
            assert frame.shape == (150, 200, 3)


class TestModelManagerEdgeCases:
    """Edge case and robustness tests."""

    def test_get_gpu_status_no_config(self) -> None:
        mm = ModelManager()
        status = mm.get_gpu_status()
        assert isinstance(status, dict)
        assert "available" in status

    def test_free_gpu_memory_no_crash(self) -> None:
        ModelManager._free_gpu_memory()  # Should not crash

    def test_multiple_load_unload_cycles(self) -> None:
        mm = ModelManager()
        for _ in range(5):
            mm.load_vace_diffusers()
            assert mm.is_loaded()
            mm.unload()
            assert not mm.is_loaded()