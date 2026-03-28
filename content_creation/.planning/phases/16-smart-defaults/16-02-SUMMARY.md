---
phase: 16-smart-defaults
plan: 02
subsystem: ui
tags: [react, nextjs, typescript, provenance, env-vars]

# Dependency graph
requires:
  - phase: 16-01
    provides: ENV_VAR_MAP keys (notify.discord_webhook_url, notify.slack_webhook_url, suno.api_key) and load_with_env_defaults provenance logic
provides:
  - GET /api/config/profiles/[name] returns { config: PipelineConfig, provenance: Record<string,"env"|"yaml"> }
  - ProfileEditor renders ENV badge next to discord_webhook_url when provenance is "env"
  - ConfigProvenance and ProfileWithProvenance types in pipeline.ts
affects:
  - Phase 17 (branding) — any future profile editor work inherits provenance prop pattern

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Server-side provenance computation in Next.js API route via process.env (secrets never reach browser)
    - Inline badge component (EnvBadge) colocated with its single usage site in ProfileEditor
    - Two-state pattern (config + provenance separately) instead of combined state to minimize diff surface

key-files:
  created: []
  modified:
    - dashboard/src/types/pipeline.ts
    - dashboard/src/app/api/config/profiles/[name]/route.ts
    - dashboard/src/components/config/ProfileEditor.tsx
    - dashboard/src/app/config/page.tsx

key-decisions:
  - "ENV_VAR_MAP inlined in route.ts as TypeScript mirror of Python ENV_VAR_MAP — keeps TS and Python sources in sync manually but avoids cross-language imports"
  - "provenance kept as separate React state (not merged into config state) to minimize diff and keep save path (PUT sends config only) unambiguous"
  - "EnvBadge defined inline in ProfileEditor.tsx rather than extracted to ui/ — single-use component with no reuse signal yet"

patterns-established:
  - "Provenance badge pattern: server computes env/yaml per field, client renders badge only — secrets never cross to browser as values, only as classification strings"

requirements-completed:
  - DFLT-02

# Metrics
duration: 8min
completed: 2026-03-29
---

# Phase 16 Plan 02: Provenance Badges Summary

**GET route returns server-side env/yaml provenance map; ProfileEditor renders muted-blue ENV badge next to Discord Webhook URL when field is sourced from environment variable**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-28T22:54:12Z
- **Completed:** 2026-03-29T00:02:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- GET /api/config/profiles/[name] now returns `{ config, provenance }` with provenance computed server-side via ENV_VAR_MAP
- `ConfigProvenance` and `ProfileWithProvenance` types added to pipeline.ts
- `EnvBadge` component added to ProfileEditor; renders next to Discord Webhook URL when provenance is "env"
- config/page.tsx unpacks new response shape, tracks provenance as separate state, passes it to ProfileEditor
- PUT save behavior unchanged — sends config only, not provenance

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend GET route and pipeline types with provenance** - `ae7231c` (feat)
2. **Task 2: Add EnvBadge component and wire into ProfileEditor** - `853c051` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `dashboard/src/types/pipeline.ts` - Added ConfigProvenance type alias and ProfileWithProvenance interface
- `dashboard/src/app/api/config/profiles/[name]/route.ts` - GET handler computes provenance via ENV_VAR_MAP, returns { config, provenance }
- `dashboard/src/components/config/ProfileEditor.tsx` - Added EnvBadge component, extended props with provenance, badged discord_webhook_url label
- `dashboard/src/app/config/page.tsx` - Added provenance state, unpacks ProfileWithProvenance, passes provenance to ProfileEditor

## Decisions Made
- ENV_VAR_MAP inlined in route.ts as a TypeScript mirror of the Python constant — avoids cross-language imports while keeping a single authoritative source per language.
- Separate provenance state (not merged into config state) keeps the save path unambiguous: PUT body is always `updated: PipelineConfig` with no provenance leakage.
- EnvBadge defined inline in ProfileEditor rather than extracted to ui/ — no reuse signal yet; extract if a second consumer emerges.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. ENV badge visibility is automatic once NOTF_DISCORD_WEBHOOK_URL is set in the environment and the YAML field is absent or empty.

## Next Phase Readiness
- Provenance display is complete; Phase 17 (branding) can build profile editor extensions with the provenance prop already in place.
- No blockers.

---
*Phase: 16-smart-defaults*
*Completed: 2026-03-29*
