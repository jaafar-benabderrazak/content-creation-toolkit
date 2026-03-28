"""Tests for shared.post_process module (POST-01 through POST-05)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from config import PipelineConfig
from shared.post_process import run_post_process, _ffmpeg_available


def _make_config(**post_overrides) -> PipelineConfig:
    return PipelineConfig(post=post_overrides)


def test_no_steps_enabled_returns_original(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    cfg = _make_config()
    with patch("shared.post_process._ffmpeg_available", return_value=True):
        result = run_post_process(video, cfg)
    assert result == video


def test_ffmpeg_missing_skips_gracefully(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    cfg = _make_config(watermark_enabled=True, watermark_text="Test")
    with patch("shared.post_process._ffmpeg_available", return_value=False):
        result = run_post_process(video, cfg)
    assert result == video


def test_watermark_calls_ffmpeg(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    cfg = _make_config(watermark_enabled=True, watermark_text="MyChannel")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("shared.post_process._ffmpeg_available", return_value=True), \
         patch("shared.post_process.subprocess.run", return_value=mock_result) as mock_run, \
         patch("shutil.move"):
        run_post_process(video, cfg)

    # FFmpeg was called with drawtext filter
    calls = [c for c in mock_run.call_args_list if "drawtext" in str(c)]
    assert len(calls) == 1


def test_subtitles_skipped_when_srt_missing(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    cfg = _make_config(subtitles_enabled=True)
    with patch("shared.post_process._ffmpeg_available", return_value=True):
        result = run_post_process(video, cfg)
    assert result == video  # No SRT found, no processing


def test_config_flags_independent(tmp_path):
    """Disabling one step does not break others."""
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    cfg = _make_config(
        watermark_enabled=False,
        subtitles_enabled=False,
        intro_enabled=True,
        intro_clip_path="",  # empty path = no intro file
        outro_enabled=False,
    )
    with patch("shared.post_process._ffmpeg_available", return_value=True):
        result = run_post_process(video, cfg)
    assert result == video
