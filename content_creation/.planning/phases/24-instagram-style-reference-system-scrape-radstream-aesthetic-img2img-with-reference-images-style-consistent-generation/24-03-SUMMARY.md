---
phase: 24-instagram-style-reference-system-scrape-radstream-aesthetic-img2img-with-reference-images-style-consistent-generation
plan: "03"
subsystem: image-generation
tags: [style-reference, seedream, ip-adapter, img2img, instagram, radstream]
dependency_graph:
  requires: ["24-01", "24-02"]
  provides: ["style-conditioned-image-generation", "style-conditioned-thumbnail"]
  affects: ["generators/image_gen.py", "shared/thumbnail_gen.py"]
tech_stack:
  added: ["bytedance/seedream-5-lite (Replicate)", "InstantStyle IP-Adapter (local CUDA path)"]
  patterns: ["data URI base64 image_input injection", "lazy StyleReferenceManager resolution", "cache key includes style_ref_handle"]
key_files:
  created: []
  modified:
    - generators/image_gen.py
    - shared/thumbnail_gen.py
decisions:
  - "_style_ref_to_data_uris resizes to 512px max side before encoding — reduces Replicate payload per research pitfall 4"
  - "cache key for _generate_single_with_variants includes style_ref_handle so styled/unstyled outputs are stored separately"
  - "_resolve_style_ref_paths catches all exceptions and falls back to no-style-ref — generation never hard-fails due to missing profile"
  - "enhance_thumbnail_image caps style refs at 4 images (vs 6 for scenes) to reduce thumbnail payload size"
  - "IP-Adapter path raises clear RuntimeError when CUDA unavailable; falls back to Replicate automatically"
  - "Seedream upgraded from seedream-3 to seedream-5-lite in both image_gen.py and thumbnail_gen.py for consistency"
metrics:
  duration: "3 min"
  completed_date: "2026-03-29"
  tasks_completed: 2
  files_modified: 2
---

# Phase 24 Plan 03: Style Reference Integration into Image Generation Summary

Style reference images from StyleReferenceManager wired into Seedream 5 `image_input` (Replicate) and local InstantStyle IP-Adapter for both scene generation and thumbnail enhancement.

## What Was Built

### Task 1: `generators/image_gen.py`

**New module-level function `_style_ref_to_data_uris(image_paths, max_refs=6)`**
Encodes reference images as base64 JPEG data URIs. Resizes to 512px max side before encoding to limit Replicate payload size. Skips missing files silently.

**New private function `_generate_ipadapter(prompt, style_ref_paths, style_strength=0.6)`**
Local SDXL + InstantStyle IP-Adapter generation. Uses `up_blocks.0 block_0` scale dict for style-only conditioning (no content bleed). Raises `RuntimeError` with clear message when CUDA unavailable. Frees GPU memory via `del pipeline; torch.cuda.empty_cache()`.

**Updated `_generate_seedream()`**
- Upgraded from `bytedance/seedream-3` to `bytedance/seedream-5-lite`
- Accepts `style_ref_paths: Optional[list] = None`
- Injects data URIs into `inp["image_input"]` when refs provided

**Updated `generate_image_api()`**
- Added `style_ref_paths`, `style_ref_backend` params
- IP-Adapter path fires first when `style_ref_backend == "local_ipadapter"` and falls back to Replicate on `RuntimeError`
- DALL-E 3 and local SD paths unchanged (no style ref support)

**Updated `generate_scenes()`**
- Added `style_ref_handle: Optional[str] = None` and `style_ref_backend: str = "replicate"`
- Forwards to `_generate_single_with_variants()` and `_generate_multi()`

**Updated `_generate_single_with_variants()`**
- Cache key `params` dict includes `"style_ref_handle": style_ref_handle or ""`
- Resolves paths via `_resolve_style_ref_paths()` before calling `generate_image_api()`

**New method `_resolve_style_ref_paths(handle)`**
Lazy-imports `StyleReferenceManager`, calls `get_reference_image_paths()`, returns `None` on any exception (logs warning — generation continues without style ref).

**Updated `_generate_multi()`**
- Accepts `style_ref_handle`, `style_ref_backend`
- Resolves style_ref_paths once before the loop; passes to each `generate_image_api()` call
- Cache key per scene includes `style_ref_handle`

### Task 2: `shared/thumbnail_gen.py`

**Updated `enhance_thumbnail_image()`**
- Added `style_ref_paths: Optional[list] = None`
- Upgraded Seedream call from `bytedance/seedream-3` to `bytedance/seedream-5-lite`
- When `style_ref_paths` provided: imports `_style_ref_to_data_uris` from `generators.image_gen`, caps at 4 refs (lower payload for thumbnail), injects into `inp["image_input"]`
- All existing fallback paths (Google Imagen, SDXL, local Pillow) unchanged

**Updated `generate_thumbnail()`**
- Added `style_ref_paths: Optional[list] = None`
- Forwards to `enhance_thumbnail_image(style_ref_paths=style_ref_paths)`
- No other changes

## Verification Results

All integration checks passed:
- `generate_scenes()` signature includes `style_ref_handle`, `style_ref_backend`
- `generate_thumbnail()` and `enhance_thumbnail_image()` include `style_ref_paths`
- `PipelineConfig.from_yaml('config/profiles/cinematic.yaml')` returns `style_ref.handle == 'radstream'`
- `_generate_seedream` source confirmed to use `bytedance/seedream-5-lite`

Checkpoint auto-approved (YOLO mode).

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `384bf7f` | feat(24-03): wire style_ref_handle into ImageGenerator.generate_scenes() |
| Task 2 | `3e19948` | feat(24-03): add style_ref_paths to enhance_thumbnail_image() and generate_thumbnail() |

## Self-Check: PASSED

- `generators/image_gen.py` exists and imports cleanly
- `shared/thumbnail_gen.py` exists and imports cleanly
- Commits `384bf7f` and `3e19948` verified in git log
