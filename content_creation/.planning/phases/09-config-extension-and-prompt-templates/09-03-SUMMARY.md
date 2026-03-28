---
phase: 09-config-extension-and-prompt-templates
plan: "03"
subsystem: config
tags: [prompt-template, compel, sdxl, string-formatting, tdd, pytest]

requires:
  - phase: 09-01
    provides: SDXLSettings with quality_suffix field consumed by PromptTemplate.render()
  - phase: 09-02
    provides: scene_templates in profile YAMLs that feed template strings into render()

provides:
  - PromptTemplate.render() — variable substitution with ValueError on unresolved keys
  - build_compel_prompt() — SDXL compel weighting helper with ImportError guard
  - tests/test_prompt_template.py — 13-test pytest suite proving render and compel contracts

affects:
  - phase-10-sdxl-generator  # calls PromptTemplate.render() for every scene

tech-stack:
  added: []
  patterns:
    - "_StrictFormatMap wraps dict.__missing__ to convert KeyError to ValueError with variable name"
    - "build_compel_prompt is a pure function with no pipeline state; tested via mock, not GPU"
    - "TDD: RED (failing tests committed) then GREEN (implementation committed) then verify full suite"

key-files:
  created:
    - config/prompt_template.py
    - tests/test_prompt_template.py
  modified: []

key-decisions:
  - "str.format_map(_StrictFormatMap) chosen over .format(**kwargs) — enables targeted ValueError with variable name instead of generic KeyError"
  - "build_compel_prompt tested via sys.modules patch not real GPU — GPU/model dependency excluded from test suite by design"
  - "_StrictFormatMap is internal (underscore prefix) — not exported from module"

patterns-established:
  - "Template variable errors must name the missing key: ValueError('Unresolved template variable: {key}') not generic KeyError"
  - "compel import guarded with try/except ImportError providing install hint — fail fast with actionable message"

requirements-completed:
  - PRMT-04
  - PRMT-05

duration: 1min
completed: 2026-03-28
---

# Phase 09 Plan 03: PromptTemplate renderer and compel weighting helper Summary

**PromptTemplate.render() with ValueError-on-missing-variable contract and mocked build_compel_prompt(), proven by 13 pytest tests via TDD RED-GREEN cycle**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-28T18:23:55Z
- **Completed:** 2026-03-28T18:24:40Z
- **Tasks:** 2 (RED: failing tests, GREEN: implementation)
- **Files modified:** 2

## Accomplishments

- `_StrictFormatMap` subclass converts `dict.__missing__` from `KeyError` to `ValueError` with variable name in message — literal braces in SDXL prompts are caught before generation, not silently passed through
- `PromptTemplate.render()` uses `str.format_map()`, appends `quality_suffix` with comma separator only when non-empty
- `build_compel_prompt()` constructs `CompelForSDXL` from pipeline tokenizer/encoder attributes, raises `ImportError` with pip install hint when compel unavailable
- 13 pytest tests: 11 for render() (happy path, ValueError error contract, quality_suffix integration with SDXLSettings), 2 for build_compel_prompt() (4-tuple return via sys.modules mock, ImportError when compel None)
- Full suite 61/61 passed — no pre-existing test regressions

## Task Commits

1. **RED: failing tests** - `cf5fd45` (test)
2. **GREEN: implementation** - `40709fe` (feat)

**Plan metadata:** pending (docs commit)

_Note: TDD tasks committed separately per RED/GREEN phases._

## Files Created/Modified

- `config/prompt_template.py` — `_StrictFormatMap`, `PromptTemplate.render()`, `build_compel_prompt()`
- `tests/test_prompt_template.py` — 13-test pytest suite

## Decisions Made

- `str.format_map(_StrictFormatMap)` over `.format(**kwargs)` — allows overriding `__missing__` to produce `ValueError` with the specific variable name rather than a bare `KeyError`
- `build_compel_prompt` tested via `patch.dict(sys.modules, {"compel": fake_module})` not real GPU — GPU/model dependency excluded from the pytest suite by design; compel mock reloads the module to pick up the patched import
- `_StrictFormatMap` given underscore prefix — internal implementation detail, not part of public API

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `PromptTemplate.render()` is the call site for every scene prompt in Phase 10 (SDXLGenerator)
- Import path: `from config.prompt_template import PromptTemplate, build_compel_prompt`
- Phase 10 must pass `sdxl.quality_suffix` from `SDXLSettings` (set by `_apply_quality_preset` validator on `PipelineConfig`) as `quality_suffix=` argument to `render()`
- `compel>=2.0.2` still needs to be validated for PyPI compatibility with current diffusers install before Phase 10 pins it in requirements.txt (pre-phase todo already in STATE.md)

---
*Phase: 09-config-extension-and-prompt-templates*
*Completed: 2026-03-28*

## Self-Check: PASSED

- config/prompt_template.py: FOUND
- tests/test_prompt_template.py: FOUND
- .planning/phases/09-config-extension-and-prompt-templates/09-03-SUMMARY.md: FOUND
- Commit cf5fd45 (RED): FOUND
- Commit 40709fe (GREEN): FOUND
