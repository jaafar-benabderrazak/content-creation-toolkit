"""Shared pipeline runner — wires post-process, thumbnail, notify, approve, publish.

Called at the tail of each pipeline's main() when --config is provided.
Each step is gated by config flags, so the full chain only runs when opted in.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)


def run_shared_pipeline(
    video_path: Path,
    config: PipelineConfig,
) -> Optional[str]:
    """Run the full shared pipeline: post-process → thumbnail → notify → approve → publish.

    Returns YouTube video ID if published, None otherwise.
    """
    current_video = video_path
    thumbnail_path = None
    video_id = None

    # Step 1: Post-processing
    try:
        from shared.post_process import run_post_process
        current_video = run_post_process(current_video, config)
    except Exception as e:
        logger.error(f"[Pipeline] Post-processing failed: {e}")
        _notify_error(config, "post-processing", str(e))
        return None

    # Step 2: Thumbnail generation
    if config.publish.thumbnail_enabled:
        try:
            from shared.thumbnail_gen import generate_thumbnail
            thumb_out = current_video.with_name(f"{current_video.stem}_thumb.jpg")
            thumbnail_path = generate_thumbnail(
                current_video,
                thumb_out,
                title=config.publish.youtube_title,
                branding=config.post.watermark_text,
            )
        except Exception as e:
            logger.warning(f"[Pipeline] Thumbnail generation failed: {e}")
            # Non-fatal — continue without thumbnail

    # Step 3: Notify + Approval gate
    if config.notify.require_approval or _has_webhooks(config):
        try:
            from shared.notifier import wait_for_approval
            approved = wait_for_approval(current_video, config, thumbnail_path)
            if not approved:
                logger.info("[Pipeline] Not approved — video retained locally")
                print(f"[Pipeline] Video saved at: {current_video}")
                return None
        except Exception as e:
            logger.error(f"[Pipeline] Notification/approval failed: {e}")
            _notify_error(config, "notification", str(e))
            return None

    # Step 4: YouTube publish
    if config.publish.youtube_enabled:
        try:
            from shared.publisher import publish_to_youtube
            video_id = publish_to_youtube(current_video, config, thumbnail_path)
            if video_id:
                print(f"[Pipeline] Published: https://youtube.com/watch?v={video_id}")
                # Notify success
                _notify_success(config, current_video, thumbnail_path, video_id)
            else:
                logger.warning("[Pipeline] YouTube upload returned no video ID")
        except Exception as e:
            logger.error(f"[Pipeline] YouTube publish failed: {e}")
            _notify_error(config, "youtube-upload", str(e))
    else:
        print(f"[Pipeline] Complete. Video at: {current_video}")

    return video_id


def _has_webhooks(config: PipelineConfig) -> bool:
    import os
    return bool(
        config.notify.discord_webhook_url
        or config.notify.slack_webhook_url
        or os.getenv("NOTF_DISCORD_WEBHOOK_URL")
        or os.getenv("NOTF_SLACK_WEBHOOK_URL")
    )


def _notify_error(config: PipelineConfig, stage: str, error: str) -> None:
    try:
        from shared.notifier import notify_error
        notify_error(config, stage, error)
    except Exception:
        pass  # Don't fail the pipeline because notification failed


def _notify_success(
    config: PipelineConfig,
    video_path: Path,
    thumbnail_path: Optional[Path],
    video_id: str,
) -> None:
    try:
        from shared.notifier import notify_completion
        notify_completion(
            config, video_path,
            thumbnail_path=thumbnail_path,
            metadata={
                "YouTube": f"https://youtube.com/watch?v={video_id}",
                "Profile": config.profile,
            },
        )
    except Exception:
        pass
