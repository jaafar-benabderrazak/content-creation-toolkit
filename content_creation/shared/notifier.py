"""Notification and approval gate module.

Sends webhook notifications to Discord and Slack, and implements
a file-based approval gate for publish decisions.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)


def _get_webhook_url(config: PipelineConfig, platform: str) -> Optional[str]:
    """Get webhook URL from config or environment variable."""
    if platform == "discord":
        return config.notify.discord_webhook_url or os.getenv("NOTF_DISCORD_WEBHOOK_URL")
    elif platform == "slack":
        return config.notify.slack_webhook_url or os.getenv("NOTF_SLACK_WEBHOOK_URL")
    return None


def send_discord(
    webhook_url: str,
    title: str,
    description: str,
    color: int = 0x00FF00,
    thumbnail_path: Optional[Path] = None,
    fields: Optional[dict[str, str]] = None,
) -> bool:
    """Send a Discord webhook notification with embed."""
    try:
        from discord_webhook import DiscordWebhook, DiscordEmbed

        webhook = DiscordWebhook(url=webhook_url)
        embed = DiscordEmbed(title=title, description=description, color=color)

        if fields:
            for name, value in fields.items():
                embed.add_embed_field(name=name, value=value, inline=True)

        webhook.add_embed(embed)

        if thumbnail_path and thumbnail_path.exists():
            with open(thumbnail_path, "rb") as f:
                webhook.add_file(file=f.read(), filename="thumbnail.jpg")

        response = webhook.execute()
        logger.info(f"[Notify] Discord: sent '{title}'")
        return True
    except ImportError:
        logger.warning("[Notify] discord-webhook not installed — pip install discord-webhook")
        return False
    except Exception as e:
        logger.error(f"[Notify] Discord failed: {e}")
        return False


def send_slack(
    webhook_url: str,
    title: str,
    description: str,
    thumbnail_path: Optional[Path] = None,
    fields: Optional[dict[str, str]] = None,
) -> bool:
    """Send a Slack webhook notification with Block Kit."""
    try:
        from slack_sdk.webhook import WebhookClient

        client = WebhookClient(webhook_url)

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": description},
            },
        ]

        if fields:
            field_blocks = []
            for name, value in fields.items():
                field_blocks.append({"type": "mrkdwn", "text": f"*{name}*\n{value}"})
            blocks.append({"type": "section", "fields": field_blocks})

        response = client.send(blocks=blocks)
        logger.info(f"[Notify] Slack: sent '{title}'")
        return True
    except ImportError:
        logger.warning("[Notify] slack-sdk not installed — pip install slack-sdk")
        return False
    except Exception as e:
        logger.error(f"[Notify] Slack failed: {e}")
        return False


def notify_completion(
    config: PipelineConfig,
    video_path: Path,
    thumbnail_path: Optional[Path] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Send completion notification to all configured channels."""
    title = "Video Generation Complete"
    fields = metadata or {}
    fields["Video"] = video_path.name
    description = f"Pipeline finished: `{video_path.name}`"

    discord_url = _get_webhook_url(config, "discord")
    if discord_url:
        send_discord(discord_url, title, description, color=0x00FF00,
                     thumbnail_path=thumbnail_path, fields=fields)

    slack_url = _get_webhook_url(config, "slack")
    if slack_url:
        send_slack(slack_url, title, description,
                   thumbnail_path=thumbnail_path, fields=fields)


def notify_error(
    config: PipelineConfig,
    stage: str,
    error: str,
) -> None:
    """Send error alert to all configured channels."""
    title = "Pipeline Error"
    description = f"Failed at stage: **{stage}**\n```{error[:500]}```"
    fields = {"Stage": stage}

    discord_url = _get_webhook_url(config, "discord")
    if discord_url:
        send_discord(discord_url, title, description, color=0xFF0000, fields=fields)

    slack_url = _get_webhook_url(config, "slack")
    if slack_url:
        send_slack(slack_url, title, description, fields=fields)


def wait_for_approval(
    video_path: Path,
    config: PipelineConfig,
    thumbnail_path: Optional[Path] = None,
) -> bool:
    """Send preview notification and wait for approval via flag file or CLI.

    Approval methods:
    1. Create a file: <video_name>.approved in the same directory
    2. Run with --approve flag (handled by caller)

    Returns True if approved, False if timed out.
    """
    if not config.notify.require_approval:
        logger.info("[Approval] Approval not required — auto-proceeding")
        return True

    # Send preview notification
    notify_completion(
        config, video_path,
        thumbnail_path=thumbnail_path,
        metadata={"Status": "Awaiting Approval", "Profile": config.profile},
    )

    approval_file = video_path.with_suffix(".approved")
    timeout = config.notify.approval_timeout_seconds

    print(f"\n[Approval] Video ready for review: {video_path}")
    print(f"[Approval] To approve, create: {approval_file}")
    print(f"[Approval] Or press Enter to approve now...")
    print(f"[Approval] Timeout: {timeout}s")

    start = time.time()
    while time.time() - start < timeout:
        if approval_file.exists():
            logger.info("[Approval] Approved via flag file")
            approval_file.unlink(missing_ok=True)
            return True

        # Check stdin for Enter press (non-blocking with 5s intervals)
        try:
            import select
            if select.select([__import__("sys").stdin], [], [], 5.0)[0]:
                logger.info("[Approval] Approved via Enter key")
                return True
        except (ImportError, OSError):
            # Windows: select doesn't work on stdin, use simple sleep
            time.sleep(5)

    logger.warning("[Approval] Timed out — video NOT published")
    return False
