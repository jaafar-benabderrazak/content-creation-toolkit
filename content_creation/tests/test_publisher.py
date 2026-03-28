"""Tests for shared.publisher module (YT-01 through YT-05)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from config import PipelineConfig
from shared.publisher import (
    check_quota_available,
    _record_quota_usage,
    upload_video,
    publish_to_youtube,
    UPLOAD_QUOTA_COST,
    CREDENTIALS_DIR,
)


def _youtube_config(**overrides) -> PipelineConfig:
    return PipelineConfig(publish={
        "youtube_enabled": True,
        "youtube_title": "Test Video",
        "youtube_description": "Test description",
        "youtube_tags": ["test"],
        "youtube_category_id": "27",
        "youtube_privacy": "private",
        **overrides,
    })


def test_quota_check_sufficient(tmp_path):
    counter = tmp_path / "quota_counter.json"
    counter.write_text(json.dumps({"date": date.today().isoformat(), "used": 0}))

    with patch("shared.publisher.CREDENTIALS_DIR", tmp_path):
        result = check_quota_available(MagicMock(), UPLOAD_QUOTA_COST)
    assert result is True


def test_quota_check_exhausted(tmp_path):
    counter = tmp_path / "quota_counter.json"
    counter.write_text(json.dumps({"date": date.today().isoformat(), "used": 9500}))

    with patch("shared.publisher.CREDENTIALS_DIR", tmp_path):
        result = check_quota_available(MagicMock(), UPLOAD_QUOTA_COST)
    assert result is False


def test_quota_resets_next_day(tmp_path):
    counter = tmp_path / "quota_counter.json"
    counter.write_text(json.dumps({"date": "2020-01-01", "used": 9999}))

    with patch("shared.publisher.CREDENTIALS_DIR", tmp_path):
        result = check_quota_available(MagicMock(), UPLOAD_QUOTA_COST)
    assert result is True


def test_record_quota_usage(tmp_path):
    with patch("shared.publisher.CREDENTIALS_DIR", tmp_path):
        _record_quota_usage(1600)
        _record_quota_usage(50)

    counter = tmp_path / "quota_counter.json"
    data = json.loads(counter.read_text())
    assert data["used"] == 1650
    assert data["date"] == date.today().isoformat()


def test_upload_disabled_returns_none():
    cfg = PipelineConfig(publish={"youtube_enabled": False})
    result = upload_video(Path("fake.mp4"), cfg)
    assert result is None


def test_publish_flow_calls_upload_and_thumbnail():
    cfg = _youtube_config()
    video = Path("fake.mp4")
    thumb = Path("fake_thumb.jpg")

    with patch("shared.publisher.upload_video", return_value="abc123") as mock_upload, \
         patch("shared.publisher.upload_thumbnail", return_value=True) as mock_thumb:
        result = publish_to_youtube(video, cfg, thumbnail_path=thumb)

    assert result == "abc123"
    mock_upload.assert_called_once_with(video, cfg)
    mock_thumb.assert_called_once_with("abc123", thumb)


def test_publish_no_thumbnail_when_disabled():
    cfg = PipelineConfig(publish={
        "youtube_enabled": True,
        "youtube_title": "Test",
        "thumbnail_enabled": False,
    })
    video = Path("fake.mp4")
    thumb = Path("fake_thumb.jpg")

    with patch("shared.publisher.upload_video", return_value="abc123") as mock_upload, \
         patch("shared.publisher.upload_thumbnail") as mock_thumb:
        publish_to_youtube(video, cfg, thumbnail_path=thumb)

    mock_thumb.assert_not_called()
