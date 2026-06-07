"""
FitStream Extend Pipeline
Temporal extension: Take a short video clip and make it longer.

Uses VACE's temporal extension capability:
  - Takes the last N frames of the existing clip
  - Generates continuation frames that maintain visual coherence
  - Chains multiple extensions for arbitrarily long videos

Usage:
    pipeline = ExtendPipeline()
    result = pipeline.extend(
        video_path="short_clip.mp4",
        prompt="Continue the scene naturally",
        target_duration=15.0,  # seconds
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
from fitstream.core.utils.video_utils import save_video, concatenate_videos, get_video_info
from fitstream.core.pipelines.base import BasePipeline


@dataclass
class ExtendResult:
    """Result of a video extension."""
    video_path: str
    original_duration: float
    final_duration: float
    num_extensions: int
    generation_time: float
    success: bool
    error: Optional[str] = None


class ExtendPipeline(BasePipeline):
    """
    Temporal extension pipeline.
    
    Takes an existing video and extends it by generating continuation frames
    that maintain visual coherence with the original.
    
    Strategies:
    1. VACE temporal extension (native, best quality)
    2. Last-frame-as-reference (fallback, uses I2V with last frame)
    """
    pipeline_name: str = "extend"
    def _execute(self, request):
        """Implement BasePipeline._execute — delegate to extend()."""
        result = self.extend(
            video_path=request.extra.get('video_path', ''),
            prompt=request.prompt,
            additional_frames=request.extra.get('additional_frames', 49),
        )
        return __import__('fitstream.core.interfaces', fromlist=['GenerationResult']).GenerationResult(
            success=result.success, video_path=result.video_path,
            error=result.error, pipeline=self.pipeline_name,
            generation_time=getattr(result, 'generation_time', 0),
            num_frames=getattr(result, 'num_frames', 0),
        )

    def __init__(self, config: FitStreamConfig = None, model_manager: ModelManager = None) -> None:
        super().__init__(config, model_manager)
    
    def extend(
        self,
        video_path: Union[str, Path],
        prompt: str = "Continue the scene naturally with smooth motion",
        output_path: Optional[str] = None,
        target_duration: float = 10.0,
        overlap_frames: int = 8,
        chunk_frames: int = 49,
        num_inference_steps: int = 30,
        guidance_scale: float = 5.0,
        seed: int = -1,
    ) -> ExtendResult:
        """
        Extend a video to a target duration.
        
        Args:
            video_path: Path to the input video to extend
            prompt: Text prompt guiding the extension
            target_duration: Desired final duration in seconds
            overlap_frames: Number of frames to overlap between chunks
            chunk_frames: Frames per extension chunk
            
        The extension works by:
        1. Extract the last `overlap_frames` from the current video
        2. Generate `chunk_frames` new frames conditioned on the overlap
        3. Trim the overlap and concatenate
        4. Repeat until target_duration is reached
        """
        start_time = time.time()
        video_path = str(video_path)
        
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        
        # Get original video info
        info = get_video_info(video_path)
        original_duration = info.get("duration", 0)
        fps = info.get("fps", 16) or 16
        
        if original_duration <= 0:
            return ExtendResult(
                video_path=video_path, original_duration=0, final_duration=0,
                num_extensions=0, generation_time=0, success=False,
                error="Could not read video duration",
            )
        
        if original_duration >= target_duration:
            logger.info(f"Video already {original_duration:.1f}s >= target {target_duration:.1f}s")
            return ExtendResult(
                video_path=video_path, original_duration=original_duration,
                final_duration=original_duration, num_extensions=0,
                generation_time=0, success=True,
            )
        
        if output_path is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = os.path.join(self.config.output_dir, f"extended_{timestamp}.mp4")
        
        logger.info(f"🔄 Extending video:")
        logger.info(f"   Input: {video_path} ({original_duration:.1f}s)")
        logger.info(f"   Target: {target_duration:.1f}s")
        logger.info(f"   Chunk: {chunk_frames} frames, overlap: {overlap_frames}")
        
        try:
            chunks = [video_path]
            current_duration = original_duration
            num_extensions = 0
            max_extensions = 20  # safety limit
            
            while current_duration < target_duration and num_extensions < max_extensions:
                logger.info(f"   Extension {num_extensions + 1}: {current_duration:.1f}s → generating...")
                
                # Extract last frame(s) from current video as reference
                last_frame = self._extract_last_frame(chunks[-1])
                
                if last_frame is None:
                    logger.warning("Could not extract last frame, stopping extension")
                    break
                
                # Generate continuation chunk
                chunk_path = os.path.join(
                    os.path.dirname(output_path),
                    f"_extend_chunk_{num_extensions}.mp4"
                )
                
                pipe = self.model_manager.load_vace_diffusers()
                
                import torch
                generator = torch.Generator(device="cpu").manual_seed(seed + num_extensions)
                
                output = pipe(
                    image=last_frame,
                    prompt=prompt,
                    height=info.get("height", 480),
                    width=info.get("width", 832),
                    num_frames=chunk_frames,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
                
                frames = output.frames
                if isinstance(frames, list) and len(frames) > 0:
                    if isinstance(frames[0], list):
                        frames = frames[0]
                
                # Skip overlap frames at the start (they overlap with the previous chunk)
                frames_to_save = frames[overlap_frames:]
                
                if len(frames_to_save) > 0:
                    save_video(frames_to_save, chunk_path, fps=int(fps))
                    chunks.append(chunk_path)
                    
                    chunk_duration = len(frames_to_save) / fps
                    current_duration += chunk_duration
                    num_extensions += 1
                    
                    logger.info(f"   → Added {chunk_duration:.1f}s (total: {current_duration:.1f}s)")
                else:
                    break
            
            # Concatenate all chunks
            if len(chunks) > 1:
                concatenate_videos(chunks, output_path, transition="none")
                
                # Clean up temp chunks
                for chunk in chunks[1:]:
                    if os.path.exists(chunk) and chunk != output_path:
                        try:
                            os.unlink(chunk)
                        except OSError:
                            pass
            else:
                import shutil
                shutil.copy2(video_path, output_path)
            
            generation_time = time.time() - start_time
            
            final_info = get_video_info(output_path)
            final_duration = final_info.get("duration", current_duration)
            
            logger.success(
                f"✅ Extended: {original_duration:.1f}s → {final_duration:.1f}s "
                f"({num_extensions} extensions, {generation_time:.1f}s)"
            )
            
            return ExtendResult(
                video_path=output_path,
                original_duration=original_duration,
                final_duration=final_duration,
                num_extensions=num_extensions,
                generation_time=generation_time,
                success=True,
            )
            
        except (RuntimeError, OSError, ValueError) as e:
            generation_time = time.time() - start_time
            logger.error(f"❌ Extension failed: {e}")
            return ExtendResult(
                video_path="", original_duration=original_duration,
                final_duration=0, num_extensions=0,
                generation_time=generation_time, success=False,
                error=str(e),
            )
    
    def _extract_last_frame(self, video_path: str):
        try:
            import cv2
            from PIL import Image
            import numpy as np
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                return None
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)
            
            return None
        except (RuntimeError, OSError, ValueError) as e:
            logger.warning(f"Failed to extract last frame: {e}")
            return None
