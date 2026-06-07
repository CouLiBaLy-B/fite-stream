"""
Image utilities for FitStream.
Handles loading, resizing, and preprocessing images for video generation.
"""

from pathlib import Path

from loguru import logger
from PIL import Image


def load_and_prepare_image(
    image_path: str | Path,
    target_width: int = 832,
    target_height: int = 480,
) -> Image.Image:
    """
    Load an image and prepare it for video generation.
    Resizes while maintaining aspect ratio and padding if necessary.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    img = Image.open(path).convert("RGB")
    logger.debug(f"Loaded image: {path.name} ({img.size[0]}x{img.size[1]})")

    img = resize_to_target(img, target_width, target_height)
    return img


def resize_to_target(
    img: Image.Image, target_width: int, target_height: int, method: str = "contain"
) -> Image.Image:
    """
    Resize image to target dimensions.

    Methods:
    - "contain": Fit inside target, add padding (preserves full image)
    - "cover": Fill target, crop excess (may lose edges)
    - "stretch": Stretch to exact size (may distort)
    """
    orig_w, orig_h = img.size

    if method == "contain":
        # Calculate scale to fit inside target
        scale = min(target_width / orig_w, target_height / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # Resize
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

        # Pad to exact target size
        result = Image.new("RGB", (target_width, target_height), (0, 0, 0))
        paste_x = (target_width - new_w) // 2
        paste_y = (target_height - new_h) // 2
        result.paste(img_resized, (paste_x, paste_y))
        return result

    elif method == "cover":
        # Calculate scale to cover target
        scale = max(target_width / orig_w, target_height / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        crop_x = (new_w - target_width) // 2
        crop_y = (new_h - target_height) // 2
        return img_resized.crop((crop_x, crop_y, crop_x + target_width, crop_y + target_height))

    else:  # stretch
        return img.resize((target_width, target_height), Image.LANCZOS)


def create_image_grid(images: list, cols: int = 4) -> Image.Image:
    if not images:
        return Image.new("RGB", (100, 100), (0, 0, 0))

    n = len(images)
    rows = (n + cols - 1) // cols

    # Get max dimensions
    max_w = max(img.size[0] for img in images)
    max_h = max(img.size[1] for img in images)

    grid = Image.new("RGB", (cols * max_w, rows * max_h), (30, 30, 30))

    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        # Center each image in its cell
        x = col * max_w + (max_w - img.size[0]) // 2
        y = row * max_h + (max_h - img.size[1]) // 2
        grid.paste(img, (x, y))

    return grid
