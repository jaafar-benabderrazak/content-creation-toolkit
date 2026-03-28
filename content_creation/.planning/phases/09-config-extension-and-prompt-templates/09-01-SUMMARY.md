---
phase: 09-config-extension-and-prompt-templates
plan: 01
subsystem: config
tags: [pydantic, sdxl, suno, pipeline-config, quality-preset, validation]

# Dependency graph
requires:
  - phase: 08-the-compilation-via-remotion-should-be-top-notch
    provides: Completed Remotion pipeline with profile system — config schema evolution base
provides:
  - SDXLSettings Pydantic sub-model with required negative_prompt, steps, guidance_scale, width, height, enable_refiner, quality_suffix
  - SunoSettings Pydantic sub-model with required genre, make_instrumental, track_count, model_version, api_key (env-loaded)
  - PipelineConfig.sdxl and .suno Optional fields (backward compat)
  - _apply_quality_preset model_validator: single quality_preset drives SDXL steps/guidance and Suno model_version simultaneously
affects:
  - phase-10-sdxl-generator-extraction (imports SDXLSettings for cache key design)
  - phase-11-suno-integration (imports SunoSettings for client instantiation)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pydantic model_validator(mode='after') for cross-model preset propagation
    - Required fields with no defaults for mandatory profile YAML fields (PRMT-02 enforcement)
    - Optional sub-model fields on PipelineConfig for backward compatibility with pre-v1.1 profiles
    - Env var loading inside model_validator to avoid hardcoding secrets

key-files:
  created: []
  modified:
    - config/pipeline_config.py

key-decisions:
  - "SDXLSettings.steps is set by quality_preset validator on PipelineConfig, not by a field default — keeps sub-model stateless and preset logic centralized"
  - "Both SDXLSettings.negative_prompt and SunoSettings.genre have no default — ValidationError on omission enforces PRMT-02 at schema load time, before any generator runs"
  - "sdxl/suno fields on PipelineConfig are Optional so all pre-Phase-9 YAML profiles load without modification"
  - "SunoSettings.api_key loaded from SUNO_API_KEY env var inside model_validator — never hardcoded, never required in YAML"

patterns-established:
  - "Preset map pattern: dict keyed by quality_preset string, each value overrides multiple sub-model fields atomically"
  - "Required-field-no-default pattern: enforce mandatory YAML keys at schema level rather than at generator runtime"

requirements-completed: [CFGX-01, CFGX-02, CFGX-03]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 9 Plan 01: Config Extension and Prompt Templates Summary

**SDXLSettings and SunoSettings Pydantic sub-models added to PipelineConfig — quality_preset drives steps, guidance_scale, and Suno model_version atomically via a single model_validator**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T17:38:25Z
- **Completed:** 2026-03-28T17:40:35Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- SDXLSettings sub-model with required `negative_prompt`, typed field bounds (steps 1-150, guidance 1.0-20.0, width/height 512-2048), and `quality_suffix` for prompt augmentation
- SunoSettings sub-model with required `genre`, `make_instrumental`, `track_count`, `model_version`, and env-var-loaded `api_key`
- `_apply_quality_preset` model_validator on PipelineConfig applies high/medium/fast preset values to both sub-models in one pass — ensures sdxl.steps and suno.model_version are always consistent with video.quality_preset
- All three existing profile YAMLs (lofi_study, cinematic, tech_tutorial) load without errors

## Task Commits

1. **Task 1: Add SDXLSettings sub-model** - `4490565` (feat)
2. **Task 2: Add SunoSettings and wire into PipelineConfig** - `ef8c2e3` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `config/pipeline_config.py` - Added SDXLSettings, SunoSettings, sdxl/suno fields on PipelineConfig, _apply_quality_preset model_validator, model_validator import

## Decisions Made

- quality_preset validator lives on PipelineConfig (not SDXLSettings) — only PipelineConfig has access to both video.quality_preset and the sdxl/suno sub-models simultaneously
- Required fields with no defaults enforce YAML compliance at config load time — catches misconfigured profiles before any expensive generator is invoked
- Pydantic v2 model_validator(mode='after') used throughout — project is on Pydantic 2.12.5

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Cinematic profile YAML contained `positive_prompt` and `scene_templates` fields not present in SDXLSettings — Pydantic v2 ignores extra fields by default, so this loaded cleanly without any model change required.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `SDXLSettings` and `SunoSettings` are importable from `config.pipeline_config` — Phase 10 cache key design can SHA-256 hash the fully-resolved SDXLSettings dict
- `SunoSettings` schema is stable — Phase 11 SunoClient instantiation can reference `suno.genre`, `suno.model_version`, `suno.track_count`, `suno.api_key` directly
- No blockers

---
*Phase: 09-config-extension-and-prompt-templates*
*Completed: 2026-03-28*
