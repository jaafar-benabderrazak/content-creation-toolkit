---
phase: 24-instagram-style-reference-system-scrape-radstream-aesthetic-img2img-with-reference-images-style-consistent-generation
plan: "01"
subsystem: generators
tags: [style-reference, instagram, color-extraction, image-generation]
dependency_graph:
  requires: []
  provides: [generators/style_reference.py, StyleReferenceManager, StyleProfile]
  affects: [generators/image_gen.py, pipeline]
tech_stack:
  added: [colorthief, scikit-learn, instaloader (optional)]
  patterns: [lazy-import for optional deps, profile.json sidecar cache, manual fallback via posts/]
key_files:
  created:
    - generators/style_reference.py
  modified: []
decisions:
  - "Lazy-import instaloader and colorthief inside their functions — module importable without these packages installed"
  - "Manual fallback: user drops .jpg files into .cache/style_reference/<handle>/posts/ and runs --extract-only to produce profile.json without instaloader"
  - "LoginRequiredException produces actionable RuntimeError with exact instaloader --login command and manual fallback path"
  - "KMeans n_clusters capped at min(5, len(all_colors)) to prevent error when fewer than 5 color samples are available"
  - "handle.lstrip('@') applied consistently — both @radstream and radstream accepted everywhere"
metrics:
  duration: "~5 min"
  completed: "2026-03-29"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
---

# Phase 24 Plan 01: Style Reference Subsystem — Scraper, Extractor, Profile Manager Summary

Instagram style reference subsystem with instaloader scraping, colorthief + KMeans color extraction, brightness/contrast/mood derivation, and persistent profile.json caching via StyleReferenceManager.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | StyleReferenceManager — scraper, extractor, and profile persistence | 732a348 | generators/style_reference.py |

## What Was Built

`generators/style_reference.py` — single-file module providing:

- `StyleProfile` dataclass: handle, scraped_at, post_count, dominant_colors, color_temperature, brightness_level, contrast_level, mood_descriptors, reference_images, prompt_prefix
- `scrape_profile_images(handle, post_limit, cache_dir, session_file)` — instaloader download with LoginRequiredException/ProfileNotExistsException/PrivateProfileNotFollowedException handling; raises RuntimeError with actionable message on failure
- `extract_style_features(image_paths)` — colorthief palette per image, KMeans(5) aggregation, PIL brightness/contrast stats, mood descriptor derivation from feature combination rules, prompt_prefix generation
- `build_style_profile(handle, image_paths, cache_dir)` — calls extraction, builds StyleProfile, writes `.cache/style_reference/<handle>/profile.json`
- `StyleReferenceManager` — `build_or_load()` checks cache first (no re-scrape on second call), manual fallback path (existing posts/ images skip scraping), `get_reference_image_paths()` returns valid paths from cached profile
- CLI: `--handle` (required), `--limit`, `--session-file`, `--extract-only`, `--refresh`

## Verification Results

```
from generators.style_reference import StyleReferenceManager, StyleProfile, extract_style_features
→ imports OK

python generators/style_reference.py --help
→ shows all 5 flags: --handle, --limit, --session-file, --extract-only, --refresh

python generators/style_reference.py --handle testhandle --extract-only
→ "No images found for @testhandle. Drop .jpg files into .cache\style_reference\testhandle\posts first."

StyleProfile fields: ['handle', 'scraped_at', 'post_count', 'dominant_colors',
  'color_temperature', 'brightness_level', 'contrast_level', 'mood_descriptors',
  'reference_images', 'prompt_prefix']
```

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `generators/style_reference.py` exists and imports cleanly
- Commit 732a348 exists in git log
- All 5 exported names (StyleReferenceManager, StyleProfile, scrape_profile_images, extract_style_features, build_style_profile) importable
- CLI --help shows all required flags
- LoginRequiredException path raises RuntimeError with manual fallback instructions
