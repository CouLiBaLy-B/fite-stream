"""
FitStream Export Pipeline
Export generated videos in multiple formats and layouts.

Supported exports:
  - MP4 (default, H.264)
  - GIF (animated, optimized)
  - WebM (VP9, web-optimized)
  - PNG sequence (individual frames)
  - Storyboard (grid of key frames as single image)
  - Social media formats (9:16 vertical, 1:1 square, with captions)
"""

import math
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from PIL import Image, ImageDraw, ImageFont


@dataclass
class ExportResult:
    """Result of an export operation."""

    output_path: str
    format: str
    file_size_mb: float
    success: bool
    error: str | None = None


class ExportPipeline:
    """
    Export generated videos in multiple formats.

    Usage:
        exporter = ExportPipeline()

        # Export as GIF
        result = exporter.to_gif("video.mp4", "output.gif", max_width=480)

        # Export as WebM
        result = exporter.to_webm("video.mp4", "output.webm")

        # Export frames as PNGs
        result = exporter.to_frames("video.mp4", "frames/")

        # Create a storyboard
        result = exporter.to_storyboard("video.mp4", "storyboard.jpg", num_frames=9)

        # Social media vertical crop
        result = exporter.to_social("video.mp4", "reel.mp4", format="9:16")
    """

    def to_gif(
        self,
        video_path: str,
        output_path: str,
        max_width: int = 480,
        fps: int = 12,
        loop: int = 0,
    ) -> ExportResult:
        """
        Convert video to optimized animated GIF.
        Uses ffmpeg's palette generation for best quality/size ratio.
        """
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # Two-pass for optimal quality: generate palette first, then apply
            palette_path = output_path + ".palette.png"

            # Pass 1: Generate palette
            cmd1 = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-vf",
                f"fps={fps},scale={max_width}:-1:flags=lanczos,palettegen=stats_mode=diff",
                palette_path,
            ]
            subprocess.run(cmd1, capture_output=True, timeout=60, check=True)

            # Pass 2: Apply palette
            cmd2 = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-i",
                palette_path,
                "-lavfi",
                f"fps={fps},scale={max_width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer",
                "-loop",
                str(loop),
                output_path,
            ]
            subprocess.run(cmd2, capture_output=True, timeout=60, check=True)

            # Clean up palette
            if os.path.exists(palette_path):
                os.unlink(palette_path)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"📦 Exported GIF: {output_path} ({size_mb:.1f}MB)")

            return ExportResult(output_path, "gif", size_mb, True)

        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            return ExportResult("", "gif", 0, False, str(e))

    def to_webm(
        self,
        video_path: str,
        output_path: str,
        quality: int = 30,
    ) -> ExportResult:
        """Convert video to WebM (VP9) for web embedding."""
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-c:v",
                "libvpx-vp9",
                "-crf",
                str(quality),
                "-b:v",
                "0",
                "-pix_fmt",
                "yuva420p",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"📦 Exported WebM: {output_path} ({size_mb:.1f}MB)")

            return ExportResult(output_path, "webm", size_mb, True)

        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            return ExportResult("", "webm", 0, False, str(e))

    def to_frames(
        self,
        video_path: str,
        output_dir: str,
        format: str = "png",
    ) -> ExportResult:
        """Extract all frames as individual images."""
        try:
            os.makedirs(output_dir, exist_ok=True)

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                os.path.join(output_dir, f"frame_%04d.{format}"),
            ]
            subprocess.run(cmd, capture_output=True, timeout=60, check=True)

            num_frames = len(list(Path(output_dir).glob(f"*.{format}")))
            logger.info(f"📦 Exported {num_frames} frames to {output_dir}")

            return ExportResult(output_dir, f"frames-{format}", 0, True)

        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            return ExportResult("", f"frames-{format}", 0, False, str(e))

    def to_storyboard(
        self,
        video_path: str,
        output_path: str,
        num_frames: int = 9,
        cols: int = 3,
        frame_width: int = 400,
        padding: int = 8,
        bg_color: tuple[int, int, int] = (20, 20, 30),
        show_timecodes: bool = True,
    ) -> ExportResult:
        """
        Create a storyboard image — a grid of key frames from the video.
        Great for sharing story previews or documentation.
        """
        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return ExportResult("", "storyboard", 0, False, "Cannot open video")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 16
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if total_frames < 1:
                cap.release()
                return ExportResult("", "storyboard", 0, False, "Empty video")

            # Calculate frame indices to sample
            indices = [int(i * (total_frames - 1) / (num_frames - 1)) for i in range(num_frames)]

            # Calculate frame size
            aspect = orig_w / orig_h if orig_h > 0 else 16 / 9
            frame_height = int(frame_width / aspect)

            rows = math.ceil(num_frames / cols)

            # Create storyboard canvas
            canvas_w = cols * frame_width + (cols + 1) * padding
            timecode_h = 24 if show_timecodes else 0
            canvas_h = rows * (frame_height + timecode_h) + (rows + 1) * padding

            canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
            draw = ImageDraw.Draw(canvas)

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except OSError:
                font = ImageFont.load_default()  # type: ignore[assignment]

            for i, frame_idx in enumerate(indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(frame_rgb)
                pil_frame = pil_frame.resize((frame_width, frame_height), Image.LANCZOS)

                row = i // cols
                col = i % cols

                x = padding + col * (frame_width + padding)
                y = padding + row * (frame_height + timecode_h + padding)

                canvas.paste(pil_frame, (x, y))

                if show_timecodes:
                    timecode = frame_idx / fps
                    tc_text = f"{int(timecode // 60):02d}:{timecode % 60:05.2f}"
                    draw.text(
                        (x + 4, y + frame_height + 2),
                        tc_text,
                        fill=(180, 180, 200),
                        font=font,
                    )

            cap.release()

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            canvas.save(output_path, "JPEG", quality=90)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"📦 Storyboard: {output_path} ({num_frames} frames, {size_mb:.1f}MB)")

            return ExportResult(output_path, "storyboard", size_mb, True)

        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            return ExportResult("", "storyboard", 0, False, str(e))

    def to_social(
        self,
        video_path: str,
        output_path: str,
        aspect: str = "9:16",
        add_watermark: bool = False,
        watermark_text: str = "Made with FitStream",
    ) -> ExportResult:
        """
        Re-format video for social media platforms.

        Aspects:
        - "9:16" — Instagram Reels, TikTok, YouTube Shorts (vertical)
        - "1:1"  — Instagram Feed (square)
        - "4:5"  — Instagram Portrait
        - "16:9" — YouTube, Twitter (landscape, default)
        """
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            aspect_filters = {
                "9:16": "crop=ih*9/16:ih,scale=1080:1920",
                "1:1": "crop=min(iw\\,ih):min(iw\\,ih),scale=1080:1080",
                "4:5": "crop=ih*4/5:ih,scale=1080:1350",
                "16:9": "crop=iw:iw*9/16,scale=1920:1080",
            }

            vf = aspect_filters.get(aspect, aspect_filters["16:9"])

            if add_watermark:
                vf += (
                    f",drawtext=text='{watermark_text}':fontsize=20:fontcolor=white@0.5:x=10:y=H-30"
                )

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"📦 Social export ({aspect}): {output_path} ({size_mb:.1f}MB)")

            return ExportResult(output_path, f"social-{aspect}", size_mb, True)

        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            return ExportResult("", f"social-{aspect}", 0, False, str(e))
