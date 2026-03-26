# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Users can find a workspace and book it in under 2 minutes
**Current focus:** Phase 1 — Auth Migration

## Current Position

Phase: 12 of 12 (Complete Auth Migration, App Router Routes, Double-Booking Prevention, Search Filters, Structured Logging, and Test Coverage)
Plan: 2 of 5 in current phase
Status: In Progress — Phase 12 Plan 02 executed
Last activity: 2026-03-26 — 12-02 complete: double-booking exclusion constraint + PostGIS search RPC + advanced_search filters (open_now, price, capacity, amenities)

Progress: [████████░░] 80%

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
| Phase 09 P02 | 30 | 2 tasks | 6 files |
| Phase 10 P01 | 4min | 2 tasks | 7 files |
| Phase 10-add-more-features P02 | 3 | 2 tasks | 5 files |
| Phase 10 P03 | 15min | 2 tasks | 4 files |
| Phase 10-add-more-features P04 | 3min | 2 tasks | 3 files |
| Phase 10 P05 | 20min | 3 tasks | 14 files |
| Phase 10 P06 | 3min | 2 tasks | 7 files |
| Phase 11 P02 | 15min | 2 tasks | 4 files |
| Phase 11 P01 | 4min | 2 tasks | 3 files |
| Phase 11 P03 | 14min | 2 tasks | 5 files |
| Phase 12 P02 | 4min | 2 tasks | 4 files |

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
- [Phase 10-add-more-features]: Replaced class-based EmailService with three standalone functions for simpler reservation call sites
- [Phase 10-add-more-features]: Marketing endpoint falls back to all users when marketing_opt_in column absent — avoids hard DB migration dependency
- [Phase 10-01]: Amount always fetched from DB (cost_credits * 100 EUR cents) — never from client request body
- [Phase 10-01]: Webhook returns 200 even on confirm failure to prevent Stripe retries — logs warning
- [Phase 10-01]: v1 payment history uses reservation rows, no separate payments table
- [Phase 10-03]: Added optional center prop to MapView to support geolocation recenter without breaking existing usages
- [Phase 10-03]: Occupancy stored 0-1 on backend, converted to 0-100% in frontend before charting
- [Phase 10-add-more-features]: Inline checkout in Pending tab (not modal) to avoid Dialog z-index issues
- [Phase 10-add-more-features]: PaymentHistory amount shown as EUR derived from cost_credits / 100 — consistent with Plan 01 v1 approach
- [Phase 10-05]: next-intl 4.8.3 URL-based locale routing with [locale] app restructure; root layout pass-through avoids duplicate html
- [Phase 10-05]: Middleware matcher excludes api|handler|_next|_vercel to prevent locale-prefixing API routes
- [Phase 10-06]: Installed @playwright/test with --legacy-peer-deps; all backend-dependent E2E tests use page.route() mocking to avoid requiring live backend
- [Phase 11-01]: LayerGroup used for Leaflet markers so clearLayers() removes old markers without destroying the map instance
- [Phase 11-01]: Separate mount-only init effect ([]) from establishments update effect ([establishments]) — root cause of marker duplication was init effect re-running on every establishments change
- [Phase 11-01]: onSelectRef and onBoundsChangeRef pattern used to avoid stale closures in Leaflet event handlers; both updated via sync useEffects
- [Phase 11-01]: computeDistance returns metres below 1000 ('850 m'), kilometres above ('1.2 km'); 500ms debounce on map moveend prevents Places API spam
- [Phase 11-02]: ResponsiveDialog wraps both Sheet and Dialog internally — callers pass children directly, no extra content wrapper needed
- [Phase 11-02]: showList = !isMobile || !showMap keeps desktop layout fully unaffected (always true when not mobile)
- [Phase 11-02]: lg:sticky lg:top-20 scopes sticky positioning to large breakpoints only, preventing booking card overlap on 375px viewports
- [Phase 11-03]: Playwright mobile-chrome project with Pixel 5 device runs all 44 E2E tests across both desktop and mobile viewports
- [Phase 11-03]: Demo dropdown buttons matched via .filter({ hasText }) — buttons contain nested divs not direct text nodes, so getByRole name match fails
- [Phase 11-03]: data-slot="select-item" is the correct Radix UI Select item selector in this shadcn setup (not data-radix-select-item)
- [Phase 11-03]: navigateToExplore helper branches on md:flex visibility to handle desktop nav vs hamburger Sheet on mobile
- [Phase 11-03]: Leaflet "Map container is already initialized." filtered as known re-init warning, not a critical error
- [Phase 12]: Half-open tstzrange '[)' in exclusion constraint allows back-to-back bookings; cancelled/completed reservations excluded via WHERE clause
- [Phase 12]: establishments_within_radius RPC pushes capacity/price filters to DB; amenities and open_now filtered in Python post-fetch
- [Phase 12]: geopy kept in requirements.txt — still used in reservations.py find_soonest_available; removed only from establishments.py per plan scope

### Roadmap Evolution

- Phase 9 added: Fix select visibility issues and integrate Google Maps open data
- Phase 10 added: Add more features
- Phase 11 added: Real map data, mobile responsive polish, and Playwright E2E testing
- Phase 12 added: Complete auth migration, App Router routes, double-booking prevention, search filters, structured logging, and test coverage

### Pending Todos

None yet.

### Blockers/Concerns

- Stack Auth user ID format compatibility with existing Supabase foreign keys — verify during Phase 1
- Stack Auth password hash import capability — may need progressive migration (re-auth on first login)

## Session Continuity

Last session: 2026-03-26
Stopped at: Completed 12-02-PLAN.md — double-booking exclusion constraint + PostGIS search RPC + advanced_search filters
Resume file: N/A — continue with 12-03
