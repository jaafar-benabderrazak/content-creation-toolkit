"""Thumbnail generation from video frames.

Extracts the sharpest frame via OpenCV Laplacian scoring,
composites title text and channel branding via Pillow,
and outputs a YouTube-compliant 1280x720 JPEG under 2MB.
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

THUMB_WIDTH = 1280
THUMB_HEIGHT = 720
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def extract_frames(video_path: Path, count: int = 10) -> list[Path]:
    """Extract evenly-spaced frames from a video using FFmpeg."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="thumb_"))
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True,
    )
    try:
        duration = float(result.stdout.strip())
    except (ValueError, AttributeError):
        duration = 60.0

    frames = []
    for i in range(count):
        t = (duration / (count + 1)) * (i + 1)
        out = tmp_dir / f"frame_{i:03d}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(video_path),
             "-frames:v", "1", "-q:v", "2", str(out)],
            capture_output=True,
        )
        if out.exists():
            frames.append(out)
    return frames


def score_sharpness(image_path: Path) -> float:
    """Score image sharpness using Laplacian variance via OpenCV."""
    try:
        import cv2
        import numpy as np
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except ImportError:
        # Fallback: use file size as proxy for detail
        return float(image_path.stat().st_size)


def select_best_frame(video_path: Path, sample_count: int = 10) -> Optional[Path]:
    """Extract frames and return the sharpest one."""
    frames = extract_frames(video_path, sample_count)
    if not frames:
        logger.warning("[Thumbnail] No frames extracted")
        return None

    scored = [(f, score_sharpness(f)) for f in frames]
    scored.sort(key=lambda x: x[1], reverse=True)
    best = scored[0][0]
    logger.info(f"[Thumbnail] Best frame: {best.name} (score: {scored[0][1]:.1f})")
    return best


def composite_text(
    image_path: Path,
    output_path: Path,
    title: str = "",
    branding: str = "",
) -> Path:
    """Composite title text and channel branding onto the thumbnail."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(image_path).convert("RGB")
    img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    # Load font — try system fonts, fall back to default
    def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        for path in [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    if title:
        font_title = _load_font(60)
        # Draw with shadow for readability
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (THUMB_WIDTH - tw) // 2
        y = THUMB_HEIGHT // 2 - 60
        # Shadow
        draw.text((x + 3, y + 3), title, fill=(0, 0, 0, 180), font=font_title)
        # Main text
        draw.text((x, y), title, fill="white", font=font_title)

    if branding:
        font_brand = _load_font(28)
        draw.text((THUMB_WIDTH - 300, THUMB_HEIGHT - 50), branding, fill="white", font=font_brand)

    # Save as JPEG, reduce quality if over 2MB
    quality = 95
    while quality >= 50:
        img.save(output_path, "JPEG", quality=quality)
        if output_path.stat().st_size <= MAX_FILE_SIZE:
            break
        quality -= 5

    if output_path.stat().st_size > MAX_FILE_SIZE:
        logger.warning(f"[Thumbnail] File exceeds 2MB even at quality {quality}")

    logger.info(f"[Thumbnail] Saved: {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
    return output_path


def generate_thumbnail(
    video_path: Path,
    output_path: Path,
    title: str = "",
    branding: str = "",
    sample_count: int = 10,
) -> Optional[Path]:
    """Full pipeline: extract best frame → composite text → save."""
    best = select_best_frame(video_path, sample_count)
    if not best:
        return None

    return composite_text(best, output_path, title=title, branding=branding)
