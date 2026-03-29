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

    # Step 0: Channel branding fetch (runs only when branding_enabled=True)
    branding_data = None
    avatar_path = None
    generated_intro_path = None
    generated_outro_path = None

    if hasattr(config, 'branding') and config.branding.branding_enabled:
        try:
            from shared.branding import fetch_channel_branding
            from pathlib import Path as _Path
            branding_data = fetch_channel_branding(refresh=config.branding.refresh_branding)
            avatar_local = _Path(branding_data.avatar_local_path)
            if avatar_local.exists():
                avatar_path = avatar_local

            # Generate intro/outro clips into .cache/branding/
            from shared.branding_clips import generate_branding_clips
            cache_dir = _Path(".cache/branding")
            # Regenerate clips if refresh was requested (delete stale clips first)
            if config.branding.refresh_branding:
                for clip in [cache_dir / "intro.mp4", cache_dir / "outro.mp4"]:
                    clip.unlink(missing_ok=True)
            generated_intro_path, generated_outro_path = generate_branding_clips(branding_data, cache_dir)
            logger.info(f"[Pipeline] Branding ready: channel={branding_data.channel_name}")
        except Exception as e:
            logger.warning(f"[Pipeline] Branding fetch failed, continuing without branding: {e}")
            branding_data = None
            avatar_path = None
            generated_intro_path = None
            generated_outro_path = None

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

        # Inject branding clips into post config if not explicitly set
        post_config = config
        if generated_intro_path or generated_outro_path:
            from config.pipeline_config import PostSettings
            post_overrides = {}
            if generated_intro_path and generated_intro_path.exists():
                if not config.post.intro_clip_path:
                    post_overrides["intro_enabled"] = True
                    post_overrides["intro_clip_path"] = str(generated_intro_path)
            if generated_outro_path and generated_outro_path.exists():
                if not config.post.outro_clip_path:
                    post_overrides["outro_enabled"] = True
                    post_overrides["outro_clip_path"] = str(generated_outro_path)
            if post_overrides:
                try:
                    updated_post = config.post.model_copy(update=post_overrides)
                except AttributeError:
                    updated_post = config.post.copy(update=post_overrides)
                try:
                    post_config = config.model_copy(update={"post": updated_post})
                except AttributeError:
                    post_config = config.copy(update={"post": updated_post})

        current_video = run_post_process(current_video, post_config)
    except Exception as e:
        logger.error(f"[Pipeline] Post-processing failed: {e}")
        _notify_error(config, "post-processing", str(e))
        return None

    # Step 3: Thumbnail generation
    if config.publish.thumbnail_enabled:
        try:
            from shared.thumbnail_gen import generate_thumbnail
            thumb_out = current_video.with_name(f"{current_video.stem}_thumb.jpg")
            # Use positive prompt for img2img thumbnail enhancement
            enhance_prompt = ""
            if hasattr(config, "sdxl") and config.sdxl:
                enhance_prompt = getattr(config.sdxl, "positive_prompt", "") or ""

            thumbnail_path = generate_thumbnail(
                current_video, thumb_out,
                title=config.publish.thumbnail_text or config.publish.youtube_title,
                branding=config.post.watermark_text,
                avatar_path=avatar_path,
                enhance_prompt=enhance_prompt,
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
