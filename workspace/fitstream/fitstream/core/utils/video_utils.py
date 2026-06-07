"""
Video utilities for FitStream.
Handles saving, concatenating, and processing video outputs.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional, List, Union, Optional
from loguru import logger


def save_video(
    frames: list,
    output_path: str,
    fps: int = 16,
    quality: int = 23,
) -> str:
    """
    Save a list of PIL Image frames as an MP4 video.
    Uses imageio for broad compatibility.
    """
    output_path = str(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    try:
        import imageio
        
        writer = imageio.get_writer(
            output_path,
            fps=fps,
            codec="libx264",
            quality=None,
            output_params=["-crf", str(quality), "-pix_fmt", "yuv420p"],
        )
        
        import numpy as np
        for frame in frames:
            if hasattr(frame, 'numpy'):
                # Torch tensor
                arr = frame.cpu().numpy()
            elif hasattr(frame, 'convert'):
                # PIL Image
                arr = np.array(frame)
            else:
                arr = np.array(frame)
            
            # Ensure uint8
            if arr.dtype != np.uint8:
                if arr.max() <= 1.0:
                    arr = (arr * 255).clip(0, 255).astype(np.uint8)
                else:
                    arr = arr.clip(0, 255).astype(np.uint8)
            
            writer.append_data(arr)
        
        writer.close()
        logger.info(f"Video saved: {output_path} ({len(frames)} frames @ {fps}fps)")
        return output_path
        
    except ImportError:
        logger.warning("imageio not available, trying diffusers export")
        from diffusers.utils import export_to_video
        export_to_video(frames, output_path, fps=fps)
        return output_path


def concatenate_videos(
    video_paths: List[str],
    output_path: str,
    transition: str = "none",
    transition_duration: float = 0.5,
) -> str:
    """
    Concatenate multiple video clips into one.
    Uses ffmpeg for reliable concatenation.
    """
    if not video_paths:
        raise ValueError("No videos to concatenate")
    
    if len(video_paths) == 1:
        # Just copy the single video
        import shutil
        shutil.copy2(video_paths[0], output_path)
        return output_path
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    if transition == "none":
        # Simple concat with ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for vpath in video_paths:
                f.write(f"file '{os.path.abspath(vpath)}'\n")
            concat_file = f.name
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.warning(f"ffmpeg concat failed, trying re-encode: {result.stderr[:200]}")
                # Fallback: re-encode
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file,
                    "-c:v", "libx264",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_path,
                ]
                subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
            
            logger.info(f"Concatenated {len(video_paths)} videos → {output_path}")
            return output_path
            
        finally:
            os.unlink(concat_file)
    
    elif transition == "crossfade":
        # Crossfade transition using ffmpeg xfade filter
        if len(video_paths) == 2:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_paths[0],
                "-i", video_paths[1],
                "-filter_complex",
                f"xfade=transition=fade:duration={transition_duration}:offset=auto",
                "-c:v", "libx264",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
        else:
            # Multi-video crossfade: do it pairwise
            temp_files = []
            current = video_paths[0]
            
            for i, next_video in enumerate(video_paths[1:]):
                temp_out = tempfile.mktemp(suffix=f"_merge_{i}.mp4")
                temp_files.append(temp_out)
                
                cmd = [
                    "ffmpeg", "-y",
                    "-i", current,
                    "-i", next_video,
                    "-filter_complex",
                    f"xfade=transition=fade:duration={transition_duration}:offset=auto",
                    "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                    temp_out,
                ]
                subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
                current = temp_out
            
            # Move final result
            import shutil
            shutil.move(current, output_path)
            
            # Clean up temp files (except the last one which was moved)
            for tf in temp_files[:-1]:
                if os.path.exists(tf):
                    os.unlink(tf)
        
        logger.info(f"Concatenated {len(video_paths)} videos with crossfade → {output_path}")
        return output_path
    
    return output_path


def get_video_info(video_path: str) -> dict:
    """Get video metadata using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ]
        import json
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
            return {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                "codec": video_stream.get("codec_name", "unknown"),
                "frames": int(video_stream.get("nb_frames", 0)),
            }
    except (RuntimeError, OSError, ImportError) as e:
        logger.warning(f"Could not get video info: {e}")
    
    return {"duration": 0, "width": 0, "height": 0, "fps": 0}
