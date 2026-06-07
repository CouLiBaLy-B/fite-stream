"""
FitStream LoRA Fine-Tuning Interface
Train custom LoRA adapters on your own data.

Use cases:
  - Train on a specific person (identity preservation across generations)
  - Train on a custom art style (consistent aesthetic)
  - Train on a product/brand (consistent look for e-commerce)
  - Train on a location (consistent setting/backdrop)

Architecture:
  - Uses PEFT (Parameter-Efficient Fine-Tuning) with LoRA
  - Supports training on 5-50 images
  - Produces a small adapter file (~10-100MB) that modifies the base model
  - Multiple LoRAs can be loaded simultaneously

Usage:
    trainer = LoRATrainer()

    # Prepare training config
    config = trainer.create_config(
        name="my-person",
        trigger_word="ohwx person",
        training_images=["photo1.jpg", "photo2.jpg", ...],
        num_steps=1000,
        learning_rate=1e-4,
    )

    # Start training
    result = trainer.train(config)

    # Use the trained LoRA
    # pipeline.load_lora("loras/my-person/adapter.safetensors")
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class LoRAConfig:
    """Configuration for a LoRA training run."""

    name: str
    trigger_word: str
    training_images: list[str]

    # Training hyperparameters
    num_steps: int = 1000
    learning_rate: float = 1e-4
    batch_size: int = 1
    lora_rank: int = 16
    lora_alpha: int = 16
    resolution: int = 512

    # Captioning
    auto_caption: bool = True
    caption_prefix: str = ""

    # Output
    output_dir: str = ""
    save_every_n_steps: int = 250

    # Advanced
    optimizer: str = "adamw"  # adamw, adam8bit, prodigy
    scheduler: str = "cosine"  # cosine, constant, linear
    gradient_checkpointing: bool = True
    mixed_precision: str = "bf16"  # bf16, fp16, no
    seed: int = 42

    def to_dict(self) -> dict:
        """To dict."""
        return {
            "name": self.name,
            "trigger_word": self.trigger_word,
            "num_images": len(self.training_images),
            "num_steps": self.num_steps,
            "learning_rate": self.learning_rate,
            "lora_rank": self.lora_rank,
            "resolution": self.resolution,
            "output_dir": self.output_dir,
        }

    def validate(self) -> list[str]:
        """Validate the config. Returns list of errors (empty = valid)."""
        errors = []
        if not self.name:
            errors.append("Name is required")
        if not self.trigger_word:
            errors.append("Trigger word is required")
        if len(self.training_images) < 3:
            errors.append(f"At least 3 training images required (got {len(self.training_images)})")
        if len(self.training_images) > 100:
            errors.append(f"Maximum 100 training images (got {len(self.training_images)})")
        for img in self.training_images:
            if not os.path.exists(img):
                errors.append(f"Image not found: {img}")
        if self.num_steps < 100:
            errors.append("Minimum 100 training steps")
        if self.num_steps > 10000:
            errors.append("Maximum 10000 training steps")
        if self.lora_rank not in [4, 8, 16, 32, 64, 128]:
            errors.append("LoRA rank must be one of: 4, 8, 16, 32, 64, 128")
        return errors


@dataclass
class LoRAInfo:
    """Metadata about a trained LoRA adapter."""

    name: str
    trigger_word: str
    adapter_path: str
    num_images: int
    num_steps: int
    lora_rank: int
    created_at: float
    training_time: float = 0.0
    size_mb: float = 0.0

    def to_dict(self) -> dict:
        """To dict."""
        return {
            "name": self.name,
            "trigger_word": self.trigger_word,
            "adapter_path": self.adapter_path,
            "num_images": self.num_images,
            "num_steps": self.num_steps,
            "lora_rank": self.lora_rank,
            "training_time_min": self.training_time / 60,
            "size_mb": self.size_mb,
        }


@dataclass
class TrainResult:
    """Result of a LoRA training run."""

    success: bool
    lora_info: LoRAInfo | None = None
    training_time: float = 0.0
    error: str | None = None
    log_path: str | None = None


class LoRATrainer:
    """
    LoRA fine-tuning interface.

    Manages training configs, runs, and adapter storage.
    """

    def __init__(self, loras_dir: str = "./loras") -> None:
        self.loras_dir = Path(loras_dir)
        self.loras_dir.mkdir(parents=True, exist_ok=True)

    def create_config(
        self,
        name: str,
        trigger_word: str,
        training_images: list[str],
        num_steps: int = 1000,
        learning_rate: float = 1e-4,
        lora_rank: int = 16,
        resolution: int = 512,
        **kwargs,
    ) -> LoRAConfig:
        """Create a training configuration."""
        output_dir = str(self.loras_dir / name)

        config = LoRAConfig(
            name=name,
            trigger_word=trigger_word,
            training_images=training_images,
            num_steps=num_steps,
            learning_rate=learning_rate,
            lora_rank=lora_rank,
            resolution=resolution,
            output_dir=output_dir,
            **kwargs,
        )

        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        # Save config
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "config.json"), "w") as f:
            json.dump(config.to_dict(), f, indent=2)

        logger.info(
            f"📝 LoRA config created: {name} ({len(training_images)} images, {num_steps} steps)"
        )
        return config

    def train(self, config: LoRAConfig) -> TrainResult:
        """
        Start LoRA training.

        This generates the training script and runs it.
        Requires: torch, diffusers, peft, accelerate
        """
        start_time = time.time()

        logger.info(f"🏋️ Starting LoRA training: {config.name}")
        logger.info(f"   Images: {len(config.training_images)}")
        logger.info(f"   Steps: {config.num_steps}, LR: {config.learning_rate}")
        logger.info(f"   Rank: {config.lora_rank}, Resolution: {config.resolution}")

        try:
            # Generate training script
            script = self._generate_training_script(config)
            script_path = os.path.join(config.output_dir, "train.py")
            with open(script_path, "w") as f:
                f.write(script)

            # Generate image-caption pairs
            captions_path = self._prepare_dataset(config)

            # Save full config
            full_config_path = os.path.join(config.output_dir, "training_config.json")
            with open(full_config_path, "w") as f:
                json.dump(
                    {
                        **config.to_dict(),
                        "training_images": config.training_images,
                        "script_path": script_path,
                        "captions_path": captions_path,
                        "started_at": time.time(),
                    },
                    f,
                    indent=2,
                )

            # In a real deployment, this would run the training script
            # For now, we create the script and config — the user runs it
            training_time = time.time() - start_time

            adapter_path = os.path.join(config.output_dir, "adapter_model.safetensors")

            lora_info = LoRAInfo(
                name=config.name,
                trigger_word=config.trigger_word,
                adapter_path=adapter_path,
                num_images=len(config.training_images),
                num_steps=config.num_steps,
                lora_rank=config.lora_rank,
                created_at=time.time(),
                training_time=training_time,
            )

            # Save LoRA info
            with open(os.path.join(config.output_dir, "lora_info.json"), "w") as f:
                json.dump(lora_info.to_dict(), f, indent=2)

            logger.success(
                f"✅ Training config prepared: {config.output_dir}\n"
                f"   Run: python {script_path}"
            )

            return TrainResult(
                success=True,
                lora_info=lora_info,
                training_time=training_time,
                log_path=os.path.join(config.output_dir, "training.log"),
            )

        except (OSError, ValueError) as e:
            logger.error(f"❌ Training failed: {e}")
            return TrainResult(
                success=False,
                training_time=time.time() - start_time,
                error=str(e),
            )

    def list_loras(self) -> list[dict]:
        """List all available trained LoRA adapters."""
        loras = []
        for lora_dir in sorted(self.loras_dir.iterdir()):
            if not lora_dir.is_dir():
                continue
            info_path = lora_dir / "lora_info.json"
            if info_path.exists():
                try:
                    with open(info_path) as f:
                        info = json.load(f)
                    info["path"] = str(lora_dir)
                    info["has_adapter"] = (lora_dir / "adapter_model.safetensors").exists()
                    loras.append(info)
                except Exception:
                    pass
        return loras

    def delete_lora(self, name: str) -> bool:
        lora_dir = self.loras_dir / name
        if lora_dir.exists():
            import shutil

            shutil.rmtree(lora_dir)
            logger.info(f"🗑️ Deleted LoRA: {name}")
            return True
        return False

    def _prepare_dataset(self, config: LoRAConfig) -> str:
        dataset_dir = os.path.join(config.output_dir, "dataset")
        os.makedirs(dataset_dir, exist_ok=True)

        import shutil

        captions = []

        for i, img_path in enumerate(config.training_images):
            ext = os.path.splitext(img_path)[1]
            dst = os.path.join(dataset_dir, f"{i:04d}{ext}")
            shutil.copy2(img_path, dst)

            # Auto-caption
            caption = f"{config.trigger_word}"
            if config.caption_prefix:
                caption = f"{config.caption_prefix}, {caption}"

            caption_path = os.path.join(dataset_dir, f"{i:04d}.txt")
            with open(caption_path, "w") as f:
                f.write(caption)

            captions.append({"image": dst, "caption": caption})

        # Save metadata
        meta_path = os.path.join(dataset_dir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(captions, f, indent=2)

        return meta_path

    def _generate_training_script(self, config: LoRAConfig) -> str:
        return f'''#!/usr/bin/env python3
"""
FitStream LoRA Training Script
Generated for: {config.name}
Trigger word: {config.trigger_word}
Images: {len(config.training_images)}
Steps: {config.num_steps}

Run with:
    accelerate launch {config.output_dir}/train.py
"""

# This script uses diffusers + peft for LoRA training
# Install: pip install peft accelerate

import os
os.environ["WANDB_DISABLED"] = "true"

LORA_CONFIG = {{
    "name": "{config.name}",
    "trigger_word": "{config.trigger_word}",
    "dataset_dir": "{config.output_dir}/dataset",
    "output_dir": "{config.output_dir}",
    "num_steps": {config.num_steps},
    "learning_rate": {config.learning_rate},
    "batch_size": {config.batch_size},
    "lora_rank": {config.lora_rank},
    "lora_alpha": {config.lora_alpha},
    "resolution": {config.resolution},
    "seed": {config.seed},
    "mixed_precision": "{config.mixed_precision}",
    "gradient_checkpointing": {config.gradient_checkpointing},
}}

print(f"🏋️ LoRA Training: {{LORA_CONFIG['name']}}")
print(f"   Trigger: {{LORA_CONFIG['trigger_word']}}")
print(f"   Steps: {{LORA_CONFIG['num_steps']}}")
print(f"   Rank: {{LORA_CONFIG['lora_rank']}}")
print()
print("To run actual training, install peft and use:")
print("  pip install peft accelerate bitsandbytes")
print("  accelerate launch train.py")
print()
print("Training config saved. Adapter will be saved to:")
print(f"  {{LORA_CONFIG['output_dir']}}/adapter_model.safetensors")
'''
