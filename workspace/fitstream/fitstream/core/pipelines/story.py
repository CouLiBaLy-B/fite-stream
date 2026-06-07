"""
FitStream Story Pipeline
Multi-scene story generation: Takes a story text and generates
a sequence of animated clips that tell a coherent narrative.

Example:
    pipeline = StoryPipeline()
    result = pipeline.generate(
        image_path="person.jpg",
        story="Marie walks through Paris. She enters a bakery. She buys a croissant.",
    )
"""

import os
import time
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.pipelines.animate import AnimatePipeline, AnimateResult
from fitstream.core.utils.video_utils import concatenate_videos
from fitstream.core.utils.prompt_utils import (
    split_story_to_scenes, 
    create_story_summary,
    Scene,
)


@dataclass
class StoryResult:
    """Result of a multi-scene story generation."""
    final_video_path: str
    scene_results: List[AnimateResult]
    scenes: List[Scene]
    total_duration: float
    total_generation_time: float
    success: bool
    error: Optional[str] = None
    
    @property
    def num_scenes_completed(self) -> int:
        """Num scenes completed."""
        return sum(1 for r in self.scene_results if r.success)


class StoryPipeline:
    """
    Multi-scene story generation pipeline.
    
    Takes a story text (or list of scenes), generates each scene
    as a video clip, and concatenates them into a final video.
    
    Usage:
        pipeline = StoryPipeline()
        
        # From free-form text
        result = pipeline.generate(
            image_path="person.jpg",
            story="A woman walks through Paris. She stops at a café. She watches the sunset.",
        )
        
        # From structured scenes
        result = pipeline.generate_from_scenes(
            image_path="person.jpg",
            scenes=[
                Scene(0, "A woman walks through a Parisian street", "medium"),
                Scene(1, "She stops at a charming sidewalk café", "medium"),
                Scene(2, "She watches the golden sunset over the Seine", "long"),
            ],
        )
    """
    pipeline_name: str = "story"

    
    def __init__(self, config: FitStreamConfig = None, model_manager: ModelManager = None) -> None:
        self.config = config or get_config()
        self.model_manager = model_manager or ModelManager(self.config)
        self.animate_pipeline = AnimatePipeline(self.config, self.model_manager)
    
    def generate(
        self,
        image_path: str,
        story: str,
        output_path: Optional[str] = None,
        style: str = "cinematic",
        preset: str = "standard",
        transition: str = "crossfade",
        max_scenes: int = None,
    ) -> StoryResult:
        """
        Generate a multi-scene story video from text.
        
        Args:
            image_path: Path to the reference person image
            story: Story text (will be automatically split into scenes)
            output_path: Where to save the final video
            style: Visual style for all scenes
            preset: Quality preset ("draft", "standard", "high")
            transition: Transition between scenes ("none", "crossfade")
            max_scenes: Maximum number of scenes (default from config)
        
        Returns:
            StoryResult with the final video and per-scene details
        """
        max_scenes = max_scenes or self.config.story.scenes_max
        
        # Split story into scenes
        scenes = split_story_to_scenes(
            story,
            max_scenes=max_scenes,
            auto_enhance=True,
            style=style,
        )
        
        if not scenes:
            return StoryResult(
                final_video_path="",
                scene_results=[],
                scenes=[],
                total_duration=0,
                total_generation_time=0,
                success=False,
                error="Could not parse any scenes from the story text",
            )
        
        # Print story summary
        summary = create_story_summary(scenes)
        logger.info(f"\n{summary}")
        
        return self.generate_from_scenes(
            image_path=image_path,
            scenes=scenes,
            output_path=output_path,
            style=style,
            preset=preset,
            transition=transition,
        )
    
    def generate_from_scenes(
        self,
        image_path: str,
        scenes: List[Scene],
        output_path: Optional[str] = None,
        style: str = "cinematic",
        preset: str = "standard",
        transition: str = "crossfade",
    ) -> StoryResult:
        """
        Generate a story from a list of pre-defined scenes.
        """
        start_time = time.time()
        
        if not scenes:
            return StoryResult(
                final_video_path="", scene_results=[], scenes=[],
                total_duration=0, total_generation_time=0,
                success=False, error="No scenes provided",
            )
        
        # Create output directory
        if output_path is None:
            timestamp = int(time.time())
            output_dir = os.path.join(self.config.output_dir, f"story_{timestamp}")
        else:
            output_dir = os.path.dirname(output_path) or self.config.output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        scenes_dir = os.path.join(output_dir, "scenes")
        os.makedirs(scenes_dir, exist_ok=True)
        
        logger.info(f"🎬 Generating story: {len(scenes)} scenes")
        logger.info(f"   Output directory: {output_dir}")
        
        # Generate each scene
        scene_results: List[AnimateResult] = []
        scene_videos: List[str] = []
        
        for scene in scenes:
            logger.info(f"\n{'='*60}")
            logger.info(f"📍 Scene {scene.index + 1}/{len(scenes)}")
            logger.info(f"   {scene.prompt[:100]}...")
            logger.info(f"{'='*60}")
            
            scene_output = os.path.join(scenes_dir, f"scene_{scene.index:03d}.mp4")
            
            # Get frame count based on duration hint
            preset_config = self.config.get_preset(preset)
            num_frames = scene.get_num_frames(fps=preset_config.fps)
            
            result = self.animate_pipeline.generate(
                image_path=image_path,
                prompt=scene.prompt,
                output_path=scene_output,
                num_frames=num_frames,
                preset=preset,
                style=style,
                enhance_prompt_flag=False,  # Already enhanced during scene parsing
            )
            
            scene_results.append(result)
            
            if result.success:
                scene_videos.append(result.video_path)
                logger.success(f"   ✅ Scene {scene.index + 1} done ({result.generation_time:.1f}s)")
            else:
                logger.error(f"   ❌ Scene {scene.index + 1} failed: {result.error}")
        
        # Concatenate all successful scenes
        if scene_videos:
            if output_path is None:
                output_path = os.path.join(output_dir, "story_final.mp4")
            
            try:
                concatenate_videos(
                    scene_videos,
                    output_path,
                    transition=transition,
                    transition_duration=0.5,
                )
                
                total_time = time.time() - start_time
                total_duration = sum(r.duration_seconds for r in scene_results if r.success)
                
                logger.success(f"\n🎉 Story generated!")
                logger.success(f"   Final video: {output_path}")
                logger.success(f"   Scenes: {len(scene_videos)}/{len(scenes)} successful")
                logger.success(f"   Duration: {total_duration:.1f}s")
                logger.success(f"   Generation time: {total_time:.1f}s")
                
                return StoryResult(
                    final_video_path=output_path,
                    scene_results=scene_results,
                    scenes=scenes,
                    total_duration=total_duration,
                    total_generation_time=total_time,
                    success=True,
                )
                
            except (RuntimeError, OSError, ValueError) as e:
                logger.error(f"Failed to concatenate scenes: {e}")
                return StoryResult(
                    final_video_path="",
                    scene_results=scene_results,
                    scenes=scenes,
                    total_duration=0,
                    total_generation_time=time.time() - start_time,
                    success=False,
                    error=f"Concatenation failed: {e}",
                )
        else:
            return StoryResult(
                final_video_path="",
                scene_results=scene_results,
                scenes=scenes,
                total_duration=0,
                total_generation_time=time.time() - start_time,
                success=False,
                error="No scenes were generated successfully",
            )
