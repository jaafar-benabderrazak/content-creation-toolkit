"""Shared pipeline runner — wires post-process, thumbnail, approval loops, publish.

Called at the tail of each pipeline's main() when --config is provided.
Each step is gated by config flags. Discord approval gates at image and video stages.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, List, Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)


def run_shared_pipeline(
    video_path: Path,
    config: PipelineConfig,
    image_paths: Optional[List[Path]] = None,
    regenerate_images_fn: Optional[Callable[[], List[Path]]] = None,
    regenerate_video_fn: Optional[Callable[[], Path]] = None,
) -> Optional[str]:
    """Run the full shared pipeline with Discord approval gates.

    Flow:
    1. Approve images via Discord (regenerate if rejected)
    2. Post-process video (watermark, subtitles, intro/outro)
    3. Generate thumbnail
    4. Approve video + thumbnail via Discord (regenerate if rejected)
    5. Auto-publish to YouTube
    6. Send final notification with YouTube link

    Returns YouTube video ID if published, None otherwise.
    """
    current_video = video_path
    thumbnail_path = None

    # Step 1: Image approval gate (if images provided)
    if image_paths and regenerate_images_fn:
        try:
            from shared.approval_loop import approve_images
            image_paths = approve_images(image_paths, config, regenerate_images_fn)
        except Exception as e:
            logger.warning(f"[Pipeline] Image approval skipped: {e}")

    # Step 2: Post-processing
    try:
        from shared.post_process import run_post_process
        current_video = run_post_process(current_video, config)
    except Exception as e:
        logger.error(f"[Pipeline] Post-processing failed: {e}")
        _notify_error(config, "post-processing", str(e))
        return None

    # Step 3: Thumbnail generation
    if config.publish.thumbnail_enabled:
        try:
            from shared.thumbnail_gen import generate_thumbnail
            thumb_out = current_video.with_name(f"{current_video.stem}_thumb.jpg")
            thumbnail_path = generate_thumbnail(
                current_video, thumb_out,
                title=config.publish.youtube_title,
                branding=config.post.watermark_text,
            )
        except Exception as e:
            logger.warning(f"[Pipeline] Thumbnail generation failed: {e}")

    # Step 4: Video + thumbnail approval gate → auto YouTube publish
    try:
        from shared.approval_loop import run_approved_pipeline
        video_id = run_approved_pipeline(
            video_path=current_video,
            config=config,
            thumbnail_path=thumbnail_path,
            regenerate_video_fn=regenerate_video_fn,
        )
        return video_id
    except Exception as e:
        logger.error(f"[Pipeline] Approval/publish failed: {e}")
        _notify_error(config, "approval-publish", str(e))

    return None


def _notify_error(config: PipelineConfig, stage: str, error: str) -> None:
    try:
        from shared.notifier import notify_error
        notify_error(config, stage, error)
    except Exception:
        pass
