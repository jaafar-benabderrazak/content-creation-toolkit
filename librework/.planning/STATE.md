# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Users can find a workspace and book it in under 2 minutes
**Current focus:** Phase 1 — Auth Migration

## Current Position

Phase: 9 of 9 (Fix Select Visibility Issues and Integrate Google Maps Open Data)
Plan: 1 of 1 in current phase
Status: In Progress — 09-01 complete
Last activity: 2026-03-21 — 09-01 complete: CSS variable hex→HSL fix, select/dropdown backgrounds now opaque

Progress: [░░░░░░░░░░] 5%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 12min | 2 tasks | 6 files |
| Phase 09 P02 | 4 | 2 tasks | 6 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Auth migration is Phase 1 — every other feature depends on unified auth
- [Roadmap]: INFRA-04 (double-booking prevention) grouped with Payments phase, not standalone
- [Roadmap]: UX polish is final phase — comprehensive responsive audit after all views exist
- [Research]: Keep RBAC roles in Supabase users table, sync only identity from Stack Auth
- [Research]: Start with basic Stripe Checkout (no Connect), add Connect later for owner payouts
- [Phase 01]: Made JWT_SECRET_KEY optional (empty default) for Stack Auth migration
- [Phase 01]: RBAC simplified to pure role-string lookup; no DB custom_roles join needed
- [Phase 09-01]: CSS variables in globals.css must use bare HSL triples (not hex) because tailwind.config.ts wraps them in hsl(var(--X))
- [Phase 09-01]: @theme inline and @custom-variant are Tailwind v4 syntax — inert and removed under v3
- [Phase 09-02]: Used --legacy-peer-deps for npm install due to pre-existing react-leaflet@5/React18 conflict
- [Phase 09-02]: Excluded openingHours from Places API fields to stay on Essentials SKU (10K free/month)
- [Phase 09-02]: APIProvider conditionally wraps children only when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is defined

### Roadmap Evolution

- Phase 9 added: Fix select visibility issues and integrate Google Maps open data

### Pending Todos

None yet.

### Blockers/Concerns

- Stack Auth user ID format compatibility with existing Supabase foreign keys — verify during Phase 1
- Stack Auth password hash import capability — may need progressive migration (re-auth on first login)

## Session Continuity

Last session: 2026-03-21
Stopped at: Completed 09-01-PLAN.md
Resume file: .planning/phases/09-fix-select-visibility-issues-and-integrate-google-maps-open-data/09-01-SUMMARY.md
