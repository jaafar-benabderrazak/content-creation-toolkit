"""Tests for shared.pipeline_runner (INTG-01 through INTG-03)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from config import PipelineConfig
from shared.pipeline_runner import run_shared_pipeline


def _config_all_off() -> PipelineConfig:
    return PipelineConfig(
        publish={"youtube_enabled": False},
        notify={"require_approval": False},
    )


def _config_full() -> PipelineConfig:
    return PipelineConfig(
        publish={"youtube_enabled": True, "youtube_title": "Test"},
        notify={"require_approval": True, "discord_webhook_url": "https://test"},
        post={"watermark_enabled": True, "watermark_text": "Test"},
    )


def test_all_disabled_returns_none(tmp_path):
    """INTG-03: no features run when all flags are off."""
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_all_off()

    with patch("shared.post_process.run_post_process", return_value=video) as pp:
        result = run_shared_pipeline(video, cfg)

    pp.assert_called_once()
    assert result is None


def test_full_chain_wiring(tmp_path):
    """INTG-01: full chain runs in correct order."""
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_full()

    call_order = []

    def mock_pp(v, c):
        call_order.append("post_process")
        return v

    def mock_thumb(v, o, **kw):
        call_order.append("thumbnail")
        return o

    def mock_approved_pipeline(*args, **kw):
        call_order.append("approve")
        call_order.append("publish")
        return "vid123"

    with patch("shared.post_process.run_post_process", side_effect=mock_pp), \
         patch("shared.thumbnail_gen.generate_thumbnail", side_effect=mock_thumb), \
         patch("shared.approval_loop.run_approved_pipeline", side_effect=mock_approved_pipeline):
        result = run_shared_pipeline(video, cfg)

    assert call_order == ["post_process", "thumbnail", "approve", "publish"]
    assert result == "vid123"


def test_unapproved_stops_publish(tmp_path):
    """INTG-01: pipeline stops if not approved."""
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")
    cfg = _config_full()

    with patch("shared.post_process.run_post_process", return_value=video), \
         patch("shared.thumbnail_gen.generate_thumbnail", return_value=None), \
         patch("shared.approval_loop.run_approved_pipeline", return_value=None):
        result = run_shared_pipeline(video, cfg)

    assert result is None


def test_syntax_both_scripts():
    """INTG-02: both pipeline scripts parse without syntax errors."""
    import ast
    for script in ["study_with_me_generator.py", "faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py"]:
        source = Path(script).read_text(encoding="utf-8")
        ast.parse(source)  # raises SyntaxError if broken
