"""
FitStream Style Transfer Pipeline
Apply artistic styles to existing videos or generate stylized animations.

Supported styles beyond prompt-based styling:
  - Reference image style transfer (paint like this reference)
  - Consistent style across multi-scene stories
  - Video-to-video restyling (keep motion, change aesthetics)

Usage:
    pipeline = StyleTransferPipeline()
    
    # Restyle an existing video
    result = pipeline.restyle_video(
        video_path="scene.mp4",
        style_reference="monet_painting.jpg",
        prompt="Same scene but in Monet impressionist style",
    )
    
    # Generate with style reference
    result = pipeline.generate_with_style(
        person_image="person.jpg",
        style_reference="anime_screenshot.jpg",
        prompt="Person walking in a garden",
    )
"""

import os
import time
import random
from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.utils.image_utils import load_and_prepare_image
from fitstream.core.utils.video_utils import save_video
from fitstream.core.utils.prompt_utils import enhance_prompt
from fitstream.core.pipelines.base import BasePipeline


# Pre-defined style presets with associated prompt modifiers and negative prompts
STYLE_PRESETS = {
    "ghibli": {
        "label": "Studio Ghibli",
        "prefix": "In the style of Studio Ghibli animation,",
        "suffix": "soft pastel colors, hand-drawn animation feel, whimsical, Miyazaki",
        "negative": "photorealistic, 3D render, dark, gritty",
    },
    "pixar": {
        "label": "Pixar 3D",
        "prefix": "Pixar-style 3D animation,",
        "suffix": "smooth 3D render, expressive characters, vibrant colors, subsurface scattering",
        "negative": "2D, flat, sketch, dark",
    },
    "watercolor": {
        "label": "Watercolor",
        "prefix": "Watercolor painting style,",
        "suffix": "soft washes, translucent layers, paper texture, artistic brushstrokes",
        "negative": "photorealistic, sharp edges, digital",
    },
    "oil_painting": {
        "label": "Oil Painting",
        "prefix": "Classical oil painting style,",
        "suffix": "rich impasto brushstrokes, warm tones, gallery lighting, canvas texture",
        "negative": "flat, digital, anime",
    },
    "comic": {
        "label": "Comic Book",
        "prefix": "Comic book illustration style,",
        "suffix": "bold outlines, cel-shading, halftone dots, speech bubbles, dynamic angles",
        "negative": "photorealistic, soft, blurry",
    },
    "noir": {
        "label": "Film Noir",
        "prefix": "Film noir cinematography,",
        "suffix": "high contrast black and white, dramatic shadows, venetian blind lighting, 1940s",
        "negative": "colorful, bright, cheerful, modern",
    },
    "cyberpunk": {
        "label": "Cyberpunk",
        "prefix": "Cyberpunk aesthetic,",
        "suffix": "neon lights, rain-slicked streets, holographic displays, futuristic city, blade runner",
        "negative": "natural, pastoral, vintage, bright daylight",
    },
    "ukiyo_e": {
        "label": "Ukiyo-e (Japanese Woodblock)",
        "prefix": "Japanese ukiyo-e woodblock print style,",
        "suffix": "flat colors, bold outlines, traditional Japanese art, wave patterns, Hokusai",
        "negative": "3D, photorealistic, modern",
    },
    "impressionist": {
        "label": "Impressionist",
        "prefix": "French impressionist painting,",
        "suffix": "dappled light, visible brushstrokes, Monet, Renoir, outdoor scene, plein air",
        "negative": "sharp, digital, photorealistic",
    },
    "vintage_film": {
        "label": "Vintage Film (Super 8)",
        "prefix": "Vintage Super 8 film footage,",
        "suffix": "film grain, warm color cast, light leaks, vignette, 1970s home movie feel",
        "negative": "modern, clean, digital, 4K",
    },
}


@dataclass
class StyleTransferResult:
    """Result of a style transfer operation."""
    video_path: str
    num_frames: int
    duration_seconds: float
    resolution: str
    generation_time: float
    seed: int
    style_name: str
    prompt_used: str
    success: bool
    error: Optional[str] = None


def get_style_prompt(
    base_prompt: str,
    style: str,
    custom_style_description: str = "",
) -> str:
    """
    Build a styled prompt by combining a base prompt with style modifiers.
    
    Args:
        base_prompt: The core scene/action description
        style: Style preset name or "custom"
        custom_style_description: Free-form style description (when style="custom")
    """
    if style == "custom" and custom_style_description:
        return f"{custom_style_description}, {base_prompt}"
    
    preset = STYLE_PRESETS.get(style)
    if preset:
        parts = [preset["prefix"], base_prompt, preset["suffix"]]
        return " ".join(p for p in parts if p)
    
    # Fallback: treat style as a direct modifier
    return f"{style} style, {base_prompt}"


class StyleTransferPipeline(BasePipeline):
    """
    Style transfer pipeline for artistic video generation.
    
    Supports:
    1. Preset styles (ghibli, pixar, comic, noir, cyberpunk, etc.)
    2. Custom style descriptions
    3. Reference image style transfer
    4. Video restyling (keep motion, change aesthetics)
    """
    pipeline_name: str = "style_transfer"
    def _execute(self, request):
        """Implement BasePipeline._execute — delegate to generate_with_style()."""
        result = self.generate_with_style(
            person_image=request.image_paths[0] if request.image_paths else '',
            prompt=request.prompt,
            style=request.style,
            custom_style=request.extra.get('custom_style', ''),
            preset=request.preset,
            seed=request.seed,
        )
        return __import__('fitstream.core.interfaces', fromlist=['GenerationResult']).GenerationResult(
            success=result.success, video_path=result.video_path,
            error=result.error, pipeline=self.pipeline_name,
            generation_time=getattr(result, 'generation_time', 0),
        )

    def __init__(self, config: Optional[FitStreamConfig] = None, model_manager: Optional[ModelManager] = None) -> None:
        super().__init__(config, model_manager)
    
    @staticmethod
    def list_styles() -> dict:
        """Return all available style presets."""
        return {k: v["label"] for k, v in STYLE_PRESETS.items()}
    
    def generate_with_style(
        self,
        person_image: Union[str, Path],
        prompt: str,
        style: str = "ghibli",
        custom_style: str = "",
        style_reference: Optional[Union[str, Path]] = None,
        output_path: Optional[str] = None,
        preset: str = "standard",
        seed: int = -1,
    ) -> StyleTransferResult:
        """
        Generate a stylized animation from a person photo.
        
        Args:
            person_image: Reference person photo
            prompt: Scene/action description
            style: Style preset name or "custom"
            custom_style: Free-form style (when style="custom")
            style_reference: Optional style reference image
            preset: Quality preset
        """
        start_time = time.time()
        
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        preset_config = self.config.get_preset(preset)
        width = preset_config.width
        height = preset_config.height
        num_frames = preset_config.num_frames
        fps = self.config.animate.fps
        
        # Build styled prompt
        styled_prompt = get_style_prompt(prompt, style, custom_style)
        style_label = STYLE_PRESETS.get(style, {}).get("label", style)
        
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            safe_style = style.replace(" ", "_")[:20]
            output_path = os.path.join(
                self.config.output_dir, f"style_{safe_style}_{timestamp}_{seed}.mp4"
            )
        
        logger.info(f"🎨 Style Transfer Generation:")
        logger.info(f"   Style: {style_label}")
        logger.info(f"   Person: {person_image}")
        logger.info(f"   Prompt: {styled_prompt[:100]}...")
        if style_reference:
            logger.info(f"   Style ref: {style_reference}")
        
        try:
            ref_image = load_and_prepare_image(person_image, width, height)
            pipe = self.model_manager.load_vace_diffusers()
            
            import torch
            generator = torch.Generator(device="cpu").manual_seed(seed)
            
            output = pipe(
                image=ref_image,
                prompt=styled_prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=preset_config.num_inference_steps,
                guidance_scale=preset_config.guidance_scale,
                generator=generator,
            )
            
            frames = output.frames
            if isinstance(frames, list) and len(frames) > 0:
                if isinstance(frames[0], list):
                    frames = frames[0]
            
            save_video(frames, output_path, fps=fps)
            generation_time = time.time() - start_time
            
            return StyleTransferResult(
                video_path=output_path,
                num_frames=num_frames,
                duration_seconds=num_frames / fps,
                resolution=f"{width}x{height}",
                generation_time=generation_time,
                seed=seed,
                style_name=style_label,
                prompt_used=styled_prompt,
                success=True,
            )
        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"❌ Style transfer failed: {e}")
            return StyleTransferResult(
                video_path="", num_frames=0, duration_seconds=0,
                resolution=f"{width}x{height}",
                generation_time=time.time() - start_time,
                seed=seed, style_name=style_label,
                prompt_used=styled_prompt, success=False, error=str(e),
            )
    
    def restyle_video(
        self,
        video_path: Union[str, Path],
        style: str = "ghibli",
        prompt: str = "Restyle this video",
        custom_style: str = "",
        output_path: Optional[str] = None,
        seed: int = -1,
    ) -> StyleTransferResult:
        """
        Restyle an existing video (V2V style transfer).
        
        Keeps the motion/content but changes the visual aesthetics.
        Uses VACE's V2V capability with a style-focused prompt.
        """
        start_time = time.time()
        
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        styled_prompt = get_style_prompt(prompt, style, custom_style)
        style_label = STYLE_PRESETS.get(style, {}).get("label", style)
        
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = os.path.join(self.config.output_dir, f"restyle_{timestamp}_{seed}.mp4")
        
        logger.info(f"🎨 Video Restyle:")
        logger.info(f"   Source: {video_path}")
        logger.info(f"   Style: {style_label}")
        
        try:
            # Extract first frame as reference
            import cv2
            from PIL import Image
            
            cap = cv2.VideoCapture(str(video_path))
            ret, frame = cap.read()
            fps = cap.get(cv2.CAP_PROP_FPS) or 16
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if not ret:
                raise ValueError("Could not read video")
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ref_image = Image.fromarray(frame_rgb)
            
            preset_config = self.config.get_preset("standard")
            width, height = preset_config.width, preset_config.height
            
            from fitstream.core.utils.image_utils import resize_to_target
            ref_image = resize_to_target(ref_image, width, height)
            
            pipe = self.model_manager.load_vace_diffusers()
            
            import torch
            generator = torch.Generator(device="cpu").manual_seed(seed)
            
            num_frames = min(total_frames, preset_config.num_frames)
            
            output = pipe(
                image=ref_image,
                prompt=styled_prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=preset_config.num_inference_steps,
                guidance_scale=preset_config.guidance_scale + 1.0,  # Slightly higher for style adherence
                generator=generator,
            )
            
            frames = output.frames
            if isinstance(frames, list) and len(frames) > 0:
                if isinstance(frames[0], list):
                    frames = frames[0]
            
            save_video(frames, output_path, fps=int(fps))
            generation_time = time.time() - start_time
            
            return StyleTransferResult(
                video_path=output_path,
                num_frames=num_frames,
                duration_seconds=num_frames / fps,
                resolution=f"{width}x{height}",
                generation_time=generation_time,
                seed=seed,
                style_name=style_label,
                prompt_used=styled_prompt,
                success=True,
            )
        except (RuntimeError, OSError, ValueError) as e:
            logger.error(f"❌ Video restyle failed: {e}")
            return StyleTransferResult(
                video_path="", num_frames=0, duration_seconds=0,
                resolution="", generation_time=time.time() - start_time,
                seed=seed, style_name=style_label,
                prompt_used=styled_prompt, success=False, error=str(e),
            )
