---
phase: 17-channel-branding
plan: "01"
subsystem: branding
tags: [youtube, oauth, cache, dataclass, pydantic]

requires:
  - phase: 16-smart-defaults
    provides: load_with_env_defaults, ENV_VAR_MAP, PipelineConfig with env-pre-fill for API keys

provides:
  - shared/branding.py — fetch_channel_branding(), BrandingData dataclass, 7-day local cache under .cache/branding/
  - config/pipeline_config.py — BrandingSettings sub-model with branding_enabled and refresh_branding flags

affects:
  - 17-02 (watermark/thumbnail consumers will read from BrandingData)
  - 17-03 (intro/outro generation reads avatar_local_path and channel_name)
  - any phase that constructs PipelineConfig (additive field, zero breaking changes)

tech-stack:
  added: []
  patterns:
    - "Google API import guard: wrap google imports inside function bodies; raise ImportError with pip hint at call time"
    - "Cache pattern: load/save JSON under .cache/<subsystem>/; TTL + explicit refresh as dual invalidation"
    - "Credential loading order: TOKEN_FILE (JSON) then TOKEN_PICKLE (pickle) — mirrors publisher.py"

key-files:
  created:
    - shared/branding.py
  modified:
    - config/pipeline_config.py

key-decisions:
  - "CACHE_TTL_HOURS = 24*7 (7 days) — explicit refresh=True is the primary invalidation; TTL is safety net only"
  - "avatar_local_path stored as absolute str in BrandingData — downstream consumers have no path-resolution burden"
  - "tagline derived from first sentence of description, capped at 80 chars; falls back to channel_name if empty"
  - "BrandingSettings not added to ENV_VAR_MAP — refresh_branding is a runtime flag, not a credential"
  - "BrandingSettings placed after notify in PipelineConfig field order — additive, no existing field reordering"

patterns-established:
  - "Import guard pattern: same as publisher.py — google imports inside function bodies, ImportError with install hint at call time"
  - "Cache helpers (_load_cache, _save_cache) are module-private; public API is fetch_channel_branding(refresh=False)"

requirements-completed: [BRND-01, BRND-05]

duration: 2min
completed: 2026-03-28
---

# Phase 17 Plan 01: Channel Branding — Fetch, Cache, Config Summary

**YouTube channel data fetched via OAuth, avatar downloaded, and persisted to a 7-day JSON cache under .cache/branding/ — with BrandingSettings wired into PipelineConfig as an additive sub-model**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-28T00:00:32Z
- **Completed:** 2026-03-28T00:02:03Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `shared/branding.py` exports `fetch_channel_branding(refresh=False)` and `BrandingData` dataclass with all 6 required fields
- Cache layer reads from `.cache/branding/branding.json` on second call — zero API requests; explicit `refresh=True` clears both JSON and avatar before re-fetch
- `BrandingSettings` (branding_enabled, refresh_branding) added to `PipelineConfig` with default_factory — existing YAML profiles load without modification

## Task Commits

1. **Task 1: Create shared/branding.py with channel fetch, avatar download, and cache** - `f1bc258` (feat)
2. **Task 2: Add BrandingSettings sub-model to pipeline_config.py** - `c841b92` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `shared/branding.py` — BrandingData dataclass, fetch_channel_branding(), _load_cache(), _save_cache(), _download_avatar(), _get_youtube_service()
- `config/pipeline_config.py` — BrandingSettings class added; PipelineConfig.branding field added after notify

## Decisions Made

- `CACHE_TTL_HOURS = 24*7`: Explicit `refresh=True` is the primary invalidation path; TTL acts as a safety net for abandoned caches only
- `avatar_local_path` stored as absolute string in BrandingData so downstream consumers have no path-resolution burden
- `tagline` = first sentence of description, capped at 80 chars; falls back to `channel_name` if description is empty
- `BrandingSettings` not in `ENV_VAR_MAP`: `refresh_branding` is a runtime flag, not a credential — plan explicitly prohibits adding it
- Field order in `PipelineConfig`: `branding` placed after `notify` (before optional `sdxl`/`suno`) — additive with no reordering of existing fields

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required for this plan. YouTube OAuth credentials (`credentials/youtube_token.json` or `.pickle`) must already exist from prior publisher setup.

## Next Phase Readiness

- `fetch_channel_branding()` is callable by any downstream consumer (watermark, thumbnail, intro/outro)
- `PipelineConfig.branding.branding_enabled` gates the feature in pipeline orchestration
- `PipelineConfig.branding.refresh_branding` allows profiles to force cache invalidation declaratively
- Blocker noted in STATE.md: intro/outro generation (BRND-03) requires validating avatar PNG dimensions and description length before implementation

---
*Phase: 17-channel-branding*
*Completed: 2026-03-28*
