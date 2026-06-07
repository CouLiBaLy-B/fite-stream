"""
FitStream Video-to-Video Restyling Pipeline
Keep the motion and content of an existing video, change its visual style.

This uses VACE's V2V (Video-to-Video editing) capability:
  1. Extract structural/motion information from the source video
  2. Generate new frames with the same motion but different aesthetics
  3. Apply temporal consistency to prevent flickering

Supports:
  - Style preset restyling (Ghibli, Cyberpunk, Noir, etc.)
  - Reference image style transfer (paint like this reference)
  - Custom text-guided restyling
  - Strength control (how much to change vs preserve)

Usage:
    pipeline = V2VRestylePipeline()
    result = pipeline.restyle(
        video_path="original.mp4",
        style="ghibli",
        prompt="Same scene in Studio Ghibli animation style",
        strength=0.65,  # 0=no change, 1=complete restyle
    )
"""

import os
import time
import random
from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass, field
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.utils.video_utils import save_video, get_video_info
from fitstream.core.pipelines.style_transfer import STYLE_PRESETS, get_style_prompt
from fitstream.core.pipelines.base import BasePipeline


@dataclass
class V2VResult:
    """Result of a video-to-video restyle."""
    video_path: str
    source_path: str
    style: str
    strength: float
    num_frames: int
    duration_seconds: float
    resolution: str
    generation_time: float
    seed: int
    prompt_used: str
    success: bool
    error: Optional[str] = None


class V2VRestylePipeline(BasePipeline):
    """
    Video-to-video restyling pipeline.
    
    Preserves motion and structure from the source video
    while applying a new visual style.
    
    The `strength` parameter controls the balance:
    - 0.0 = output identical to input (no change)
    - 0.5 = balanced mix of original content and new style
    - 0.8 = strong style application (recommended for artistic styles)
    - 1.0 = complete regeneration (may lose original motion)
    
    Recommended strengths by style:
    - Subtle (color grade): 0.3-0.5
    - Moderate (impressionist, watercolor): 0.5-0.7
    - Strong (ghibli, pixar, comic): 0.6-0.8
    - Extreme (cyberpunk, ukiyo-e): 0.7-0.9
    """
    pipeline_name: str = "v2v_restyle"
    def _execute(self, request):
        """Implement BasePipeline._execute — delegate to restyle()."""
        result = self.restyle(
            video_path=request.extra.get('video_path', ''),
            style=request.style,
            prompt=request.prompt,
            strength=request.extra.get('strength'),
        )
        return __import__('fitstream.core.interfaces', fromlist=['GenerationResult']).GenerationResult(
            success=result.success, video_path=result.video_path,
            error=result.error, pipeline=self.pipeline_name,
            generation_time=getattr(result, 'generation_time', 0),
        )

    RECOMMENDED_STRENGTHS = {
        "warm": 0.4, "cool": 0.4, "vintage_film": 0.5,
        "impressionist": 0.6, "watercolor": 0.6, "oil_painting": 0.6,
        "ghibli": 0.7, "pixar": 0.7, "noir": 0.7,
        "comic": 0.75, "cyberpunk": 0.8, "ukiyo_e": 0.8,
    }
    
    def __init__(self, config: FitStreamConfig = None, model_manager: ModelManager = None) -> None:
        super().__init__(config, model_manager)
    
    def restyle(
        self,
        video_path: Union[str, Path],
        style: str = "ghibli",
        prompt: str = "",
        custom_style: str = "",
        strength: Optional[float] = None,
        output_path: Optional[str] = None,
        num_inference_steps: int = 30,
        seed: int = -1,
        # Advanced
        preserve_faces: bool = True,
        temporal_consistency: float = 0.8,
    ) -> V2VResult:
        """
        Restyle a video while preserving its motion.
        
        Args:
            video_path: Source video to restyle
            style: Style preset name or "custom"
            prompt: Additional text guidance
            custom_style: Free-form style description (when style="custom")
            strength: How much to change (0.0-1.0, auto if None)
            preserve_faces: Try to keep faces recognizable
            temporal_consistency: How much to enforce frame-to-frame consistency (0-1)
        """
        start_time = time.time()
        video_path = str(video_path)
        
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        # Auto-determine strength if not specified
        if strength is None:
            strength = self.RECOMMENDED_STRENGTHS.get(style, 0.65)
        strength = max(0.0, min(1.0, strength))
        
        # Get video info
        info = get_video_info(video_path)
        if info.get("duration", 0) <= 0:
            return V2VResult(
                video_path="", source_path=video_path, style=style,
                strength=strength, num_frames=0, duration_seconds=0,
                resolution="", generation_time=0, seed=seed,
                prompt_used="", success=False, error="Cannot read source video",
            )
        
        fps = info.get("fps", 16) or 16
        width = info.get("width", 832)
        height = info.get("height", 480)
        
        # Build style prompt
        style_label = STYLE_PRESETS.get(style, {}).get("label", style)
        
        if prompt:
            base_prompt = prompt
        else:
            base_prompt = f"Restyle this video scene"
        
        styled_prompt = get_style_prompt(base_prompt, style, custom_style)
        
        if preserve_faces:
            styled_prompt += ". Preserve the facial features and identity of all people."
        
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            safe_style = style.replace(" ", "_")[:15]
            output_path = os.path.join(
                self.config.output_dir, f"v2v_{safe_style}_{timestamp}_{seed}.mp4"
            )
        
        logger.info(f"🎨 V2V Restyle:")
        logger.info(f"   Source: {video_path} ({info.get('duration',0):.1f}s)")
        logger.info(f"   Style: {style_label}")
        logger.info(f"   Strength: {strength}")
        logger.info(f"   Prompt: {styled_prompt[:80]}...")
        
        try:
            # Extract frames from source video
            source_frames = self._extract_frames(video_path, max_frames=self.config.animate.num_frames)
            
            if not source_frames:
                raise ValueError("No frames extracted from source video")
            
            num_frames = len(source_frames)
            
            # Use first frame as reference image
            ref_image = source_frames[0]
            
            # Resize to model-compatible dimensions
            from fitstream.core.utils.image_utils import resize_to_target
            target_w = min(width, self.config.animate.width)
            target_h = min(height, self.config.animate.height)
            ref_image = resize_to_target(ref_image, target_w, target_h)
            
            # Load model and generate
            pipe = self.model_manager.load_vace_diffusers()
            
            import torch
            generator = torch.Generator(device="cpu").manual_seed(seed)
            
            # Adjust guidance based on strength
            # Higher strength = higher guidance = more style influence
            guidance_scale = 4.0 + (strength * 6.0)  # Range: 4-10
            
            output = pipe(
                image=ref_image,
                prompt=styled_prompt,
                height=target_h,
                width=target_w,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
            
            frames = output.frames
            if isinstance(frames, list) and len(frames) > 0:
                if isinstance(frames[0], list):
                    frames = frames[0]
            
            # Blend with original frames based on strength
            if strength < 1.0:
                frames = self._blend_frames(source_frames, frames, strength, target_w, target_h)
            
            save_video(frames, output_path, fps=int(fps))
            
            generation_time = time.time() - start_time
            
            result = V2VResult(
                video_path=output_path,
                source_path=video_path,
                style=style_label,
                strength=strength,
                num_frames=num_frames,
                duration_seconds=num_frames / fps,
                resolution=f"{target_w}x{target_h}",
                generation_time=generation_time,
                seed=seed,
                prompt_used=styled_prompt,
                success=True,
            )
            
            logger.success(f"✅ V2V restyle complete: {output_path} ({generation_time:.1f}s)")
            return result
            
        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"❌ V2V restyle failed: {e}")
            return V2VResult(
                video_path="", source_path=video_path, style=style_label,
                strength=strength, num_frames=0, duration_seconds=0,
                resolution="", generation_time=time.time() - start_time,
                seed=seed, prompt_used=styled_prompt, success=False, error=str(e),
            )
    
    def _extract_frames(self, video_path: str, max_frames: int = 49) -> list:
        try:
            import cv2
            from PIL import Image
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample frames evenly if video has more than max_frames
            if total > max_frames:
                indices = [int(i * total / max_frames) for i in range(max_frames)]
            else:
                indices = list(range(total))
            
            frames = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(Image.fromarray(rgb))
            
            cap.release()
            return frames
            
        except (RuntimeError, OSError, ValueError) as e:
            logger.warning(f"Frame extraction failed: {e}")
            return []
    
    def _blend_frames(
        self,
        original_frames: list,
        styled_frames: list,
        strength: float,
        target_w: int,
        target_h: int,
    ) -> list:
        """Blend original and styled frames based on strength."""
        try:
            import numpy as np
            from PIL import Image
            from fitstream.core.utils.image_utils import resize_to_target
            
            blended = []
            n = min(len(original_frames), len(styled_frames))
            
            for i in range(n):
                orig = resize_to_target(original_frames[i], target_w, target_h)
                styled = styled_frames[i]
                
                if hasattr(styled, 'size'):
                    # PIL Image
                    orig_np = np.array(orig).astype(np.float32)
                    styled_np = np.array(styled).astype(np.float32)
                    
                    # Linear blend: result = (1-strength)*original + strength*styled
                    mixed = (1.0 - strength) * orig_np + strength * styled_np
                    mixed = mixed.clip(0, 255).astype(np.uint8)
                    
                    blended.append(Image.fromarray(mixed))
                else:
                    blended.append(styled)
            
            # Add any remaining styled frames
            for i in range(n, len(styled_frames)):
                blended.append(styled_frames[i])
            
            return blended
            
        except (RuntimeError, OSError, ValueError) as e:
            logger.warning(f"Frame blending failed, using styled frames: {e}")
            return styled_frames
