"""Remotion video renderer — calls npx remotion render as subprocess.

Replaces MoviePy for video composition. The Python pipeline generates
images and audio (AI layer), then hands off to Remotion for assembly.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REMOTION_DIR = Path(__file__).parent.parent / "remotion"


def _ensure_remotion_installed() -> bool:
    """Check that Remotion's node_modules exist."""
    node_modules = REMOTION_DIR / "node_modules"
    if not node_modules.exists():
        logger.info("[Remotion] Installing dependencies...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"[Remotion] npm install failed: {result.stderr[:500]}")
            return False
    return True


def render_study_video(
    images: list[Path],
    audio_path: Optional[Path],
    output_path: Path,
    scene_duration: float = 25.0,
    duration_minutes: int = 120,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    enable_parallax: bool = True,
    enable_particles: bool = True,
    timer_enabled: bool = True,
    style: str = "cinematic",
) -> Path:
    """Render a study video using Remotion."""
    if not _ensure_remotion_installed():
        raise RuntimeError("Remotion not installed")

    # Convert image paths to file:// URIs for Remotion
    image_uris = [f"file:///{str(p).replace(chr(92), '/')}" for p in images if p.exists()]

    # Calculate actual duration based on images
    total_frames = len(image_uris) * int(scene_duration * fps)

    props = {
        "images": image_uris,
        "audioFile": f"file:///{str(audio_path).replace(chr(92), '/')}" if audio_path and audio_path.exists() else "",
        "sceneDuration": scene_duration,
        "style": style,
        "enableParallax": enable_parallax,
        "enableParticles": enable_particles,
        "timerEnabled": timer_enabled,
        "durationMinutes": duration_minutes,
    }

    return _render(
        composition="StudyVideo",
        props=props,
        output_path=output_path,
        frames=total_frames,
        fps=fps,
        width=width,
        height=height,
    )


def render_tech_tutorial(
    background_image: Optional[Path],
    audio_path: Optional[Path],
    output_path: Path,
    title: str = "",
    bullets: Optional[list[str]] = None,
    fps: int = 30,
    duration_seconds: int = 60,
) -> Path:
    """Render a tech tutorial video using Remotion."""
    if not _ensure_remotion_installed():
        raise RuntimeError("Remotion not installed")

    props = {
        "backgroundImage": f"file:///{str(background_image).replace(chr(92), '/')}" if background_image and background_image.exists() else "",
        "audioFile": f"file:///{str(audio_path).replace(chr(92), '/')}" if audio_path and audio_path.exists() else "",
        "title": title,
        "bullets": bullets or [],
        "subtitlesSrt": "",
    }

    return _render(
        composition="TechTutorial",
        props=props,
        output_path=output_path,
        frames=duration_seconds * fps,
        fps=fps,
        width=1080,
        height=1920,
    )


def _render(
    composition: str,
    props: dict,
    output_path: Path,
    frames: int,
    fps: int,
    width: int,
    height: int,
) -> Path:
    """Execute npx remotion render."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write props to temp file (avoids shell escaping issues)
    props_file = REMOTION_DIR / ".render-props.json"
    props_file.write_text(json.dumps(props), encoding="utf-8")

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",
        composition,
        str(output_path.absolute()),
        "--props", str(props_file.absolute()),
        "--frames", f"0-{frames - 1}",
        "--fps", str(fps),
        "--width", str(width),
        "--height", str(height),
        "--codec", "h264",
        "--crf", "18",
    ]

    logger.info(f"[Remotion] Rendering {composition} → {output_path}")
    logger.info(f"[Remotion] {frames} frames at {fps}fps = {frames/fps:.0f}s")

    result = subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR),
        capture_output=True,
        text=True,
        timeout=7200,  # 2h max
    )

    # Clean up props file
    props_file.unlink(missing_ok=True)

    if result.returncode != 0:
        logger.error(f"[Remotion] Render failed:\n{result.stderr[:1000]}")
        raise RuntimeError(f"Remotion render failed: {result.stderr[:500]}")

    if result.stdout:
        logger.info(f"[Remotion] {result.stdout[-200:]}")

    logger.info(f"[Remotion] Done: {output_path}")
    return output_path
