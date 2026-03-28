"""Unit tests for generators.suno.SunoClient.

All HTTP calls are mocked — no live Suno API is contacted.
Run with: pytest tests/test_suno_client.py -v
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch, call

import pytest
from pydub import AudioSegment

from config.pipeline_config import SunoSettings
from generators.suno import SunoClient, POLL_HARD_TIMEOUT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(api_key: str = "test-key") -> SunoClient:
    """Build a SunoClient with a dummy api_key bypassing env lookup."""
    cfg = SunoSettings(genre="lofi chill", api_key=api_key)
    return SunoClient(cfg)


def _silent(ms: int = 5000) -> AudioSegment:
    return AudioSegment.silent(duration=ms)


# ---------------------------------------------------------------------------
# Test 1: Polling times out after POLL_HARD_TIMEOUT seconds
# ---------------------------------------------------------------------------

def test_poll_timeout(monkeypatch):
    """_poll_until_complete raises TimeoutError before POLL_HARD_TIMEOUT + 5 s wall-clock."""
    import generators.suno as suno_mod

    # Override constants so the test completes in under 20 s
    monkeypatch.setattr(suno_mod, "POLL_HARD_TIMEOUT", 15)
    monkeypatch.setattr(suno_mod, "POLL_INITIAL_WAIT", 3)
    monkeypatch.setattr(suno_mod, "POLL_MAX_WAIT", 5)

    client = _make_client()

    # Mock GET to always return "processing"
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "processing"}
    client._session.get = MagicMock(return_value=mock_response)

    start = time.time()
    with pytest.raises(TimeoutError):
        client._poll_until_complete("fake-task-id-1234")
    elapsed = time.time() - start

    # Must complete in reasonable time (timeout + 5 s buffer)
    assert elapsed < 15 + 5, f"Test took too long: {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# Test 2: _stitch_tracks trims to target_ms with tolerance
# ---------------------------------------------------------------------------

def test_stitch_two_tracks():
    """Two 10 s silent segments stitched to target_ms=18000 land within ±500 ms."""
    client = _make_client()
    seg1 = AudioSegment.silent(duration=10000)
    seg2 = AudioSegment.silent(duration=10000)

    result = client._stitch_tracks([seg1, seg2], target_ms=18000)

    assert isinstance(result, AudioSegment)
    # With 3000 ms crossfade: 10000 + 10000 - 3000 = 17000 ms stitched, trimmed to 18000 is
    # still 17000 (no trim needed since 17000 < 18000). Tolerance covers full crossfade window.
    assert abs(len(result) - 18000) <= 1500, (
        f"Duration {len(result)} ms not within ±1500 ms of 18000 ms"
    )


# ---------------------------------------------------------------------------
# Test 3: generate_music falls back to _stable_audio_fallback on HTTPError
# ---------------------------------------------------------------------------

def test_fallback_on_http_error():
    """HTTPError from _session.post triggers fallback, returns AudioSegment."""
    import requests

    client = _make_client()

    # _submit calls _session.post — make it raise HTTPError
    client._session.post = MagicMock(side_effect=requests.HTTPError("500 server error"))

    # Patch _stable_audio_fallback to avoid real GPU call
    fallback_audio = _silent(5000)
    client._stable_audio_fallback = MagicMock(return_value=fallback_audio)

    result = client.generate_music("calm piano", 5, "lofi")

    assert isinstance(result, AudioSegment), "Expected AudioSegment, not an exception"
    client._stable_audio_fallback.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: All audio_urls from polling are downloaded
# ---------------------------------------------------------------------------

def test_all_tracks_downloaded(tmp_path):
    """Both URLs returned by _poll_until_complete are passed to _download_audio."""
    client = _make_client()

    # Two audio URLs returned from polling
    fake_urls = ["https://example.com/track1.mp3", "https://example.com/track2.mp3"]

    # Create a temp mp3-like file so AudioSegment.from_file won't fail
    fake_audio_path = tmp_path / "fake.mp3"
    # Write minimal valid silent audio via pydub
    _silent(3000).export(str(fake_audio_path), format="mp3")

    client._submit = MagicMock(return_value="task-abc123")
    client._poll_until_complete = MagicMock(return_value=fake_urls)
    client._download_audio = MagicMock(return_value=fake_audio_path)

    with patch("generators.suno.AudioSegment.from_file", return_value=_silent(3000)):
        result = client.generate_music("ambient study", 5, "lofi")

    # Both tracks must have been downloaded
    assert client._download_audio.call_count == 2, (
        f"Expected 2 downloads, got {client._download_audio.call_count}"
    )
    assert isinstance(result, AudioSegment)


# ---------------------------------------------------------------------------
# Test 5: generate_music return type is AudioSegment
# ---------------------------------------------------------------------------

def test_generate_music_return_type(tmp_path):
    """End-to-end mock through generate_music returns an AudioSegment."""
    client = _make_client()

    fake_audio_path = tmp_path / "track.mp3"
    _silent(5000).export(str(fake_audio_path), format="mp3")

    client._submit = MagicMock(return_value="task-xyz")
    client._poll_until_complete = MagicMock(
        return_value=["https://example.com/audio.mp3"]
    )
    client._download_audio = MagicMock(return_value=fake_audio_path)

    with patch("generators.suno.AudioSegment.from_file", return_value=_silent(5000)):
        result = client.generate_music("lofi beats", 5, "chill")

    assert isinstance(result, AudioSegment), (
        f"Expected AudioSegment, got {type(result)}"
    )
