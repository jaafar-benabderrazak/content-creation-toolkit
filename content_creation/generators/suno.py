"""SunoClient — REST-based music generation with polling, stitching, and Stable Audio fallback.

Follows the same boundary pattern as SDXLGenerator: SunoSettings is injected as a typed
argument; no direct import of pipeline_config at class level beyond the type hint.
"""
from __future__ import annotations

import logging
import math
import os
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, List

import requests
from pydub import AudioSegment

if TYPE_CHECKING:
    from config.pipeline_config import SunoSettings

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

SUNO_BASE_URL = os.environ.get("SUNO_BASE_URL", "https://api.sunoapi.org")
SUNO_MAX_TRACK_SECONDS = 240   # conservative; actual Suno v5 max ~4 min
POLL_INITIAL_WAIT = 5          # seconds
POLL_MAX_WAIT = 60             # cap for exponential backoff
POLL_HARD_TIMEOUT = 300        # seconds — total wall-clock limit


# ---------------------------------------------------------------------------
# SunoClient
# ---------------------------------------------------------------------------

class SunoClient:
    """REST client for async Suno music generation.

    Submits generation tasks, polls with exponential backoff (hard 300 s timeout),
    downloads all generated tracks, stitches them for long durations, and falls
    back to Stable Audio on any failure.

    Parameters
    ----------
    suno_cfg:
        SunoSettings instance (already resolved from PipelineConfig).
    """

    def __init__(self, suno_cfg: "SunoSettings") -> None:
        if suno_cfg.api_key is None:
            raise ValueError(
                "SUNO_API_KEY is not set. Set the environment variable or pass "
                "api_key directly in SunoSettings."
            )
        self.suno_cfg = suno_cfg
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {suno_cfg.api_key}",
                "Content-Type": "application/json",
            }
        )
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_music(
        self, prompt: str, duration_seconds: int, genre: str
    ) -> AudioSegment:
        """Generate music for the given prompt and return a pydub AudioSegment.

        Handles multi-track stitching when duration exceeds SUNO_MAX_TRACK_SECONDS.
        Falls back to Stable Audio on any failure — never raises.

        Parameters
        ----------
        prompt:
            Descriptive music prompt (style / mood / instruments).
        duration_seconds:
            Target duration in seconds.
        genre:
            Genre tag prepended to prompt (e.g. ``"lofi chill"``).

        Returns
        -------
        AudioSegment
            Audio segment covering the full requested duration.
        """
        try:
            target_ms = duration_seconds * 1000

            if duration_seconds > SUNO_MAX_TRACK_SECONDS:
                n_tracks = math.ceil(duration_seconds / SUNO_MAX_TRACK_SECONDS)
                chunk_seconds = math.ceil(duration_seconds / n_tracks)
                task_ids: List[str] = [
                    self._submit(prompt, chunk_seconds, genre)
                    for _ in range(n_tracks)
                ]
            else:
                task_ids = [self._submit(prompt, duration_seconds, genre)]

            audio_urls: List[str] = []
            for task_id in task_ids:
                # _poll_until_complete returns all audio_urls for a task
                urls = self._poll_until_complete(task_id)
                audio_urls.extend(urls)

            segments: List[AudioSegment] = []
            for url in audio_urls:
                path = self._download_audio(url)
                segments.append(AudioSegment.from_file(str(path)))

            return self._stitch_tracks(segments, target_ms)

        except Exception as e:  # noqa: BLE001 — catches TimeoutError, HTTPError, RuntimeError, etc.
            logging.warning("[Suno] Fallback triggered: %s", e)
            return self._stable_audio_fallback(prompt, duration_seconds)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _submit(self, prompt: str, duration: int, genre: str) -> str:
        """POST a generation request and return task_id.

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response.
        """
        payload = {
            "prompt": f"{genre} {prompt}",
            "make_instrumental": self.suno_cfg.make_instrumental,
            "duration": duration,
            "mv": self.suno_cfg.model_version,
            # Field name per sunoapi.org docs — may differ on kie.ai
            "count": self.suno_cfg.track_count,
        }
        resp = self._session.post(f"{SUNO_BASE_URL}/api/v1/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["task_id"]  # Field name per sunoapi.org docs

    def _poll_until_complete(self, task_id: str) -> List[str]:
        """Poll until the task completes or POLL_HARD_TIMEOUT is exceeded.

        Returns
        -------
        list[str]
            All audio_urls from the completed task's data list.

        Raises
        ------
        RuntimeError
            If Suno reports a task error status.
        TimeoutError
            If polling exceeds POLL_HARD_TIMEOUT seconds.
        """
        wait = POLL_INITIAL_WAIT
        elapsed = 0
        while elapsed < POLL_HARD_TIMEOUT:
            resp = self._session.get(f"{SUNO_BASE_URL}/api/v1/task/{task_id}")
            data = resp.json()
            status = data.get("status", "")
            if status == "completed":
                # Field names per sunoapi.org docs — may differ on kie.ai
                return [track["audio_url"] for track in data.get("data", [])]
            if status == "error":
                raise RuntimeError(f"Suno task failed: {data}")
            self.logger.info(
                "[Suno] Polling task %s... status=%s elapsed=%ds",
                task_id[:8],
                status,
                elapsed,
            )
            time.sleep(wait)
            elapsed += wait
            wait = min(wait * 2, POLL_MAX_WAIT)
        raise TimeoutError(
            f"Suno task {task_id} exceeded {POLL_HARD_TIMEOUT}s timeout"
        )

    def _download_audio(self, url: str) -> Path:
        """Stream-download audio from url to a temp file.

        Returns
        -------
        Path
            Path to the downloaded MP3 temp file.
        """
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        with self._session.get(url, stream=True) as resp:
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        return tmp_path

    def _stitch_tracks(
        self, segments: List[AudioSegment], target_ms: int
    ) -> AudioSegment:
        """Concatenate all segments with 3000 ms crossfade and trim to target_ms.

        Parameters
        ----------
        segments:
            One or more AudioSegment objects in order.
        target_ms:
            Exact target duration in milliseconds.

        Returns
        -------
        AudioSegment
            Stitched (and trimmed) audio.
        """
        if not segments:
            return AudioSegment.silent(duration=target_ms)

        track = segments[0]
        for seg in segments[1:]:
            track = track.append(seg, crossfade=3000)

        # Trim to exact target length
        if len(track) > target_ms:
            track = track[:target_ms]

        return track

    def _stable_audio_fallback(
        self, prompt: str, duration_seconds: int
    ) -> AudioSegment:
        """Generate audio via Stable Audio as a fallback.

        Returns silent AudioSegment when stable_audio_tools is not installed.

        Parameters
        ----------
        prompt:
            Music generation prompt passed through to stable_audio_tools.
        duration_seconds:
            Target duration in seconds.

        Returns
        -------
        AudioSegment
            Generated (or silent) audio covering the full duration.
        """
        try:
            import io

            import torch
            import torchaudio
            from einops import rearrange
            from stable_audio_tools import get_pretrained_model
            from stable_audio_tools.inference.generation import (
                generate_diffusion_cond,
            )
        except ImportError:
            self.logger.warning(
                "[Suno] stable_audio_tools not installed — returning silent AudioSegment"
            )
            return AudioSegment.silent(duration=duration_seconds * 1000)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info("[Suno Fallback] Using device: %s", device)

        model_name = "stabilityai/stable-audio-open-1.0"
        try:
            model, model_config = get_pretrained_model(model_name)
        except Exception:  # noqa: BLE001
            model_name = "stabilityai/stable-audio-open-small"
            model, model_config = get_pretrained_model(model_name)

        sample_rate = int(model_config["sample_rate"])
        sample_size = int(model_config["sample_size"])
        model = model.to(device)

        segments: List[AudioSegment] = []
        total_generated = 0
        segment_seconds = 47  # stable-audio-open max per inference

        while total_generated < duration_seconds:
            remaining = duration_seconds - total_generated
            chunk_len = min(segment_seconds, remaining + 10)

            conditioning = [{"prompt": prompt, "seconds_total": int(chunk_len)}]

            output = generate_diffusion_cond(
                model,
                steps=100,
                conditioning=conditioning,
                sample_size=sample_size,
                sampler_type="dpmpp-2m-sde",
                device=device,
            )
            output = rearrange(output, "b d n -> d (b n)")
            wav = output.to(torch.float32)
            wav = wav / (torch.max(torch.abs(wav)) + 1e-8) * 0.8
            wav = (wav * 32767.0).clamp(-32767, 32767).to(torch.int16).cpu()

            buf = io.BytesIO()
            torchaudio.save(buf, wav, sample_rate, format="wav")
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="wav")
            segments.append(segment)
            total_generated += chunk_len
            self.logger.info(
                "[Suno Fallback] Generated %d segments (%ds/%ds)",
                len(segments),
                int(total_generated),
                duration_seconds,
            )

        return self._stitch_tracks(segments, duration_seconds * 1000)
