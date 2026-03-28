---
phase: 11-suno-music-integration
plan: 02
subsystem: audio
tags: [suno, music-generation, threading, concurrent-futures, pydub, stable-audio]

requires:
  - phase: 11-01
    provides: SunoClient with polling, stitching, Stable Audio fallback

provides:
  - ThreadPoolExecutor Suno submission wired into study_with_me_generator.py
  - Async Suno music generation overlapped with SDXL image batch (hides 60-180s latency)
  - suno_generation progress.json key for resume capability
  - Stable Audio fallback path preserved when no Suno config or no API key

affects: [study_with_me_generator, pipeline-orchestration, audio-generation]

tech-stack:
  added: [concurrent.futures.ThreadPoolExecutor, concurrent.futures.Future]
  patterns:
    - Submit long-running I/O task in background thread before CPU-bound batch; collect result after batch completes

key-files:
  created: []
  modified:
    - study_with_me_generator.py

key-decisions:
  - "ThreadPoolExecutor(max_workers=1) used directly — no additional library; keeps dependency surface minimal"
  - "_suno_executor.shutdown(wait=False) after audio block — does not block video assembly if future already resolved"

patterns-established:
  - "Step 0 pattern: submit background I/O before the heavy CPU loop (SDXL); collect after loop via future.result()"

requirements-completed: [SUNO-07]

duration: 5min
completed: 2026-03-28
---

# Phase 11 Plan 02: Suno Orchestrator Wiring Summary

**ThreadPoolExecutor wiring submits Suno generation before SDXL batch, collecting result after images complete — hiding Suno's 60-180s latency behind image generation time**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T18:17:00Z
- **Completed:** 2026-03-28T18:22:14Z
- **Tasks:** 1 (+ 1 checkpoint auto-approved in YOLO mode)
- **Files modified:** 1

## Accomplishments
- Step 0 block submits `SunoClient.generate_music` to `ThreadPoolExecutor` before the SDXL image generation loop
- Step 2 audio block collects `_suno_future.result()` after image loop; blocks only for remaining Suno time (usually zero)
- Stable Audio fallback path unchanged — triggered when `_suno_cfg` is None or `api_key` is unset
- `suno_generation` key written to progress.json recording source (`suno` vs `stable_audio`) and duration
- `_suno_executor.shutdown(wait=False)` releases thread after audio block without delaying video assembly

## Task Commits

1. **Task 1: ThreadPoolExecutor Suno submission before SDXL batch** - `d5f33ce` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `study_with_me_generator.py` — Added imports, Step 0 Suno submission block, updated Step 2 audio resolution, executor cleanup

## Decisions Made
- `ThreadPoolExecutor(max_workers=1)` chosen over `asyncio` — orchestrator is synchronous; no event loop in scope
- `shutdown(wait=False)` after audio block — future is already resolved at that point; avoids spurious blocking

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Verification script used default encoding on Windows (cp1252); added `encoding='utf-8'` to `open()` calls in verification. Not a code issue — test runner quirk on Windows.

## User Setup Required
None - no external service configuration required.
Set `SUNO_API_KEY` environment variable to activate Suno path at runtime; without it the Stable Audio fallback runs transparently.

## Next Phase Readiness
- Phase 11 complete: SunoClient (11-01) + orchestrator wiring (11-02) both committed
- Suno path activates automatically when `suno:` block present in YAML config and `SUNO_API_KEY` is set
- Full pipeline dry-run (`python study_with_me_generator.py --dry-run --minutes 5`) verifies import chain end-to-end

---
*Phase: 11-suno-music-integration*
*Completed: 2026-03-28*
