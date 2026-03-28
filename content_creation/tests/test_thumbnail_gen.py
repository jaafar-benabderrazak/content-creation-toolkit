"""Tests for shared.thumbnail_gen module (THMB-01 through THMB-03)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from shared.thumbnail_gen import (
    score_sharpness,
    composite_text,
    THUMB_WIDTH,
    THUMB_HEIGHT,
    MAX_FILE_SIZE,
)


@pytest.fixture
def sample_image(tmp_path):
    """Create a small test image."""
    from PIL import Image
    img = Image.new("RGB", (1920, 1080), color=(100, 150, 200))
    p = tmp_path / "frame.jpg"
    img.save(p, "JPEG")
    return p


def test_composite_text_dimensions(sample_image, tmp_path):
    out = tmp_path / "thumb.jpg"
    composite_text(sample_image, out, title="Test Title", branding="@Channel")
    from PIL import Image
    img = Image.open(out)
    assert img.size == (THUMB_WIDTH, THUMB_HEIGHT)


def test_composite_text_under_2mb(sample_image, tmp_path):
    out = tmp_path / "thumb.jpg"
    composite_text(sample_image, out, title="Test Title")
    assert out.stat().st_size <= MAX_FILE_SIZE


def test_composite_text_jpeg_format(sample_image, tmp_path):
    out = tmp_path / "thumb.jpg"
    composite_text(sample_image, out, title="Hello")
    from PIL import Image
    img = Image.open(out)
    assert img.format == "JPEG"


def test_score_sharpness_returns_float(sample_image):
    score = score_sharpness(sample_image)
    assert isinstance(score, float)
    assert score >= 0


def test_composite_no_text(sample_image, tmp_path):
    """Empty title/branding should still produce valid output."""
    out = tmp_path / "thumb.jpg"
    composite_text(sample_image, out, title="", branding="")
    assert out.exists()
    assert out.stat().st_size > 0
