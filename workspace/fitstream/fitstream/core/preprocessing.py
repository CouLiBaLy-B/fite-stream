"""
FitStream Preprocessing Engine
Handles image/video preprocessing before generation:
  - Person detection & cropping
  - Garment segmentation (for try-on mask creation)
  - Image quality assessment
  - Auto-captioning with vision-language models
  - Aspect ratio normalization
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
from dataclasses import dataclass
from loguru import logger
from PIL import Image, ImageFilter, ImageStat
import numpy as np


@dataclass
class ImageAnalysis:
    """Result of analyzing an input image."""
    width: int
    height: int
    aspect_ratio: float
    is_portrait: bool
    brightness: float        # 0-255
    contrast: float          # 0-100+
    sharpness: float         # 0-100+
    has_face: bool
    face_area_pct: float     # 0-100
    quality_score: float     # 0-1
    issues: List[str]
    recommendations: List[str]


class PreprocessingEngine:
    """
    Image and video preprocessing for optimal generation results.
    
    This engine analyzes inputs and applies corrections to maximize
    the quality of generated videos. It works without a GPU by
    using lightweight heuristics and PIL operations.
    """
    
    # Target resolutions for different quality presets
    TARGETS = {
        "draft": (480, 320),
        "standard": (832, 480),
        "high": (832, 480),
        "hd": (1280, 720),
    }
    
    def analyze_image(self, image_path: Union[str, Path]) -> ImageAnalysis:
        """
        Analyze an input image and return quality metrics + recommendations.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        img = Image.open(path).convert("RGB")
        w, h = img.size
        aspect = w / h
        
        # Brightness analysis
        stat = ImageStat.Stat(img)
        brightness = stat.mean[0] * 0.299 + stat.mean[1] * 0.587 + stat.mean[2] * 0.114
        
        # Contrast (standard deviation of luminance)
        gray = img.convert("L")
        gray_stat = ImageStat.Stat(gray)
        contrast = gray_stat.stddev[0]
        
        # Sharpness (Laplacian variance)
        gray_np = np.array(gray, dtype=np.float64)
        laplacian = np.array([
            [0,  1, 0],
            [1, -4, 1],
            [0,  1, 0]
        ], dtype=np.float64)
        from scipy.signal import convolve2d
        try:
            lap = convolve2d(gray_np, laplacian, mode='valid')
            sharpness = lap.var()
        except ImportError:
            # Fallback without scipy
            edge_img = gray.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edge_img)
            sharpness = edge_stat.stddev[0] ** 2
        
        # Simple face detection heuristic (skin color ratio)
        img_np = np.array(img)
        r, g, b = img_np[:,:,0], img_np[:,:,1], img_np[:,:,2]
        skin_mask = (
            (r > 60) & (g > 40) & (b > 20) &
            (r > g) & (r > b) &
            (np.abs(r.astype(int) - g.astype(int)) > 15) &
            (r > 80)
        )
        skin_pct = skin_mask.sum() / skin_mask.size * 100
        has_face = skin_pct > 3  # at least 3% skin-colored pixels
        
        # Build issues and recommendations
        issues = []
        recommendations = []
        
        if w < 400 or h < 400:
            issues.append(f"Low resolution ({w}x{h})")
            recommendations.append("Use a higher resolution image (at least 800px on shortest side)")
        
        if brightness < 40:
            issues.append("Image is very dark")
            recommendations.append("Use a brighter image or increase exposure")
        elif brightness > 220:
            issues.append("Image is overexposed")
            recommendations.append("Use an image with more balanced lighting")
        
        if contrast < 20:
            issues.append("Very low contrast")
            recommendations.append("Use an image with more distinct colors and lighting")
        
        if sharpness < 100:
            issues.append("Image may be blurry")
            recommendations.append("Use a sharp, in-focus image")
        
        if not has_face and skin_pct < 1:
            issues.append("No person detected in image")
            recommendations.append("Upload a clear photo of a person (face visible preferred)")
        
        if aspect > 2.5 or aspect < 0.4:
            issues.append(f"Extreme aspect ratio ({aspect:.2f})")
            recommendations.append("Use an image closer to 16:9 or 3:4 aspect ratio")
        
        # Quality score (0-1)
        score = 1.0
        score -= len(issues) * 0.15
        score -= max(0, (100 - min(sharpness, 500)) / 500) * 0.2
        score -= max(0, abs(brightness - 128) / 128) * 0.1
        score = max(0.0, min(1.0, score))
        
        return ImageAnalysis(
            width=w,
            height=h,
            aspect_ratio=aspect,
            is_portrait=h > w,
            brightness=brightness,
            contrast=contrast,
            sharpness=min(sharpness, 1000),
            has_face=has_face,
            face_area_pct=skin_pct,
            quality_score=score,
            issues=issues,
            recommendations=recommendations,
        )
    
    def auto_crop_person(
        self,
        image_path: Union[str, Path],
        target_width: int = 832,
        target_height: int = 480,
        padding_pct: float = 0.1,
    ) -> Image.Image:
        """
        Auto-crop the image to center on the person, then resize to target.
        Uses a simple center-weighted crop since we expect person-centered photos.
        """
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        target_aspect = target_width / target_height
        current_aspect = w / h
        
        if abs(current_aspect - target_aspect) < 0.05:
            # Already close to target aspect, just resize
            return img.resize((target_width, target_height), Image.LANCZOS)
        
        if current_aspect > target_aspect:
            # Too wide — crop sides (center crop)
            new_w = int(h * target_aspect)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            # Too tall — crop top/bottom (bias slightly toward top for head)
            new_h = int(w / target_aspect)
            top = max(0, (h - new_h) // 3)  # bias toward top (head)
            img = img.crop((0, top, w, top + new_h))
        
        return img.resize((target_width, target_height), Image.LANCZOS)
    
    def prepare_garment_image(
        self,
        image_path: Union[str, Path],
        target_width: int = 832,
        target_height: int = 480,
    ) -> Image.Image:
        """
        Prepare a garment image for try-on.
        Centers the garment on a clean background.
        """
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size
        
        # Check if image has transparency (flat-lay/product image)
        if img.mode == "RGBA":
            alpha = np.array(img)[:, :, 3]
            has_transparency = (alpha < 250).sum() > (alpha.size * 0.05)
        else:
            has_transparency = False
        
        # Convert to RGB
        if has_transparency:
            # Paste on white background
            bg = Image.new("RGB", (w, h), (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        
        # Resize to target
        from fitstream.core.utils.image_utils import resize_to_target
        return resize_to_target(img, target_width, target_height, method="contain")
    
    def create_quality_report(self, analysis: ImageAnalysis) -> str:
        """Create a human-readable quality report."""
        lines = []
        
        # Score emoji
        if analysis.quality_score >= 0.8:
            score_emoji = "🟢"
            score_label = "Excellent"
        elif analysis.quality_score >= 0.6:
            score_emoji = "🟡"
            score_label = "Good"
        elif analysis.quality_score >= 0.4:
            score_emoji = "🟠"
            score_label = "Fair"
        else:
            score_emoji = "🔴"
            score_label = "Poor"
        
        lines.append(f"{score_emoji} Quality: {score_label} ({analysis.quality_score:.0%})")
        lines.append(f"   Resolution: {analysis.width}×{analysis.height} ({'portrait' if analysis.is_portrait else 'landscape'})")
        lines.append(f"   Brightness: {analysis.brightness:.0f}/255")
        lines.append(f"   Contrast: {analysis.contrast:.0f}")
        lines.append(f"   Sharpness: {analysis.sharpness:.0f}")
        lines.append(f"   Person detected: {'✅' if analysis.has_face else '❌'}")
        
        if analysis.issues:
            lines.append(f"\n   ⚠️ Issues:")
            for issue in analysis.issues:
                lines.append(f"      • {issue}")
        
        if analysis.recommendations:
            lines.append(f"\n   💡 Recommendations:")
            for rec in analysis.recommendations:
                lines.append(f"      • {rec}")
        
        return "\n".join(lines)
