---
phase: 18-ai-prompt-generation
plan: 01
subsystem: api
tags: [openai, sdxl, suno, prompt-engineering, gpt-4o-mini]

requires:
  - phase: 17-channel-branding
    provides: BrandingSettings and profile YAML structure including video.style_prompt

provides:
  - PromptGenerator class with generate(tags, profile_style) returning structured dict
  - PromptGenerationError exception for all OpenAI and validation failures
  - _build_profile_style() staticmethod for reading video.style_prompt from PipelineConfig

affects:
  - study_with_me_generator.py (caller that writes result to YAML)
  - any future phase that consumes positive_prompt, negative_prompt, scene_templates, music_prompt

tech-stack:
  added: [openai>=1.0 (client-style, not legacy ChatCompletion)]
  patterns:
    - OpenAI json_object response_format for structured generation
    - PromptGenerationError wraps all upstream exceptions for clean caller interface
    - TYPE_CHECKING guard keeps PipelineConfig import out of module-level execution

key-files:
  created: [generators/prompt_generator.py]
  modified: []

key-decisions:
  - "No module-level side effects — PromptGenerator instantiation is the API key check point, not import time"
  - "scene_templates count validated exactly at 8 — raises PromptGenerationError with actual count if wrong"
  - "All OpenAI exceptions caught and re-raised as PromptGenerationError — callers only handle one exception type"

patterns-established:
  - "PromptGenerator._build_profile_style() as the canonical accessor for video.style_prompt — callers never read config fields directly"
  - "json_object response_format + explicit key validation — two-layer contract with OpenAI"

requirements-completed: [AGEN-01, AGEN-02, AGEN-03, AGEN-04]

duration: 1min
completed: 2026-03-28
---

# Phase 18 Plan 01: AI Prompt Generation Summary

**OpenAI-backed PromptGenerator that converts tags + profile style into SDXL positive/negative prompts, 8 scene templates, and a Suno music prompt via gpt-4o-mini with json_object enforcement**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-28T23:35:01Z
- **Completed:** 2026-03-28T23:36:01Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `generators/prompt_generator.py` with `PromptGenerator` class and `PromptGenerationError`
- `generate()` builds two-part prompt (system + user), calls OpenAI with `response_format={"type": "json_object"}`, validates all 4 required keys and exactly 8 scene_templates
- `_build_profile_style()` staticmethod provides canonical access to `video.style_prompt` from PipelineConfig
- Zero module-level side effects — safe to import without any credentials present

## Task Commits

Each task was committed atomically:

1. **Task 1: Create generators/prompt_generator.py with PromptGenerator and PromptGenerationError** - `2b2379e` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `generators/prompt_generator.py` - PromptGenerator class, PromptGenerationError, generate() method, _build_profile_style() staticmethod

## Decisions Made
- No module-level side effects: the API key check happens at `__init__`, not at import time, so the module is safe to import in any context including testing
- All OpenAI exceptions wrapped as PromptGenerationError — callers only need to handle one exception type regardless of upstream failure mode
- scene_templates validated for exactly 8 items with count reported in the error message for debugging

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required beyond `OPENAI_API_KEY` already documented in existing env var setup.

## Next Phase Readiness
- `PromptGenerator.generate()` ready for consumption by `study_with_me_generator.py`
- Callers pass `tags` (user input) and `profile_style` (from `PromptGenerator._build_profile_style(config)`)
- Write returned dict keys directly to YAML for downstream SDXL and Suno consumers

---
*Phase: 18-ai-prompt-generation*
*Completed: 2026-03-28*

## Self-Check: PASSED

- generators/prompt_generator.py: FOUND
- Commit 2b2379e: FOUND
