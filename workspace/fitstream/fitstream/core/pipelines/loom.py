"""
FitStream LoomVideo Pipeline
Multi-image composition using LoomVideo's unique @Image N referencing.

This pipeline allows combining MULTIPLE reference images into a single
coherent video — e.g. person + garment + location + accessory.

LoomVideo is the ONLY model that supports this natively via its
Negative Temporal RoPE and Deepstack injection architecture.

Usage:
    pipeline = LoomPipeline()
    result = pipeline.generate(
        images=["person.jpg", "red_dress.jpg", "paris_cafe.jpg"],
        prompt="The woman (@Image 1) wearing the elegant dress (@Image 2) "
               "sits at the Parisian café (@Image 3), sipping coffee",
    )
"""

import os
import re
import time
import random
from pathlib import Path
from typing import Optional, List, Union, Dict
from dataclasses import dataclass
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.utils.image_utils import load_and_prepare_image
from fitstream.core.utils.video_utils import save_video
from fitstream.core.utils.prompt_utils import enhance_prompt


@dataclass
class LoomResult:
    """Result of a LoomVideo multi-image generation."""
    video_path: str
    num_frames: int
    duration_seconds: float
    resolution: str
    generation_time: float
    seed: int
    prompt_used: str
    num_reference_images: int
    task: str
    success: bool
    error: Optional[str] = None


def validate_image_references(prompt: str, num_images: int) -> List[str]:
    """
    Validate that @Image references in prompt match the number of images provided.
    Returns list of warnings (empty if all OK).
    """
    warnings = []
    
    # Find all @Image N references
    refs = re.findall(r'@Image\s+(\d+)', prompt, re.IGNORECASE)
    ref_indices = set(int(r) for r in refs)
    
    if not ref_indices:
        warnings.append(
            "No @Image references found in prompt. "
            "Use '@Image 1', '@Image 2' etc. to reference your images."
        )
    
    for idx in ref_indices:
        if idx < 1 or idx > num_images:
            warnings.append(
                f"@Image {idx} referenced but only {num_images} images provided. "
                f"Valid range: @Image 1 to @Image {num_images}"
            )
    
    # Check for unreferenced images
    for i in range(1, num_images + 1):
        if i not in ref_indices:
            warnings.append(f"Image {i} provided but not referenced in prompt. Add @Image {i} to use it.")
    
    return warnings


def build_multi_image_prompt(
    descriptions: Dict[int, str],
    action: str = "",
    style: str = "cinematic",
) -> str:
    """
    Build a prompt for multi-image composition.
    
    Args:
        descriptions: {1: "the woman", 2: "the red dress", 3: "the café"}
        action: "walks through the scene"
    """
    parts = []
    for idx, desc in sorted(descriptions.items()):
        parts.append(f"{desc} (@Image {idx})")
    
    prompt = ", ".join(parts)
    if action:
        prompt = f"{prompt}. {action}"
    
    return enhance_prompt(prompt, style=style)


class LoomPipeline:
    """
    LoomVideo multi-image composition pipeline.
    
    Unique capabilities vs VACE:
    - Combine 2-8 reference images in one video
    - @Image N syntax for explicit image referencing in prompts
    - Specialized for fashion/e-commerce scenarios
    - 5.41x faster than comparable models (Scale-and-Add conditioning)
    
    Supports 4 tasks:
    - t2v: Text-to-Video (no images)
    - mi2v: Multi-Image-to-Video (main use case)
    - edit: Instruction-based video editing
    - ref_edit: Reference-guided video editing
    """
    pipeline_name: str = "loom"

    
    SUPPORTED_TASKS = ["t2v", "mi2v", "edit", "ref_edit"]
    
    def __init__(self, config: FitStreamConfig = None, model_manager: ModelManager = None) -> None:
        self.config = config or get_config()
        self.model_manager = model_manager or ModelManager(self.config)
        self._loom_available = self._check_loomvideo()
    
    def _check_loomvideo(self) -> bool:
        """Check if LoomVideo is downloaded and available."""
        loom_path = Path(self.config.models_dir) / "LoomVideo"
        if loom_path.exists():
            has_weights = any(loom_path.rglob("*.safetensors")) or any(loom_path.rglob("*.bin"))
            if has_weights:
                logger.info("LoomVideo model found")
                return True
        logger.info("LoomVideo not found — will fall back to VACE for multi-image tasks")
        return False
    
    @property
    def is_available(self) -> bool:
        """Is available."""
        return self._loom_available
    
    def generate(
        self,
        images: List[Union[str, Path]],
        prompt: str,
        output_path: Optional[str] = None,
        task: str = "mi2v",
        # Generation params
        width: int = 832,
        height: int = 480,
        num_frames: int = 97,
        num_inference_steps: int = 50,
        guidance_scale: float = 5.0,
        seed: int = -1,
        style: str = "cinematic",
        # For edit/ref_edit tasks
        source_video: Optional[str] = None,
    ) -> LoomResult:
        """
        Generate a video from multiple reference images + prompt.
        
        Args:
            images: List of reference image paths (referenced as @Image 1, @Image 2, etc.)
            prompt: Text prompt with @Image N references
            task: "t2v", "mi2v", "edit", or "ref_edit"
            source_video: Source video path (for edit/ref_edit tasks only)
        """
        start_time = time.time()
        
        if task not in self.SUPPORTED_TASKS:
            return LoomResult(
                video_path="", num_frames=0, duration_seconds=0, resolution="",
                generation_time=0, seed=0, prompt_used=prompt, num_reference_images=len(images),
                task=task, success=False, error=f"Unknown task: {task}. Use: {self.SUPPORTED_TASKS}",
            )
        
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = os.path.join(self.config.output_dir, f"loom_{task}_{timestamp}_{seed}.mp4")
        
        # Validate references
        warnings = validate_image_references(prompt, len(images))
        for w in warnings:
            logger.warning(f"  ⚠️ {w}")
        
        prompt_used = enhance_prompt(prompt, style=style)
        
        logger.info(f"🎨 LoomVideo Generation:")
        logger.info(f"   Task: {task}")
        logger.info(f"   Images: {len(images)}")
        for i, img in enumerate(images, 1):
            logger.info(f"     @Image {i}: {img}")
        logger.info(f"   Prompt: {prompt_used[:100]}...")
        
        try:
            if self._loom_available:
                return self._generate_loomvideo(
                    images, prompt_used, output_path, task,
                    width, height, num_frames, num_inference_steps,
                    guidance_scale, seed, source_video, start_time,
                )
            else:
                return self._generate_vace_fallback(
                    images, prompt_used, output_path,
                    width, height, num_frames, num_inference_steps,
                    guidance_scale, seed, start_time,
                )
        except (RuntimeError, OSError, ValueError) as e:
            generation_time = time.time() - start_time
            logger.error(f"❌ LoomVideo generation failed: {e}")
            return LoomResult(
                video_path="", num_frames=0, duration_seconds=0,
                resolution=f"{width}x{height}", generation_time=generation_time,
                seed=seed, prompt_used=prompt_used, num_reference_images=len(images),
                task=task, success=False, error=str(e),
            )
    
    def _generate_loomvideo(
        self, images, prompt, output_path, task,
        width, height, num_frames, steps, guidance, seed,
        source_video, start_time,
    ) -> LoomResult:
        """Generate using the native LoomVideo model."""
        import subprocess
        
        loom_dir = Path(self.config.models_dir) / "LoomVideo"
        loom_repo = loom_dir.parent / "LoomVideo-repo"
        
        # Prepare image paths argument
        image_paths_str = " ".join(str(Path(img).resolve()) for img in images)
        
        cmd = [
            "accelerate", "launch", "--num_processes=1",
            str(loom_repo / "scripts" / "inference" / "generate.py"),
            "--config_path", str(loom_repo / "configs" / "inference" / "generation.yaml"),
            "--ckpt_path", str(loom_dir),
            "--task", task,
            "--prompt", prompt,
            "--ref_image_paths", *[str(Path(img).resolve()) for img in images],
            "--height", str(height),
            "--width", str(width),
            "--num_frames", str(num_frames),
            "--num_inference_steps", str(steps),
            "--seed", str(seed),
            "--output_path", str(output_path),
        ]
        
        if source_video and task in ("edit", "ref_edit"):
            cmd.extend(["--source_video_path", str(source_video)])
        
        logger.info(f"   Running LoomVideo inference...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            raise RuntimeError(f"LoomVideo inference failed: {result.stderr[:500]}")
        
        generation_time = time.time() - start_time
        fps = self.config.animate.fps
        
        return LoomResult(
            video_path=output_path,
            num_frames=num_frames,
            duration_seconds=num_frames / fps,
            resolution=f"{width}x{height}",
            generation_time=generation_time,
            seed=seed,
            prompt_used=prompt,
            num_reference_images=len(images),
            task=task,
            success=True,
        )
    
    def _generate_vace_fallback(
        self, images, prompt, output_path,
        width, height, num_frames, steps, guidance, seed, start_time,
    ) -> LoomResult:
        """Fallback: use VACE with the first image as reference."""
        logger.info("   Using VACE fallback (LoomVideo not available)")
        
        # Strip @Image references from prompt for VACE
        clean_prompt = re.sub(r'\(@Image\s+\d+\)', '', prompt).strip()
        clean_prompt = re.sub(r'\s+', ' ', clean_prompt)
        
        pipe = self.model_manager.load_vace_diffusers()
        
        # Use first image as the primary reference
        ref_image = load_and_prepare_image(images[0], width, height)
        
        import torch
        generator = torch.Generator(device="cpu").manual_seed(seed)
        
        output = pipe(
            image=ref_image,
            prompt=clean_prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        )
        
        frames = output.frames
        if isinstance(frames, list) and len(frames) > 0:
            if isinstance(frames[0], list):
                frames = frames[0]
        
        save_video(frames, output_path, fps=self.config.animate.fps)
        
        generation_time = time.time() - start_time
        
        return LoomResult(
            video_path=output_path,
            num_frames=num_frames,
            duration_seconds=num_frames / self.config.animate.fps,
            resolution=f"{width}x{height}",
            generation_time=generation_time,
            seed=seed,
            prompt_used=clean_prompt,
            num_reference_images=len(images),
            task="mi2v (vace fallback)",
            success=True,
        )
