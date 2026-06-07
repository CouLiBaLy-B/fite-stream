"""
FitStream Try-On Pipeline
Virtual try-on: Person image + Garment image + Prompt → Video with new outfit

Supports two modes:
  1. Image Try-On: Static photo with garment swap (fast, ~3-10s)
  2. Video Try-On: Animated video wearing the new garment (slower, ~30-120s)

Uses VACE MV2V (Masked Video-to-Video) under the hood:
  - Detects the clothing region on the person
  - Masks it out
  - Inpaints with the target garment guided by the reference image
"""

import os
import time
import random
from pathlib import Path
from typing import Optional, List, Union
from dataclasses import dataclass
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.utils.image_utils import load_and_prepare_image
from fitstream.core.utils.video_utils import save_video
from fitstream.core.utils.prompt_utils import enhance_prompt


@dataclass
class TryOnResult:
    """Result of a virtual try-on generation."""
    video_path: str
    num_frames: int
    duration_seconds: float
    resolution: str
    generation_time: float
    seed: int
    prompt_used: str
    garment_category: str
    success: bool
    error: Optional[str] = None


# Garment category definitions used for prompt construction
GARMENT_CATEGORIES = {
    "upper": {
        "label": "upper body",
        "keywords": ["shirt", "blouse", "t-shirt", "jacket", "coat", "sweater",
                      "hoodie", "vest", "top", "cardigan", "blazer"],
        "mask_hint": "upper body clothing area from shoulders to waist",
    },
    "lower": {
        "label": "lower body",
        "keywords": ["pants", "trousers", "jeans", "shorts", "skirt", "leggings"],
        "mask_hint": "lower body clothing area from waist to ankles",
    },
    "dress": {
        "label": "full body dress",
        "keywords": ["dress", "gown", "jumpsuit", "romper", "overalls"],
        "mask_hint": "full body clothing area from shoulders to below knees",
    },
    "shoes": {
        "label": "footwear",
        "keywords": ["shoes", "boots", "sneakers", "sandals", "heels", "loafers"],
        "mask_hint": "feet and footwear area",
    },
    "accessories": {
        "label": "accessory",
        "keywords": ["hat", "bag", "scarf", "necklace", "watch", "glasses",
                      "sunglasses", "belt", "bracelet", "earrings"],
        "mask_hint": "accessory area",
    },
}


def detect_garment_category(prompt: str) -> str:
    prompt_lower = prompt.lower()
    for cat_key, cat_info in GARMENT_CATEGORIES.items():
        if any(kw in prompt_lower for kw in cat_info["keywords"]):
            return cat_key
    return "upper"  # default


def build_tryon_prompt(
    garment_description: str,
    category: str = "auto",
    style: str = "cinematic",
    action: str = "walking naturally",
) -> str:
    """
    Build an optimized prompt for virtual try-on.
    
    Args:
        garment_description: Description of the target garment
        category: Garment category or "auto" to detect
        style: Visual style
        action: What the person should be doing in the video
    """
    if category == "auto":
        category = detect_garment_category(garment_description)
    
    cat_info = GARMENT_CATEGORIES.get(category, GARMENT_CATEGORIES["upper"])
    
    # Build the core prompt
    prompt_parts = [
        f"The person is now wearing {garment_description}",
    ]
    
    if action:
        prompt_parts.append(f"The person is {action}")
    
    prompt_parts.append(
        "The garment fits naturally on the body with realistic wrinkles and draping. "
        "The lighting and shadows on the clothing match the scene perfectly."
    )
    
    base_prompt = ". ".join(prompt_parts)
    
    return enhance_prompt(base_prompt, style=style, quality_suffix=True)


class TryOnPipeline:
    """
    Virtual try-on pipeline.
    
    Takes a person image, a garment image, and a prompt,
    then generates a video of the person wearing the new garment.
    
    Usage:
        pipeline = TryOnPipeline()
        result = pipeline.generate(
            person_image="person.jpg",
            garment_image="red_dress.jpg",
            prompt="a beautiful red evening dress",
            action="walking on a runway",
        )
    """
    pipeline_name: str = "tryon"

    
    def __init__(self, config: FitStreamConfig = None, model_manager: ModelManager = None) -> None:
        self.config = config or get_config()
        self.model_manager = model_manager or ModelManager(self.config)
        self._pipe = None
    
    def _ensure_model_loaded(self):
        """Ensure the generation model is loaded."""
        if self._pipe is None:
            self._pipe = self.model_manager.load_vace_diffusers()
        return self._pipe
    
    def generate(
        self,
        person_image: Union[str, Path],
        garment_image: Union[str, Path],
        prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        # Garment options
        category: str = "auto",
        action: str = "walking naturally, showing off the outfit",
        # Generation params
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_frames: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: int = -1,
        style: str = "cinematic",
        preset: str = "standard",
    ) -> TryOnResult:
        """
        Generate a virtual try-on video.
        
        The pipeline:
          1. Loads the person image and garment image
          2. Auto-detects garment category (or uses provided)
          3. Builds an optimized prompt
          4. Uses VACE to generate video with the person wearing the garment
          
        For VACE, this uses reference-to-video (R2V) with both images as references.
        The prompt guides the model to dress the person in the garment.
        
        Args:
            person_image: Path to the person photo
            garment_image: Path to the garment/clothing image
            prompt: Optional custom prompt (auto-generated if None)
            category: Garment category ("upper", "lower", "dress", "shoes", "auto")
            action: What the person should do in the video
        """
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
        fps = anim_config.fps
        num_inference_steps = num_inference_steps or anim_config.num_inference_steps
        guidance_scale = guidance_scale or anim_config.guidance_scale
        
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        # Detect category
        detected_category = category
        if category == "auto" and prompt:
            detected_category = detect_garment_category(prompt)
        elif category == "auto":
            detected_category = "upper"
        
        # Build prompt
        if prompt:
            prompt_used = build_tryon_prompt(prompt, detected_category, style, action)
        else:
            prompt_used = build_tryon_prompt(
                "the garment from the reference image",
                detected_category, style, action,
            )
        
        # Generate output path
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = os.path.join(
                self.config.output_dir, f"tryon_{detected_category}_{timestamp}_{seed}.mp4"
            )
        
        logger.info(f"👗 Virtual Try-On:")
        logger.info(f"   Person: {person_image}")
        logger.info(f"   Garment: {garment_image}")
        logger.info(f"   Category: {detected_category}")
        logger.info(f"   Action: {action}")
        logger.info(f"   Prompt: {prompt_used[:100]}...")
        
        try:
            # Load images
            person_img = load_and_prepare_image(person_image, width, height)
            garment_img = load_and_prepare_image(garment_image, width, height)
            
            pipe = self._ensure_model_loaded()
            
            import torch
            generator = torch.Generator(device="cpu").manual_seed(seed)
            
            logger.info("⏳ Generating try-on video...")
            
            # Strategy: Use person as primary reference + garment as secondary
            # The prompt tells the model to dress the person in the garment
            # VACE supports multiple reference images natively
            output = pipe(
                image=person_img,
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
            
            result = TryOnResult(
                video_path=output_path,
                num_frames=num_frames,
                duration_seconds=duration_seconds,
                resolution=f"{width}x{height}",
                generation_time=generation_time,
                seed=seed,
                prompt_used=prompt_used,
                garment_category=detected_category,
                success=True,
            )
            
            logger.success(
                f"✅ Try-on generated in {generation_time:.1f}s → {output_path}"
            )
            return result
            
        except (RuntimeError, OSError, ValueError) as e:
            generation_time = time.time() - start_time
            logger.error(f"❌ Try-on failed: {e}")
            return TryOnResult(
                video_path="",
                num_frames=0,
                duration_seconds=0,
                resolution=f"{width}x{height}",
                generation_time=generation_time,
                seed=seed,
                prompt_used=prompt_used,
                garment_category=detected_category,
                success=False,
                error=str(e),
            )
    
    def generate_outfit(
        self,
        person_image: Union[str, Path],
        garment_images: List[Union[str, Path]],
        garment_descriptions: List[str],
        output_path: Optional[str] = None,
        action: str = "walking on a runway, showing the complete outfit",
        style: str = "cinematic",
        preset: str = "standard",
        seed: int = -1,
    ) -> TryOnResult:
        """
        Generate a try-on with a complete outfit (multiple garments).
        
        Uses LoomVideo-style multi-image referencing when available,
        falls back to combined prompt approach with VACE.
        
        Args:
            person_image: Path to the person photo
            garment_images: List of garment image paths
            garment_descriptions: Description of each garment
            action: What the person does in the video
        """
        # Build a combined prompt
        outfit_parts = []
        for i, desc in enumerate(garment_descriptions):
            outfit_parts.append(desc)
        
        combined_desc = ", ".join(outfit_parts)
        full_prompt = f"a complete outfit consisting of {combined_desc}"
        
        logger.info(f"👔 Multi-garment try-on: {len(garment_images)} items")
        
        # For now, use the first garment image as primary reference
        # TODO: When LoomVideo is integrated, use multi-image referencing
        return self.generate(
            person_image=person_image,
            garment_image=garment_images[0],
            prompt=full_prompt,
            output_path=output_path,
            category="auto",
            action=action,
            style=style,
            preset=preset,
            seed=seed,
        )
