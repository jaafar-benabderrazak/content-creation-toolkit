# Requirements

## v1 Requirements

### Authentication (AUTH)

- [ ] **AUTH-01**: User can sign up and log in via Stack Auth (email/password), replacing all custom JWT auth
- [ ] **AUTH-02**: User session is managed by Stack Auth SDK; frontend uses `useUser()` instead of custom hooks
- [x] **AUTH-03**: Backend verifies Stack Auth JWTs via JWKS (RS256, cached) instead of custom `decode_access_token()`
- [ ] **AUTH-04**: All three frontend auth hooks (useAuth, useSimpleAuth, useAuth_replit) are replaced by Stack Auth's hook
- [ ] **AUTH-05**: Legacy auth code is removed (Supabase Auth router, next-auth, python-jose, passlib)
- [ ] **AUTH-06**: Navbar correctly shows authenticated/unauthenticated state based on Stack Auth session
- [ ] **AUTH-07**: Owner components use correct token source (no more token vs access_token mismatch)
- [x] **AUTH-08**: RBAC roles (customer, owner, admin) work with Stack Auth user metadata
- [ ] **AUTH-09**: Existing user accounts are migrated or re-created in Stack Auth

### Payments (PAY)

- [x] **PAY-01**: User can pay for a reservation using Stripe Checkout (card payment)
- [x] **PAY-02**: Backend creates Stripe Checkout sessions and handles webhooks for payment confirmation
- [x] **PAY-03**: Reservation status updates automatically on successful payment (webhook-driven)
- [ ] **PAY-04**: User can view payment history and receipts

### Email (EMAIL)

- [x] **EMAIL-01**: System sends transactional emails for password reset, booking confirmation, and cancellation
- [x] **EMAIL-02**: Email delivery uses Resend (or equivalent) instead of printing tokens to console
- [x] **EMAIL-03**: System can send marketing emails (promotions, newsletter) to opted-in users

### Search & Discovery (SEARCH)

- [x] **SEARCH-01**: User can discover establishments via interactive map + list view
- [ ] **SEARCH-02**: Spatial queries use PostGIS instead of in-memory distance filtering
- [ ] **SEARCH-03**: User can filter by price range, amenities, capacity, and rating
- [ ] **SEARCH-04**: User can filter by "open now" based on establishment opening hours

### UX & Frontend (UX)

- [x] **UX-01**: All views are fully responsive on mobile, tablet, and desktop
- [ ] **UX-02**: UI is refreshed with consistent design system (colors, typography, spacing, components)
- [ ] **UX-03**: Frontend uses proper App Router routes instead of SPA-in-one-page conditional rendering

### Internationalization (I18N)

- [ ] **I18N-01**: next-intl is configured with `[locale]` routing (FR/EN)
- [ ] **I18N-02**: All user-facing UI text is translated to French and English

### Owner Tools (OWNER)

- [x] **OWNER-01**: Owner can view analytics dashboard showing occupancy rates, revenue, and booking trends

### Infrastructure (INFRA)

- [ ] **INFRA-01**: Auth, RBAC, and core API endpoints have automated test coverage
- [ ] **INFRA-02**: Backend uses structured logging (structlog) instead of print statements
- [x] **INFRA-03**: Password column naming is standardized to `hashed_password` across all migrations and scripts
- [ ] **INFRA-04**: Double-booking is prevented at the database level (exclusion constraint or RPC function)

## v2 Requirements (Deferred)

- Credit + Stripe hybrid payments (use credits or card) -- adds complexity; ship card-only first
- Stripe Connect for owner payouts -- marketplace model; ship basic payments first
- Refund handling with cancellation policies -- ship manual refunds first
- Invoice generation -- nice-to-have; receipts suffice for v1
- Booking reminders (email before upcoming reservation) -- ship confirmations first
- Owner notifications (new booking, cancellation alerts) -- add after transactional emails work
- Social login via Stack Auth (Google, GitHub) -- add after core auth migration
- Guided onboarding flow (sign-up to first booking) -- add after core UX is solid
- Multi-location management for owners -- add after single-location analytics works
- Self-service owner onboarding with admin approval -- add after owner tools stabilize
- Backend returns error codes for frontend translation -- add as i18n matures

## Out of Scope

- Native mobile app -- responsive web covers mobile; not justified pre-launch
- Real-time chat -- email/notifications suffice for user-owner communication
- AI recommendations -- premature without usage data; solid search/filter is the priority
- Cryptocurrency payments -- Stripe covers all needed payment methods
- Dynamic pricing / subscriptions -- keep pricing simple for first release
- Self-hosted auth -- Stack Auth handles auth infrastructure

## Traceability

<!-- Updated by roadmapper: requirement → phase mapping -->

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1: Auth Migration | Pending |
| AUTH-02 | Phase 1: Auth Migration | Pending |
| AUTH-03 | Phase 1: Auth Migration | Complete |
| AUTH-04 | Phase 1: Auth Migration | Pending |
| AUTH-05 | Phase 1: Auth Migration | Pending |
| AUTH-06 | Phase 1: Auth Migration | Pending |
| AUTH-07 | Phase 1: Auth Migration | Pending |
| AUTH-08 | Phase 1: Auth Migration | Complete |
| AUTH-09 | Phase 1: Auth Migration | Pending |
| PAY-01 | Phase 6: Stripe Payments | Complete |
| PAY-02 | Phase 6: Stripe Payments | Complete |
| PAY-03 | Phase 6: Stripe Payments | Complete |
| PAY-04 | Phase 6: Stripe Payments | Pending |
| EMAIL-01 | Phase 4: Email Delivery | Complete |
| EMAIL-02 | Phase 4: Email Delivery | Complete |
| EMAIL-03 | Phase 4: Email Delivery | Complete |
| SEARCH-01 | Phase 5: Search & Discovery | Complete |
| SEARCH-02 | Phase 5: Search & Discovery | Pending |
| SEARCH-03 | Phase 5: Search & Discovery | Pending |
| SEARCH-04 | Phase 5: Search & Discovery | Pending |
| UX-01 | Phase 8: UI Polish & Responsive Design | Complete |
| UX-02 | Phase 8: UI Polish & Responsive Design | Pending |
| UX-03 | Phase 3: Frontend Restructuring & i18n | Pending |
| I18N-01 | Phase 3: Frontend Restructuring & i18n | Pending |
| I18N-02 | Phase 3: Frontend Restructuring & i18n | Pending |
| OWNER-01 | Phase 7: Owner Analytics | Complete |
| INFRA-01 | Phase 2: Testing & Logging | Pending |
| INFRA-02 | Phase 2: Testing & Logging | Pending |
| INFRA-03 | Phase 1: Auth Migration | Complete |
| INFRA-04 | Phase 6: Stripe Payments | Pending |

---
*Last updated: 2026-02-20 after roadmap creation*
