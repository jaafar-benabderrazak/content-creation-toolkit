# LibreWork

## What This Is

LibreWork is a coworking and shared workspace reservation platform that connects people looking for workspaces with establishment owners who offer them. Users can discover, explore, and book coworking spaces, while owners manage their establishments, track reservations, and grow their business. The platform targets the French and English-speaking market with a modern, mobile-first experience.

## Core Value

Users can find a workspace and book it in under 2 minutes -- the search-to-reservation flow must be fast, clear, and reliable.

## Requirements

### Validated

- ✓ User registration and login (custom JWT + Supabase) -- existing
- ✓ Establishment listings with details, categories, amenities -- existing
- ✓ Space discovery with search and filtering -- existing
- ✓ Reservation creation and management -- existing
- ✓ Owner dashboard for managing establishments -- existing
- ✓ RBAC with customer/owner/admin roles -- existing
- ✓ Reviews and ratings system -- existing
- ✓ Favorites / saved spaces -- existing
- ✓ Credit system for reservations -- existing
- ✓ Loyalty program -- existing
- ✓ Group reservations -- existing
- ✓ Notification system (backend structure) -- existing
- ✓ Calendar export (iCal) -- existing
- ✓ Audit logging -- existing

### Active

- [ ] Migrate authentication to Stack Auth (https://app.stack-auth.com/)
- [ ] Unify frontend auth hooks (consolidate useAuth, useSimpleAuth, useAuth_replit into one)
- [ ] Remove legacy auth code (Supabase Auth router, next-auth remnants)
- [ ] Fix Navbar authenticated state (currently hardcoded to false)
- [ ] Fix owner component token mismatch (token vs access_token)
- [ ] Implement working email delivery (password reset, notifications)
- [ ] Stripe payments integration for reservations
- [ ] Owner analytics dashboard (occupancy, revenue, trends)
- [ ] Multi-location management for owners
- [ ] Self-service owner onboarding with admin approval workflow
- [ ] Mobile-responsive design across all views
- [ ] Smooth onboarding flow (sign-up to first reservation)
- [ ] Improved search and discovery (filters, map view, open-now)
- [ ] Modern, clean UI refresh
- [ ] Internationalization (French + English)
- [ ] Working push/email notifications
- [ ] Standardize password column naming (hashed_password everywhere)
- [ ] Add proper test coverage (auth, RBAC, core endpoints)
- [ ] Add structured logging (replace print statements)

### Out of Scope

- Native mobile app -- web-first, responsive approach covers mobile for now
- Real-time chat between users and owners -- not needed for MVP; email/notifications suffice
- AI-powered recommendations -- premature; focus on solid search/filter first
- Cryptocurrency payments -- Stripe covers the needed payment methods
- Self-hosted auth -- Stack Auth handles auth infrastructure
- Dynamic pricing / subscriptions -- keep pricing simple for first release

## Context

**Current state:** LibreWork has a functional but fragile codebase. The backend (FastAPI + Supabase) covers most domain logic. The frontend (Next.js + React) has components for all major views but suffers from auth inconsistencies and incomplete features. The biggest structural problem is the auth layer: three frontend hooks, two backend auth routers, and none of them are the intended provider (Stack Auth).

**Tech debt highlights:**
- Dual auth systems (legacy Supabase Auth + enhanced custom JWT) with overlapping routes
- Three frontend auth hooks with different token key expectations
- Navbar hardcoded as unauthenticated; owner components use wrong localStorage key
- Password reset prints token to console instead of sending email
- No test coverage beyond health check; no frontend tests at all
- No structured logging; print statements in production code
- Spatial queries use in-memory filtering instead of PostGIS

**Existing stack:** Next.js 14.2 (App Router), FastAPI 0.115, React 18, Supabase (PostgreSQL), Tailwind CSS, shadcn/ui, React Query, Zustand. Backend uses Pydantic v2, python-jose for JWT, passlib for password hashing.

**Target auth provider:** Stack Auth (https://app.stack-auth.com/) -- managed auth with SSO, social login, and token management. Replaces custom JWT, Supabase Auth, and next-auth.

**Deployment:** Pre-launch. No real users. Docker Compose for local dev; Vercel + Railway suggested for production.

## Constraints

- **Auth provider**: Stack Auth (https://app.stack-auth.com/) -- decided; do not build another custom auth system
- **Payments**: Stripe -- decided; integrate for reservation payments
- **Database**: Supabase PostgreSQL -- keep as DB only; remove auth dependency on Supabase
- **Stack flexibility**: Open to replacing parts of the frontend/backend stack if justified, but default to extending what exists
- **Timeline**: Flexible -- quality over speed; no hard deadline
- **Languages**: French + English support required (i18n)
- **Mobile**: Must be responsive; no native app

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Stack Auth for authentication | Managed auth reduces custom code, provides SSO/social login, better security than hand-rolled JWT | -- Pending |
| Stripe for payments | Industry standard, well-documented, handles compliance | -- Pending |
| Supabase as DB only | Decouple auth from DB provider; Stack Auth handles identity | -- Pending |
| Self-service owner onboarding + admin approval | Lower friction for growth; admin approval maintains quality | -- Pending |
| i18n (FR + EN) | Target market is French-speaking but English broadens reach | -- Pending |
| Keep Next.js + FastAPI stack | Existing code works; rewrite cost not justified | -- Pending |

---
*Last updated: 2026-02-20 after initialization*
