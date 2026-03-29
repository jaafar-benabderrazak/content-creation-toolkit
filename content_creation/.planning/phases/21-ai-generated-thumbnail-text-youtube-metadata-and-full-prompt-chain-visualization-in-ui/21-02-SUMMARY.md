---
phase: 21-ai-generated-thumbnail-text-youtube-metadata-and-full-prompt-chain-visualization-in-ui
plan: 02
subsystem: pipeline, ui
tags: [yaml, gradio, prompt-chain, youtube-metadata, publish-settings]

# Dependency graph
requires:
  - phase: 21-01
    provides: PromptGenerator 8-key output (thumbnail_text, youtube_title, youtube_description, youtube_tags) and PublishSettings.thumbnail_text field

provides:
  - _run_prompt_generation writes publish.thumbnail_text, publish.youtube_title, publish.youtube_description, publish.youtube_tags to YAML after AI call
  - preview_prompts() shows Publish Metadata (saved) section from loaded config
  - preview_prompts() shows AI Thumbnail Text, AI YouTube Title, AI YouTube Description, AI YouTube Tags after AI generation

affects: [pipeline_runner, gradio_app, 21-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "publish block write-back follows same guard pattern as sdxl/suno blocks: check None, mutate, yaml.dump(sort_keys=False)"
    - "preview_prompts sections are purely additive: new rows appended inside existing try blocks, no structural change"

key-files:
  created: []
  modified:
    - study_with_me_generator.py
    - gradio_app.py

key-decisions:
  - "No new decisions — publish write-back uses yaml.safe_load → mutate → yaml.dump(sort_keys=False) per Phase 18-02 decision"

patterns-established:
  - "Publish metadata display in preview_prompts: saved section always shown (when config loads), AI section shown only when tags trigger generation"

requirements-completed: [PMETA-03, PMETA-04]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 21 Plan 02: Publish Metadata YAML Write-back and Full Prompt Chain Visualization Summary

**YAML write-back of 4 publish fields (thumbnail_text, youtube_title, youtube_description, youtube_tags) from AI response, and 7-section prompt chain display in Gradio preview_prompts**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T09:35:38Z
- **Completed:** 2026-03-28T09:37:38Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `_run_prompt_generation` now writes all 4 publish metadata fields to the profile YAML after a successful AI call, alongside the existing sdxl and suno write-backs
- `preview_prompts()` in Gradio shows a "Publish Metadata (saved)" section with thumbnail_text, youtube_title, youtube_description (truncated at 100 chars), and youtube_tags count when a valid config is loaded
- `preview_prompts()` appends AI Thumbnail Text, AI YouTube Title, AI YouTube Description, and AI YouTube Tags rows after the existing AI scene rows when tags are provided and generation succeeds

## Task Commits

1. **Task 1: Write new metadata fields to YAML in _run_prompt_generation** - `cae6066` (feat)
2. **Task 2: Show full 7-section prompt chain in preview_prompts** - `42a297c` (feat)

## Files Created/Modified
- `study_with_me_generator.py` - Added publish block write-back (thumbnail_text, youtube_title, youtube_description, youtube_tags) after suno block; extended print summary with 3 new log lines
- `gradio_app.py` - Added Publish Metadata (saved) section after suno rows in saved-config block; added 4 AI metadata rows after AI scene loop

## Decisions Made
None - followed plan as specified. Publish write-back uses established Phase 18-02 yaml.safe_load → mutate → yaml.dump(sort_keys=False) pattern.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
Pre-existing: `configs/last_run.yaml` fails `PipelineConfig.from_yaml()` due to missing `suno.genre` field — unrelated to this plan. The publish metadata section is correctly gated inside the same `try/except` as other profile fields. Scene Templates section (separate raw yaml.safe_load path) still displays correctly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- publish.thumbnail_text, publish.youtube_title, publish.youtube_description, youtube_tags are now written to YAML after AI generation — pipeline_runner.py can read them in Plan 21-03
- Gradio UI shows complete 7-section prompt chain for pre-launch review

---
*Phase: 21-ai-generated-thumbnail-text-youtube-metadata-and-full-prompt-chain-visualization-in-ui*
*Completed: 2026-03-28*
