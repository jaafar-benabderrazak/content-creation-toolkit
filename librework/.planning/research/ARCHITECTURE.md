# Architecture Patterns

**Domain:** Coworking/shared workspace reservation platform
**Researched:** 2026-02-20
**Confidence:** MEDIUM-HIGH (Stack Auth docs partially inaccessible; patterns verified via REST API docs, GitHub issues, and community examples)

## Current Architecture Summary

LibreWork is a separated frontend/backend monorepo:

- **Frontend:** Next.js 14 (App Router), React 18, Tailwind + shadcn/ui, React Query, Zustand
- **Backend:** FastAPI 0.115, Pydantic v2, python-jose (JWT), passlib (bcrypt)
- **Database:** Supabase PostgreSQL (used via Python client, no ORM)
- **Auth (current):** Custom JWT with HS256 signing, dual auth subsystems (legacy + enhanced)
- **Frontend routing:** SPA-style — single `page.tsx` with conditional component rendering via `useState`

The frontend is effectively a client-rendered SPA living inside the App Router. It uses `localStorage` for tokens and `axios` interceptors for Bearer auth. The backend exposes all endpoints under `/api/v1` with FastAPI's `Depends()` for auth injection.

## Recommended Architecture (Post-Integration)

### High-Level Component Map

```
┌──────────────────────────────────────────────────────────┐
│                        BROWSER                           │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Next.js Frontend  (Vercel)                         │ │
│  │                                                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │ │
│  │  │ Stack    │  │ next-intl│  │ React Query +    │  │ │
│  │  │ Auth SDK │  │ i18n     │  │ Axios client     │  │ │
│  │  └────┬─────┘  └──────────┘  └────────┬─────────┘  │ │
│  │       │                               │             │ │
│  │       │  access_token via             │  Bearer     │ │
│  │       │  getAuthHeaders()             │  token      │ │
│  └───────┼───────────────────────────────┼─────────────┘ │
└──────────┼───────────────────────────────┼───────────────┘
           │                               │
           ▼                               ▼
┌────────────────┐              ┌──────────────────────────┐
│  Stack Auth    │              │  FastAPI Backend (Railway)│
│  (Managed)     │              │                          │
│                │   JWKS       │  ┌──────────────────┐    │
│  - User mgmt   │◄─────────────│  │ stack_auth_dep() │    │
│  - Social login │              │  │ (JWKS verify)    │    │
│  - Token issue  │              │  └──────┬───────────┘    │
│  - JWKS endpoint│              │         │                │
└────────────────┘              │  ┌──────▼───────────┐    │
                                │  │ RBAC middleware   │    │
┌────────────────┐              │  └──────┬───────────┘    │
│  Stripe        │              │         │                │
│                │   webhooks   │  ┌──────▼───────────┐    │
│  - Checkout    │─────────────►│  │ API Routers      │    │
│  - Connect     │              │  │ (reservations,   │    │
│  - Webhooks    │              │  │  payments,       │    │
│                │              │  │  analytics, etc) │    │
└────────────────┘              │  └──────┬───────────┘    │
                                │         │                │
                                │  ┌──────▼───────────┐    │
                                │  │ Supabase Client   │    │
                                │  └──────┬───────────┘    │
                                └─────────┼────────────────┘
                                          │
                                          ▼
                                ┌──────────────────────────┐
                                │  Supabase PostgreSQL     │
                                │                          │
                                │  users, establishments,  │
                                │  reservations, payments, │
                                │  analytics_events        │
                                └──────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Next.js Frontend** | UI rendering, i18n, client-side auth state, Stripe Checkout redirect | Stack Auth SDK, FastAPI Backend |
| **Stack Auth (Managed)** | User registration, login, social login, token issuance, JWKS | Frontend (SDK), Backend (JWKS verification) |
| **FastAPI Backend** | Business logic, RBAC, data access, Stripe webhooks, analytics aggregation | Stack Auth (JWKS), Supabase (DB), Stripe (webhooks + API) |
| **Supabase PostgreSQL** | Data persistence, RLS (future), stored procedures | Backend only (no direct frontend access) |
| **Stripe** | Payment processing, checkout sessions, webhook events | Backend (API + webhooks), Frontend (redirect to Checkout) |

### Boundary Rules

1. **Frontend never talks to Supabase directly** — all data flows through FastAPI. The existing `frontend/src/lib/supabase.ts` client should be removed.
2. **Frontend never handles payment logic** — it redirects to Stripe Checkout and shows results; all payment state lives in the backend.
3. **Backend is the single source of truth for RBAC** — Stack Auth provides identity; the backend's `users` table and RBAC system control authorization.
4. **Stack Auth is the single source of truth for identity** — no password hashing, no custom JWT issuance, no refresh token management in the backend.

---

## Integration Pattern: Stack Auth → FastAPI

### Strategy: JWT Verification via JWKS (LOCAL)

**Why not the REST API approach:** Stack Auth offers two verification methods — calling their REST API (`/api/v1/users/me`) or verifying the JWT locally using their JWKS endpoint. Local JWKS verification is strongly preferred because:

- No network round-trip per request (latency: ~0ms vs ~100-200ms)
- No dependency on Stack Auth's availability for every API call
- The existing codebase already uses `python-jose` for JWT operations

**JWKS Endpoint:**
```
https://api.stack-auth.com/api/v1/projects/<PROJECT_ID>/.well-known/jwks.json
```

Cache the JWKS with a 30-minute TTL (per Stack Auth maintainer recommendation in [stack-auth/stack-auth#627](https://github.com/stack-auth/stack-auth/issues/627)).

**Confidence:** HIGH — JWKS endpoint URL confirmed via GitHub issue and official docs reference. Caching TTL confirmed by maintainer.

### Implementation: New FastAPI Dependency

Replace both `dependencies.get_current_user` and `auth_enhanced.get_current_user` with a single Stack Auth dependency:

```python
# backend/app/core/stack_auth.py

import httpx
from jose import jwt, jwk, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from app.core.config import settings
import time

security = HTTPBearer()

_jwks_cache = {"keys": None, "fetched_at": 0}
JWKS_TTL_SECONDS = 1800  # 30 minutes

async def _get_jwks():
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_TTL_SECONDS:
        return _jwks_cache["keys"]

    url = f"https://api.stack-auth.com/api/v1/projects/{settings.STACK_AUTH_PROJECT_ID}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        _jwks_cache["keys"] = resp.json()["keys"]
        _jwks_cache["fetched_at"] = now
        return _jwks_cache["keys"]

async def get_current_user_id(
    credentials = Depends(security),
) -> str:
    token = credentials.credentials
    keys = await _get_jwks()

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key = next((k for k in keys if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Unknown signing key")

        payload = jwt.decode(
            token, key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing sub claim")
        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Key changes from current auth:**

| Aspect | Current | After Stack Auth |
|--------|---------|------------------|
| Signing algorithm | HS256 (symmetric) | RS256 (asymmetric, JWKS) |
| Token issuer | FastAPI backend | Stack Auth (managed) |
| Token storage (frontend) | `localStorage.access_token` | Stack Auth SDK manages tokens internally |
| Header format | `Authorization: Bearer <token>` | Same — Stack Auth tokens are standard JWTs |
| User lookup | Decode JWT → fetch from `users` table | Decode JWT → fetch from `users` table (same) |
| Refresh flow | Custom `/auth/refresh` endpoint | Stack Auth SDK handles refresh automatically |

### User Sync: Stack Auth ↔ Supabase `users` Table

Stack Auth manages identity (email, name, social accounts). The `users` table in Supabase holds domain data (role, credits, loyalty). These must stay in sync.

**Strategy: First-request provisioning (lazy sync)**

1. Stack Auth issues a JWT with a `sub` claim (the Stack Auth user ID).
2. On each authenticated request, the FastAPI dependency decodes the JWT and looks up `sub` in the `users` table.
3. If the user doesn't exist in `users`, create a row with defaults (`role=customer`, `coffee_credits=10`).
4. If they exist, proceed normally.

This avoids needing a webhook from Stack Auth for user creation and handles the case cleanly.

**Migration path for existing users:** Write a one-time migration script that:
1. Creates Stack Auth accounts for each existing user (via Stack Auth REST API).
2. Updates the `users.id` column to use the Stack Auth user ID (or adds a `stack_auth_id` column and maps).

**Confidence:** MEDIUM — Lazy sync is a well-established pattern. The user ID format from Stack Auth (UUID vs custom) needs verification during implementation.

### Frontend Auth Changes

Replace the three auth hooks (`useAuth`, `useSimpleAuth`, `useAuth_replit`) with Stack Auth's React SDK:

```typescript
// Single source of auth truth
import { useUser } from "@stackframe/stack";

// In components:
const user = useUser({ or: "redirect" }); // redirects to login if not authed
const user = useUser();                     // returns null if not authed
```

**Token passing to backend** — The axios interceptor changes from reading `localStorage` to using Stack Auth's `getAuthHeaders()`:

```typescript
import { stackClientApp } from "@/lib/stack-auth";

api.interceptors.request.use(async (config) => {
  const authHeaders = await stackClientApp.getAuthHeaders();
  if (authHeaders) {
    config.headers = { ...config.headers, ...authHeaders };
  }
  return config;
});
```

The backend extracts the token from `Authorization: Bearer <token>` (or `x-stack-access-token` header — both work; Bearer is more conventional for existing code).

---

## Integration Pattern: Stripe Payments

### Decision: Stripe Checkout (not Elements) + Webhooks on FastAPI

**Why Stripe Checkout:** Pre-built payment page hosted by Stripe. No PCI compliance burden, no card form to build, handles 3D Secure automatically. Perfect for a reservation booking flow where users pay a known amount.

**Why webhooks on FastAPI (not Next.js):**
- The backend owns reservation state and database writes — putting webhooks in Next.js would create a split-brain where payment confirmation lives in a different process from reservation confirmation.
- Next.js API routes in serverless environments (Vercel) have cold-start issues with webhook signature verification (timestamp tolerance failures).
- FastAPI handles raw request bodies cleanly via `Request.body()`, which is required for Stripe signature verification.

**Confidence:** HIGH — This is the standard architecture for Next.js + separate backend. Serverless webhook issues are well-documented.

### Payment Flow

```
User clicks "Book & Pay"
        │
        ▼
┌───────────────────┐     POST /payments/checkout-session
│  Frontend         │────────────────────────────────────►┌──────────────────┐
│                   │                                      │  FastAPI Backend  │
│                   │◄─────────────────────────────────────│                  │
│                   │     { checkout_url: "..." }           │  1. Validate      │
│                   │                                      │     reservation   │
│  2. Redirect to   │                                      │  2. Create Stripe │
│     Stripe        │                                      │     Checkout      │
│     Checkout      │                                      │     Session       │
│                   │                                      │  3. Save pending  │
│                   │                                      │     payment row   │
└───────────────────┘                                      └──────────────────┘
        │
        ▼
┌───────────────────┐
│  Stripe Checkout  │
│  (hosted)         │
│                   │
│  User pays →      │
└───────┬───────────┘
        │
        │  success_url redirect          webhook: checkout.session.completed
        │  (just UI confirmation)         │
        ▼                                 ▼
┌───────────────────┐           ┌──────────────────┐
│  Frontend         │           │  FastAPI Backend  │
│  /booking/success │           │                  │
│  "Booking         │           │  POST /webhooks/ │
│   confirmed!"     │           │       stripe     │
│                   │           │                  │
│  (polls backend   │           │  1. Verify sig   │
│   for actual      │           │  2. Update       │
│   status)         │           │     payment →    │
│                   │           │     completed    │
│                   │           │  3. Confirm      │
│                   │           │     reservation  │
│                   │           │  4. Deduct       │
│                   │           │     credits (if  │
│                   │           │     hybrid)      │
└───────────────────┘           └──────────────────┘
```

### Database Schema Additions

```sql
-- New table: payments
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reservation_id UUID NOT NULL REFERENCES reservations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    stripe_checkout_session_id TEXT UNIQUE,
    stripe_payment_intent_id TEXT UNIQUE,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency TEXT NOT NULL DEFAULT 'eur',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_payments_reservation ON payments(reservation_id);
CREATE INDEX idx_payments_stripe_session ON payments(stripe_checkout_session_id);
```

### Reservation Flow Change

Currently, `create_reservation` immediately confirms and deducts credits. With Stripe:

1. `POST /reservations` creates reservation with `status = 'pending_payment'` (new status).
2. `POST /payments/checkout-session` creates a Stripe Checkout Session linked to the reservation.
3. Frontend redirects user to Stripe.
4. Webhook `checkout.session.completed` fires → backend updates payment to `completed`, reservation to `confirmed`.
5. If payment fails or user abandons, a background task (or Stripe webhook `checkout.session.expired`) cancels the reservation after a timeout.

**Credits + Stripe coexistence:** Keep credits as an alternative payment method. The checkout flow branches: if user selects credits, deduct immediately and confirm; if user selects Stripe, follow the flow above.

### Stripe Connect (Future — Not MVP)

For owner payouts, Stripe Connect with "separate charges and transfers" would be the right model. Each owner would onboard as a Connected Account, and the platform takes an application fee per reservation. This is complex and should be deferred post-launch — for now, the platform collects all payments and settles with owners offline.

**Confidence:** HIGH for Checkout + webhook pattern. MEDIUM for Connect (not yet implemented, standard but complex).

---

## Integration Pattern: Internationalization (i18n)

### Strategy: Frontend-Owned i18n with Backend Error Codes

**Core principle:** The frontend handles all user-facing text translation. The backend returns structured error codes and data, not translated strings.

**Why this split:**
- The frontend already renders all UI — it knows the user's locale.
- The backend serves multiple clients (could serve a mobile app later) — embedding locale-specific strings in API responses couples the backend to presentation concerns.
- `next-intl` is the mature, well-supported i18n library for Next.js App Router and handles server components natively.

**Confidence:** HIGH — `next-intl` is the community standard for Next.js i18n. Backend-returns-codes pattern is a well-established API design practice.

### Frontend i18n Architecture

**Library:** `next-intl` (v4+)

**Routing approach:** `as-needed` locale prefix — French (`/fr/explore`) and English (`/explore` — default, no prefix). This requires moving from the current SPA-in-one-page pattern to proper App Router routes.

**File structure after i18n:**
```
frontend/
├── src/
│   ├── app/
│   │   └── [locale]/
│   │       ├── layout.tsx          ← NextIntlClientProvider wraps here
│   │       ├── page.tsx            ← Home
│   │       ├── explore/page.tsx    ← Explore
│   │       ├── spaces/[id]/page.tsx
│   │       ├── dashboard/page.tsx
│   │       ├── owner/
│   │       │   ├── dashboard/page.tsx
│   │       │   └── admin/page.tsx
│   │       ├── booking/
│   │       │   ├── success/page.tsx
│   │       │   └── cancel/page.tsx
│   │       ├── login/page.tsx
│   │       └── register/page.tsx
│   ├── i18n/
│   │   ├── routing.ts             ← defineRouting({locales: ['en','fr'], defaultLocale: 'en'})
│   │   ├── request.ts             ← getRequestConfig for server components
│   │   └── navigation.ts          ← locale-aware Link, redirect, useRouter
│   ├── messages/
│   │   ├── en.json
│   │   └── fr.json
│   └── middleware.ts              ← createMiddleware from next-intl
```

**This requires a structural refactor:** The current SPA pattern (`page.tsx` with `useState` for page switching) must be replaced with actual App Router routes. This is a prerequisite for i18n because `next-intl` uses the `[locale]` dynamic segment. The refactor is also independently valuable — it enables proper URL-based navigation, deep linking, and browser back/forward.

### Backend i18n Strategy

The backend does NOT translate messages. Instead:

1. **Error responses** return a machine-readable code + English fallback:
   ```json
   {
     "error_code": "INSUFFICIENT_CREDITS",
     "detail": "Insufficient credits. Need 5, have 2",
     "params": {"required": 5, "available": 2}
   }
   ```

2. **The frontend maps error codes to translations:**
   ```json
   // messages/en.json
   {
     "errors": {
       "INSUFFICIENT_CREDITS": "Insufficient credits. You need {required}, but have {available}."
     }
   }
   // messages/fr.json
   {
     "errors": {
       "INSUFFICIENT_CREDITS": "Crédits insuffisants. Vous avez besoin de {required}, mais vous n'en avez que {available}."
     }
   }
   ```

3. **User-generated content** (establishment names, descriptions, reviews) stays in the language it was written. No backend translation layer needed for MVP.

4. **Accept-Language header** — The frontend sends the user's locale in `Accept-Language` on API requests. The backend can use this for future locale-sensitive logic (date formatting, currency display) but does not use it for text translation.

**Confidence:** HIGH — error-code pattern is standard REST API practice. `next-intl` is well-documented for this use case.

---

## Integration Pattern: Owner Analytics Dashboard

### Strategy: Aggregation Queries in FastAPI, Visualization in Frontend

Analytics does not require a separate service or data pipeline at LibreWork's scale (pre-launch, likely < 1000 reservations). The pattern is:

1. **Backend exposes analytics endpoints** that run aggregation queries against existing tables.
2. **Frontend renders charts** using a lightweight library (Recharts, already common in the React ecosystem).

### Analytics Endpoints

```
GET /api/v1/analytics/occupancy
  ?establishment_id=...&period=week|month|year
  → { data: [{ date: "2026-02-20", occupancy_rate: 0.75, total_slots: 40, booked_slots: 30 }] }

GET /api/v1/analytics/revenue
  ?establishment_id=...&period=week|month|year
  → { data: [{ date: "2026-02-20", revenue_cents: 15000, reservations: 12 }] }

GET /api/v1/analytics/trends
  ?establishment_id=...
  → { popular_hours: [...], popular_days: [...], avg_duration_hours: 2.3, repeat_rate: 0.45 }
```

### Data Source

All analytics derive from existing tables — no separate analytics events table needed for MVP:

- **Occupancy:** `reservations` table grouped by date, compared against total `spaces` count
- **Revenue:** `payments` table grouped by date (once Stripe is integrated)
- **Trends:** `reservations` table aggregated by hour-of-day, day-of-week

If analytics queries become too slow on the main database (unlikely at MVP scale), add materialized views or a daily aggregation cron job — not a separate data warehouse.

**Confidence:** HIGH — straightforward aggregation pattern, no exotic infrastructure needed.

---

## Suggested Build Order

Dependencies between features dictate this sequence:

### Phase 1: Auth Migration (Stack Auth)
**Prerequisite for everything.** All other features depend on a working, unified auth system.

1. Set up Stack Auth project, configure social providers
2. Create `backend/app/core/stack_auth.py` with JWKS verification dependency
3. Install `@stackframe/stack` SDK in frontend
4. Replace `useAuth` / `useSimpleAuth` / `useAuth_replit` with Stack Auth's `useUser`
5. Update axios interceptor to use `getAuthHeaders()`
6. Update all backend routers to use the new `get_current_user` dependency
7. Remove legacy auth files: `security.py` (JWT issuance), `auth_simple.py`, `auth_enhanced.py`, `auth.py` router, `auth_enhanced.py` router
8. Run user migration script for any existing test data

**Risk:** User ID format mismatch between Stack Auth and existing `users.id` (currently `UUID REFERENCES auth.users`). The migration must handle re-keying or adding a mapping column.

### Phase 2: Frontend Route Refactor
**Prerequisite for i18n.** Also independently valuable.

1. Convert SPA page-switching (`useState<Page>`) to actual App Router routes
2. Move each "page" component into its own route directory
3. Replace `onNavigate` prop threading with Next.js `<Link>` and `useRouter`
4. Add `[locale]` segment wrapper (prepares for i18n)

**Risk:** Low — mechanical refactor, but touches every component's navigation props.

### Phase 3: Internationalization (i18n)
**Depends on Phase 2** (route structure must exist for `[locale]` segment).

1. Install and configure `next-intl`
2. Create `/messages/en.json` and `/messages/fr.json` with initial translations
3. Add `middleware.ts` for locale detection
4. Wrap root layout with `NextIntlClientProvider`
5. Convert hardcoded strings in components to `useTranslations()` / `getTranslations()`
6. Standardize backend error responses to use error codes with params

### Phase 4: Stripe Payments
**Depends on Phase 1** (auth must work for payment endpoints). Independent of i18n.

1. Add `payments` table migration
2. Add `pending_payment` status to reservation enum
3. Create `backend/app/api/v1/payments.py` router (checkout session creation)
4. Create `backend/app/api/v1/webhooks.py` router (Stripe webhook handler)
5. Add Stripe config to `Settings` (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`)
6. Build checkout flow in frontend (book → redirect → success/cancel pages)
7. Handle credits-vs-Stripe branching in reservation creation

### Phase 5: Owner Analytics
**Depends on Phase 1** (owner auth) and **Phase 4** (revenue data from payments).

1. Create `backend/app/api/v1/analytics.py` router
2. Write aggregation queries for occupancy, revenue, trends
3. Build frontend dashboard charts (Recharts or similar)
4. Add owner-only route protection using Stack Auth permissions or backend RBAC

### Parallelism Opportunities

- **Phase 2 + Phase 4** can run in parallel (route refactor and Stripe backend work are independent).
- **Phase 3** must wait for Phase 2.
- **Phase 5** can start its backend work during Phase 3/4, with frontend work after Phase 4 completes.

```
Phase 1: Auth ──────────────────►
                                  \
Phase 2: Routes ──────────►        \
                            \       \
Phase 3: i18n ──────────────►\       \
                               \      \
Phase 4: Stripe ────────────────►──────►
                                        \
Phase 5: Analytics ──────────────────────►
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Dual Auth During Migration
**What:** Keeping both custom JWT and Stack Auth active simultaneously with feature flags.
**Why bad:** Every endpoint must handle both token formats. Bugs emerge from token confusion (the existing `token` vs `access_token` localStorage key issue proves this). Doubles testing surface.
**Instead:** Migrate auth in one phase. The project has no live users — there's no need for gradual rollout.

### Anti-Pattern 2: Stripe Webhooks in Next.js API Routes
**What:** Handling `checkout.session.completed` in `app/api/webhooks/stripe/route.ts`.
**Why bad:** Creates two sources of truth for reservation state. The backend owns `reservations` and `payments` tables — splitting write responsibility across processes leads to race conditions and consistency bugs.
**Instead:** All Stripe webhooks go to FastAPI. The frontend only shows UI based on what it reads from the backend.

### Anti-Pattern 3: Translating in the Backend
**What:** Having FastAPI return locale-specific error messages using `Accept-Language`.
**Why bad:** Couples backend to presentation. Makes error handling inconsistent (some errors translated, some not). Breaks when the backend serves non-browser clients.
**Instead:** Backend returns error codes + params. Frontend translates.

### Anti-Pattern 4: Premature Analytics Infrastructure
**What:** Adding Kafka, ClickHouse, or a separate analytics database before there's enough data to justify it.
**Why bad:** Massive complexity for a pre-launch product with near-zero data volume. Simple SQL aggregations handle the workload fine.
**Instead:** Aggregate from existing tables. Revisit when query performance becomes measurable problem (likely > 100k reservations).

### Anti-Pattern 5: Stack Auth REST API Per Request
**What:** Calling Stack Auth's `/api/v1/users/me` on every authenticated request instead of JWKS verification.
**Why bad:** Adds 100-200ms latency to every API call. Creates a hard dependency on Stack Auth availability. Rate limit risk under load.
**Instead:** JWKS-based local JWT verification with 30-minute cache. Only call the REST API for admin operations (user management, role changes).

---

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|-------------|-------------|-------------|
| Auth verification | JWKS local verify (fine) | JWKS local verify (fine) | JWKS local verify (fine) |
| Payment webhooks | Single FastAPI endpoint (fine) | Single endpoint (fine) | Async queue (SQS/Redis) between webhook receipt and processing |
| Analytics queries | Direct SQL aggregation | Direct SQL, maybe add indexes | Materialized views or pre-computed daily rollups |
| i18n bundle size | Both locales loaded (fine) | Both locales loaded (fine) | Split by route/namespace if bundles grow |
| Database | Single Supabase instance | Single instance with read replica | Connection pooling (PgBouncer), read replicas |

---

## Sources

- Stack Auth JWKS endpoint: [stack-auth/stack-auth#627](https://github.com/stack-auth/stack-auth/issues/627) — HIGH confidence
- Stack Auth backend integration: [docs.stack-auth.com/docs/python/concepts/backend-integration](https://docs.stack-auth.com/docs/python/concepts/backend-integration) — MEDIUM confidence (docs redirect; info from search extracts)
- Stack Auth permissions/RBAC: [docs.stack-auth.com/docs/js/concepts/permissions](https://docs.stack-auth.com/docs/js/concepts/permissions) — MEDIUM confidence
- Stack Auth token format (`getAuthJson`): [docs.stack-auth.com/sdk/objects/stack-app](https://docs.stack-auth.com/sdk/objects/stack-app) — MEDIUM confidence
- Stripe Checkout + FastAPI: [fast-saas.com/blog/fastapi-stripe-integration](https://www.fast-saas.com/blog/fastapi-stripe-integration/) — HIGH confidence
- Stripe webhooks signature verification: [docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature) — HIGH confidence
- Stripe Connect marketplace: [docs.stripe.com/connect](https://docs.stripe.com/connect) — HIGH confidence
- next-intl App Router setup: [next-intl.dev/docs/getting-started/app-router/with-i18n-routing](https://next-intl.dev/docs/getting-started/app-router/with-i18n-routing) — HIGH confidence
- next-intl server components: [next-intl.dev/docs/environments/server-client-components](https://next-intl.dev/docs/environments/server-client-components) — HIGH confidence
- FastAPI i18n patterns: [lokalise.com/blog/fastapi-internationalization](https://lokalise.com/blog/fastapi-internationalization/) — MEDIUM confidence

---

*Architecture research: 2026-02-20*
