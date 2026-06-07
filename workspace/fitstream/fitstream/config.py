"""
FitStream Configuration Manager
Loads and manages configuration from YAML files with environment overrides.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger


@dataclass
class AnimateConfig:
    width: int = 832
    height: int = 480
    num_frames: int = 49
    fps: int = 16
    num_inference_steps: int = 30
    guidance_scale: float = 5.0
    seed: int = -1


@dataclass
class ModelConfig:
    name: str = "Wan2.1-VACE-1.3B-Preview"
    hf_repo: str = "Wan-AI/Wan2.1-VACE-1.3B-Preview"
    local_path: str = "./models/VACE-Wan2.1-1.3B-Preview"
    dtype: str = "bfloat16"
    device: str = "cuda"
    offload_model: bool = True
    t5_cpu: bool = True
    enable_vae_slicing: bool = True
    enable_model_cpu_offload: bool = True


@dataclass
class StoryConfig:
    scenes_max: int = 8
    transition_frames: int = 8
    extend_overlap: int = 4


@dataclass 
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    max_concurrent_jobs: int = 2
    job_timeout: int = 600


@dataclass
class FitStreamConfig:
    """Main configuration for FitStream."""
    project_name: str = "FitStream"
    version: str = "0.1.0"
    model: ModelConfig = field(default_factory=ModelConfig)
    animate: AnimateConfig = field(default_factory=AnimateConfig)
    story: StoryConfig = field(default_factory=StoryConfig)
    api: APIConfig = field(default_factory=APIConfig)
    output_dir: str = "./outputs"
    models_dir: str = "./models"
    
    @classmethod
    def from_yaml(cls, path: str = None) -> "FitStreamConfig":
        if path is None:
            # Look for config in standard locations
            candidates = [
                Path("config/default.yaml"),
                Path(__file__).parent.parent / "config" / "default.yaml",
                Path.home() / ".fitstream" / "config.yaml",
            ]
            for candidate in candidates:
                if candidate.exists():
                    path = str(candidate)
                    break
        
        config = cls()
        
        if path and os.path.exists(path):
            with open(path) as f:
                data = yaml.safe_load(f)
            
            if data:
                # Parse model config
                if "models" in data:
                    default_model = data["models"].get("default", "vace_1_3b")
                    model_key = default_model.replace("-", "_")
                    if model_key in data["models"]:
                        m = data["models"][model_key]
                        config.model = ModelConfig(
                            name=m.get("name", config.model.name),
                            hf_repo=m.get("hf_repo", config.model.hf_repo),
                            local_path=m.get("local_path", config.model.local_path),
                            dtype=m.get("dtype", config.model.dtype),
                            device=m.get("device", config.model.device),
                            offload_model=m.get("offload_model", config.model.offload_model),
                            t5_cpu=m.get("t5_cpu", config.model.t5_cpu),
                        )
                
                # Parse generation config
                if "generation" in data and "animate" in data["generation"]:
                    a = data["generation"]["animate"]
                    config.animate = AnimateConfig(
                        width=a.get("width", config.animate.width),
                        height=a.get("height", config.animate.height),
                        num_frames=a.get("num_frames", config.animate.num_frames),
                        fps=a.get("fps", config.animate.fps),
                        num_inference_steps=a.get("num_inference_steps", config.animate.num_inference_steps),
                        guidance_scale=a.get("guidance_scale", config.animate.guidance_scale),
                        seed=a.get("seed", config.animate.seed),
                    )
                
                # Parse output config
                if "output" in data:
                    config.output_dir = data["output"].get("directory", config.output_dir)
            
            logger.info(f"Configuration loaded from {path}")
        else:
            logger.warning("No config file found, using defaults")
        
        # Environment variable overrides
        config.model.device = os.environ.get("FITSTREAM_DEVICE", config.model.device)
        config.output_dir = os.environ.get("FITSTREAM_OUTPUT_DIR", config.output_dir)
        
        return config
    
    def get_preset(self, name: str) -> AnimateConfig:
        presets = {
            "draft": AnimateConfig(480, 320, 33, 16, 15, 4.0, -1),
            "standard": AnimateConfig(832, 480, 49, 16, 30, 5.0, -1),
            "high": AnimateConfig(832, 480, 81, 16, 50, 6.0, -1),
        }
        return presets.get(name, presets["standard"])


# Singleton config
_config: Optional[FitStreamConfig] = None

def get_config(reload: bool = False) -> FitStreamConfig:
    global _config
    if _config is None or reload:
        _config = FitStreamConfig.from_yaml()
    return _config
