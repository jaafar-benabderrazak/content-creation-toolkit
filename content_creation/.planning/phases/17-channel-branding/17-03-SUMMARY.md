---
phase: 17-channel-branding
plan: "03"
subsystem: video-processing
tags: [ffmpeg, branding, video, lavfi, drawtext, overlay, subprocess]

requires:
  - phase: 17-01
    provides: BrandingData dataclass with channel_name, tagline, avatar_local_path fields

provides:
  - shared/branding_clips.py with generate_intro_clip(), generate_outro_clip(), generate_branding_clips()
  - FFmpeg lavfi compositing for black-background intro/outro MP4 clips from BrandingData
  - Conditional avatar overlay — renders text-only cleanly when avatar file absent

affects:
  - post_process.py (intro/outro concatenation can now call generate_branding_clips instead of requiring supplied files)
  - any pipeline step that assembles branding_enabled=True output

tech-stack:
  added: []
  patterns:
    - "FFmpeg filter_complex with [1:v]scale/overlay + drawtext chain for image+text compositing"
    - "Avatar-present vs avatar-absent branching for simpler FFmpeg command construction"
    - "_run_ffmpeg helper mirrored from post_process.py (copy, not import) to keep module self-contained"
    - "Lazy subprocess import inside _run_ffmpeg — module top-level has only logging and pathlib"

key-files:
  created:
    - shared/branding_clips.py
  modified: []

key-decisions:
  - "Avatar branching uses two explicit FFmpeg command builds rather than dynamic filter_complex assembly — clearer, easier to debug"
  - "fade=out uses st= (start time in seconds) not frame-count for outro, matching FFmpeg lavfi behavior"
  - "generate_branding_clips skips existing files — callers control cache invalidation (consistent with 17-01 cache strategy)"
  - "No new pip dependencies — only stdlib subprocess + FFmpeg binary already required by post_process.py"

patterns-established:
  - "BrandingData passed as argument, never imported at module level — keeps branding_clips.py decoupled from branding.py import chain"
  - "fontfile='' yields empty string when no system font found — FFmpeg uses its default font silently"

requirements-completed:
  - BRND-03

duration: 1min
completed: 2026-03-28
---

# Phase 17 Plan 03: Channel Branding Clips Summary

**FFmpeg lavfi intro/outro clip generator from BrandingData — black-bg, drawtext channel name/tagline, conditional avatar overlay, fade-in/out, no pip deps**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-28T23:21:06Z
- **Completed:** 2026-03-28T23:22:10Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- generate_intro_clip(): 3-second MP4 with channel name + tagline, fade-in, optional centered-top avatar overlay
- generate_outro_clip(): 4-second MP4, same layout, fade-out last 1s, "Thanks for watching!" tagline fallback
- generate_branding_clips(): wrapper returning (intro_path, outro_path), skips existing files
- Clean avatar-absent path — renders text-only without error when avatar file not present

## Task Commits

1. **Task 1: Create shared/branding_clips.py with FFmpeg intro/outro generation** - `cac676b` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `shared/branding_clips.py` - Intro/outro clip generation from BrandingData using FFmpeg lavfi+drawtext+overlay

## Decisions Made
- Avatar branching uses two explicit command builds (with/without avatar) rather than dynamic filter_complex assembly — simpler and easier to debug
- `fade=out` uses `st=` (start time in seconds float) not frame-count for clarity in outro filter
- `generate_branding_clips` skips existing files — consistent with 17-01 cache-first strategy; explicit regeneration is caller responsibility
- No pip dependencies added — FFmpeg binary already required by post_process.py

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- shared/branding_clips.py ready for integration into post_process.py branding_enabled=True path
- Downstream consumers (post_process.py intro/outro concat) can call generate_branding_clips(branding, cache_dir) to obtain clip paths on demand
- No blockers for remaining Phase 17 plans

---
*Phase: 17-channel-branding*
*Completed: 2026-03-28*
