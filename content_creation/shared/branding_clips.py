"""Intro and outro MP4 clip generation from BrandingData using FFmpeg lavfi compositing.

Generates programmatic intro/outro clips from cached channel avatar, name, and tagline.
No pip dependencies beyond stdlib — uses only FFmpeg subprocess.

Public API:
    generate_intro_clip(branding, output_path, duration) -> Path
    generate_outro_clip(branding, output_path, duration) -> Path
    generate_branding_clips(branding, cache_dir) -> tuple[Path, Path]
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------

def _run_ffmpeg(args: list[str], description: str) -> None:
    import subprocess
    cmd = ["ffmpeg", "-y"] + args
    logger.info(f"[BrandingClip] {description}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed during '{description}': {result.stderr[:500]}")


def _escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")


def _find_font() -> str:
    """Return the path to a usable bold font, or empty string to use FFmpeg default."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_intro_clip(
    branding,
    output_path: Path,
    duration: float = 3.0,
) -> Path:
    """Generate a 1920x1080 intro MP4 clip from BrandingData.

    Produces a black-background clip with:
    - Channel name centered (fontsize 72, white)
    - Tagline below channel name (fontsize 36, gray)
    - Avatar overlaid centered-top if branding.avatar_local_path exists
    - Fade-in over first 1 second

    Args:
        branding: BrandingData instance (channel_name, tagline, avatar_local_path).
        output_path: Destination path for the generated MP4.
        duration: Clip length in seconds (default 3.0).

    Returns:
        output_path after successful generation.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    font = _find_font()
    fontfile_part = f"fontfile='{font}':" if font else ""

    name = _escape_drawtext(branding.channel_name)
    tagline = _escape_drawtext(branding.tagline)

    # 30 fps — fade-in: first 30 frames (1 second)
    fade_filter = "fade=in:0:30"

    has_avatar = bool(
        getattr(branding, "avatar_local_path", None)
        and Path(branding.avatar_local_path).exists()
    )

    if not has_avatar:
        vf = (
            f"drawtext={fontfile_part}text='{name}':fontsize=72:fontcolor=white"
            f":x=(w-tw)/2:y=(h-th)/2+40,"
            f"drawtext={fontfile_part}text='{tagline}':fontsize=36:fontcolor=#aaaaaa"
            f":x=(w-tw)/2:y=(h-th)/2+130,"
            f"{fade_filter}"
        )
        args = [
            "-f", "lavfi",
            "-i", f"color=black:s=1920x1080:d={duration}:r=30",
            "-vf", vf,
            "-an",
            str(output_path),
        ]
        _run_ffmpeg(args, f"intro clip (no avatar) -> {output_path.name}")
    else:
        avatar_path = branding.avatar_local_path
        filter_complex = (
            f"[1:v]scale=160:160[logo];"
            f"[0:v][logo]overlay=x=(W-160)/2:y=80,"
            f"drawtext={fontfile_part}text='{name}':fontsize=72:fontcolor=white"
            f":x=(w-tw)/2:y=(h-th)/2+40,"
            f"drawtext={fontfile_part}text='{tagline}':fontsize=36:fontcolor=#aaaaaa"
            f":x=(w-tw)/2:y=(h-th)/2+130,"
            f"{fade_filter}[v]"
        )
        args = [
            "-f", "lavfi",
            "-i", f"color=black:s=1920x1080:d={duration}:r=30",
            "-i", str(avatar_path),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-an",
            str(output_path),
        ]
        _run_ffmpeg(args, f"intro clip (with avatar) -> {output_path.name}")

    return output_path


def generate_outro_clip(
    branding,
    output_path: Path,
    duration: float = 4.0,
) -> Path:
    """Generate a 1920x1080 outro MP4 clip from BrandingData.

    Same layout as intro but with fade-out over the last 1 second.
    Tagline defaults to "Thanks for watching!" when branding.tagline is empty
    or identical to channel_name.

    Args:
        branding: BrandingData instance.
        output_path: Destination path for the generated MP4.
        duration: Clip length in seconds (default 4.0).

    Returns:
        output_path after successful generation.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    font = _find_font()
    fontfile_part = f"fontfile='{font}':" if font else ""

    name = _escape_drawtext(branding.channel_name)

    # Tagline: use "Thanks for watching!" if empty or same as channel name
    raw_tagline = getattr(branding, "tagline", "") or ""
    if not raw_tagline or raw_tagline.strip() == branding.channel_name.strip():
        raw_tagline = "Thanks for watching!"
    tagline = _escape_drawtext(raw_tagline)

    # 30 fps — fade-out: start at (duration - 1) seconds, 30 frames
    fade_start = int((duration - 1) * 30)
    fade_filter = f"fade=out:st={duration - 1}:d=1"

    has_avatar = bool(
        getattr(branding, "avatar_local_path", None)
        and Path(branding.avatar_local_path).exists()
    )

    if not has_avatar:
        vf = (
            f"drawtext={fontfile_part}text='{name}':fontsize=72:fontcolor=white"
            f":x=(w-tw)/2:y=(h-th)/2+40,"
            f"drawtext={fontfile_part}text='{tagline}':fontsize=36:fontcolor=#aaaaaa"
            f":x=(w-tw)/2:y=(h-th)/2+130,"
            f"{fade_filter}"
        )
        args = [
            "-f", "lavfi",
            "-i", f"color=black:s=1920x1080:d={duration}:r=30",
            "-vf", vf,
            "-an",
            str(output_path),
        ]
        _run_ffmpeg(args, f"outro clip (no avatar) -> {output_path.name}")
    else:
        avatar_path = branding.avatar_local_path
        filter_complex = (
            f"[1:v]scale=160:160[logo];"
            f"[0:v][logo]overlay=x=(W-160)/2:y=80,"
            f"drawtext={fontfile_part}text='{name}':fontsize=72:fontcolor=white"
            f":x=(w-tw)/2:y=(h-th)/2+40,"
            f"drawtext={fontfile_part}text='{tagline}':fontsize=36:fontcolor=#aaaaaa"
            f":x=(w-tw)/2:y=(h-th)/2+130,"
            f"{fade_filter}[v]"
        )
        args = [
            "-f", "lavfi",
            "-i", f"color=black:s=1920x1080:d={duration}:r=30",
            "-i", str(avatar_path),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-an",
            str(output_path),
        ]
        _run_ffmpeg(args, f"outro clip (with avatar) -> {output_path.name}")

    return output_path


def generate_branding_clips(branding, cache_dir: Path) -> tuple[Path, Path]:
    """Generate both intro and outro clips, writing to cache_dir.

    Only generates files that do not already exist. Callers control
    when to regenerate (e.g., after a branding refresh).

    Args:
        branding: BrandingData instance.
        cache_dir: Directory for output files (created if absent).

    Returns:
        (intro_path, outro_path) tuple of generated clip paths.
    """
    cache_dir = Path(cache_dir)
    intro_path = cache_dir / "intro.mp4"
    outro_path = cache_dir / "outro.mp4"

    if not intro_path.exists():
        generate_intro_clip(branding, intro_path)
    else:
        logger.info(f"[BrandingClip] intro.mp4 already exists, skipping")

    if not outro_path.exists():
        generate_outro_clip(branding, outro_path)
    else:
        logger.info(f"[BrandingClip] outro.mp4 already exists, skipping")

    return (intro_path, outro_path)
