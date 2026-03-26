# Roadmap: LibreWork

## Overview

LibreWork has a functional codebase with substantial domain logic but is held back by a fragmented auth system, no real payments, no email delivery, and a single-page architecture that blocks internationalization. This roadmap takes the platform from a fragile prototype to a launch-ready coworking marketplace. The critical path is clear: unified auth first (everything depends on it), then structural frontend fixes that unlock i18n, then the three pillars of user value — email, search, and payments — followed by owner tools and a final responsive design pass.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Auth Migration** - Replace fragmented auth (3 hooks, 2 backends) with unified Stack Auth
- [ ] **Phase 2: Testing & Logging** - Add automated tests for auth/RBAC and structured logging
- [ ] **Phase 3: Frontend Restructuring & i18n** - Extract proper App Router routes and add French/English support
- [ ] **Phase 4: Email Delivery** - Ship real transactional and marketing emails via Resend
- [ ] **Phase 5: Search & Discovery** - Interactive map, PostGIS spatial queries, filters, and "open now"
- [ ] **Phase 6: Stripe Payments** - Real card payments with webhook-driven confirmation and double-booking prevention
- [ ] **Phase 7: Owner Analytics** - Dashboard showing occupancy, revenue, and booking trends
- [ ] **Phase 8: UI Polish & Responsive Design** - Consistent design system and mobile-first responsive pass

## Phase Details

### Phase 1: Auth Migration
**Goal**: Users authenticate through Stack Auth with a single, unified auth system — no more fragmented hooks, dual backends, or hardcoded states
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07, AUTH-08, AUTH-09, INFRA-03
**Success Criteria** (what must be TRUE):
  1. User can sign up and log in via Stack Auth (email/password) from the frontend
  2. User stays logged in across browser sessions without re-authentication
  3. Navbar correctly reflects authenticated/unauthenticated state on every page
  4. Owner dashboard is only accessible to users with the owner role (RBAC enforced end-to-end)
  5. No legacy auth code remains in the codebase (no python-jose, passlib, next-auth, Supabase Auth imports)
**Plans:** 5 plans

Plans:
- [ ] 01-01-PLAN.md — Backend auth foundation (DB migration, Stack Auth JWT verification, dependencies, RBAC simplification)
- [ ] 01-02-PLAN.md — Frontend Stack Auth setup (SDK install, provider, handler route, Navbar, API interceptor)
- [ ] 01-03-PLAN.md — Backend router migration & legacy cleanup (update 15+ router imports, delete legacy auth files)
- [ ] 01-04-PLAN.md — Frontend component migration & legacy cleanup (replace all hook usages, delete legacy files)
- [ ] 01-05-PLAN.md — RBAC integration & end-to-end verification (webhook, owner self-promotion, full flow test)

### Phase 2: Testing & Logging
**Goal**: Backend is verified with automated tests and instrumented with structured logging for debugging
**Depends on**: Phase 1
**Requirements**: INFRA-01, INFRA-02
**Success Criteria** (what must be TRUE):
  1. Automated tests pass for auth endpoints, RBAC role enforcement, and core reservation API
  2. Backend logs are structured JSON with request context (no print statements remain in production code)
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Frontend Restructuring & i18n
**Goal**: Frontend uses proper App Router routes with bilingual French/English support via next-intl
**Depends on**: Phase 1
**Requirements**: UX-03, I18N-01, I18N-02
**Success Criteria** (what must be TRUE):
  1. Each major view (home, search, booking, profile, owner dashboard) has its own URL route
  2. URLs include locale prefix (/fr/search, /en/search) with working locale switcher
  3. Switching language changes all visible UI text to the selected language
  4. Browser back/forward navigation works correctly between pages
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Email Delivery
**Goal**: System sends real emails for all transactional flows and marketing to opted-in users
**Depends on**: Phase 1
**Requirements**: EMAIL-01, EMAIL-02, EMAIL-03
**Success Criteria** (what must be TRUE):
  1. User receives an email with a working reset link when requesting password reset
  2. User receives a confirmation email immediately after booking a reservation
  3. Admin can send a promotional email to users who opted into marketing communications
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Search & Discovery
**Goal**: Users discover spaces through an interactive map with powerful filtering and real-time availability
**Depends on**: Phase 3
**Requirements**: SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04
**Success Criteria** (what must be TRUE):
  1. User sees establishments on an interactive map alongside a synchronized list view
  2. Searching by location returns results sorted by proximity using PostGIS spatial queries
  3. User can filter results by price range, amenities, capacity, and rating simultaneously
  4. User can filter to see only establishments that are open right now
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

### Phase 6: Stripe Payments
**Goal**: Users pay for reservations with real money via Stripe, with webhook-driven status updates and database-level booking integrity
**Depends on**: Phase 1, Phase 3
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, INFRA-04
**Success Criteria** (what must be TRUE):
  1. User completes a reservation payment via Stripe Checkout (card payment)
  2. Reservation status automatically updates to "confirmed" after successful payment (no manual intervention)
  3. User can view their payment history and download receipts
  4. Two overlapping reservations for the same space and time cannot exist (database-enforced exclusion constraint)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD
- [ ] 06-03: TBD

### Phase 7: Owner Analytics
**Goal**: Owners see their business performance at a glance with real data
**Depends on**: Phase 6
**Requirements**: OWNER-01
**Success Criteria** (what must be TRUE):
  1. Owner dashboard displays occupancy rates, revenue totals, and booking trends with charts
  2. Analytics data reflects actual reservation and payment records from the system (not mocked)
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

### Phase 8: UI Polish & Responsive Design
**Goal**: Every view looks great and works perfectly on any device with a consistent design language
**Depends on**: Phase 5, Phase 6, Phase 7
**Requirements**: UX-01, UX-02
**Success Criteria** (what must be TRUE):
  1. Every view renders correctly and is fully usable on mobile (375px), tablet (768px), and desktop (1280px)
  2. UI uses a consistent design system (colors, typography, spacing, component patterns) across all pages
  3. Mobile navigation is intuitive (hamburger/drawer menu, touch-friendly tap targets)
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

## Dependency Graph

```
Phase 1 (Auth)
├──> Phase 2 (Testing & Logging)
├──> Phase 3 (Routes & i18n)
│    ├──> Phase 5 (Search)
│    └──> Phase 6 (Payments) ←── also depends on Phase 1
├──> Phase 4 (Email)
│
Phase 6 (Payments)
└──> Phase 7 (Owner Analytics)

Phase 5 + Phase 6 + Phase 7
└──> Phase 8 (UI Polish)
```

**Parallelization opportunities:**
- Phases 2, 3, 4 can all begin after Phase 1 (partially overlapping)
- Phases 4 and 5 are fully independent of each other
- Phases 5 and 6 are independent of each other (both need Phase 3)
- Phase 7 backend queries can start during late Phase 6

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auth Migration | 0/? | Not started | - |
| 2. Testing & Logging | 0/? | Not started | - |
| 3. Frontend Restructuring & i18n | 0/? | Not started | - |
| 4. Email Delivery | 0/? | Not started | - |
| 5. Search & Discovery | 0/? | Not started | - |
| 6. Stripe Payments | 0/? | Not started | - |
| 7. Owner Analytics | 0/? | Not started | - |
| 8. UI Polish & Responsive Design | 0/? | Not started | - |

### Phase 9: Fix select visibility issues and integrate Google Maps open data

**Goal:** Select/popover/dropdown components render with correct opaque backgrounds by fixing CSS variable format, and Explore page shows real establishments from Google Places API with map markers at real GPS coordinates
**Depends on:** Nothing (independent bugfix + feature addition)
**Requirements:** UX-01, SEARCH-01
**Plans:** 2/2 plans complete

Plans:
- [ ] 09-01-PLAN.md — Fix CSS variable hex-to-HSL mismatch in globals.css (select/popover visibility bug)
- [ ] 09-02-PLAN.md — Integrate Google Maps Places API (New) for real establishment data on Explore page

### Phase 10: Add more features

**Goal:** Stripe Checkout payments, Resend email notifications, next-intl i18n (FR/EN), enhanced owner analytics dashboard, user-location map centering, and Playwright E2E tests for all features
**Depends on:** Phase 9
**Requirements:** PAY-01, PAY-02, PAY-03, PAY-04, EMAIL-01, EMAIL-02, EMAIL-03, I18N-01, I18N-02, OWNER-01, SEARCH-01
**Success Criteria** (what must be TRUE):
  1. User can pay for a reservation via Stripe Checkout and reservation status updates automatically
  2. User receives booking confirmation and cancellation emails via Resend
  3. URLs include locale prefix (/en, /fr) with working language switcher
  4. Owner dashboard shows revenue and occupancy charts with real data
  5. Explore map centers on user's geolocation when permission granted
  6. Playwright E2E tests cover all Phase 10 features
**Plans:** 6/6 plans complete

Plans:
- [ ] 10-01-PLAN.md — Stripe backend payments + webhook handler (PAY-01, PAY-02, PAY-03)
- [ ] 10-02-PLAN.md — Resend email integration for transactional and marketing emails (EMAIL-01, EMAIL-02, EMAIL-03)
- [ ] 10-03-PLAN.md — Owner analytics charts + explore geolocation centering (OWNER-01, SEARCH-01)
- [ ] 10-04-PLAN.md — Stripe frontend checkout flow + payment history (PAY-04)
- [ ] 10-05-PLAN.md — next-intl i18n with locale routing and translations (I18N-01, I18N-02)
- [x] 10-06-PLAN.md — Playwright E2E tests for all Phase 10 features (completed 2026-03-22)

### Phase 11: Real map data, mobile responsive polish, and Playwright E2E testing

**Goal:** Enhance map with search-by-area (Leaflet moveend), fix marker layer management bug, enrich place detail popups with distance display. Mobile responsive audit across ExplorePage, EstablishmentDetails, and UserDashboard. Playwright E2E tests for demo mode, booking flow, map interaction, and mobile viewports.
**Depends on:** Phase 10
**Requirements:** SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04, UX-01, UX-02, UX-03
**Success Criteria** (what must be TRUE):
  1. Dragging the map loads new establishments for the visible area (search-by-area)
  2. Markers clear and re-render without duplicates when establishments change
  3. On mobile (375px), map and list toggle exclusively; booking card does not overlap content
  4. Playwright E2E tests pass for demo flow, map toggle, mobile layouts, and booking form
**Plans:** 3/3 plans complete

Plans:
- [ ] 11-01-PLAN.md — Fix marker layer bug, add search-by-area via moveend, add distance display (SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04)
- [ ] 11-02-PLAN.md — Mobile responsive: ResponsiveDialog, map/list toggle, booking card reflow, scrollable tabs (UX-01, UX-02, UX-03)
- [ ] 11-03-PLAN.md — Playwright E2E tests: demo flow, map interaction, mobile viewports, booking form (SEARCH-01, UX-01)

### Phase 12: Complete auth migration, App Router routes, double-booking prevention, search filters, structured logging, and test coverage

**Goal:** Finalize Stack Auth migration by removing all legacy auth code, extract SPA views into proper App Router routes, add database-level double-booking prevention, implement PostGIS spatial search with price/capacity/amenity/open-now filters, add structured logging, and establish pytest test coverage for auth/RBAC/reservations
**Depends on:** Phase 11
**Requirements:** AUTH-01, AUTH-02, AUTH-04, AUTH-05, AUTH-06, AUTH-07, AUTH-09, UX-03, SEARCH-02, SEARCH-03, SEARCH-04, INFRA-01, INFRA-02, INFRA-04
**Plans:** 1/5 plans executed

Plans:
- [ ] 12-01-PLAN.md — Backend legacy auth deletion + structlog setup (AUTH-05, INFRA-02)
- [ ] 12-02-PLAN.md — Double-booking exclusion constraint + PostGIS search RPC + search filters (INFRA-04, SEARCH-02, SEARCH-03, SEARCH-04)
- [ ] 12-03-PLAN.md — App Router route extraction, onNavigate removal, home-client.tsx deletion (UX-03, AUTH-06)
- [ ] 12-04-PLAN.md — Frontend auth consolidation to Stack Auth useUser() + user migration script (AUTH-01, AUTH-02, AUTH-04, AUTH-07, AUTH-09)
- [ ] 12-05-PLAN.md — pytest test infrastructure + auth/RBAC/reservation test coverage (INFRA-01)

---
*Created: 2026-02-20*
*Depth: comprehensive (8 phases)*
*Coverage: 30/30 requirements mapped*
