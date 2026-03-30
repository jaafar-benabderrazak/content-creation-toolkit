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


def enhance_thumbnail_image(
    image_path: Path,
    prompt: str = "",
    output_path: Optional[Path] = None,
    style_ref_paths: Optional[list] = None,
) -> Path:
    """Transform the best frame into a thumbnail-optimized image via img2img.

    Uses Replicate (Seedream 5 img2img) or local Pillow enhancement as fallback.
    The goal: make the frame more dramatic, vibrant, and eye-catching.

    Parameters
    ----------
    image_path : Path
        Source frame to enhance.
    prompt : str
        Enhancement prompt.
    output_path : Path, optional
        Where to save the result.
    style_ref_paths : list, optional
        Paths to style reference images injected into Seedream 5 image_input
        for aesthetic conditioning. Capped at 4 images to limit payload size.
    """
    import os
    from PIL import Image, ImageEnhance, ImageFilter

    out = output_path or image_path.with_name(f"{image_path.stem}_enhanced.jpg")

    import requests as req
    import io
    import base64

    img_bytes = image_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode()
    enhance_prompt = f"youtube thumbnail style, vibrant, dramatic lighting, cinematic, {prompt}"
    neg_prompt = "blurry, low quality, text, watermark, ugly, deformed"

    # --- Try 1: Seedream 5 img2img via Replicate ---
    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if replicate_token and prompt:
        try:
            import replicate
            os.environ["REPLICATE_API_TOKEN"] = replicate_token
            data_uri = f"data:image/jpeg;base64,{b64}"

            inp = {
                "image": data_uri,
                "prompt": enhance_prompt,
                "aspect_ratio": "16:9",
                "output_format": "png",
                "num_outputs": 1,
            }

            if style_ref_paths:
                from generators.image_gen import _style_ref_to_data_uris
                ref_uris = _style_ref_to_data_uris(style_ref_paths, max_refs=4)
                if ref_uris:
                    inp["image_input"] = ref_uris
                    logger.info(f"[Thumbnail] Style ref: {len(ref_uris)} images injected into Seedream")

            logger.info(f"[Thumbnail] img2img via Seedream 5 (Replicate)...")
            result = replicate.run("bytedance/seedream-5-lite", input=inp)
            url = result[0] if isinstance(result, list) else result
            img_data = req.get(str(url)).content
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)
            img.save(str(out), "JPEG", quality=95)
            logger.info("[Thumbnail] Enhanced via Seedream 5 img2img")
            return out
        except Exception as e:
            logger.warning(f"[Thumbnail] Seedream failed ({e}), trying next...")

    # --- Try 2: Google Imagen via Gemini API ---
    google_key = os.environ.get("GOOGLE_API_KEY")
    if google_key and prompt:
        try:
            logger.info("[Thumbnail] img2img via Imagen (Google)...")
            resp = req.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict",
                headers={"Content-Type": "application/json"},
                params={"key": google_key},
                json={
                    "instances": [{
                        "prompt": enhance_prompt,
                        "image": {"bytesBase64Encoded": b64},
                    }],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "16:9",
                        "guidanceScale": 60,
                    },
                },
                timeout=30,
            )
            if resp.ok:
                data = resp.json()
                img_b64 = data["predictions"][0]["bytesBase64Encoded"]
                img = Image.open(io.BytesIO(base64.b64decode(img_b64))).convert("RGB")
                img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)
                img.save(str(out), "JPEG", quality=95)
                logger.info("[Thumbnail] Enhanced via Google Imagen")
                return out
            else:
                logger.warning(f"[Thumbnail] Imagen failed: {resp.status_code}")
        except Exception as e:
            logger.warning(f"[Thumbnail] Imagen failed ({e}), trying next...")

    # --- Try 3: SDXL img2img via Replicate ---
    if replicate_token and prompt:
        try:
            import replicate
            data_uri = f"data:image/jpeg;base64,{b64}"

            logger.info("[Thumbnail] img2img via SDXL (Replicate)...")
            result = replicate.run(
                "stability-ai/sdxl",
                input={
                    "image": data_uri,
                    "prompt": enhance_prompt,
                    "negative_prompt": neg_prompt,
                    "prompt_strength": 0.35,
                    "num_inference_steps": 25,
                    "width": 1280,
                    "height": 720,
                },
            )
            url = result[0] if isinstance(result, list) else result
            img_data = req.get(str(url)).content
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            img.save(str(out), "JPEG", quality=95)
            logger.info("[Thumbnail] Enhanced via SDXL img2img")
            return out
        except Exception as e:
            logger.warning(f"[Thumbnail] SDXL img2img failed ({e}), using local enhancement")

    # Fallback: aggressive local Pillow enhancement
    img = Image.open(image_path).convert("RGB")
    img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)

    # Dramatic enhancement for thumbnail pop
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = ImageEnhance.Color(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img = ImageEnhance.Brightness(img).enhance(1.08)

    img.save(str(out), "JPEG", quality=95)
    logger.info(f"[Thumbnail] Enhanced locally (contrast+color+sharpness boost)")
    return out


def _claude_optimize_text(
    image_path: Path,
    title: str,
    thumbnail_prompt: str = "",
    positive_prompt: str = "",
    youtube_title: str = "",
) -> dict:
    """Use Claude Vision to analyze the thumbnail image and design the optimal text overlay.

    Context inputs:
    - image_path: the enhanced thumbnail frame (what Claude sees)
    - title: the generated thumbnail_text (e.g., "UNDERGROUND CYBER VIBES")
    - thumbnail_prompt: the img2img prompt used to enhance this frame
    - positive_prompt: the SDXL prompt that generated the original scene
    - youtube_title: the video's YouTube title for thematic coherence

    Returns dict with: text, position, font_size, text_color, outline_color,
    glow_color, lines, emphasis_word.
    """
    try:
        import anthropic
        import base64

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {}

        img_bytes = image_path.read_bytes()
        b64 = base64.b64encode(img_bytes).decode()
        media_type = "image/jpeg" if str(image_path).lower().endswith(".jpg") else "image/png"

        # Build rich context from all available prompts
        context_parts = []
        if thumbnail_prompt:
            context_parts.append(f"Image enhancement prompt: \"{thumbnail_prompt}\"")
        if positive_prompt:
            context_parts.append(f"Original scene prompt: \"{positive_prompt[:200]}\"")
        if youtube_title:
            context_parts.append(f"YouTube title: \"{youtube_title}\"")
        context_block = "\n".join(context_parts) if context_parts else "(no additional context)"

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=(
                "You are a YouTube thumbnail text designer who creates scroll-stopping overlays. "
                "You understand color theory, visual hierarchy, typography psychology, and YouTube CTR optimization. "
                "You analyze the actual image content to make data-driven placement decisions."
            ),
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Design the text overlay for this YouTube thumbnail.\n\n"
                            f"Suggested text: \"{title}\"\n"
                            f"Context:\n{context_block}\n\n"
                            "ANALYZE the image carefully, then return JSON:\n\n"
                            "- text: final overlay text (2-5 words, ALL CAPS). "
                            "Refine the suggestion — make it punchier, more curiosity-driving. "
                            "Use power words: SECRET, HIDDEN, ULTIMATE, DARK, PERFECT, MIDNIGHT, GOLDEN, LOST. "
                            "The text should complement the image mood, not just describe it.\n\n"
                            "- position: where to place text (bottom-left | bottom-center | top-left | center). "
                            "LOOK at the image — find the area with least visual detail or darkest region. "
                            "Never place text over a face, bright light source, or key focal point.\n\n"
                            "- font_size: pixels (60-90). Larger if 2 words, smaller if 4+ words. "
                            "Must be readable at YouTube's 320x180 preview size.\n\n"
                            "- text_color: hex color that POPS against this specific image. "
                            "Analyze dominant colors — pick a complementary or high-contrast accent. "
                            "Warm images → cool text (#E0F0FF). Cool images → warm text (#FFE066). "
                            "Dark images → bright white (#FFFFFF). Bright images → deep color (#1a1a2e).\n\n"
                            "- outline_color: hex for thick outline. Usually very dark (#000000, #0a0a0a). "
                            "Match the image's shadow tone if visible.\n\n"
                            "- glow_color: hex for the blur glow behind text. "
                            "Use a muted version of the image's dominant accent color for cohesion.\n\n"
                            "- lines: array of 1-2 strings — split the text for visual balance. "
                            "If 4+ words, split into 2 lines. Line 1 should have the hook word.\n\n"
                            "- emphasis_word: which single word should be slightly larger or different color "
                            "for visual hierarchy (the most important/curiosity word).\n\n"
                            "Return JSON only."
                        ),
                    },
                ],
            }],
        )

        import json
        import re
        text = response.content[0].text
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
        result = json.loads(text)
        logger.info(
            f"[Thumbnail] Claude design: \"{result.get('text', '?')}\" "
            f"at {result.get('position', '?')} "
            f"color={result.get('text_color', '?')} "
            f"emphasis={result.get('emphasis_word', '?')}"
        )
        return result
    except Exception as e:
        logger.warning(f"[Thumbnail] Claude text optimization failed: {e}")
        return {}


def composite_text(
    image_path: Path,
    output_path: Path,
    title: str = "",
    branding: str = "",
    avatar_path: Optional[Path] = None,
    thumbnail_prompt: str = "",
    positive_prompt: str = "",
    youtube_title: str = "",
) -> Path:
    """Composite title text with YouTube-optimized visual effects.

    Uses Claude Vision to analyze the image + generation prompts and design
    the optimal text overlay (position, color, size, emphasis).
    Falls back to default positioning if Claude is unavailable.
    """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

    img = Image.open(image_path).convert("RGB")
    img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)

    # --- Step 0: Ask Claude for optimal text placement ---
    claude_opts = _claude_optimize_text(
        image_path, title,
        thumbnail_prompt=thumbnail_prompt,
        positive_prompt=positive_prompt,
        youtube_title=youtube_title,
    ) if title else {}

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

    # --- Step 3: Title text with Claude-optimized placement ---
    if title:
        # Use Claude recommendations or defaults
        final_text = claude_opts.get("text", title).upper()
        font_size = claude_opts.get("font_size", 72)
        position = claude_opts.get("position", "bottom-left")
        text_color_hex = claude_opts.get("text_color", "#FFFFF0")
        outline_color_hex = claude_opts.get("outline_color", "#000000")
        glow_color_hex = claude_opts.get("glow_color", outline_color_hex)
        emphasis_word = claude_opts.get("emphasis_word", "").upper()
        text_lines = claude_opts.get("lines", None)

        # Parse hex colors
        def _hex_to_rgb(h: str) -> tuple:
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        try:
            text_color = _hex_to_rgb(text_color_hex)
            outline_color = _hex_to_rgb(outline_color_hex)
            glow_color = _hex_to_rgb(glow_color_hex)
        except (ValueError, IndexError):
            text_color = (255, 255, 240)
            outline_color = (0, 0, 0)
            glow_color = (0, 0, 0)

        font_title = _load_font(int(font_size))

        # Word-wrap: use Claude's lines or auto-wrap
        if text_lines and isinstance(text_lines, list):
            lines = [l.upper() for l in text_lines]
        else:
            words = final_text.split()
            lines = []
            current_line = ""
            max_width = THUMB_WIDTH - 120

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

        # Position based on Claude recommendation
        line_height = int(font_size) + 10
        total_height = len(lines) * line_height

        if position == "top-left":
            start_y = 60
            x_base = 60
        elif position == "center":
            start_y = (THUMB_HEIGHT - total_height) // 2
            x_base = None  # center each line
        elif position == "bottom-center":
            start_y = THUMB_HEIGHT - total_height - 80
            x_base = None
        else:  # bottom-left (default)
            start_y = THUMB_HEIGHT - total_height - 80
            x_base = 60

        for i, line in enumerate(lines):
            if x_base is None:
                # Center the line
                bbox = draw.textbbox((0, 0), line, font=font_title)
                tw = bbox[2] - bbox[0]
                x = (THUMB_WIDTH - tw) // 2
            else:
                x = x_base
            y = start_y + i * line_height

            # Glow effect with Claude-chosen glow color
            glow_layer = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            glow_draw.text((x, y), line, fill=(*glow_color, 200), font=font_title)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
            img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Thick outline (8 directions)
            for ox, oy in [(-3,-3),(-3,0),(-3,3),(0,-3),(0,3),(3,-3),(3,0),(3,3)]:
                draw.text((x + ox, y + oy), line, fill=outline_color, font=font_title)

            # Main text — emphasis word gets slightly different treatment
            if emphasis_word and emphasis_word in line:
                # Render word by word, emphasis word gets accent color
                words_in_line = line.split()
                curr_x = x
                for word in words_in_line:
                    word_text = word + " "
                    if word == emphasis_word:
                        # Emphasis: slightly larger or accent color
                        accent = tuple(min(c + 40, 255) for c in text_color)
                        draw.text((curr_x, y), word_text, fill=accent, font=font_title)
                    else:
                        draw.text((curr_x, y), word_text, fill=text_color, font=font_title)
                    bbox = draw.textbbox((0, 0), word_text, font=font_title)
                    curr_x += bbox[2] - bbox[0]
            else:
                draw.text((x, y), line, fill=text_color, font=font_title)

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
    enhance_prompt: str = "",
    thumbnail_prompt: str = "",
    positive_prompt: str = "",
    youtube_title: str = "",
    style_ref_paths: Optional[list] = None,
) -> Optional[Path]:
    """Full pipeline: extract best frame → img2img enhance → Claude text design → save.

    Parameters
    ----------
    title : str
        Text overlay (from thumbnail_text). Claude may refine it.
    enhance_prompt : str
        Legacy prompt for img2img. Overridden by thumbnail_prompt if set.
    thumbnail_prompt : str
        Dedicated img2img prompt from prompt generator. Also sent to Claude
        for context-aware text design.
    positive_prompt : str
        SDXL positive prompt (scene context for Claude).
    youtube_title : str
        YouTube title (thematic coherence for Claude).
    style_ref_paths : list, optional
        Style reference images for Seedream 5 conditioning.
    """
    best = select_best_frame(video_path, sample_count)
    if not best:
        return None

    # Step 1: Enhance the frame
    enhanced = enhance_thumbnail_image(
        best,
        prompt=thumbnail_prompt or enhance_prompt,
        output_path=best.with_name(f"{best.stem}_enhanced.jpg"),
        style_ref_paths=style_ref_paths,
    )

    # Step 2: Claude-designed text overlay
    return composite_text(
        enhanced, output_path,
        title=title, branding=branding, avatar_path=avatar_path,
        thumbnail_prompt=thumbnail_prompt,
        positive_prompt=positive_prompt,
        youtube_title=youtube_title,
    )
