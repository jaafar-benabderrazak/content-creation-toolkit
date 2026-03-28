---
phase: 16-smart-defaults
plan: 01
subsystem: config
tags: [pydantic, env-vars, config, pipeline, provenance]

# Dependency graph
requires:
  - phase: 09-config-extension-and-prompt-templates
    provides: PipelineConfig with NotifySettings and SunoSettings models
provides:
  - ENV_VAR_MAP constant mapping dotted field paths to env var names
  - load_with_env_defaults classmethod on PipelineConfig
  - Provenance dict tracking "env" vs "yaml" source for each mapped field
affects: [17-channel-branding, 18-ai-prompt-generation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Env-var fallback pattern: YAML always wins; env fills only None/empty fields"
    - "Provenance tracking: dict[str, Literal['env','yaml']] returned alongside config"
    - "model_copy(update=...) for mutating frozen Pydantic v2 sub-models"
    - "Raw YAML pre-read to determine provenance before model validator runs"

key-files:
  created: []
  modified:
    - config/pipeline_config.py

key-decisions:
  - "Only map fields that exist in the Pydantic schema — OPENAI_API_KEY and REPLICATE_API_TOKEN have no PipelineConfig fields; excluded from ENV_VAR_MAP"
  - "suno.api_key provenance determined from raw YAML dict before model construction because the existing model validator injects the env value automatically"
  - "Pydantic v1 fallback (.copy) kept alongside v2 (.model_copy) for compatibility"

patterns-established:
  - "ENV_VAR_MAP: module-level constant — add entries here when new credential fields are added to the Pydantic schema"
  - "load_with_env_defaults: preferred load path for runtime code that needs env pre-fill; from_yaml remains for tests and tools that don't"

requirements-completed: [DFLT-01]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 16 Plan 01: Smart Defaults — Env Var Fallback Loading Summary

**PipelineConfig.load_with_env_defaults classmethod with ENV_VAR_MAP and provenance tracking: YAML wins over env, fills None/empty fields from NOTF_DISCORD_WEBHOOK_URL, NOTF_SLACK_WEBHOOK_URL, SUNO_API_KEY**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T10:30:06Z
- **Completed:** 2026-03-28T10:32:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `ENV_VAR_MAP` module-level constant covering the three credential fields that exist in PipelineConfig
- Implemented `load_with_env_defaults(path)` classmethod returning `(PipelineConfig, dict[str, str])` tuple
- YAML precedence enforced: non-null YAML values are never overwritten by env vars
- Provenance dict records "env" or "yaml" for every key in ENV_VAR_MAP
- `suno.api_key` provenance handled correctly via raw YAML pre-read (model validator runs before our loop)
- Pydantic v1/v2 fallbacks in place for both `.model_copy` and `.copy`

## Task Commits

1. **Task 1: Add ENV_VAR_MAP and load_with_env_defaults to PipelineConfig** - `0e51579` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `config/pipeline_config.py` - Added `import os`, `ENV_VAR_MAP` constant, `load_with_env_defaults` classmethod

## Decisions Made
- OPENAI_API_KEY and REPLICATE_API_TOKEN excluded from ENV_VAR_MAP — no corresponding PipelineConfig fields exist; inventing fields would violate schema correctness
- suno.api_key provenance uses raw YAML comparison before model construction because `_load_api_key_from_env` validator already injects env value during `from_yaml`; checking after construction would always see a filled value when env var is set

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `load_with_env_defaults` is the stable load path for Phase 17 channel branding (needs YOUTUBE_API_KEY or similar future fields)
- Provenance dict available for debug logging / CLI --dry-run output in later phases
- ENV_VAR_MAP is the single place to add new credential field mappings as schema grows

---
*Phase: 16-smart-defaults*
*Completed: 2026-03-28*
