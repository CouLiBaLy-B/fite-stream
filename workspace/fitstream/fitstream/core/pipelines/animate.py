"""
FitStream Animate Pipeline
Core pipeline: Photo of a person + text prompt → Animated video.
"""

from __future__ import annotations

import os
import time
import random
from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass
from loguru import logger

from fitstream.config import FitStreamConfig, AnimateConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.utils.image_utils import load_and_prepare_image
from fitstream.core.utils.video_utils import save_video
from fitstream.core.utils.prompt_utils import enhance_prompt
from fitstream.core.interfaces import GenerationRequest, GenerationResult
from fitstream.core.pipelines.base import BasePipeline


@dataclass
class AnimateResult:
    """Result of an animation generation."""
    video_path: str
    num_frames: int
    duration_seconds: float
    resolution: str
    generation_time: float
    seed: int
    prompt_used: str
    success: bool
    error: Optional[str] = None


class AnimatePipeline(BasePipeline):
    """
    Main animation pipeline.
    Takes a reference image + prompt and generates a video.
    """
    
    pipeline_name: str = "animate"
    
    def __init__(
        self,
        config: Optional[FitStreamConfig] = None,
        model_manager: Optional[ModelManager] = None,
    ) -> None:
        super().__init__(config, model_manager)
        self._pipe = None
    
    def _ensure_model_loaded(self):
        """Ensure the generation model is loaded."""
        if self._pipe is None:
            self._pipe = self.model_manager.load_vace_diffusers()
        return self._pipe
    
    def _execute(self, request: GenerationRequest) -> GenerationResult:
        """Implement BasePipeline._execute — delegate to generate()."""
        result = self.generate(
            image_path=request.image_paths[0] if request.image_paths else "",
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            num_frames=request.num_frames,
            fps=request.fps,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            style=request.style,
            preset=request.preset,
        )
        return GenerationResult(
            success=result.success,
            video_path=result.video_path,
            error=result.error,
            num_frames=result.num_frames,
            duration_seconds=result.duration_seconds,
            resolution=result.resolution,
            generation_time=result.generation_time,
            seed=result.seed,
            prompt_used=result.prompt_used,
            pipeline=self.pipeline_name,
        )
    
    def generate(
        self,
        image_path: Union[str, Path],
        prompt: str,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        style: str = "cinematic",
        enhance_prompt_flag: bool = True,
        preset: Optional[str] = None,
        ref_images: Optional[List[str]] = None,
    ) -> AnimateResult:
        """Generate an animated video from a person's photo and a text prompt."""
        start_time = time.time()
        
        # Apply preset
        if preset:
            preset_config = self.config.get_preset(preset)
            width = width or preset_config.width
            height = height or preset_config.height
            num_frames = num_frames or preset_config.num_frames
            num_inference_steps = num_inference_steps or preset_config.num_inference_steps
            guidance_scale = guidance_scale or preset_config.guidance_scale
        
        anim_config = self.config.animate
        width = width or anim_config.width
        height = height or anim_config.height
        num_frames = num_frames or anim_config.num_frames
        fps = fps or anim_config.fps
        num_inference_steps = num_inference_steps or anim_config.num_inference_steps
        guidance_scale = guidance_scale or anim_config.guidance_scale
        resolved_seed = seed if seed is not None and seed >= 0 else random.randint(0, 2**32 - 1)
        
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = os.path.join(self.config.output_dir, f"animate_{timestamp}_{resolved_seed}.mp4")
        
        prompt_used = enhance_prompt(prompt, style=style) if enhance_prompt_flag else prompt
        
        logger.info(
            f"🎬 [{self.pipeline_name}] image={image_path} "
            f"res={width}x{height} frames={num_frames} steps={num_inference_steps} seed={resolved_seed}"
        )
        
        try:
            ref_image = load_and_prepare_image(image_path, width, height)
            pipe = self._ensure_model_loaded()
            
            import torch
            generator = torch.Generator(device="cpu").manual_seed(resolved_seed)
            
            output = pipe(
                image=ref_image,
                prompt=prompt_used,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
            
            frames = output.frames
            if isinstance(frames, list) and len(frames) > 0:
                if isinstance(frames[0], list):
                    frames = frames[0]
            
            save_video(frames, output_path, fps=fps)
            
            generation_time = time.time() - start_time
            duration_seconds = num_frames / fps
            
            logger.success(
                f"✅ [{self.pipeline_name}] {generation_time:.1f}s → {output_path} "
                f"({duration_seconds:.1f}s video)"
            )
            
            return AnimateResult(
                video_path=output_path,
                num_frames=num_frames,
                duration_seconds=duration_seconds,
                resolution=f"{width}x{height}",
                generation_time=generation_time,
                seed=resolved_seed,
                prompt_used=prompt_used,
                success=True,
            )
            
        except MemoryError:
            generation_time = time.time() - start_time
            logger.error(f"❌ [{self.pipeline_name}] GPU OOM after {generation_time:.1f}s")
            return AnimateResult(
                video_path="", num_frames=0, duration_seconds=0,
                resolution=f"{width}x{height}", generation_time=generation_time,
                seed=resolved_seed, prompt_used=prompt_used,
                success=False, error="GPU out of memory. Try draft quality.",
            )
        
        except FileNotFoundError as e:
            generation_time = time.time() - start_time
            logger.error(f"❌ [{self.pipeline_name}] File not found: {e}")
            return AnimateResult(
                video_path="", num_frames=0, duration_seconds=0,
                resolution=f"{width}x{height}", generation_time=generation_time,
                seed=resolved_seed, prompt_used=prompt_used,
                success=False, error=f"Image not found: {e}",
            )
        
        except Exception as e:
            generation_time = time.time() - start_time
            logger.exception(f"❌ [{self.pipeline_name}] Unexpected error")
            return AnimateResult(
                video_path="", num_frames=0, duration_seconds=0,
                resolution=f"{width}x{height}", generation_time=generation_time,
                seed=resolved_seed, prompt_used=prompt_used,
                success=False, error=f"{type(e).__name__}: {e}",
            )
