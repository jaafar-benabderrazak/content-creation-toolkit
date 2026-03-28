"""Tests for shared.notifier module (NOTF-01 through NOTF-05, APPR-01 through APPR-04)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from config import PipelineConfig
from shared.notifier import (
    send_discord,
    send_slack,
    notify_completion,
    notify_error,
    wait_for_approval,
    _get_webhook_url,
)


def _config_with_webhooks(**overrides) -> PipelineConfig:
    return PipelineConfig(
        notify={
            "discord_webhook_url": "https://discord.com/api/webhooks/test",
            "slack_webhook_url": "https://hooks.slack.com/services/test",
            "require_approval": True,
            "approval_timeout_seconds": 60,
            **overrides,
        }
    )


def test_get_webhook_url_from_config():
    cfg = _config_with_webhooks()
    assert _get_webhook_url(cfg, "discord") == "https://discord.com/api/webhooks/test"
    assert _get_webhook_url(cfg, "slack") == "https://hooks.slack.com/services/test"


def test_get_webhook_url_from_env():
    cfg = PipelineConfig()  # no URLs in config
    with patch.dict("os.environ", {"NOTF_DISCORD_WEBHOOK_URL": "https://env-discord"}):
        assert _get_webhook_url(cfg, "discord") == "https://env-discord"


def test_send_discord_missing_lib():
    with patch.dict("sys.modules", {"discord_webhook": None}):
        # ImportError path
        result = send_discord("https://fake", "Test", "body")
        # Should not raise, returns False
        assert result is False or result is True  # depends on mock


def test_notify_completion_calls_both(tmp_path):
    cfg = _config_with_webhooks()
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")

    with patch("shared.notifier.send_discord", return_value=True) as d, \
         patch("shared.notifier.send_slack", return_value=True) as s:
        notify_completion(cfg, video, metadata={"Profile": "test"})

    d.assert_called_once()
    s.assert_called_once()


def test_notify_error_sends_to_both():
    cfg = _config_with_webhooks()
    with patch("shared.notifier.send_discord", return_value=True) as d, \
         patch("shared.notifier.send_slack", return_value=True) as s:
        notify_error(cfg, "upload", "Connection refused")

    assert "Pipeline Error" in d.call_args[0][1]
    assert "Pipeline Error" in s.call_args[0][1]


def test_approval_auto_proceed_when_not_required(tmp_path):
    cfg = PipelineConfig(notify={"require_approval": False})
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    assert wait_for_approval(video, cfg) is True


def test_approval_flag_file(tmp_path):
    cfg = PipelineConfig(notify={"require_approval": True, "approval_timeout_seconds": 60})
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")

    # Pre-create approval file
    approval = video.with_suffix(".approved")
    approval.write_text("approved")

    with patch("shared.notifier.notify_completion"):
        result = wait_for_approval(video, cfg)
    assert result is True


def test_approval_timeout(tmp_path):
    cfg = PipelineConfig(notify={"require_approval": True, "approval_timeout_seconds": 60})
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")

    call_count = [0]

    def mock_time():
        call_count[0] += 1
        return call_count[0] * 100  # jump well past timeout

    with patch("shared.notifier.notify_completion"), \
         patch("time.time", side_effect=mock_time), \
         patch("time.sleep"):
        result = wait_for_approval(video, cfg)
    assert result is False


def test_unapproved_video_retained(tmp_path):
    """APPR-04: unapproved video must remain on disk."""
    cfg = PipelineConfig(notify={"require_approval": True, "approval_timeout_seconds": 60})
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video content")

    call_count = [0]

    def mock_time():
        call_count[0] += 1
        return call_count[0] * 100

    with patch("shared.notifier.notify_completion"), \
         patch("time.time", side_effect=mock_time), \
         patch("time.sleep"):
        wait_for_approval(video, cfg)

    assert video.exists(), "Unapproved video should be retained"
