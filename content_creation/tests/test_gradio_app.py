"""Tests for gradio_app module (CONF-02)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from gradio_app import list_profiles, load_profile, save_config


def test_list_profiles_includes_default():
    profiles = list_profiles()
    assert "(default)" in profiles


def test_list_profiles_finds_yaml_files():
    profiles = list_profiles()
    assert "lofi_study" in profiles
    assert "tech_tutorial" in profiles
    assert "cinematic" in profiles


def test_load_default_profile():
    vals = load_profile("(default)")
    assert vals["profile"] == "default"
    assert vals["resolution"] == "1080p"
    assert vals["youtube_enabled"] is False


def test_load_named_profile():
    vals = load_profile("lofi_study")
    assert vals["profile"] == "lofi-study"
    assert vals["mood"] == "relaxed-focus"
    assert "lofi" in vals["style_prompt"].lower()


def test_save_config_creates_file(tmp_path):
    with patch("gradio_app.LAST_RUN_FILE", tmp_path / "last_run.yaml"):
        result = save_config(
            "test", "style", "music", "mood", 10, "720p",
            "fast", 8, False, "", False, False, "title", "desc",
            "tag1, tag2", "private", "", "", True,
        )
    assert "saved" in result.lower()


def test_save_config_roundtrip(tmp_path):
    last_run = tmp_path / "last_run.yaml"
    with patch("gradio_app.LAST_RUN_FILE", last_run):
        save_config(
            "roundtrip-test", "my style", "my music", "chill", 30, "1080p",
            "high", 12, True, "@me", False, True, "My Video", "My desc",
            "ai, test", "unlisted", "", "", False,
        )

    from config import PipelineConfig
    cfg = PipelineConfig.from_yaml(last_run)
    assert cfg.profile == "roundtrip-test"
    assert cfg.video.style_prompt == "my style"
    assert cfg.publish.youtube_enabled is True
    assert cfg.publish.youtube_tags == ["ai", "test"]
