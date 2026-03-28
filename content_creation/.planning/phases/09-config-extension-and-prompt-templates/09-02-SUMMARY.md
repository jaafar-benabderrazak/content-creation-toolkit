---
phase: 09-config-extension-and-prompt-templates
plan: 02
subsystem: config
tags: [yaml, sdxl, suno, profiles, prompt-templates]

# Dependency graph
requires:
  - phase: 09-config-extension-and-prompt-templates
    provides: SDXLSettings and SunoSettings Pydantic sub-models (Plan 09-01)

provides:
  - lofi_study.yaml with sdxl block (negative_prompt, positive_prompt, scene_templates) and suno block
  - cinematic.yaml with sdxl block and suno block
  - tech_tutorial.yaml with sdxl block and suno block
  - Per-profile SDXL negative prompts: 7 SDXL-optimized style-deviation terms each
  - Per-profile Suno genre mapping: lofi chill, orchestral cinematic, upbeat electronic
  - scene_templates with {weather}/{time_of_day} placeholders for PromptTemplate.render() in Plan 09-03

affects:
  - 09-03-prompt-template-renderer
  - 10-sdxl-extraction
  - 11-suno-integration

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SDXL negative prompts: short (7 terms), style-focused, per-profile — no shared mega-list"
    - "scene_templates use {positive_prompt}, {weather}, {time_of_day} as PromptTemplate variables"
    - "suno block contains genre, prompt_tags, make_instrumental: true, track_count: 2"
    - "tech_tutorial omits {weather}/{time_of_day} in scene_templates — consistent with enable_weather: false"

key-files:
  created: []
  modified:
    - config/profiles/lofi_study.yaml
    - config/profiles/cinematic.yaml
    - config/profiles/tech_tutorial.yaml

key-decisions:
  - "SDXL negative prompts capped at 7 terms per profile — SD1.5 mega-lists degrade SDXL output (v1.1 Research decision)"
  - "tech_tutorial scene_templates contain no {weather}/{time_of_day} variables — consistent with enable_weather: false in existing profile"
  - "track_count: 2 on all profiles — generate 2 Suno tracks, use best (per SUNO-05)"

patterns-established:
  - "Profile YAML is single source of truth for SDXL and Suno generation parameters — no hardcoded prompts in Python source"
  - "scene_templates act as PromptTemplate strings — PromptTemplate.render() resolves {positive_prompt}, {weather}, {time_of_day} at runtime"
  - "make_instrumental: true is mandatory on all profiles — vocal bleed is unacceptable in study/ambient content"

requirements-completed: [PRMT-01, PRMT-02, PRMT-03]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 9 Plan 02: Config Extension and Prompt Templates — Profile SDXL/Suno Blocks Summary

**Per-profile SDXL prompt blocks and Suno genre blocks added to all three YAMLs — profiles are now the single source of truth for generation parameters, eliminating hardcoded prompt strings from Python source**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-28T17:38:29Z
- **Completed:** 2026-03-28T17:39:40Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added sdxl and suno blocks to lofi_study.yaml: 7-term negative prompt, 3 scene_templates with {weather}/{time_of_day}, suno genre "lofi chill"
- Added sdxl and suno blocks to cinematic.yaml: 7-term negative prompt targeting style deviations, suno genre "orchestral cinematic"
- Added sdxl and suno blocks to tech_tutorial.yaml: 7-term negative prompt targeting environment issues, scene_templates without weather/time variables (consistent with enable_weather: false)

## Task Commits

1. **Task 1: Add sdxl and suno blocks to lofi_study.yaml** - `739ee0e` (feat)
2. **Task 2: Add sdxl and suno blocks to cinematic.yaml and tech_tutorial.yaml** - `7081025` (feat)

## Files Created/Modified

- `config/profiles/lofi_study.yaml` - Added sdxl block (negative_prompt, positive_prompt, scene_templates) and suno block
- `config/profiles/cinematic.yaml` - Added sdxl block and suno block
- `config/profiles/tech_tutorial.yaml` - Added sdxl block (no weather/time vars) and suno block

## Decisions Made

- SDXL negative prompts kept at exactly 7 terms per profile — SDXL performs worse with SD1.5-style mega-lists (established in v1.1 Research)
- tech_tutorial scene_templates deliberately omit {weather} and {time_of_day} — the profile already has enable_weather: false, keeping templates consistent
- make_instrumental: true set on all profiles — vocal bleed is unacceptable for study/ambient/tutorial content

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three profile YAMLs now contain sdxl and suno blocks; Plan 09-03 (PromptTemplate renderer) can safely import and render scene_templates
- SDXLSettings/SunoSettings Pydantic sub-models (Plan 09-01) will validate these blocks at load time once integrated
- Plan 10 (SDXL extraction) can use sdxl.negative_prompt and sdxl.positive_prompt from profiles — no hardcoded strings needed

---
*Phase: 09-config-extension-and-prompt-templates*
*Completed: 2026-03-28*
