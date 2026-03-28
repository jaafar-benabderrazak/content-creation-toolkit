"""Post-processing pipeline for video content.

Applies watermark, subtitle burn-in, and intro/outro concatenation
via FFmpeg subprocess calls. Each step is independently toggleable
via PipelineConfig.post settings.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)


def _ffmpeg_available() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _run_ffmpeg(args: list[str], description: str) -> None:
    cmd = ["ffmpeg", "-y"] + args
    logger.info(f"[PostProcess] {description}")
    logger.debug(f"[PostProcess] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed during '{description}': {result.stderr[:500]}"
        )


def apply_watermark(video_path: Path, output_path: Path, text: str, position: str) -> Path:
    """Burn a text watermark onto the video."""
    pos_map = {
        "top-left": "x=20:y=20",
        "top-right": "x=w-tw-20:y=20",
        "bottom-left": "x=20:y=h-th-20",
        "bottom-right": "x=w-tw-20:y=h-th-20",
        "center": "x=(w-tw)/2:y=(h-th)/2",
    }
    xy = pos_map.get(position, pos_map["bottom-right"])
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")
    drawtext = (
        f"drawtext=text='{escaped_text}':"
        f"fontsize=24:fontcolor=white@0.5:{xy}"
    )
    _run_ffmpeg(
        ["-i", str(video_path), "-vf", drawtext, "-codec:a", "copy", str(output_path)],
        f"Watermark: '{text}' at {position}",
    )
    return output_path


def burn_subtitles(video_path: Path, output_path: Path, srt_path: Path) -> Path:
    """Burn SRT subtitles into the video."""
    if not srt_path.exists():
        raise FileNotFoundError(f"SRT file not found: {srt_path}")
    srt_str = str(srt_path).replace("\\", "/").replace(":", "\\:")
    _run_ffmpeg(
        ["-i", str(video_path), "-vf", f"subtitles='{srt_str}'", "-codec:a", "copy", str(output_path)],
        f"Subtitle burn-in from {srt_path.name}",
    )
    return output_path


def concat_intro_outro(
    video_path: Path,
    output_path: Path,
    intro_path: Optional[Path] = None,
    outro_path: Optional[Path] = None,
) -> Path:
    """Concatenate intro and/or outro clips to the main video."""
    parts = []
    if intro_path and intro_path.exists():
        parts.append(intro_path)
    parts.append(video_path)
    if outro_path and outro_path.exists():
        parts.append(outro_path)

    if len(parts) == 1:
        shutil.copy2(video_path, output_path)
        return output_path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in parts:
            f.write(f"file '{str(p).replace(chr(92), '/')}'\n")
        list_path = f.name

    try:
        _run_ffmpeg(
            ["-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", str(output_path)],
            "Concat intro/outro",
        )
    finally:
        Path(list_path).unlink(missing_ok=True)

    return output_path


def run_post_process(video_path: Path, config: PipelineConfig) -> Path:
    """Run the full post-processing pipeline based on config settings.

    Returns the path to the final processed video.
    """
    if not _ffmpeg_available():
        logger.warning("[PostProcess] FFmpeg not found — skipping post-processing")
        return video_path

    post = config.post
    current = video_path
    work_dir = video_path.parent
    step = 0

    # Step 1: Watermark
    if post.watermark_enabled and post.watermark_text:
        step += 1
        out = work_dir / f"_pp_step{step}_watermark{video_path.suffix}"
        current = apply_watermark(current, out, post.watermark_text, post.watermark_position)

    # Step 2: Subtitles
    if post.subtitles_enabled:
        srt = Path(post.subtitles_srt_path) if post.subtitles_srt_path else video_path.with_suffix(".srt")
        if srt.exists():
            step += 1
            out = work_dir / f"_pp_step{step}_subtitles{video_path.suffix}"
            current = burn_subtitles(current, out, srt)
        else:
            logger.warning(f"[PostProcess] Subtitles enabled but SRT not found: {srt}")

    # Step 3: Intro/Outro
    intro = Path(post.intro_clip_path) if post.intro_enabled and post.intro_clip_path else None
    outro = Path(post.outro_clip_path) if post.outro_enabled and post.outro_clip_path else None
    if intro or outro:
        step += 1
        out = work_dir / f"_pp_step{step}_concat{video_path.suffix}"
        current = concat_intro_outro(current, out, intro, outro)

    # If we did any processing, rename final output
    if current != video_path:
        final = work_dir / f"{video_path.stem}_processed{video_path.suffix}"
        shutil.move(str(current), str(final))
        # Clean up intermediate files
        for f in work_dir.glob("_pp_step*"):
            if f != final:
                f.unlink(missing_ok=True)
        logger.info(f"[PostProcess] Done: {final}")
        return final

    logger.info("[PostProcess] No post-processing steps enabled")
    return video_path
