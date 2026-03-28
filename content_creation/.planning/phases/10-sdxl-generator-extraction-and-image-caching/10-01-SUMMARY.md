---
phase: 10-sdxl-generator-extraction-and-image-caching
plan: "01"
subsystem: generators
tags: [sdxl, image-generation, caching, sha256, prompt-assembly]
dependency_graph:
  requires:
    - config/pipeline_config.py (SDXLSettings)
    - config/prompt_template.py (PromptTemplate, build_compel_prompt)
  provides:
    - generators/__init__.py (package marker)
    - generators/sdxl.py (SDXLGenerator class)
  affects:
    - study_with_me_generator.py (future Phase 10 wiring plan)
tech_stack:
  added:
    - hashlib.sha256 for full-param cache key derivation
    - pathlib.Path glob for cache lookup
    - lazy torch/diffusers import pattern in _generate_one
  patterns:
    - SHA-256 hash of JSON-serialised param dict (sort_keys=True) as cache key
    - JSON sidecar (.json) collocated with every generated PNG
    - GPU/model imports deferred inside _generate_one for GPU-free unit testing
key_files:
  created:
    - generators/__init__.py
    - generators/sdxl.py
  modified: []
decisions:
  - STYLE_VARIATIONS and WEATHER_EFFECTS copied verbatim from study_with_me_generator.py to preserve existing behaviour during extraction
  - Cache key uses full 64-char SHA-256 digest (not truncated) per SDXL-02 requirement
  - _cache_lookup requires both PNG and JSON sidecar to exist — partial writes treated as cache misses
  - weather effect appended only when environment==indoor AND steps>=25 (medium/high quality), matching original logic
metrics:
  duration: 1 min
  completed: 2026-03-28
  tasks_completed: 2
  files_created: 2
  files_modified: 0
requirements_satisfied:
  - SDXL-01
  - SDXL-02
  - SDXL-03
  - SDXL-04
---

# Phase 10 Plan 01: SDXLGenerator Package Creation Summary

**One-liner:** `generators/` package with SDXLGenerator — SHA-256 hash-keyed disk cache, JSON sidecars, and lazy GPU imports for GPU-free unit testing.

## What Was Built

Two files establish the `generators/` module boundary before the inline code in `study_with_me_generator.py` is replaced:

- `generators/__init__.py` — empty package marker with module docstring; makes `from generators.sdxl import SDXLGenerator` importable from project root
- `generators/sdxl.py` — full `SDXLGenerator` implementation with:
  - `build_prompt()` — resolves template variables via `PromptTemplate.render()`, appends random style variation, conditionally appends weather effect for indoor scenes at medium/high quality
  - `generate_batch()` — iterates scenes, computes SHA-256 cache key per scene, logs `[SDXL] Cache hit: scene N` or `[SDXL] Generating scene N ...`, writes PNG + JSON sidecar on miss
  - `_cache_key()` — module-level function; `json.dumps(params, sort_keys=True)` → `hashlib.sha256(...).hexdigest()` → 64-char digest
  - `_generate_one()` — lazy imports `torch` and `diffusers` inside method body; loads SDXL pipeline, applies compel conditioning (falls back to plain strings on `ImportError`), unloads pipeline after generation
  - `_write_sidecar()` — writes JSON with all 9 param keys: `prompt`, `negative_prompt`, `steps`, `guidance_scale`, `width`, `height`, `profile`, `seed`, `model_id`
  - `_cache_lookup()` — globs cache dir for `*_{key}.png`, returns path only if sidecar JSON also exists

## Verification Results

1. `python -c "from generators.sdxl import SDXLGenerator; print('import ok')"` — exits 0, no GPU
2. `python -c "from generators.sdxl import _cache_key; p={'a':1,'b':2}; assert _cache_key(p)==_cache_key({'b':2,'a':1}); print('key ok')"` — exits 0, sort_keys normalisation confirmed
3. `_generate_one` — `import torch` is inside the method body, not at module level; confirmed by inspection
4. `_write_sidecar` — produces valid JSON with all 9 required keys; confirmed by inspection and sidecar spec match

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create generators/__init__.py | 74ad349 | generators/__init__.py |
| 2 | Implement generators/sdxl.py | b5a868a | generators/sdxl.py |

## Self-Check: PASSED
