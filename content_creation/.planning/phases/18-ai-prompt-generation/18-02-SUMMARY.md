---
phase: 18-ai-prompt-generation
plan: 02
subsystem: api
tags: [openai, yaml, argparse, sdxl, suno, prompt-generation]

# Dependency graph
requires:
  - phase: 18-01
    provides: PromptGenerator.generate() and PromptGenerationError
provides:
  - "--tags CLI flag in study_with_me_generator.py"
  - "_run_prompt_generation() writes SDXL+Suno prompts to profile YAML before image generation"
  - "cinematic.yaml sdxl.positive_prompt field verified present"
affects: [study_with_me_generator, config/profiles, generators/prompt_generator]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy import inside function body — avoid module-level import cost for optional features"
    - "YAML write-back pattern: safe_load → mutate dict → dump with sort_keys=False"
    - "Graceful degradation: PromptGenerationError caught, warning printed, pipeline continues"

key-files:
  created: []
  modified:
    - study_with_me_generator.py
    - config/profiles/cinematic.yaml (verified, no change needed)

key-decisions:
  - "Lazy imports of yaml and generators.prompt_generator inside _run_prompt_generation — zero overhead when --tags is not used"
  - "PromptGenerationError is the single catch surface — callers never handle raw OpenAI exceptions"
  - "cinematic.yaml positive_prompt was already present from prior phase — Task 2 was a verification pass only"

patterns-established:
  - "Prompt generation hook: call _run_prompt_generation before SDXLGenerator.generate_batch(), after config load"
  - "YAML write-back: read raw with yaml.safe_load, mutate, write with yaml.dump(sort_keys=False)"

requirements-completed: [AGEN-04, AGEN-05]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 18 Plan 02: AI Prompt Generation Wire-Up Summary

**--tags flag in study_with_me_generator.py calls PromptGenerator.generate() and writes SDXL/Suno prompts to the profile YAML before image generation, with silent fallback when OPENAI_API_KEY is absent**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T00:00:00Z
- **Completed:** 2026-03-28T00:05:00Z
- **Tasks:** 2
- **Files modified:** 1 (study_with_me_generator.py; cinematic.yaml verified but unchanged)

## Accomplishments
- Added `--tags` argument to the pipeline's argparse definition with full description
- Defined `_run_prompt_generation()` module-level helper with lazy imports, YAML write-back, and graceful fallback on `PromptGenerationError`
- Wired the prompt generation call into `main()` between config load and video setup
- Verified cinematic.yaml already contains `sdxl.positive_prompt`, `sdxl.scene_templates`, and `suno.prompt_tags` — no file change required

## Task Commits

1. **Task 1: --tags CLI flag and PromptGenerator wiring** - `57930db` (feat)
2. **Task 2: cinematic.yaml positive_prompt verification** - no commit (verification pass only)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `study_with_me_generator.py` - Added `_run_prompt_generation()` function and `--tags` argparse argument; wired call after config load
- `config/profiles/cinematic.yaml` - Verified; `sdxl.positive_prompt` already present, no modification needed

## Decisions Made
- Task 2 required no file change — `positive_prompt` was already in cinematic.yaml from a prior phase; the task executed as a pure verification pass
- Lazy imports preserved in `_run_prompt_generation` — yaml and generators.prompt_generator are not loaded at module level

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Python default encoding on Windows (cp1252) caused UnicodeDecodeError in the AST verification command; resolved by adding `encoding='utf-8'` to `open()` in the verify script. File itself uses UTF-8 throughout.

## User Setup Required
None - no external service configuration required. OPENAI_API_KEY is read from environment at runtime; missing key triggers graceful fallback.

## Next Phase Readiness
- End-to-end tag pipeline is live: `python study_with_me_generator.py --tags 'lofi, rain, cozy' --config config/profiles/cinematic.yaml --out out.mp4`
- With a valid OPENAI_API_KEY, cinematic.yaml sdxl and suno blocks are overwritten with 8 scene templates and updated music prompt
- Without OPENAI_API_KEY, pipeline continues using existing YAML prompts with a warning

---
*Phase: 18-ai-prompt-generation*
*Completed: 2026-03-28*
