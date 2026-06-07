"""
FitStream A/B Testing Pipeline
Generate multiple variants of the same scene for comparison.

Use cases:
  - Compare different styles on the same prompt
  - Compare different prompts on the same image
  - Compare different seeds (variation exploration)
  - Compare different presets (quality vs speed)
  - Generate and rank variants automatically

Usage:
    ab = ABTestingPipeline()
    
    # Compare styles
    result = ab.compare_styles(
        image="person.jpg",
        prompt="Walking in a garden",
        styles=["cinematic", "ghibli", "noir"],
    )
    
    # Compare prompts
    result = ab.compare_prompts(
        image="person.jpg",
        prompts=["Walking happily", "Walking sadly", "Running fast"],
    )
    
    # Variation exploration (same prompt, different seeds)
    result = ab.explore_variations(
        image="person.jpg",
        prompt="Elegant fashion walk",
        num_variations=4,
    )
"""

import os
import time
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager


@dataclass
class Variant:
    """A single variant in an A/B test."""
    id: str
    label: str
    video_path: str = ""
    seed: int = 0
    prompt: str = ""
    style: str = ""
    preset: str = ""
    generation_time: float = 0.0
    success: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestResult:
    """Result of an A/B test with multiple variants."""
    test_id: str
    test_type: str
    variants: List[Variant]
    total_time: float
    num_successful: int
    output_dir: str
    comparison_grid: str = ""  # Path to comparison storyboard
    
    def to_dict(self) -> dict:
        """To dict."""
        return {
            "test_id": self.test_id,
            "test_type": self.test_type,
            "total_time": self.total_time,
            "num_successful": self.num_successful,
            "num_total": len(self.variants),
            "variants": [
                {
                    "id": v.id,
                    "label": v.label,
                    "video_path": v.video_path,
                    "seed": v.seed,
                    "style": v.style,
                    "generation_time": v.generation_time,
                    "success": v.success,
                    "error": v.error,
                }
                for v in self.variants
            ],
            "comparison_grid": self.comparison_grid,
        }


class ABTestingPipeline:
    """
    A/B testing for video generation — compare multiple variants side by side.
    """
    
    def __init__(self, config: FitStreamConfig = None, model_manager: ModelManager = None) -> None:
        self.config = config or get_config()
        self.model_manager = model_manager or ModelManager(self.config)
    
    def compare_styles(
        self,
        image_path: str,
        prompt: str,
        styles: List[str],
        preset: str = "draft",
        seed: int = -1,
    ) -> ABTestResult:
        """
        Generate the same scene in multiple styles for comparison.
        Same seed ensures consistent composition across styles.
        """
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        test_id = f"style_{int(time.time())}"
        output_dir = os.path.join(self.config.output_dir, "ab_tests", test_id)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"🔬 A/B Test — Comparing {len(styles)} styles")
        
        variants = []
        start_time = time.time()
        
        for style in styles:
            variant_id = f"{test_id}_{style}"
            output_path = os.path.join(output_dir, f"{style}.mp4")
            
            logger.info(f"  🎨 Generating style: {style}")
            
            variant = Variant(
                id=variant_id,
                label=f"Style: {style}",
                seed=seed,
                prompt=prompt,
                style=style,
                preset=preset,
            )
            
            try:
                from fitstream.core.pipelines.style_transfer import StyleTransferPipeline
                pipeline = StyleTransferPipeline(self.config, self.model_manager)
                result = pipeline.generate_with_style(
                    person_image=image_path,
                    prompt=prompt,
                    style=style,
                    preset=preset,
                    seed=seed,
                    output_path=output_path,
                )
                
                variant.video_path = result.video_path
                variant.generation_time = result.generation_time
                variant.success = result.success
                variant.error = result.error
                
            except (RuntimeError, OSError, ValueError) as e:
                variant.error = str(e)
                logger.error(f"  ❌ Style {style} failed: {e}")
            
            variants.append(variant)
        
        total_time = time.time() - start_time
        successful = sum(1 for v in variants if v.success)
        
        logger.success(f"🔬 A/B Test complete: {successful}/{len(variants)} variants ({total_time:.1f}s)")
        
        return ABTestResult(
            test_id=test_id,
            test_type="styles",
            variants=variants,
            total_time=total_time,
            num_successful=successful,
            output_dir=output_dir,
        )
    
    def compare_prompts(
        self,
        image_path: str,
        prompts: List[str],
        style: str = "cinematic",
        preset: str = "draft",
        seed: int = -1,
    ) -> ABTestResult:
        """Generate the same image with different prompts."""
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        test_id = f"prompt_{int(time.time())}"
        output_dir = os.path.join(self.config.output_dir, "ab_tests", test_id)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"🔬 A/B Test — Comparing {len(prompts)} prompts")
        
        variants = []
        start_time = time.time()
        
        for i, prompt in enumerate(prompts):
            variant_id = f"{test_id}_p{i}"
            output_path = os.path.join(output_dir, f"prompt_{i}.mp4")
            
            logger.info(f"  📝 Prompt {i+1}: {prompt[:50]}...")
            
            variant = Variant(
                id=variant_id,
                label=f"Prompt {i+1}: {prompt[:40]}...",
                seed=seed,
                prompt=prompt,
                style=style,
                preset=preset,
            )
            
            try:
                from fitstream.core.pipelines.animate import AnimatePipeline
                pipeline = AnimatePipeline(self.config, self.model_manager)
                result = pipeline.generate(
                    image_path=image_path,
                    prompt=prompt,
                    style=style,
                    preset=preset,
                    seed=seed,
                    output_path=output_path,
                )
                
                variant.video_path = result.video_path
                variant.generation_time = result.generation_time
                variant.success = result.success
                variant.error = result.error
                
            except (RuntimeError, OSError, ValueError) as e:
                variant.error = str(e)
            
            variants.append(variant)
        
        total_time = time.time() - start_time
        successful = sum(1 for v in variants if v.success)
        
        return ABTestResult(
            test_id=test_id,
            test_type="prompts",
            variants=variants,
            total_time=total_time,
            num_successful=successful,
            output_dir=output_dir,
        )
    
    def explore_variations(
        self,
        image_path: str,
        prompt: str,
        num_variations: int = 4,
        style: str = "cinematic",
        preset: str = "draft",
        base_seed: Optional[int] = None,
    ) -> ABTestResult:
        """
        Generate N variations with different seeds.
        Great for exploring different interpretations of the same prompt.
        """
        if base_seed is None:
            base_seed = random.randint(0, 2**32 - 1)
        
        seeds = [base_seed + i * 12345 for i in range(num_variations)]
        
        test_id = f"explore_{int(time.time())}"
        output_dir = os.path.join(self.config.output_dir, "ab_tests", test_id)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"🔬 Exploring {num_variations} variations of: {prompt[:50]}...")
        
        variants = []
        start_time = time.time()
        
        for i, seed in enumerate(seeds):
            variant_id = f"{test_id}_v{i}"
            output_path = os.path.join(output_dir, f"variation_{i}_seed{seed}.mp4")
            
            variant = Variant(
                id=variant_id,
                label=f"Variation {i+1} (seed={seed})",
                seed=seed,
                prompt=prompt,
                style=style,
                preset=preset,
            )
            
            try:
                from fitstream.core.pipelines.animate import AnimatePipeline
                pipeline = AnimatePipeline(self.config, self.model_manager)
                result = pipeline.generate(
                    image_path=image_path,
                    prompt=prompt,
                    style=style,
                    preset=preset,
                    seed=seed,
                    output_path=output_path,
                )
                
                variant.video_path = result.video_path
                variant.generation_time = result.generation_time
                variant.success = result.success
                variant.error = result.error
                
            except (RuntimeError, OSError, ValueError) as e:
                variant.error = str(e)
            
            variants.append(variant)
        
        total_time = time.time() - start_time
        successful = sum(1 for v in variants if v.success)
        
        return ABTestResult(
            test_id=test_id,
            test_type="variations",
            variants=variants,
            total_time=total_time,
            num_successful=successful,
            output_dir=output_dir,
        )
