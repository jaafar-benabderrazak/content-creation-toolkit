"""Approval loops — Discord preview + CLI validation with regeneration cycles.

Sends previews to Discord, waits for CLI approval, regenerates on rejection.
Covers: image approval, video/thumbnail approval, final publish approval.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)

MAX_REGENERATION_ATTEMPTS = 5


def _send_discord_image(
    webhook_url: str,
    image_path: Path,
    title: str,
    description: str,
) -> bool:
    """Send an image preview to Discord with embed."""
    try:
        from discord_webhook import DiscordWebhook, DiscordEmbed

        webhook = DiscordWebhook(url=webhook_url)
        embed = DiscordEmbed(title=title, description=description, color=0x3498DB)
        webhook.add_embed(embed)

        if image_path.exists():
            with open(image_path, "rb") as f:
                webhook.add_file(file=f.read(), filename=image_path.name)

        webhook.execute()
        return True
    except Exception as e:
        logger.warning(f"[Approval] Discord send failed: {e}")
        return False


def _send_discord_video_snippet(
    webhook_url: str,
    video_path: Path,
    thumbnail_path: Optional[Path],
    title: str,
    description: str,
) -> bool:
    """Send a video snippet + thumbnail to Discord."""
    try:
        from discord_webhook import DiscordWebhook, DiscordEmbed

        webhook = DiscordWebhook(url=webhook_url)
        embed = DiscordEmbed(title=title, description=description, color=0x2ECC71)

        # Extract a 15s snippet for preview
        snippet_path = video_path.parent / f"{video_path.stem}_snippet.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-t", "15",
             "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
             "-c:a", "aac", "-b:a", "128k", str(snippet_path)],
            capture_output=True, timeout=60,
        )

        webhook.add_embed(embed)

        if thumbnail_path and thumbnail_path.exists():
            with open(thumbnail_path, "rb") as f:
                webhook.add_file(file=f.read(), filename="thumbnail.jpg")

        if snippet_path.exists() and snippet_path.stat().st_size < 25 * 1024 * 1024:
            with open(snippet_path, "rb") as f:
                webhook.add_file(file=f.read(), filename="preview.mp4")

        webhook.execute()

        snippet_path.unlink(missing_ok=True)
        return True
    except Exception as e:
        logger.warning(f"[Approval] Discord video send failed: {e}")
        return False


def _get_discord_url(config: PipelineConfig) -> Optional[str]:
    import os
    return (
        config.notify.discord_webhook_url
        or os.environ.get("NOTF_DISCORD_WEBHOOK_URL")
    )


def _cli_approve(prompt_text: str) -> str:
    """Ask user for approval via CLI. Returns 'approve', 'reject', or 'skip'."""
    print(f"\n{'='*60}")
    print(prompt_text)
    print(f"{'='*60}")
    print("  [Enter]  = Approve")
    print("  r        = Reject (regenerate)")
    print("  s        = Skip validation")
    print(f"{'='*60}")

    try:
        response = input("> ").strip().lower()
        if response in ("r", "reject", "no", "n"):
            return "reject"
        if response in ("s", "skip"):
            return "skip"
        return "approve"
    except (EOFError, KeyboardInterrupt):
        return "approve"


# ---------------------------------------------------------------------------
# Image Approval Loop
# ---------------------------------------------------------------------------

def approve_images(
    image_paths: List[Path],
    config: PipelineConfig,
    regenerate_fn: Callable[[], List[Path]],
) -> List[Path]:
    """Send generated images to Discord for preview, approve or regenerate.

    Parameters
    ----------
    image_paths : list[Path]
        Current generated image paths.
    config : PipelineConfig
        Pipeline config (for Discord webhook URL).
    regenerate_fn : callable
        Function that regenerates images and returns new paths.

    Returns
    -------
    list[Path]
        Approved image paths.
    """
    discord_url = _get_discord_url(config)

    for attempt in range(1, MAX_REGENERATION_ATTEMPTS + 1):
        # Send preview to Discord
        if discord_url and image_paths:
            base_image = image_paths[0]  # Send the base/first image
            _send_discord_image(
                discord_url,
                base_image,
                title=f"Image Preview (attempt {attempt}/{MAX_REGENERATION_ATTEMPTS})",
                description=(
                    f"Profile: **{config.profile}**\n"
                    f"Scenes: **{len(image_paths)}** variants from 1 base image\n"
                    f"React in Discord, then approve/reject in terminal."
                ),
            )
            logger.info(f"[Approval] Image preview sent to Discord (attempt {attempt})")

        # CLI approval
        decision = _cli_approve(
            f"Image preview sent to Discord (attempt {attempt}/{MAX_REGENERATION_ATTEMPTS}). "
            f"Approve these {len(image_paths)} scene images?"
        )

        if decision == "approve":
            logger.info("[Approval] Images approved")
            if discord_url:
                _send_discord_image(
                    discord_url, image_paths[0],
                    title="Images Approved",
                    description=f"Proceeding with {len(image_paths)} scenes.",
                )
            return image_paths

        if decision == "skip":
            logger.info("[Approval] Image validation skipped")
            return image_paths

        # Reject → regenerate
        logger.info(f"[Approval] Images rejected, regenerating (attempt {attempt + 1})...")
        if discord_url:
            from shared.notifier import send_discord
            send_discord(
                discord_url,
                title="Images Rejected",
                description=f"Regenerating... (attempt {attempt + 1})",
                color=0xE74C3C,
            )

        if attempt < MAX_REGENERATION_ATTEMPTS:
            image_paths = regenerate_fn()

    logger.warning("[Approval] Max regeneration attempts reached, using last result")
    return image_paths


# ---------------------------------------------------------------------------
# Video/Thumbnail Approval Loop
# ---------------------------------------------------------------------------

def approve_video(
    video_path: Path,
    thumbnail_path: Optional[Path],
    config: PipelineConfig,
    regenerate_fn: Optional[Callable[[], Path]] = None,
) -> bool:
    """Send video snippet + thumbnail to Discord, approve or reject.

    Parameters
    ----------
    video_path : Path
        Rendered video file.
    thumbnail_path : Path, optional
        Generated thumbnail.
    config : PipelineConfig
        Pipeline config.
    regenerate_fn : callable, optional
        If provided, rejection triggers re-render.

    Returns
    -------
    bool
        True if approved, False if rejected after all attempts.
    """
    discord_url = _get_discord_url(config)

    for attempt in range(1, MAX_REGENERATION_ATTEMPTS + 1):
        if discord_url:
            size_mb = video_path.stat().st_size / (1024 * 1024)
            _send_discord_video_snippet(
                discord_url,
                video_path,
                thumbnail_path,
                title=f"Video Preview (attempt {attempt})",
                description=(
                    f"Profile: **{config.profile}**\n"
                    f"Size: **{size_mb:.0f} MB**\n"
                    f"Thumbnail + 15s snippet attached.\n"
                    f"Approve in terminal to publish to YouTube."
                ),
            )
            logger.info(f"[Approval] Video preview sent to Discord (attempt {attempt})")

        decision = _cli_approve(
            f"Video preview sent to Discord (attempt {attempt}). "
            f"Approve for YouTube publication?"
        )

        if decision == "approve":
            logger.info("[Approval] Video approved for publication")
            return True

        if decision == "skip":
            logger.info("[Approval] Video validation skipped — approved by default")
            return True

        if regenerate_fn and attempt < MAX_REGENERATION_ATTEMPTS:
            logger.info("[Approval] Video rejected, re-rendering...")
            video_path = regenerate_fn()
        else:
            break

    logger.warning("[Approval] Video not approved after all attempts")
    return False


# ---------------------------------------------------------------------------
# Full Pipeline with Approval Gates
# ---------------------------------------------------------------------------

def run_approved_pipeline(
    video_path: Path,
    config: PipelineConfig,
    image_paths: Optional[List[Path]] = None,
    thumbnail_path: Optional[Path] = None,
    regenerate_images_fn: Optional[Callable[[], List[Path]]] = None,
    regenerate_video_fn: Optional[Callable[[], Path]] = None,
) -> Optional[str]:
    """Run the full pipeline with Discord approval gates at each stage.

    Flow:
    1. Approve images (if provided) → regenerate if rejected
    2. Approve video + thumbnail → regenerate if rejected
    3. Auto-publish to YouTube on approval
    4. Send final notification to Discord with YouTube link

    Returns YouTube video ID or None.
    """
    discord_url = _get_discord_url(config)

    # Gate 1: Image approval
    if image_paths and regenerate_images_fn:
        image_paths = approve_images(image_paths, config, regenerate_images_fn)

    # Gate 2: Video + thumbnail approval
    approved = approve_video(
        video_path, thumbnail_path, config, regenerate_video_fn
    )

    if not approved:
        logger.info("[Pipeline] Video not approved — not publishing")
        if discord_url:
            from shared.notifier import send_discord
            send_discord(
                discord_url,
                title="Publication Cancelled",
                description="Video was not approved. No upload to YouTube.",
                color=0xE74C3C,
            )
        return None

    # Gate 3: Auto-publish to YouTube
    video_id = None
    if config.publish.youtube_enabled:
        try:
            from shared.publisher import publish_to_youtube
            video_id = publish_to_youtube(video_path, config, thumbnail_path)

            if video_id and discord_url:
                from shared.notifier import send_discord
                send_discord(
                    discord_url,
                    title="Published to YouTube",
                    description=(
                        f"**{config.publish.youtube_title}**\n"
                        f"https://youtube.com/watch?v={video_id}\n"
                        f"Profile: {config.profile}"
                    ),
                    color=0xFF0000,  # YouTube red
                )
                logger.info(f"[Pipeline] Published and notified: {video_id}")

        except Exception as e:
            logger.error(f"[Pipeline] YouTube publish failed: {e}")
            if discord_url:
                from shared.notifier import send_discord
                send_discord(
                    discord_url,
                    title="YouTube Upload Failed",
                    description=f"Error: {str(e)[:300]}",
                    color=0xE74C3C,
                )
    else:
        logger.info("[Pipeline] YouTube publishing disabled in config")
        if discord_url:
            from shared.notifier import send_discord
            send_discord(
                discord_url,
                title="Video Ready (No Upload)",
                description=f"Video approved but YouTube publishing is disabled.\nFile: `{video_path.name}`",
                color=0x3498DB,
            )

    return video_id
