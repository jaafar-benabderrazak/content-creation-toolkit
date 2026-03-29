"""Thumbnail generation from video frames.

Extracts the sharpest frame via OpenCV Laplacian scoring,
composites title text with YouTube-optimized visual effects,
and outputs a 1280x720 JPEG under 2MB.
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
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except ImportError:
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
    avatar_path: Optional[Path] = None,
) -> Path:
    """Composite title text with YouTube-optimized visual effects."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

    img = Image.open(image_path).convert("RGB")
    img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)

    # --- Step 1: Enhance base image ---
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Brightness(img).enhance(1.05)

    # --- Step 2: Bottom gradient overlay (dark → transparent) ---
    gradient = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)
    for y in range(THUMB_HEIGHT // 3, THUMB_HEIGHT):
        progress = (y - THUMB_HEIGHT // 3) / (THUMB_HEIGHT * 2 // 3)
        alpha = int(progress * 180)
        grad_draw.line([(0, y), (THUMB_WIDTH, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), gradient).convert("RGB")

    draw = ImageDraw.Draw(img)

    # --- Font loading ---
    def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",       # Impact — classic YouTube thumbnail font
            "C:/Windows/Fonts/arialbd.ttf",       # Arial Bold
            "C:/Windows/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ] if bold else [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    # --- Step 3: Title text (bottom-left, large, with glow + outline) ---
    if title:
        # Word-wrap long titles
        font_title = _load_font(72)
        words = title.upper().split()
        lines = []
        current_line = ""
        max_width = THUMB_WIDTH - 120  # 60px margin each side

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font_title)
            if bbox[2] - bbox[0] > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

        # Position: bottom-left with margin
        line_height = 80
        total_height = len(lines) * line_height
        start_y = THUMB_HEIGHT - total_height - 80  # 80px from bottom

        for i, line in enumerate(lines):
            x = 60
            y = start_y + i * line_height

            # Glow effect (blurred shadow layer)
            glow_layer = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            glow_draw.text((x, y), line, fill=(0, 0, 0, 200), font=font_title)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=6))
            img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
            draw = ImageDraw.Draw(img)  # re-create draw after composite

            # Thick outline (draw text offset in 8 directions)
            outline_color = (0, 0, 0)
            for ox, oy in [(-3,-3),(-3,0),(-3,3),(0,-3),(0,3),(3,-3),(3,0),(3,3)]:
                draw.text((x + ox, y + oy), line, fill=outline_color, font=font_title)

            # Main text — white with slight yellow tint for warmth
            draw.text((x, y), line, fill=(255, 255, 240), font=font_title)

    # --- Step 4: Branding text (top-right, subtle) ---
    if branding:
        font_brand = _load_font(24, bold=False)
        # Semi-transparent pill background
        bbox = draw.textbbox((0, 0), branding, font=font_brand)
        bw = bbox[2] - bbox[0]
        pill_x = THUMB_WIDTH - bw - 40
        pill_y = 20
        draw.rounded_rectangle(
            [pill_x - 12, pill_y - 6, pill_x + bw + 12, pill_y + 30],
            radius=15,
            fill=(0, 0, 0, 120),
        )
        draw.text((pill_x, pill_y), branding, fill=(255, 255, 255, 220), font=font_brand)

    # --- Step 5: Avatar corner logo (bottom-right) ---
    if avatar_path and avatar_path.exists():
        try:
            avatar = Image.open(avatar_path).convert("RGBA")
            logo_size = 90
            avatar = avatar.resize((logo_size, logo_size), Image.LANCZOS)
            # Circular mask with border
            mask = Image.new("L", (logo_size, logo_size), 0)
            from PIL import ImageDraw as _IDraw
            _IDraw.Draw(mask).ellipse((0, 0, logo_size, logo_size), fill=255)
            avatar.putalpha(mask)
            # White border ring
            border = Image.new("RGBA", (logo_size + 6, logo_size + 6), (0, 0, 0, 0))
            border_draw = ImageDraw.Draw(border)
            border_draw.ellipse((0, 0, logo_size + 5, logo_size + 5), fill=(255, 255, 255, 200))
            border.paste(avatar, (3, 3), avatar)
            x = THUMB_WIDTH - logo_size - 24
            y = THUMB_HEIGHT - logo_size - 24
            img = Image.alpha_composite(img.convert("RGBA"), Image.new("RGBA", img.size, (0, 0, 0, 0)))
            img.paste(border, (x, y), border)
            img = img.convert("RGB")
            logger.info(f"[Thumbnail] Avatar composited from {avatar_path.name}")
        except Exception as e:
            logger.warning(f"[Thumbnail] Avatar overlay skipped: {e}")

    # --- Step 6: Subtle vignette ---
    vignette = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0, 0, 0, 0))
    vig_draw = ImageDraw.Draw(vignette)
    for i in range(40):
        alpha = int((i / 40) * 60)
        vig_draw.rectangle(
            [i, i, THUMB_WIDTH - i, THUMB_HEIGHT - i],
            outline=(0, 0, 0, alpha),
        )
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

    # --- Save with quality optimization ---
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
    avatar_path: Optional[Path] = None,
) -> Optional[Path]:
    """Full pipeline: extract best frame -> composite text -> save."""
    best = select_best_frame(video_path, sample_count)
    if not best:
        return None

    return composite_text(best, output_path, title=title, branding=branding, avatar_path=avatar_path)
