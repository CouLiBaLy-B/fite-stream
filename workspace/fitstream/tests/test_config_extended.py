"""Tests for FitStream configuration — presets, env overrides, YAML loading."""

import os
import tempfile
import yaml
import pytest
from fitstream.config import FitStreamConfig, AnimateConfig, get_config


class TestConfigPresets:
    """Quality presets — draft, standard, high."""

    def test_draft_preset(self) -> None:
        config = FitStreamConfig()
        preset = config.get_preset("draft")
        assert preset.width == 480
        assert preset.height == 320
        assert preset.num_frames == 33
        assert preset.num_inference_steps == 15
        assert preset.guidance_scale == 4.0

    def test_standard_preset(self) -> None:
        config = FitStreamConfig()
        preset = config.get_preset("standard")
        assert preset.width == 832
        assert preset.height == 480
        assert preset.num_frames == 49
        assert preset.num_inference_steps == 30
        assert preset.guidance_scale == 5.0

    def test_high_preset(self) -> None:
        config = FitStreamConfig()
        preset = config.get_preset("high")
        assert preset.num_frames == 81
        assert preset.num_inference_steps == 50
        assert preset.guidance_scale == 6.0

    def test_unknown_preset_falls_back_to_standard(self) -> None:
        config = FitStreamConfig()
        preset = config.get_preset("nonexistent")
        assert preset.width == 832  # Standard
        assert preset.num_inference_steps == 30


class TestConfigYAML:
    """YAML configuration loading."""

    def test_load_from_yaml_animation_params(self) -> None:
        """Verify YAML overrides animation params correctly."""
        import tempfile, yaml, os

        yaml_content = {"generation": {"animate": {"width": 1024, "num_frames": 97}}, "output": {"directory": "/custom/output"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            tmp_path = f.name

        try:
            config = FitStreamConfig.from_yaml(tmp_path)
            assert config.animate.width == 1024
            assert config.animate.num_frames == 97
            assert config.output_dir == "/custom/output"
        finally:
            os.unlink(tmp_path)

    def test_from_yaml_nonexistent_file(self) -> None:
        config = FitStreamConfig.from_yaml("/nonexistent/config.yaml")
        # Should use defaults
        assert config.animate.width == 832

    def test_from_yaml_empty_file(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")  # Empty
            tmp_path = f.name
        try:
            config = FitStreamConfig.from_yaml(tmp_path)
            assert config.animate.width == 832  # Defaults
        finally:
            os.unlink(tmp_path)


class TestConfigEnvOverrides:
    """Environment variable overrides."""

    def test_device_override(self, monkeypatch) -> None:
        monkeypatch.setenv("FITSTREAM_DEVICE", "cpu")
        config = FitStreamConfig.from_yaml()
        assert config.model.device == "cpu"

    def test_output_dir_override(self, monkeypatch) -> None:
        monkeypatch.setenv("FITSTREAM_OUTPUT_DIR", "/env/output")
        config = FitStreamConfig.from_yaml()
        assert config.output_dir == "/env/output"


class TestConfigDefaults:
    """Default configuration values."""

    def test_default_animate_config(self) -> None:
        config = FitStreamConfig()
        assert config.animate.width == 832
        assert config.animate.height == 480
        assert config.animate.num_frames == 49
        assert config.animate.fps == 16
        assert config.animate.num_inference_steps == 30
        assert config.animate.guidance_scale == 5.0

    def test_default_model_config(self) -> None:
        config = FitStreamConfig()
        assert config.model.name == "Wan2.1-VACE-1.3B-Preview"
        assert config.model.dtype == "bfloat16"
        assert config.model.device == "cuda"
        assert config.model.offload_model is True
        assert config.model.t5_cpu is True

    def test_default_api_config(self) -> None:
        config = FitStreamConfig()
        assert config.api.host == "0.0.0.0"
        assert config.api.port == 8000
        assert config.api.max_concurrent_jobs == 2
        assert config.api.job_timeout == 600


class TestGetConfig:
    """Singleton config behavior."""

    def test_get_config_returns_instance(self) -> None:
        config = get_config()
        assert isinstance(config, FitStreamConfig)

    def test_get_config_is_singleton(self) -> None:
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_get_config_reload(self) -> None:
        c1 = get_config()
        c2 = get_config(reload=True)
        # Still a FitStreamConfig, may or may not be same instance
        assert isinstance(c2, FitStreamConfig)
