---
phase: 16-smart-defaults
plan: 03
subsystem: infra
tags: [pydantic, yaml, env-vars, cli, pipeline-config, setup]

# Dependency graph
requires:
  - phase: 09-config-extension
    provides: PipelineConfig with to_yaml/from_yaml, NotifySettings, SunoSettings

provides:
  - setup.py CLI that scans KNOWN_ENV_VARS and writes config/profiles/starter.yaml
  - KNOWN_ENV_VARS constant mapping 6 env vars to dotted PipelineConfig fields
  - --force flag for safe re-runs on existing files

affects:
  - 16-smart-defaults (downstream plans that need credentials pre-filled)
  - 17-channel-branding (BRND API keys sourced via this setup flow)
  - 18-ai-prompt-generation (OPENAI_API_KEY noted in KNOWN_ENV_VARS)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dotted-field injection: 'notify.discord_webhook_url' parsed and applied via model_copy chain"
    - "Optional section guard: _inject_field silently skips None sections (suno=None default)"
    - "Pydantic v1/v2 dual support: model_copy with copy fallback"

key-files:
  created:
    - setup.py
  modified: []

key-decisions:
  - "KNOWN_ENV_VARS is a list of dicts (not a dict) to preserve declaration order in printed output"
  - "Sections that are None (suno=None) silently skip injection — no partial initialisation of required-field models"
  - "Exit code 0 always — missing vars are informational, not errors"
  - "Warning on existing file printed to stderr, not stdout, to keep output clean for piping"

patterns-established:
  - "KNOWN_ENV_VARS pattern: centralised registry of all pipeline credentials with field paths and human descriptions"
  - "_inject_field helper: dotted-path injection into nested Pydantic models without modifying the model class"

requirements-completed: [DFLT-03]

# Metrics
duration: 1min
completed: 2026-03-28
---

# Phase 16 Plan 03: Smart Defaults Summary

**setup.py first-run CLI that scans 6 known env vars and writes a PipelineConfig-valid starter YAML with credentials pre-filled and missing vars listed**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-28T22:50:12Z
- **Completed:** 2026-03-28T22:51:56Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- setup.py CLI scans NOTF_DISCORD_WEBHOOK_URL, NOTF_SLACK_WEBHOOK_URL, SUNO_API_KEY, OPENAI_API_KEY, REPLICATE_API_TOKEN, YOUTUBE_QUOTA_USED
- Injects found values into PipelineConfig via dotted-field path (e.g. notify.discord_webhook_url)
- Guards against overwrite without --force; writes to --output path with mkdir -p
- Generated YAML passes PipelineConfig.from_yaml() with no validation errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Write setup.py first-run CLI** - `b040e19` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `setup.py` - First-run CLI: env var scanner, PipelineConfig builder, YAML writer, found/missing printer

## Decisions Made

- KNOWN_ENV_VARS uses list-of-dicts (not dict) to preserve insertion order in stdout output
- Sections that are None (suno starts as None since genre has no default) silently skip injection — avoids partial model initialisation with missing required fields
- Exit code 0 always; missing vars are informational only
- Existing-file warning goes to stderr so stdout stays clean for scripting

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. One edge case noted: `suno: Optional[SunoSettings] = None` by default in PipelineConfig; SUNO_API_KEY appears as "found (pre-filled)" in summary output but injection silently skips (section is None). This matches plan intent — the value is shown as found so the user knows the key was detected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- setup.py ready for immediate use on fresh checkouts
- KNOWN_ENV_VARS serves as a single-source registry for all future phases that add credentials
- Phase 16 remaining plans (16-04+) can reference KNOWN_ENV_VARS to add new entries as new env vars are introduced

---
*Phase: 16-smart-defaults*
*Completed: 2026-03-28*
