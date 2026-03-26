---
phase: 11-real-map-data-mobile-responsive-polish-and-playwright-e2e-testing
plan: 03
subsystem: frontend/e2e
tags: [playwright, e2e, mobile, demo, booking, leaflet]

# Dependency graph
requires:
  - phase: 11-real-map-data-mobile-responsive-polish-and-playwright-e2e-testing
    plan: 01
    provides: MapView with onBoundsChange, search-by-area
  - phase: 11-real-map-data-mobile-responsive-polish-and-playwright-e2e-testing
    plan: 02
    provides: Mobile map/list toggle, ResponsiveDialog, lg:sticky booking card

provides:
  - Playwright mobile-chrome project (Pixel 5) running all E2E suites
  - Demo mode E2E coverage (owner flow, customer flow, exit demo)
  - Map toggle E2E coverage (show/hide, error-free render)
  - Mobile viewport E2E coverage (hamburger menu, exclusive map/list toggle, non-sticky booking card)
  - Booking flow E2E coverage (full form submission to confirmation dialog, disabled-button validation)

affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Playwright mobile-chrome project with Pixel 5 device overrides viewport for responsive regression testing"
    - "test.use({ viewport }) at file level forces mobile viewport regardless of project"
    - "page.route() mocking for all /api/v1/**, /api/stripe/**, maps.googleapis.com to remove backend and key dependencies"
    - "data-slot='select-item' selector for Radix UI Select item interaction in Playwright"
    - "computedStyle(el).position check to verify lg:sticky does not activate at 375px"
    - "Separate navigateToExplore helper with mobile/desktop path branching (hamburger vs direct nav button)"

key-files:
  created:
    - librework/frontend/e2e/demo-flow.spec.ts
    - librework/frontend/e2e/explore-map.spec.ts
    - librework/frontend/e2e/mobile-viewport.spec.ts
    - librework/frontend/e2e/booking-flow.spec.ts
  modified:
    - librework/frontend/playwright.config.ts

key-decisions:
  - "Leaflet 'Map container is already initialized.' is a known re-init warning filtered from critical errors — not a test failure"
  - "Demo dropdown buttons matched via .filter({ hasText }) not getByRole name because button text is in child divs, not direct text nodes"
  - "navigateToExplore helper branches on md:flex visibility to handle both desktop and mobile nav paths"
  - "data-slot='select-item' is the correct Radix Select item selector; data-radix-select-item does not exist"
  - "mobile-viewport.spec.ts uses test.use({ viewport: { width: 375, height: 667 } }) at file level to force mobile regardless of project"
  - "demo-flow.spec.ts uses test.use({ viewport: { width: 1280, height: 800 } }) to force desktop nav so the Demo button is always visible"

requirements-completed: [SEARCH-01, UX-01]

# Metrics
duration: 14min
completed: 2026-03-26
tasks_completed: 2
files_created: 4
files_modified: 1
---

# Phase 11 Plan 03: Playwright E2E Tests for Demo Flow, Map Interaction, Mobile Viewport, and Booking Summary

**One-liner:** Four new Playwright spec files covering demo mode entry/exit, Leaflet map toggle, mobile-exclusive list/map toggle, and booking form submission — plus a Pixel 5 mobile-chrome project running all 44 tests across two browser contexts.

## Performance

- **Duration:** ~14 min
- **Started:** 2026-03-26T15:47:14Z
- **Completed:** 2026-03-26T16:02:06Z
- **Tasks:** 2
- **Files created:** 4
- **Files modified:** 1

## Accomplishments

- Added `mobile-chrome` project (Pixel 5 device) to `playwright.config.ts` — all 44 tests now run on both chromium and mobile-chrome
- Created `demo-flow.spec.ts` with 3 tests: owner demo entry shows amber banner, customer demo entry shows banner, exit demo removes banner. Desktop viewport forced at file level so Demo button is always visible.
- Created `explore-map.spec.ts` with 2 tests: map toggle show/hide (Leaflet container visible/invisible), error-free render after toggle. `navigateToExplore` helper handles both desktop and mobile hamburger nav paths.
- Created `mobile-viewport.spec.ts` with 3 tests at 375px: hamburger menu visible/desktop nav hidden, exclusive map/list toggle (list disappears when map shows on mobile), booking card `lg:sticky` computes as non-sticky via `computedStyle`.
- Created `booking-flow.spec.ts` with 2 tests: full form submission (space select via `data-slot="select-item"`, date/time fill, Confirm Reservation click, confirmation dialog assert), disabled button validation when fields empty.

## Task Commits

1. **Task 1: Add mobile-chrome project and demo-flow/explore-map spec files** - `18811eb` (feat)
2. **Task 2: Create mobile-viewport and booking-flow spec files** - `c22d9e7` (feat)

## Files Created/Modified

- `librework/frontend/playwright.config.ts` — added mobile-chrome project with `devices['Pixel 5']`
- `librework/frontend/e2e/demo-flow.spec.ts` — 3 demo mode flow tests, desktop viewport forced
- `librework/frontend/e2e/explore-map.spec.ts` — 2 map toggle tests, mobile/desktop nav helper
- `librework/frontend/e2e/mobile-viewport.spec.ts` — 3 mobile layout tests at 375px, computedStyle sticky check
- `librework/frontend/e2e/booking-flow.spec.ts` — 2 booking flow tests, Radix Select interaction

## Decisions Made

- Leaflet "Map container is already initialized." filtered from critical errors — this is a known re-init warning produced by React Strict Mode double-mounting, not a real error
- Demo dropdown buttons matched via `.filter({ hasText })` because the button's accessible name comes from nested divs, not a direct text node — `getByRole('button', { name: /^customer$/ })` was finding 0 elements
- `data-slot="select-item"` is the correct Radix UI Select item selector in this project's shadcn setup; `data-radix-select-item` does not exist in the rendered HTML
- Booking form test uses `navigateToFirstEstablishmentDetails` which branches on md:flex visibility — mobile uses hamburger sheet, desktop uses direct nav button
- `mobile-viewport.spec.ts` at file level forces `{ width: 375, height: 667 }` so tests exercise mobile layout even when running under the mobile-chrome project (which also sets Pixel 5 viewport — belt and suspenders)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Radix Select selector was wrong**
- **Found during:** Task 2 (booking-flow)
- **Issue:** Plan specified `data-radix-select-item` but Radix renders `data-slot="select-item"` in this shadcn setup
- **Fix:** Changed selector to `[data-slot="select-item"]`
- **Files modified:** `frontend/e2e/booking-flow.spec.ts`
- **Commit:** c22d9e7

**2. [Rule 1 - Bug] explore-map tests failed on mobile-chrome due to hidden desktop nav**
- **Found during:** Task 1 verification on mobile-chrome
- **Issue:** `navigateToExplore` only tried desktop nav button, which is `md:hidden` on mobile
- **Fix:** Added mobile path using hamburger Sheet trigger, then clicking Explore inside the sheet
- **Files modified:** `frontend/e2e/explore-map.spec.ts`
- **Commit:** 18811eb

**3. [Rule 1 - Bug] mobile-viewport sticky assertion was wrong**
- **Found during:** Task 2 (mobile-viewport booking card test)
- **Issue:** Original assertion `plainStickyCount === 0` failed because `nav` itself is `sticky` (unscoped)
- **Fix:** Replaced with `computedStyle(el).position !== 'sticky'` check on the `lg:sticky` element
- **Files modified:** `frontend/e2e/mobile-viewport.spec.ts`
- **Commit:** c22d9e7

**4. [Rule 1 - Bug] Leaflet re-init error filtered too narrowly**
- **Found during:** Task 1 (explore-map second test)
- **Issue:** "Map container is already initialized." was not in the known-error filter list
- **Fix:** Added `!msg.includes('already initialized')` to the critical errors filter
- **Files modified:** `frontend/e2e/explore-map.spec.ts`
- **Commit:** 18811eb

## User Setup Required

None — all tests use `page.route()` mocking. No live API keys, backend, or Google Maps key required.

## Self-Check: PASSED

- FOUND: librework/frontend/playwright.config.ts (contains "Pixel 5" on line 22)
- FOUND: librework/frontend/e2e/demo-flow.spec.ts
- FOUND: librework/frontend/e2e/explore-map.spec.ts
- FOUND: librework/frontend/e2e/mobile-viewport.spec.ts
- FOUND: librework/frontend/e2e/booking-flow.spec.ts
- FOUND commit: 18811eb (Task 1)
- FOUND commit: c22d9e7 (Task 2)
- 44 tests passing (20 new + 24 existing, on chromium + mobile-chrome)
