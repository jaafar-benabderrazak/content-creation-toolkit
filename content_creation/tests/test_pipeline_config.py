"""Tests for config.PipelineConfig schema validation (CONF-04)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from config import PipelineConfig
from config.pipeline_config import VideoSettings, PostSettings, PublishSettings, NotifySettings


def _write_yaml(data: dict, tmp_path: Path) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return p


VALID_MINIMAL = {
    "profile": "test-profile",
    "video": {
        "style_prompt": "test style",
        "mood": "test",
        "duration_minutes": 5,
    },
}


# --- Construction ---

def test_default_construction():
    cfg = PipelineConfig()
    assert cfg.profile == "default"
    assert cfg.video.duration_minutes == 120
    assert cfg.publish.youtube_enabled is False
    assert cfg.notify.require_approval is True


def test_sub_model_defaults():
    cfg = PipelineConfig()
    assert cfg.video.resolution == "1080p"
    assert cfg.video.quality_preset == "high"
    assert cfg.post.watermark_enabled is False
    assert cfg.publish.youtube_privacy == "private"
    assert cfg.notify.approval_timeout_seconds == 3600


# --- from_yaml valid ---

def test_from_yaml_valid_minimal(tmp_path):
    p = _write_yaml(VALID_MINIMAL, tmp_path)
    cfg = PipelineConfig.from_yaml(p)
    assert cfg.profile == "test-profile"
    assert cfg.video.mood == "test"
    assert cfg.video.enable_parallax is True  # default preserved


def test_from_yaml_named_profiles():
    profiles_dir = Path("config/profiles")
    yaml_files = list(profiles_dir.glob("*.yaml"))
    if not yaml_files:
        pytest.skip("Profile YAML files not yet created")
    for yaml_file in yaml_files:
        cfg = PipelineConfig.from_yaml(yaml_file)
        assert cfg.profile != "default", f"{yaml_file.name} did not set profile name"
        assert len(cfg.video.style_prompt) > 10


# --- from_yaml invalid ---

def test_from_yaml_wrong_type_duration(tmp_path):
    data = {**VALID_MINIMAL, "video": {**VALID_MINIMAL["video"], "duration_minutes": "two-hours"}}
    p = _write_yaml(data, tmp_path)
    with pytest.raises(Exception) as exc_info:
        PipelineConfig.from_yaml(p)
    err = str(exc_info.value).lower()
    assert "duration_minutes" in err or "duration" in err


def test_from_yaml_invalid_resolution(tmp_path):
    data = {**VALID_MINIMAL, "video": {**VALID_MINIMAL["video"], "resolution": "4K"}}
    p = _write_yaml(data, tmp_path)
    with pytest.raises(Exception):
        PipelineConfig.from_yaml(p)


def test_from_yaml_invalid_youtube_privacy(tmp_path):
    data = {**VALID_MINIMAL, "publish": {"youtube_privacy": "secret"}}
    p = _write_yaml(data, tmp_path)
    with pytest.raises(Exception):
        PipelineConfig.from_yaml(p)


def test_from_yaml_duration_below_minimum(tmp_path):
    data = {**VALID_MINIMAL, "video": {**VALID_MINIMAL["video"], "duration_minutes": 0}}
    p = _write_yaml(data, tmp_path)
    with pytest.raises(Exception):
        PipelineConfig.from_yaml(p)


def test_from_yaml_empty_file(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    with pytest.raises((ValueError, Exception)):
        PipelineConfig.from_yaml(p)


# --- File not found ---

def test_from_yaml_file_not_found():
    with pytest.raises(FileNotFoundError):
        PipelineConfig.from_yaml(Path("nonexistent_config_xyz.yaml"))


# --- Round-trip ---

def test_yaml_round_trip(tmp_path):
    original = PipelineConfig.from_yaml(Path("config/profiles/lofi_study.yaml"))
    saved_path = tmp_path / "round_trip.yaml"
    original.to_yaml(saved_path)
    reloaded = PipelineConfig.from_yaml(saved_path)
    assert reloaded.profile == original.profile
    assert reloaded.video.style_prompt == original.video.style_prompt
    assert reloaded.video.mood == original.video.mood
    assert reloaded.video.duration_minutes == original.video.duration_minutes
    assert reloaded.publish.youtube_enabled == original.publish.youtube_enabled


def test_to_yaml_creates_valid_file(tmp_path):
    cfg = PipelineConfig()
    out_path = tmp_path / "out.yaml"
    cfg.to_yaml(out_path)
    assert out_path.exists()
    data = yaml.safe_load(out_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "profile" in data
    assert "video" in data
