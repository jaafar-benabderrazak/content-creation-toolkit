---
phase: 21-ai-generated-thumbnail-text-youtube-metadata-and-full-prompt-chain-visualization-in-ui
plan: 01
subsystem: api
tags: [prompt-generator, pipeline-config, pydantic, openai, anthropic, youtube-metadata]

# Dependency graph
requires:
  - phase: 18-ai-prompt-generation
    provides: PromptGenerator class with 4-key output contract and PromptGenerationError
provides:
  - PromptGenerator._REQUIRED_KEYS with 8 keys (original 4 + thumbnail_text, youtube_title, youtube_description, youtube_tags)
  - _validate() enforcing youtube_tags is a list of 15-20 items
  - _USER_PROMPT instructing model to generate all 4 new metadata fields
  - PublishSettings.thumbnail_text field (str, default "") YAML-safe
affects:
  - 21-02 (pipeline write-back reads these 8 keys from generate() result)
  - 21-03 (thumbnail compositing reads thumbnail_text from PublishSettings)
  - UI visualization of prompt chain (all 8 keys now available)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level alias _validate = PromptGenerator._validate exposes static method for direct import"
    - "youtube_tags validation enforces exact count range (15-20) not just type — prevents under/over-generation"

key-files:
  created: []
  modified:
    - generators/prompt_generator.py
    - config/pipeline_config.py

key-decisions:
  - "_validate alias at module level: static method exposed as module-level name to match plan's import contract (from generators.prompt_generator import _validate)"
  - "thumbnail_text placed after youtube_tags in PublishSettings — no ENV_VAR_MAP entry needed (generated content, not credential)"
  - "youtube_tags count validation added in _validate() alongside existing scene_templates count check — parallel structure"

patterns-established:
  - "youtube_tags count range 15-20: enforced in _validate(), must be maintained in any provider that writes to this field"
  - "All 4 new metadata fields driven purely by _USER_PROMPT and _REQUIRED_KEYS — no provider-side (_generate_claude / _generate_openai) changes needed"

requirements-completed: [PMETA-01, PMETA-02]

# Metrics
duration: 2min
completed: 2026-03-29
---

# Phase 21 Plan 01: Extend PromptGenerator and PublishSettings for YouTube Metadata Summary

**PromptGenerator extended to 8-key output (adding thumbnail_text, youtube_title, youtube_description, youtube_tags with 15-20 count enforcement), and PublishSettings.thumbnail_text field added for YAML-safe persistence**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-29T12:50:36Z
- **Completed:** 2026-03-29T12:52:36Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Extended _REQUIRED_KEYS from 4 to 8 entries covering all new YouTube metadata fields
- Updated _USER_PROMPT with precise generation instructions for thumbnail_text, youtube_title, youtube_description, youtube_tags
- Added youtube_tags list + count validation (15-20 items) in _validate()
- Added PublishSettings.thumbnail_text: str = "" with full YAML round-trip support

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend PromptGenerator with 4 new metadata output keys** - `956170c` (feat)
2. **Task 2: Add thumbnail_text field to PublishSettings** - `84968fe` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `generators/prompt_generator.py` - 8-key _REQUIRED_KEYS, expanded _USER_PROMPT, youtube_tags validation in _validate(), module-level _validate alias
- `config/pipeline_config.py` - thumbnail_text: str = "" added to PublishSettings after youtube_tags

## Decisions Made
- Module-level `_validate` alias added so plan's exact import contract (`from generators.prompt_generator import _validate`) works without restructuring the class. Zero behavioral change.
- `thumbnail_text` placed after `youtube_tags` in PublishSettings — preserves logical grouping of YouTube fields; no ENV_VAR_MAP entry (generated content, not a credential).
- youtube_tags count validated as range 15-20 (not exact), matching the _USER_PROMPT instruction that says "exactly 15-20 SEO tags".

## Deviations from Plan

None - plan executed exactly as written.

The plan's verify block imported `_validate` directly from the module (`from generators.prompt_generator import _validate`), but the method is defined as a static method on `PromptGenerator`. Added a module-level alias `_validate = PromptGenerator._validate` to satisfy this contract without changing class structure. Counted as plan compliance, not a deviation.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PromptGenerator.generate() now returns 8-key dicts; all downstream consumers expecting the new fields can proceed
- PublishSettings.thumbnail_text exists and round-trips through YAML; pipeline write-back (21-02) can store generated thumbnail_text
- Thumbnail compositing (21-03) can read thumbnail_text from config.publish.thumbnail_text

---
*Phase: 21-ai-generated-thumbnail-text-youtube-metadata-and-full-prompt-chain-visualization-in-ui*
*Completed: 2026-03-29*
