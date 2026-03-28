---
phase: "08-the-compilation-via-remotion-should-be-top-notch"
plan: "04"
subsystem: "shared/remotion_renderer"
tags: [remotion, python, rendering, quality, profiles, audio]
dependency_graph:
  requires: ["08-02", "08-03"]
  provides: ["Python-Remotion bridge with profile-aware quality flags and WAV conversion"]
  affects: ["any Python pipeline call to render_study_video or render_tech_tutorial"]
tech_stack:
  added: []
  patterns: ["profile-based quality resolution", "WAV conversion helper for audio visualization", "TransitionSeries-aware frame count calculation"]
key_files:
  created: []
  modified:
    - shared/remotion_renderer.py
decisions:
  - "_resolve_quality uses lofi-study defaults as fallback for unknown profiles"
  - "WAV conversion caches result on disk (wav_path.exists() check) to avoid re-encoding on re-renders"
  - "On ffmpeg WAV conversion failure, return original path — AudioVisualizer renders null gracefully, no crash"
  - "TransitionSeries overlap subtraction uses per-profile _TRANSITION_DURATION map (cinematic=20, lofi-study=15, tech-tutorial=12)"
metrics:
  duration: "2 min"
  completed: "2026-03-28"
  tasks_completed: 1
  files_modified: 1
---

# Phase 8 Plan 4: Profile-Aware Python-Remotion Bridge Summary

Extended `shared/remotion_renderer.py` to close the Python-TypeScript contract: profile prop forwarded to both compositions, CRF/preset resolved per profile, bt709 color space and AAC audio flags applied to every render, sceneDurations passed with TransitionSeries-aware frame math, and WAV conversion helper added for audio visualization.

## What Was Built

### _resolve_quality() helper
Maps profile names to (crf, x264_preset) tuples. Cinematic gets CRF 16 + slow preset for archival quality. lofi-study and tech-tutorial get CRF 18 + medium. Preview tier gets CRF 28 + veryfast for fast iteration. Unknown profiles fall back to lofi-study defaults.

### _ensure_wav() helper
Converts any audio file to WAV before passing to Remotion's useWindowedAudioData hook. WAV format is required because HTTP Range byte-seeking on MP3 VBR files causes the hook to return null. Caches the .wav output — re-runs skip conversion. Degrades gracefully on ffmpeg failure: returns the original path so AudioVisualizer renders nothing instead of crashing.

### render_study_video() extensions
Three new backward-compatible parameters:
- `profile: str = "lofi-study"` — forwarded to Remotion props and _render()
- `scene_durations: Optional[list[float]] = None` — forwarded as `sceneDurations` prop; when provided, frame count is computed with TransitionSeries overlap subtraction
- `audio_visualization: bool = False` — triggers _ensure_wav() call when True and audio_path is set

### render_tech_tutorial() extension
New `profile: str = "tech-tutorial"` parameter forwarded to props and _render().

### _render() subprocess command
Accepts `profile` parameter. Resolves CRF and x264-preset via _resolve_quality(). Every invocation now includes:
- `--crf` (profile-resolved)
- `--x264-preset` (profile-resolved)
- `--color-space bt709` (correct YouTube/broadcast color space)
- `--audio-codec aac`
- `--audio-bitrate 320k`

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

All checks passed:
- `_resolve_quality('cinematic')` → `(16, 'slow')`
- `_resolve_quality('lofi-study')` → `(18, 'medium')`
- `_resolve_quality('preview')` → `(28, 'veryfast')`
- `render_study_video` signature includes: profile, scene_durations, audio_visualization
- `--color-space bt709`, `--audio-codec aac`, `--x264-preset` present in cmd list

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1    | 00b1ffb | feat(08-04): extend remotion_renderer with profile props, quality flags, WAV helper |

## Self-Check: PASSED
