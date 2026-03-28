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

_QUALITY_MAP = {
    "cinematic":     {"crf": 16, "preset": "slow"},
    "lofi-study":    {"crf": 18, "preset": "medium"},
    "tech-tutorial": {"crf": 18, "preset": "medium"},
    "preview":       {"crf": 28, "preset": "veryfast"},
}


def _resolve_quality(profile: str) -> tuple[int, str]:
    """Return (crf, x264_preset) for the given profile name."""
    q = _QUALITY_MAP.get(profile, _QUALITY_MAP["lofi-study"])
    return q["crf"], q["preset"]


def _ensure_wav(audio_path: Path) -> Path:
    """Convert audio to WAV if it is not already WAV. Returns path to WAV file.

    useWindowedAudioData in Remotion requires WAV format (HTTP Range byte-seeking).
    MP3 VBR encoding breaks byte-offset seeking, causing the hook to return null.
    """
    if audio_path.suffix.lower() == ".wav":
        return audio_path
    wav_path = audio_path.with_suffix(".wav")
    if wav_path.exists():
        return wav_path
    logger.info(f"[Remotion] Converting {audio_path.name} to WAV for audio visualization...")
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(audio_path), str(wav_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning(f"[Remotion] WAV conversion failed: {result.stderr[:200]}. Audio visualization will be disabled.")
        return audio_path  # return original; AudioVisualizer will render null (no crash)
    return wav_path


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
            shell=(sys.platform == "win32"),
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
    profile: str = "lofi-study",
    scene_durations: Optional[list[float]] = None,
    audio_visualization: bool = False,
) -> Path:
    """Render a study video using Remotion."""
    if not _ensure_remotion_installed():
        raise RuntimeError("Remotion not installed")

    # Copy images into remotion/public/ so staticFile() can serve them
    import shutil
    public_dir = REMOTION_DIR / "public" / "assets"
    public_dir.mkdir(parents=True, exist_ok=True)
    image_uris = []
    for p in images:
        if p.exists():
            dest = public_dir / p.name
            shutil.copy2(str(p), str(dest))
            image_uris.append(f"/assets/{p.name}")  # served via staticFile()

    # Calculate actual duration based on images, accounting for TransitionSeries overlap
    if scene_durations:
        # TransitionSeries overlaps transitions: each boundary subtracts transitionDuration frames
        # transitionDuration from profile map (default 15 frames for lofi-study)
        _TRANSITION_DURATION = {"cinematic": 20, "lofi-study": 15, "tech-tutorial": 12}
        td = _TRANSITION_DURATION.get(profile, 15)
        n_transitions = max(len(scene_durations) - 1, 0)
        total_frames = max(
            sum(int(d * fps) for d in scene_durations) - n_transitions * td,
            1,
        )
    else:
        total_frames = len(image_uris) * int(scene_duration * fps)

    # Handle audio visualization: convert to WAV if needed
    audio_file_uri = ""
    if audio_path and audio_path.exists():
        effective_audio = _ensure_wav(audio_path) if audio_visualization else audio_path
        audio_file_uri = f"file:///{str(effective_audio).replace(chr(92), '/')}"

    props = {
        "images": image_uris,
        "audioFile": audio_file_uri,
        "sceneDuration": scene_duration,
        "style": style,
        "enableParallax": enable_parallax,
        "enableParticles": enable_particles,
        "timerEnabled": timer_enabled,
        "durationMinutes": duration_minutes,
        "profile": profile,
        "sceneDurations": scene_durations or [],
    }

    return _render(
        composition="StudyVideo",
        props=props,
        output_path=output_path,
        frames=total_frames,
        fps=fps,
        width=width,
        height=height,
        profile=profile,
    )


def render_tech_tutorial(
    background_image: Optional[Path],
    audio_path: Optional[Path],
    output_path: Path,
    title: str = "",
    bullets: Optional[list[str]] = None,
    fps: int = 30,
    duration_seconds: int = 60,
    profile: str = "tech-tutorial",
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
        "profile": profile,
    }

    return _render(
        composition="TechTutorial",
        props=props,
        output_path=output_path,
        frames=duration_seconds * fps,
        fps=fps,
        width=1080,
        height=1920,
        profile=profile,
    )


def _render(
    composition: str,
    props: dict,
    output_path: Path,
    frames: int,
    fps: int,
    width: int,
    height: int,
    profile: str = "lofi-study",
) -> Path:
    """Execute npx remotion render."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    crf, x264_preset = _resolve_quality(profile)

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
        "--crf", str(crf),
        "--x264-preset", x264_preset,
        "--color-space", "bt709",
        "--audio-codec", "aac",
        "--audio-bitrate", "320k",
    ]

    logger.info(f"[Remotion] Rendering {composition} → {output_path}")
    logger.info(f"[Remotion] {frames} frames at {fps}fps = {frames/fps:.0f}s")

    result = subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR),
        capture_output=True,
        text=True,
        timeout=7200,  # 2h max
        shell=(sys.platform == "win32"),  # npx.cmd needs shell on Windows
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
