"""Tests for shared.approval_loop module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from config import PipelineConfig
from shared.approval_loop import approve_images, approve_video, run_approved_pipeline


def _config_with_discord() -> PipelineConfig:
    return PipelineConfig(
        notify={"discord_webhook_url": "https://discord.com/api/webhooks/test"},
        publish={"youtube_enabled": True, "youtube_title": "Test"},
    )


def test_approve_images_on_first_try(tmp_path):
    img = tmp_path / "scene.jpg"
    img.write_bytes(b"fake")
    cfg = _config_with_discord()

    with patch("shared.approval_loop._send_discord_image", return_value=True), \
         patch("shared.approval_loop._cli_approve", return_value="approve"):
        result = approve_images([img], cfg, lambda: [img])

    assert result == [img]


def test_approve_images_reject_then_approve(tmp_path):
    img1 = tmp_path / "scene_v1.jpg"
    img1.write_bytes(b"v1")
    img2 = tmp_path / "scene_v2.jpg"
    img2.write_bytes(b"v2")
    cfg = _config_with_discord()

    call_count = [0]

    def mock_approve(*args):
        call_count[0] += 1
        return "reject" if call_count[0] == 1 else "approve"

    with patch("shared.approval_loop._send_discord_image", return_value=True), \
         patch("shared.approval_loop._cli_approve", side_effect=mock_approve), \
         patch("shared.notifier.send_discord", return_value=True):
        result = approve_images([img1], cfg, lambda: [img2])

    assert result == [img2]


def test_approve_video_approved(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_with_discord()

    with patch("shared.approval_loop._send_discord_video_snippet", return_value=True), \
         patch("shared.approval_loop._cli_approve", return_value="approve"):
        assert approve_video(video, None, cfg) is True


def test_approve_video_rejected(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_with_discord()

    with patch("shared.approval_loop._send_discord_video_snippet", return_value=True), \
         patch("shared.approval_loop._cli_approve", return_value="reject"):
        assert approve_video(video, None, cfg) is False


def test_run_approved_pipeline_publishes(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_with_discord()

    with patch("shared.approval_loop.approve_video", return_value=True), \
         patch("shared.publisher.publish_to_youtube", return_value="yt123"), \
         patch("shared.notifier.send_discord", return_value=True):
        result = run_approved_pipeline(video, cfg)

    assert result == "yt123"


def test_run_approved_pipeline_cancelled(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_with_discord()

    with patch("shared.approval_loop.approve_video", return_value=False), \
         patch("shared.notifier.send_discord", return_value=True):
        result = run_approved_pipeline(video, cfg)

    assert result is None
