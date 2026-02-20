# Project Research Summary

**Project:** LibreWork
**Domain:** Coworking / shared workspace reservation marketplace (two-sided: customers + space owners)
**Researched:** 2026-02-20
**Confidence:** HIGH

## Executive Summary

LibreWork is a brownfield coworking reservation platform built on Next.js 14 + FastAPI + Supabase PostgreSQL. The existing codebase has substantial domain logic — reservations, credits, reviews, favorites, group bookings, RBAC — but is held back by a fragmented authentication system (three frontend hooks, two backend implementations), no real payment processing (credits only), no email delivery, and a single-page SPA architecture that blocks internationalization. The research consensus across all four dimensions is clear: **auth migration is the critical-path prerequisite**, followed by structural frontend refactoring, with payments and i18n as the two highest-value additions.

The recommended approach is to migrate authentication to Stack Auth (already a project constraint) using local JWKS JWT verification on the FastAPI backend (not per-request API calls), then restructure the frontend from its current SPA-in-one-page pattern to proper App Router routes. This unlocks both `next-intl` i18n (which requires the `[locale]` dynamic segment) and proper deep linking. Stripe Checkout (hosted) should handle payments, with webhooks processed exclusively on the FastAPI backend. The existing credit system should coexist with Stripe as a wallet/loyalty layer — this is a genuine differentiator that competitors lack.

The primary risks are concentrated in the auth migration phase: orphaned token paths across 19 route files, frontend auth state fragmentation from three hooks, RBAC silent failures, and user identity mapping. These are well-understood and preventable with exhaustive dependency auditing and integration tests. The payments phase carries two critical pitfalls — webhook idempotency and double-booking race conditions — both solvable with database-level constraints. Overall confidence is high: the recommended stack is mature, patterns are well-documented, and the codebase audit reveals no architectural blockers.

## Key Findings

### Recommended Stack

The stack additions are conservative and high-confidence. No experimental or unproven technologies are recommended.

**Core additions:**
- **Stack Auth** (`@stackframe/stack` + `httpx` for backend JWKS verification): Replaces three frontend auth hooks with one `useUser()`, eliminates custom JWT issuance, provides pre-built auth UI components. Backend verifies tokens locally via JWKS (no per-request API call).
- **Stripe** (Node SDK for checkout session creation in Next.js, Python SDK for webhooks/refunds in FastAPI): Hosted Checkout avoids PCI compliance burden. Stripe Connect (Express accounts, Destination Charges) for owner payouts.
- **next-intl** (v4.8): De facto standard for Next.js App Router i18n. ICU message format handles French grammar (plurals, gender). Tiny bundle (~2KB client-side).
- **Resend**: Simplest transactional email provider. Replaces "print token to console" flow. Free tier covers pre-launch.
- **structlog**: Structured JSON logging for FastAPI. Replaces scattered `print()` statements with context-rich, parseable logs.
- **Vitest + Playwright**: Frontend unit tests (Vitest, fast, Vite-native) and E2E tests (Playwright, cross-browser, mobile emulation). Both officially recommended by Next.js.

**Packages to remove:** `next-auth`, `python-jose[cryptography]`, `passlib[bcrypt]`, Supabase Auth methods.

**Packages to keep (no changes):** Next.js 14, React 18, FastAPI 0.115, Tailwind 3.3, React Query, Zustand, shadcn/ui, Pydantic 2, Recharts.

### Expected Features

**Must have (table stakes — gaps that block launch):**
- T2: Real payment acceptance (Stripe) — #1 gap; credits-only is not a real product
- T6: Booking confirmation + reminder emails — industry standard, 98% open rate on reminders
- T3 + T4: Map-based search with filters — core discovery; PostGIS exists but frontend uses in-memory filtering
- T5: Mobile responsive — 70% of coworking searches happen on mobile
- T10: Owner notifications for new bookings — owners must know when bookings happen
- T13: Basic owner revenue/booking stats — owners won't list without performance visibility

**Should have (differentiators):**
- D1: Credit wallet + Stripe hybrid — unique competitive advantage over Peerspace, Upflex
- D4: Self-service owner onboarding — grows supply side without sales team
- D5: "Open Now" real-time availability — high value for spontaneous bookers, low marginal cost
- D9: Bilingual (FR + EN) from day one — captures both French and international markets

**Defer (v2+):**
- D2: Deep analytics dashboard — needs booking volume first
- D3: Multi-location management — needs mature owner tooling
- D7: Group split payment — complex, niche use case
- D6: Smart search with autocomplete — nice-to-have after basic search
- Real-time chat (A1), AI recommendations (A2), dynamic pricing (A3), native app (A5), multi-currency (A10)

### Architecture Approach

The architecture is a clean three-tier separation: Next.js frontend (rendering, i18n, client auth state), FastAPI backend (business logic, RBAC, data access, webhook processing), Supabase PostgreSQL (persistence). Stack Auth is a managed external service for identity. Stripe is external for payments. The frontend never talks to Supabase directly — all data flows through FastAPI. The backend is the single source of truth for both RBAC and reservation state.

**Major components:**
1. **Next.js Frontend** (Vercel) — UI rendering, Stack Auth SDK for auth state, next-intl for i18n, Stripe Checkout redirect
2. **FastAPI Backend** (Railway) — JWKS token verification, RBAC, reservation logic, Stripe webhooks, analytics aggregation, Resend email delivery
3. **Supabase PostgreSQL** — Data persistence, PostGIS spatial queries, EXCLUSION constraints for double-booking prevention
4. **Stack Auth** (managed) — User registration, login, social auth, token issuance, JWKS endpoint
5. **Stripe** (managed) — Payment processing, Checkout sessions, Connect for owner payouts, webhook events

**Key boundary rules:**
- Frontend never talks to Supabase directly
- Frontend never handles payment logic (redirect only)
- Backend is the single source of truth for RBAC (Stack Auth provides identity, Supabase `users` table provides roles)
- Stack Auth is the single source of truth for identity (no custom JWT, no password storage)

### Critical Pitfalls

1. **Auth migration orphaned token paths** — 19 route files import auth deps from different sources. Replace the dependency functions at the source (`dependencies.py`), not route-by-route. Test every protected endpoint after migration.
2. **Frontend auth state fragmentation** — Three hooks + hardcoded `isAuthenticated = false` in Navbar. Replace in-place (don't add a fourth hook). Fix Navbar in the same commit. Audit all `localStorage.getItem('token')` calls.
3. **Stripe webhook double-processing** — At-least-once delivery + credit system = double-crediting risk. Use `processed_webhook_events` table with UNIQUE constraint on event ID. Wrap business logic in DB transaction.
4. **Reservation double-booking race condition** — No database-level overlap prevention. Add PostgreSQL EXCLUSION constraint on `(space_id, tsrange(start_time, end_time))` using `btree_gist` extension.
5. **User identity mapping during migration** — Existing users have bcrypt hashes and UUIDs referenced across all foreign keys. Migration must preserve or map IDs. Progressive migration (verify old hash on first Stack Auth login) is the safest fallback.

## Implications for Roadmap

Based on combined research, the dependency graph dictates a clear phase structure. Auth is the foundation, frontend restructuring enables i18n, payments are independent of i18n but depend on auth, and analytics depends on both auth and payment data.

### Phase 1: Auth Migration (Stack Auth)
**Rationale:** Every other feature depends on stable, unified authentication. The current system has three frontend hooks and two backend implementations — this fragmentation is the single largest source of bugs and the blocker for all forward progress.
**Delivers:** Single `useUser()` hook, JWKS-based backend verification, unified RBAC, cleaned-up codebase (remove `next-auth`, `python-jose`, `passlib`)
**Addresses:** Foundation for T2, T6, T10, T13, T14, D4 — all require authenticated users
**Avoids:** Pitfalls #1 (orphaned token paths), #2 (user migration), #5 (frontend fragmentation), #7 (verification latency via JWKS), #11 (next-auth removal), #13 (RBAC silent failure)

### Phase 2: Frontend Route Refactor + i18n Setup
**Rationale:** The SPA-in-one-page architecture blocks `next-intl` (requires `[locale]` segment) and proper deep linking. i18n must be set up before building any new UI — retrofitting is 3x more expensive (confirmed by industry consensus). These are tightly coupled and should be one phase.
**Delivers:** Proper App Router routes with URL-based navigation, `[locale]` dynamic segment, `next-intl` configured with `fr.json` + `en.json`, locale-aware middleware, bilingual base for all subsequent UI work
**Addresses:** D9 (bilingual), prerequisite for T3/T4/T5 (all new UI), T9 (booking history page)
**Avoids:** Pitfalls #6 (string concatenation), #9 (route structure breaks), #15 (key maintainability)

### Phase 3: Email Notifications + Search/Map
**Rationale:** These are independent of each other and of payments, but both are table-stakes gaps. Email unblocks booking confirmations, password reset, and owner alerts. Map search is the core discovery experience. Can be worked on in parallel.
**Delivers:** Transactional email via Resend (confirmations, reminders, password reset), map-based search with PostGIS `ST_DWithin`, filter panel (amenities, price, category, "Open Now"), mobile-responsive search view
**Addresses:** T1 (instant booking confirmation), T3 (map search), T4 (filters), T5 (mobile responsive), T6 (email notifications), T10 (owner booking alerts), D5 ("Open Now")
**Avoids:** No critical pitfalls specific to this phase; standard implementation patterns

### Phase 4: Stripe Payments + Credit Hybrid
**Rationale:** Payments are the #1 table-stakes gap but depend on stable auth (Phase 1) and benefit from i18n being in place (Phase 2) for payment UI strings. The credit system must be reconciled with Stripe — coexistence as wallet + Stripe is the recommended approach.
**Delivers:** Stripe Checkout (hosted) for real payments, `payments` table, webhook processing with idempotency, `pending_payment` reservation status, credit-Stripe hybrid checkout, cancellation refund mirroring to Stripe
**Addresses:** T2 (real payments), T9 (receipts — legally required with real payments), T7 (cancellation policy display), D1 (credit + Stripe hybrid)
**Avoids:** Pitfalls #3 (webhook idempotency), #4 (double-booking race condition), #8 (Connect account type lock-in), #10 (authorization expiry), #12 (credit system conflict), #14 (webhook auth bypass)

### Phase 5: Owner Dashboard + Analytics
**Rationale:** Owners need visibility into performance to stay engaged. Basic stats require reservation + payment data (Phase 4). Owner onboarding with Stripe Connect requires Stripe integration.
**Delivers:** Owner reservation management dashboard, basic stats (bookings, revenue, occupancy, ratings), owner self-service onboarding wizard, Stripe Connect Express onboarding for payouts
**Addresses:** T11 (reservation management), T13 (basic stats), T14 (payout visibility), D4 (owner onboarding)
**Avoids:** Pitfall anti-pattern #4 in architecture (premature analytics infrastructure — keep it simple SQL)

### Phase 6: Polish + Advanced Features
**Rationale:** These are valuable differentiators but not blockers. Build after core flow is solid and there's real booking data.
**Delivers:** Deep analytics (occupancy heatmaps, trends), multi-location management, QR code live check-in, smart search with autocomplete, calendar sync improvements
**Addresses:** D2 (deep analytics), D3 (multi-location), D6 (smart search), D8 (QR check-in), D10 (calendar sync)

### Phase Ordering Rationale

- **Auth first** because every authenticated endpoint, webhook, and user flow depends on it. No point building features on a fractured auth foundation.
- **Route refactor + i18n second** because all new UI work in Phases 3-6 should be bilingual from the start. Retrofitting i18n is confirmed to be 3x more expensive.
- **Email + Search in Phase 3** because they're independent of payments and provide immediate user value. Email is trivial with Resend; search leverages existing PostGIS.
- **Payments in Phase 4** (not earlier) because auth and i18n should be stable first. Payment UI needs translations. Webhook handlers need the unified auth system. However, Phases 3 and 4 can partially overlap.
- **Owner features in Phase 5** because they depend on payment data and need Stripe Connect, which is complex and benefits from Stripe familiarity gained in Phase 4.
- **Polish in Phase 6** because these are enhancement layers that need real usage data and mature underlying systems.

### Parallelism Opportunities

- Phase 2 backend work (email setup, search API) can start during Phase 2 frontend route refactor
- Phase 3 email and search are fully independent — can be worked on in parallel
- Phase 4 backend (Stripe webhooks, payment API) can overlap with Phase 3 frontend (search UI)
- Phase 5 backend analytics queries can start during late Phase 4

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Auth Migration):** Stack Auth JWKS endpoint format, user ID mapping strategy, progressive password migration feasibility — Stack Auth Python patterns have medium confidence due to partial doc accessibility
- **Phase 4 (Payments):** Stripe Connect Express onboarding flow, Destination Charges vs Separate Charges decision, credit-to-EUR conversion rules, authorization window handling for advance bookings

Phases with standard patterns (skip research-phase):
- **Phase 2 (Routes + i18n):** next-intl has excellent documentation; App Router refactoring is mechanical
- **Phase 3 (Email + Search):** Resend integration is trivial; PostGIS + Mapbox are well-documented
- **Phase 5 (Analytics):** Simple SQL aggregation; Recharts for visualization — no exotic patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommended packages are mature, actively maintained, with first-party documentation verified. No experimental choices. |
| Features | HIGH | Feature priorities derived from multiple competitor analyses (Peerspace, WeWork, Upflex, Optix, Spacebring), Stripe case studies, and direct codebase audit of existing capabilities. |
| Architecture | MEDIUM-HIGH | Core patterns (JWKS verification, Stripe Checkout + webhooks, next-intl) are well-documented. Stack Auth Python integration has partial doc gaps (JWKS endpoint confirmed via GitHub issue, not official docs). |
| Pitfalls | HIGH | All critical pitfalls confirmed via direct codebase analysis. Existing issues (three auth hooks, two `get_current_user` implementations, no test coverage) independently verified. |

**Overall confidence:** HIGH

### Gaps to Address

- **Stack Auth user ID format:** Is it a UUID compatible with existing Supabase foreign keys, or a custom format requiring a mapping column? Verify during Phase 1 implementation by creating a test user in Stack Auth.
- **Stack Auth password hash import:** Can Stack Auth accept bcrypt hashes during user migration, or does progressive migration (re-auth on first login) need to be the primary strategy? Check Stack Auth Admin API during Phase 1 planning.
- **Stripe Connect vs basic Checkout for MVP:** Architecture research recommends deferring Connect post-launch (collect all payments to platform, settle with owners offline). Features research recommends Connect from the start for owner trust. **Recommendation: start with basic Checkout (no Connect), add Connect in Phase 5 when owner onboarding is built.** This avoids premature complexity.
- **Credit-to-EUR conversion rate:** If credits coexist with Stripe, what's the exchange rate? Is it fixed (1 credit = €1) or variable? This is a product decision that impacts Phase 4 implementation.
- **RBAC mapping to Stack Auth Teams:** Stack Auth supports Teams with hierarchical permissions. Decide whether to use Stack Auth Teams for customer/owner/admin roles or keep roles in Supabase `users` table. **Recommendation: keep roles in Supabase** (it's application-specific data), sync only identity from Stack Auth.

## Sources

### Primary (HIGH confidence)
- Stack Auth JWKS endpoint: [stack-auth/stack-auth#627](https://github.com/stack-auth/stack-auth/issues/627)
- Stack Auth npm package: https://www.npmjs.com/package/@stackframe/stack
- Stripe Checkout documentation: https://docs.stripe.com/checkout/quickstart
- Stripe Connect documentation: https://docs.stripe.com/connect
- Stripe webhook signature verification: https://docs.stripe.com/webhooks/signature
- next-intl App Router setup: https://next-intl.dev/docs/getting-started/app-router/with-i18n-routing
- Playwright documentation: https://playwright.dev
- Vitest documentation: https://vitest.dev
- Optix coworking booking systems comparison: optixapp.com/blog
- Spacebring coworking software guide: spacebring.com
- LibreWork codebase audit: `.planning/codebase/CONCERNS.md`, backend route files, frontend hooks

### Secondary (MEDIUM confidence)
- Stack Auth backend integration docs: https://docs.stack-auth.com/docs/python/concepts/backend-integration (docs redirect; info from search extracts)
- Stack Auth permissions/RBAC: https://docs.stack-auth.com/docs/js/concepts/permissions
- Resend FastAPI integration: https://resend.com/fastapi
- eOffice "Instant Booking: New Standard for 2026": eoffice.net
- Othership listing guide: knowledge.othership.com

### Tertiary (LOW confidence)
- Stack Auth password hash import capability — not documented; needs direct API testing
- Stripe Extended Authorization eligibility — requires merchant account review

---
*Research completed: 2026-02-20*
*Ready for roadmap: yes*
