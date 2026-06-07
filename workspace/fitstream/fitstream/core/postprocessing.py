"""
FitStream Video Post-Processing
Apply transformations to generated videos after creation.

Features:
  - Upscaling (2x, 4x via ffmpeg/lanczos or AI-based)
  - Video stabilization (deshake filter)
  - Color grading presets (warm, cool, vintage, cinematic, vibrant)
  - Slow motion / speed adjustment
  - Looping (seamless loop creation)
  - Audio addition (background music/sound effects)
  - Watermark overlay
  - Trim / crop

Usage:
    pp = PostProcessor()
    pp.upscale("input.mp4", "output_2x.mp4", factor=2)
    pp.color_grade("input.mp4", "output_warm.mp4", preset="warm")
    pp.slow_motion("input.mp4", "output_slow.mp4", factor=2.0)
    pp.add_audio("input.mp4", "music.mp3", "output_with_audio.mp4")
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class PostProcessResult:
    """Result of a post-processing operation."""
    output_path: str
    operation: str
    file_size_mb: float
    success: bool
    error: Optional[str] = None


COLOR_GRADE_PRESETS = {
    "warm": "curves=r='0/0 0.3/0.35 0.6/0.65 1/1':g='0/0 0.5/0.5 1/1':b='0/0 0.3/0.25 0.6/0.55 1/0.9'",
    "cool": "curves=r='0/0 0.3/0.25 0.6/0.55 1/0.9':g='0/0 0.5/0.5 1/1':b='0/0 0.3/0.35 0.6/0.65 1/1'",
    "vintage": "curves=r='0/0.05 0.3/0.35 0.6/0.6 1/0.9':g='0/0.05 0.3/0.3 0.6/0.55 1/0.85':b='0/0.1 0.3/0.25 0.6/0.5 1/0.8',hue=s=0.7",
    "cinematic": "eq=contrast=1.15:brightness=0.02:saturation=0.9,curves=m='0/0 0.05/0 0.15/0.12 0.85/0.88 0.95/1 1/1'",
    "vibrant": "eq=saturation=1.4:contrast=1.1",
    "desaturated": "eq=saturation=0.5:contrast=1.05",
    "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "noir": "hue=s=0,eq=contrast=1.5:brightness=-0.05",
}


class PostProcessor:
    """
    Video post-processing engine using ffmpeg.
    All operations are non-destructive (create new output file).
    """
    
    @staticmethod
    def list_color_presets() -> dict:
        """List available color grading presets."""
        return {k: k.replace("_", " ").title() for k in COLOR_GRADE_PRESETS}
    
    def _run_ffmpeg(self, cmd: list, operation: str, output_path: str) -> PostProcessResult:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RuntimeError(result.stderr[-500:] if result.stderr else "ffmpeg failed")
            
            size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0
            logger.info(f"✅ Post-process [{operation}]: {output_path} ({size_mb:.1f}MB)")
            return PostProcessResult(output_path, operation, size_mb, True)
            
        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            logger.error(f"❌ Post-process [{operation}] failed: {e}")
            return PostProcessResult("", operation, 0, False, str(e))
    
    def upscale(
        self,
        input_path: str,
        output_path: str,
        factor: int = 2,
    ) -> PostProcessResult:
        """Run an ffmpeg command and return a structured result."""
        """
        Upscale video resolution (2x or 4x) using Lanczos interpolation.
        For AI-based upscaling, use a dedicated super-resolution model.
        """
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"scale=iw*{factor}:ih*{factor}:flags=lanczos",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ]
        return self._run_ffmpeg(cmd, f"upscale_{factor}x", output_path)
    
    def stabilize(
        self,
        input_path: str,
        output_path: str,
        shakiness: int = 5,
    ) -> PostProcessResult:
        """
        Stabilize shaky video using ffmpeg's vidstabdetect + vidstabtransform.
        Two-pass process: analyze → transform.
        """
        import tempfile
        transforms_file = tempfile.mktemp(suffix=".trf")
        
        try:
            # Pass 1: Analyze
            cmd1 = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", f"vidstabdetect=shakiness={shakiness}:result={transforms_file}",
                "-f", "null", "-",
            ]
            subprocess.run(cmd1, capture_output=True, timeout=120, check=True)
            
            # Pass 2: Transform
            cmd2 = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", f"vidstabtransform=input={transforms_file}:smoothing=10,unsharp=5:5:0.8:3:3:0.4",
                "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                output_path,
            ]
            return self._run_ffmpeg(cmd2, "stabilize", output_path)
        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            return PostProcessResult("", "stabilize", 0, False, str(e))
        finally:
            if os.path.exists(transforms_file):
                os.unlink(transforms_file)
    
    def color_grade(
        self,
        input_path: str,
        output_path: str,
        preset: str = "cinematic",
    ) -> PostProcessResult:
        """Apply a color grading preset."""
        vf = COLOR_GRADE_PRESETS.get(preset)
        if not vf:
            return PostProcessResult("", "color_grade", 0, False,
                                     f"Unknown preset: {preset}. Available: {list(COLOR_GRADE_PRESETS)}")
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            output_path,
        ]
        return self._run_ffmpeg(cmd, f"color_grade_{preset}", output_path)
    
    def slow_motion(
        self,
        input_path: str,
        output_path: str,
        factor: float = 2.0,
    ) -> PostProcessResult:
        """
        Create slow motion video.
        factor=2.0 → half speed, factor=0.5 → double speed.
        """
        pts_factor = factor  # Higher = slower
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"setpts={pts_factor}*PTS",
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            output_path,
        ]
        return self._run_ffmpeg(cmd, f"slow_motion_{factor}x", output_path)
    
    def loop(
        self,
        input_path: str,
        output_path: str,
        count: int = 3,
    ) -> PostProcessResult:
        """Create a looping video by repeating the input N times."""
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(count - 1),
            "-i", input_path,
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            output_path,
        ]
        return self._run_ffmpeg(cmd, f"loop_{count}x", output_path)
    
    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        volume: float = 0.5,
    ) -> PostProcessResult:
        """Add background audio/music to a video."""
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[1:a]volume={volume}[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            output_path,
        ]
        return self._run_ffmpeg(cmd, "add_audio", output_path)
    
    def add_watermark(
        self,
        input_path: str,
        output_path: str,
        text: str = "FitStream",
        position: str = "bottom_right",
        opacity: float = 0.4,
        font_size: int = 24,
    ) -> PostProcessResult:
        """Add a text watermark to the video."""
        positions = {
            "top_left": "x=10:y=10",
            "top_right": "x=W-tw-10:y=10",
            "bottom_left": "x=10:y=H-th-10",
            "bottom_right": "x=W-tw-10:y=H-th-10",
            "center": "x=(W-tw)/2:y=(H-th)/2",
        }
        pos = positions.get(position, positions["bottom_right"])
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"drawtext=text='{text}':fontsize={font_size}:fontcolor=white@{opacity}:{pos}",
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            output_path,
        ]
        return self._run_ffmpeg(cmd, "watermark", output_path)
    
    def trim(
        self,
        input_path: str,
        output_path: str,
        start: float = 0.0,
        duration: Optional[float] = None,
        end: Optional[float] = None,
    ) -> PostProcessResult:
        """Trim video to a specific time range."""
        cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", input_path]
        if duration:
            cmd.extend(["-t", str(duration)])
        elif end:
            cmd.extend(["-to", str(end - start)])
        cmd.extend(["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", output_path])
        
        return self._run_ffmpeg(cmd, "trim", output_path)
    
    def chain(
        self,
        input_path: str,
        output_path: str,
        operations: list,
    ) -> PostProcessResult:
        """
        Chain multiple post-processing operations.
        
        Args:
            operations: List of dicts, e.g.:
                [
                    {"op": "color_grade", "preset": "cinematic"},
                    {"op": "upscale", "factor": 2},
                    {"op": "watermark", "text": "FitStream"},
                ]
        """
        import tempfile
        
        current_input = input_path
        temp_files = []
        
        for i, op_config in enumerate(operations):
            op = op_config.pop("op", "")
            is_last = (i == len(operations) - 1)
            current_output = output_path if is_last else tempfile.mktemp(suffix=".mp4")
            
            if not is_last:
                temp_files.append(current_output)
            
            method = getattr(self, op, None)
            if method is None:
                logger.warning(f"Unknown post-processing operation: {op}")
                continue
            
            result = method(current_input, current_output, **op_config)
            if not result.success:
                # Clean up temp files
                for tf in temp_files:
                    if os.path.exists(tf):
                        os.unlink(tf)
                return result
            
            current_input = current_output
        
        # Clean up temp files
        for tf in temp_files:
            if os.path.exists(tf):
                os.unlink(tf)
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0
        return PostProcessResult(output_path, "chain", size_mb, True)
