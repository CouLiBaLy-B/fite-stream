"""Tests for configuration — can run without GPU."""

import pytest

from fitstream.config import FitStreamConfig, ModelConfig


class TestConfig:
    def test_default_config(self):
        config = FitStreamConfig()
        assert config.project_name == "FitStream"
        assert config.animate.width == 832
        assert config.animate.height == 480

    def test_presets(self):
        config = FitStreamConfig()

        draft = config.get_preset("draft")
        assert draft.width == 480
        assert draft.num_inference_steps == 15

        high = config.get_preset("high")
        assert high.num_frames == 81
        assert high.num_inference_steps == 50

    def test_from_yaml(self):
        config = FitStreamConfig.from_yaml("nonexistent.yaml")
        assert config.project_name == "FitStream"  # Falls back to defaults

    def test_model_config_defaults(self):
        mc = ModelConfig()
        assert mc.offload_model
        assert mc.t5_cpu


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
