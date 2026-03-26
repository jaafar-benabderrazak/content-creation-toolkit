# Phase 12: Complete Auth Migration, App Router Routes, Double-Booking Prevention, Search Filters, Structured Logging, and Test Coverage - Research

**Researched:** 2026-03-26
**Domain:** Full-stack cleanup — auth migration completion, Next.js App Router routing, PostgreSQL exclusion constraints, PostGIS spatial queries, structlog, pytest
**Confidence:** HIGH (codebase read directly; all claims grounded in source files)

---

## Summary

Phase 12 closes every remaining v1 requirement. The codebase is in an intermediate state: Stack Auth is wired at the SDK and JWT-verification layer (AUTH-03 done), but three legacy auth files still exist in the backend (`security.py`, `auth_simple.py`, `auth_enhanced.py`) that use `python-jose` + `passlib` and are still imported by `main.py`. On the frontend, `home-client.tsx` implements SPA-style conditional rendering across six views using `useState<Page>`, with `onNavigate` callbacks threading through Navbar and all page components — none of these views have their own App Router routes yet. The database schema has `opening_hours` as a JSONB column on `establishments` and a `location GEOGRAPHY(POINT)` column with a GIST index, making both PostGIS queries and open-now filtering achievable without schema changes. Double-booking currently has only an application-level check via `check_space_availability` RPC; no database-level exclusion constraint exists on the `reservations` table. The backend has no structured logging — `supabase.py` has raw `print()` calls at module level, and scattered `print()` calls exist in `auth_enhanced.py`.

**Primary recommendation:** Execute in five plans: (1) backend legacy auth removal + structlog, (2) double-booking exclusion constraint + PostGIS search, (3) App Router route extraction (UX-03), (4) frontend auth migration completion, (5) pytest coverage.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | User can sign up and log in via Stack Auth (email/password) | Login/register pages already use `<SignIn>` / Stack SDK; backend `auth.py` and `auth_enhanced.py` routers still expose legacy endpoints that must be removed |
| AUTH-02 | Frontend uses `useUser()` instead of custom hooks | `useAuth.tsx` wraps `useUser()` — thin wrapper exists but components still receive `onNavigate` which implies SPA wiring, not real auth state driving routes |
| AUTH-04 | All three frontend auth hooks replaced by Stack Auth's hook | Only `useAuth.tsx` found (wraps `useUser()`); `useSimpleAuth` and `useAuth_replit` do not appear in current frontend src — may already be gone or were never migrated in |
| AUTH-05 | Legacy auth code removed (Supabase Auth router, next-auth, python-jose, passlib) | `security.py`, `auth_simple.py`, `auth_enhanced.py` all import `from jose` and `passlib` — these three files + their router registrations must be deleted |
| AUTH-06 | Navbar shows correct auth state based on Stack Auth session | Navbar already uses `useUser()` from `@stackframe/stack` — but navigates via `onNavigate('dashboard')` not `router.push('/dashboard')` |
| AUTH-07 | Owner components use correct token source | `api.ts` already sends `x-stack-access-token`; `dependencies.py` reads that header — token source is correct; issue may be stale component-level token passing |
| AUTH-09 | Existing user accounts migrated or re-created in Stack Auth | `stack_auth_id` column added by migration 20260221; no migration script exists yet for seeding existing users |
| UX-03 | Frontend uses App Router routes instead of SPA conditional rendering | `home-client.tsx` drives all navigation via `useState<Page>` + `onNavigate` callbacks; 6 views need own routes: `/`, `/explore`, `/establishments/[id]`, `/dashboard`, `/owner/dashboard`, `/owner/admin` |
| SEARCH-02 | Spatial queries use PostGIS instead of in-memory distance filtering | `establishments.py` uses `geopy.distance.geodesic` in Python after fetching all rows; `location GEOGRAPHY(POINT)` + GIST index already exists; needs `ST_DWithin` SQL via `supabase.rpc()` |
| SEARCH-03 | User can filter by price range, amenities, capacity, and rating | `advanced_search` endpoint exists but filters amenities in Python; capacity filter absent; price filter absent; rating filter present in query |
| SEARCH-04 | User can filter by "open now" | `advanced_search` has `open_now` parameter with `# TODO: Implement` — `opening_hours` JSONB is `{"monday": {"open": "09:00", "close": "18:00"}, ...}` |
| INFRA-01 | Auth, RBAC, and core API endpoints have automated test coverage | `tests/test_main.py` has 2 trivial tests; pytest + pytest-asyncio already in requirements.txt |
| INFRA-02 | Backend uses structured logging (structlog) instead of print statements | `supabase.py` has 5 print calls at import time; `auth_enhanced.py` has 1; no logging framework configured |
| INFRA-04 | Double-booking prevented at database level | `create_reservation` calls `check_space_availability` RPC — RPC exists as application guard but no PostgreSQL exclusion constraint on `reservations` table |
</phase_requirements>

---

## Current Codebase State (Ground Truth)

### Backend Auth Files — What Exists and Must Go

| File | Status | Action |
|------|--------|--------|
| `app/core/security.py` | Legacy — `python-jose` + `passlib`, `create_access_token`, `decode_access_token`, `get_current_user_id` | DELETE |
| `app/core/auth_simple.py` | Legacy — identical to `security.py`, duplicate | DELETE |
| `app/core/auth_enhanced.py` | Legacy — `python-jose` + `passlib`, CivilDocPro-style custom JWT | DELETE |
| `app/api/v1/auth.py` | Legacy — registers `/auth/register` + `/auth/login` using Supabase Auth SDK sign_up | DELETE |
| `app/api/v1/auth_enhanced.py` | Legacy — registers `/auth/register` (duplicate route), `/auth/login`, password reset | DELETE |
| `app/core/dependencies.py` | GOOD — uses `verify_stack_auth_token` from `stack_auth.py` | KEEP |
| `app/core/stack_auth.py` | GOOD — PyJWKClient, ES256 verification | KEEP |
| `app/main.py` | Imports both `auth` and `auth_enhanced` routers | REMOVE those two imports |

**Confirmed**: `requirements.txt` contains `python-jose` (via `python-multipart` transitive? No — check directly). The file lists packages without `python-jose` or `passlib` by name — they are imported via `from jose` and `from passlib`. These are likely installed as transitive deps or were added manually. They must be removed from `requirements.txt` and from all import sites.

Actual `requirements.txt` does NOT list `python-jose` or `passlib` explicitly — they are not in the file. This means they are likely already-installed transitive packages. After deleting the three files that import them, they become unused automatically. No `requirements.txt` edit needed unless they appear as explicit entries (they do not).

### Frontend Auth — What Exists

- `useAuth.tsx` — wraps `useUser()` from `@stackframe/stack`, returns normalized user object. This is the unified hook. Any legacy `useSimpleAuth` / `useAuth_replit` references are absent from current `src/`. AUTH-04 may already be satisfied at hook level.
- `Navbar.tsx` — uses `useUser()` directly (not `useAuth()`). Auth state is correct. Navigation calls `onNavigate()` (SPA) instead of `router.push()`.
- `api.ts` — interceptor reads Stack Auth access token via `stackClientApp.getUser()` then `user.getAuthJson()`. Token header is `x-stack-access-token`. This is correct.
- `stack/client.ts` — `StackClientApp` with `tokenStore: "nextjs-cookie"`. Correct.
- Login/Register pages — use `<SignIn>` / `<SignUp>` from `@stackframe/stack`. Stack Auth UI is already wired.

### Frontend Routing — The SPA Problem

`home-client.tsx` manages `Page` type state: `'home' | 'explore' | 'details' | 'dashboard' | 'owner-dashboard' | 'owner-admin'`. All views render conditionally in a single client component. The `[locale]/page.tsx` renders `<HomeClient />` in a Suspense boundary.

**Components that use `onNavigate` and must be migrated:**
- `HomePage.tsx`
- `ExplorePage.tsx`
- `EstablishmentDetails.tsx`
- `UserDashboard.tsx`
- `OwnerDashboard.tsx`
- `OwnerAdminPage.tsx`
- `Navbar.tsx`
- `UserProfileComponent.tsx`
- `owner/EnhancedOwnerDashboard.tsx`
- `OwnerDashboardEnhanced.tsx`

Target App Router structure (under `[locale]`):
```
app/[locale]/
├── page.tsx              → HomePage
├── explore/
│   └── page.tsx          → ExplorePage
├── establishments/
│   └── [id]/
│       └── page.tsx      → EstablishmentDetails
├── dashboard/
│   └── page.tsx          → UserDashboard
├── owner/
│   ├── dashboard/
│   │   └── page.tsx      → OwnerDashboard
│   └── admin/
│       └── page.tsx      → OwnerAdminPage
├── login/
│   └── page.tsx          → (already exists, uses <SignIn>)
└── register/
    └── page.tsx          → (already exists, uses <SignUp>)
```

### Database — Reservations and Double-Booking

Current `reservations` table (from `database_schema_replit.sql`):
- `space_id UUID`, `start_time TIMESTAMP WITH TIME ZONE`, `end_time TIMESTAMP WITH TIME ZONE`
- `status reservation_status` ENUM: `pending | confirmed | cancelled | completed`
- One constraint: `CHECK (end_time > start_time)`
- No exclusion constraint

**The RPC `check_space_availability` exists** (called in `reservations.py` line 134) but is not defined in any migration file we can see — it is likely a function created directly in Supabase. It returns a boolean but provides no database-level guarantee.

**PostgreSQL exclusion constraint approach** (INFRA-04):
```sql
-- Requires btree_gist extension
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE reservations
ADD CONSTRAINT no_overlapping_reservations
EXCLUDE USING GIST (
    space_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (status IN ('pending', 'confirmed'));
```

This constraint fires at INSERT/UPDATE time and rejects overlaps atomically, even under concurrent requests. Cancelled/completed reservations are excluded from the range check via the `WHERE` clause.

**Alternative: RPC function** — wrap insert in a Postgres function that uses `FOR UPDATE` advisory lock or `SELECT ... FOR UPDATE SKIP LOCKED`. The exclusion constraint is simpler and more reliable.

### Database — PostGIS Search (SEARCH-02)

The `establishments` table has:
```sql
location GEOGRAPHY(POINT)
CREATE INDEX idx_establishments_location ON establishments USING GIST(location);
```

The `EstablishmentBase` schema has `latitude` and `longitude` float fields. The `location` column is a geography point — these are parallel representations. Current code reads `latitude`/`longitude` columns directly; `location` column may be populated or may not be (depends on existing data).

**PostGIS query via Supabase RPC:**
```python
# Create a Postgres function:
# CREATE FUNCTION establishments_within_radius(lat float, lng float, radius_meters float)
# RETURNS SETOF establishments AS $$
#   SELECT * FROM establishments
#   WHERE is_active = true
#   AND ST_DWithin(
#     location::geography,
#     ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
#     radius_meters
#   )
#   ORDER BY ST_Distance(location::geography,
#     ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography)
# $$ LANGUAGE sql STABLE;

result = supabase.rpc('establishments_within_radius', {
    'lat': latitude, 'lng': longitude, 'radius_meters': radius_km * 1000
}).execute()
```

**Important**: If the `location` column is NULL for existing rows (populated only with lat/lng), a migration must populate it:
```sql
UPDATE establishments
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE location IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;
```

### Database — Open-Now Filter (SEARCH-04)

`opening_hours` is `JSONB` with structure `{"monday": {"open": "09:00", "close": "18:00"}, "tuesday": ...}`. Days are lowercase weekday names. "closed" can be represented as `{"open": "closed", "close": "closed"}` or absent.

**Approach**: Implement in Python (simpler, avoids complex JSONB SQL):
```python
from datetime import datetime
import pytz

def is_open_now(opening_hours: dict, timezone: str = "Europe/Paris") -> bool:
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    day_name = now.strftime("%A").lower()  # "monday", "tuesday", etc.
    day_hours = opening_hours.get(day_name)
    if not day_hours:
        return False
    open_str = day_hours.get("open", "closed")
    close_str = day_hours.get("close", "closed")
    if open_str == "closed" or close_str == "closed":
        return False
    open_time = datetime.strptime(open_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo)
    close_time = datetime.strptime(close_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo)
    return open_time <= now <= close_time
```

`pytz` is already in `requirements.txt`.

### Search Filters — Missing Fields (SEARCH-03)

The `advanced_search` endpoint has `min_price`/`max_price` parameters but the filtering code does nothing with them (not implemented). `capacity` filter is also absent from implementation.

**Problem**: Price and capacity are on the `spaces` table, not `establishments`. The search endpoint returns establishments, not spaces. Options:
1. Fetch spaces per establishment in the query and filter establishments that have at least one space meeting criteria — expensive N+1.
2. Add a sub-query or join via RPC: `SELECT DISTINCT e.* FROM establishments e JOIN spaces s ON s.establishment_id = e.id WHERE s.capacity >= min_capacity AND s.credit_price_per_hour BETWEEN min_price AND max_price`.
3. Store denormalized `min_price` / `max_capacity` on establishments table.

**Recommended**: Option 2 — Supabase RPC that does the JOIN, returns EstablishmentResponse-compatible rows. Avoids denormalization.

`EstablishmentResponse` schema does not have `rating` as a column (it's an average computed from reviews). The `advanced_search` sorts by `x.rating` — this field is likely absent from DB rows unless a `rating` column was added in a later migration. Need to verify — the `database_schema_replit.sql` does not have a `rating` column on `establishments`. This is a latent bug; the filter likely silently fails.

### Structured Logging — What to Replace (INFRA-02)

`structlog` is NOT in `requirements.txt` — must be added.

Files with `print()` that need replacement:
- `app/core/supabase.py`: 5 print calls at module import time (startup diagnostics)
- `app/api/v1/auth_enhanced.py`: 1 print call (password reset token — this file gets deleted anyway)

Additional logging needed across all routers: request context (method, path, user_id, status).

**structlog setup pattern for FastAPI:**
```python
import structlog
import logging

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
```

Middleware pattern for request context:
```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        method=request.method,
        path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    response = await call_next(request)
    structlog.get_logger().info("request", status=response.status_code)
    return response
```

### Test Infrastructure — Current State (INFRA-01)

`backend/tests/test_main.py` has 2 tests: `test_root()` and `test_health_check()`. Both use `TestClient` from FastAPI which is synchronous. `pytest-asyncio` is installed.

**Problem**: `TestClient` initialization calls `app = FastAPI(...)` which imports `supabase.py` which runs `print()` at module level AND connects to Supabase. Tests will fail without `SUPABASE_URL` and `SUPABASE_KEY` env vars.

**Pattern for mocking Supabase in tests:**
```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

@pytest.fixture
def mock_supabase():
    with patch("app.core.supabase.get_supabase") as mock:
        mock.return_value = MagicMock()
        yield mock

@pytest.fixture
def client(mock_supabase):
    from app.main import app
    return TestClient(app)
```

**Pattern for mocking Stack Auth JWT verification:**
```python
@pytest.fixture
def mock_stack_auth():
    with patch("app.core.stack_auth.verify_stack_auth_token") as mock:
        mock.return_value = {"sub": "test-stack-user-id"}
        yield mock
```

Tests needed per INFRA-01:
- Auth: `POST /api/v1/auth/me` returns 401 without token, 200 with valid token
- RBAC: owner-only endpoints return 403 for customer role
- Reservations: `POST /api/v1/reservations` creates reservation, returns 409 on overlap

**Note**: `pytest-asyncio` mode must be set in `pyproject.toml` or `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

Or per-test with `@pytest.mark.asyncio`.

---

## Standard Stack

### Core (Backend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| structlog | >=24.0 | Structured JSON logging | Standard for FastAPI; processor pipeline, contextvars support |
| PyJWT[crypto] | >=2.9.0 | Stack Auth JWT verification | Already installed; ES256 JWKS verification |
| pytest | 8.3.4 | Test runner | Already installed |
| pytest-asyncio | 0.24.0 | Async test support | Already installed |
| btree_gist | PostgreSQL extension | Enables exclusion constraints on non-range types | Required for `EXCLUDE USING GIST` with UUID equality |

### Core (Frontend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @stackframe/stack | ^2.8.70 | Auth SDK | Already installed; `useUser()`, `<SignIn>`, `<SignUp>` |
| next-intl | installed | Locale-aware routing | Already configured; `useRouter` from `next-intl/navigation` for locale-aware pushes |
| next/navigation | built-in | App Router navigation | `useRouter`, `useParams` for route extraction |

### Anti-Patterns to Avoid
- **Using `router.push('/explore')` without locale prefix**: Use `useRouter` from `next-intl/navigation`, not `next/navigation`, so locale is automatically prepended.
- **Making `EstablishmentDetails` a pure client component**: It can be a Server Component that fetches establishment data by `params.id` if no auth is needed.
- **Deleting `onNavigate` props before routes exist**: Migrate one page at a time; keep `onNavigate` in remaining SPA components until all are migrated.

---

## Architecture Patterns

### App Router Migration Strategy

The SPA has 6 views. Migration order: extract each view as its own route page; replace `onNavigate(target)` calls with `router.push(localePath)`.

```
home-client.tsx before → state machine over 6 views
[locale]/page.tsx after → import HomePage directly, no HomeClient
[locale]/explore/page.tsx → import ExplorePage directly
[locale]/establishments/[id]/page.tsx → import EstablishmentDetails with params.id
[locale]/dashboard/page.tsx → import UserDashboard (auth-guarded)
[locale]/owner/dashboard/page.tsx → import OwnerDashboard (owner-guarded)
[locale]/owner/admin/page.tsx → import OwnerAdminPage (owner-guarded)
```

Navbar links change from `onNavigate('explore')` to `router.push('/explore')` (via next-intl's `useRouter`).

**Auth guard pattern** for protected routes (dashboard, owner):
```tsx
// app/[locale]/dashboard/page.tsx
import { useUser } from '@stackframe/stack'
import { redirect } from 'next/navigation'

export default function DashboardPage() {
  // For Server Component: use stackServerApp.getUser()
  // For Client Component: useUser({ or: 'redirect' })
  const user = useUser({ or: 'redirect' }) // Stack Auth built-in redirect
  return <UserDashboard />
}
```

Stack Auth's `useUser({ or: 'redirect' })` will automatically redirect to `/login` if unauthenticated. This replaces custom auth guards.

### Double-Booking Prevention — SQL Migration

New migration file `supabase/migrations/20260326000000_double_booking_constraint.sql`:
```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE reservations
ADD CONSTRAINT no_overlapping_reservations
EXCLUDE USING GIST (
    space_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (status IN ('pending', 'confirmed'));
```

The `'[)'` range is half-open: includes start, excludes end. Two back-to-back reservations (end of first = start of second) do not overlap.

Backend: catch the `exclusion_violation` (PostgreSQL error code `23P01`) and return HTTP 409:
```python
except Exception as e:
    if "no_overlapping_reservations" in str(e) or "23P01" in str(e):
        raise HTTPException(status_code=409, detail="Time slot already booked")
    raise HTTPException(status_code=400, detail=str(e))
```

### PostGIS Search RPC

New migration `supabase/migrations/20260326000001_postgis_search_rpc.sql`:
```sql
CREATE OR REPLACE FUNCTION establishments_within_radius(
    lat float, lng float, radius_meters float,
    min_capacity int DEFAULT NULL,
    min_price int DEFAULT NULL,
    max_price int DEFAULT NULL
)
RETURNS TABLE (
    id uuid, owner_id uuid, name text, description text,
    address text, city text, latitude float, longitude float,
    category text, opening_hours jsonb, amenities text[],
    services text[], images text[], is_active boolean,
    created_at timestamptz, updated_at timestamptz,
    distance_meters float
) AS $$
    SELECT e.*,
        ST_Distance(
            e.location::geography,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
        ) AS distance_meters
    FROM establishments e
    WHERE e.is_active = true
      AND ST_DWithin(
          e.location::geography,
          ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
          radius_meters
      )
      AND (min_capacity IS NULL OR EXISTS (
          SELECT 1 FROM spaces s
          WHERE s.establishment_id = e.id
            AND s.is_available = true
            AND s.capacity >= min_capacity
      ))
      AND (min_price IS NULL OR EXISTS (
          SELECT 1 FROM spaces s
          WHERE s.establishment_id = e.id
            AND s.is_available = true
            AND s.credit_price_per_hour >= min_price
      ))
      AND (max_price IS NULL OR EXISTS (
          SELECT 1 FROM spaces s
          WHERE s.establishment_id = e.id
            AND s.is_available = true
            AND s.credit_price_per_hour <= max_price
      ))
    ORDER BY distance_meters
$$ LANGUAGE sql STABLE;
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auth state in routes | Custom auth context/HOC | `useUser({ or: 'redirect' })` from `@stackframe/stack` | Built-in redirect, loading states, server-side support |
| Locale-aware navigation | Manual path construction with locale prefix | `useRouter` from `next-intl/navigation` | Automatically prepends current locale |
| Double-booking prevention | Application-level mutex or lock table | PostgreSQL exclusion constraint with `btree_gist` | Atomic at DB level, works under concurrent requests |
| Spatial distance filtering | Python `geopy.distance.geodesic` post-fetch | PostGIS `ST_DWithin` + `ST_Distance` in SQL | Pushes filtering to DB; avoids full-table scan |
| Structured logging format | Custom JSON log formatter | `structlog` with `JSONRenderer` processor | Handles contextvars, exception formatting, async-safe |
| JWT in tests | Real JWKS HTTP call | `unittest.mock.patch` on `verify_stack_auth_token` | Eliminates network dependency in unit tests |

**Key insight:** The exclusion constraint is not just a performance choice — it is the only correct solution under concurrent HTTP requests. Two simultaneous booking requests for the same slot will both pass the application-level `check_space_availability` RPC check before either commits. Only a DB constraint catches the race.

---

## Common Pitfalls

### Pitfall 1: Duplicate `/auth/register` Routes
**What goes wrong:** Both `auth.py` and `auth_enhanced.py` register `router = APIRouter(prefix="/auth")` with `@router.post("/register")`. FastAPI silently uses the first registered route and ignores the second. When deleting these routers, verify `/api/v1/auth/register` no longer exists (Stack Auth manages signup from frontend).
**How to avoid:** After deleting both routers from `main.py`, run `GET /docs` and confirm no `/auth/register` endpoint appears.

### Pitfall 2: `onNavigate` Prop Threading Breaks After Partial Route Migration
**What goes wrong:** Migrating `ExplorePage` to its own route but leaving `EstablishmentDetails` as a SPA component means clicking "View Details" in the new `/explore` page calls `onNavigate('details', id)` — but there's no `HomeClient` state machine listening anymore.
**How to avoid:** Migrate all views in one plan, or keep `home-client.tsx` alive until the last view is extracted. The cleanest approach: migrate all six views in a single plan with `router.push()` replacing `onNavigate` at each call site.

### Pitfall 3: `location` Column NULL for Existing Rows
**What goes wrong:** Establishments have `latitude`/`longitude` columns populated but `location GEOGRAPHY(POINT)` is NULL. PostGIS `ST_DWithin` query returns zero results.
**How to avoid:** Run the backfill UPDATE before deploying the PostGIS RPC:
```sql
UPDATE establishments
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE location IS NULL;
```
Add a trigger to keep `location` in sync when lat/lng are updated.

### Pitfall 4: TestClient Fails Due to Supabase Import Side Effects
**What goes wrong:** `from app.main import app` triggers `import app.core.supabase` which runs `print()` calls and instantiates `Settings()` which requires `SUPABASE_URL` env var — tests fail before any test runs.
**How to avoid:** Use `pytest-env` or `monkeypatch.setenv` before import, or mock at the module level with `@pytest.fixture(autouse=True)`. Set minimal env vars in `conftest.py`:
```python
import os
os.environ.setdefault("SUPABASE_URL", "http://mock")
os.environ.setdefault("SUPABASE_KEY", "mock-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "mock-service-key")
os.environ.setdefault("STACK_PROJECT_ID", "mock-project")
```

### Pitfall 5: btree_gist Extension Not Enabled
**What goes wrong:** The exclusion constraint migration fails with `ERROR: data type uuid has no default operator class for access method "gist"`.
**How to avoid:** The `btree_gist` PostgreSQL extension must be enabled in Supabase before the exclusion constraint can be created. Add `CREATE EXTENSION IF NOT EXISTS btree_gist;` at the top of the migration. In Supabase, extensions can be enabled via the Dashboard under Database > Extensions.

### Pitfall 6: `useUser({ or: 'redirect' })` in Server Components
**What goes wrong:** `useUser` is a client hook. Using it in a Server Component causes a build error.
**How to avoid:** For Server Component auth guards, use `stackServerApp.getUser()` from `@stackframe/stack/server`. For the App Router page components in this project (which are all client components due to `useState` usage), `useUser({ or: 'redirect' })` works correctly.

### Pitfall 7: `rating` Field Missing from `EstablishmentResponse` in DB
**What goes wrong:** `advanced_search` sorts by `x.rating` but `establishments` table has no `rating` column. Python `AttributeError` or silent sort on `None` values.
**How to avoid:** Either add a computed `rating` column (AVG from reviews via trigger) or remove the `rating` field from `EstablishmentResponse` and sort by a different field. For SEARCH-03, the filter `min_rating` should query the `reviews` table average per establishment. This requires a subquery in the RPC.

---

## Code Examples

### Stack Auth User Hook in App Router Page
```tsx
// Source: @stackframe/stack documentation + current frontend/src/stack/client.ts
'use client'
import { useUser } from '@stackframe/stack'
import { useRouter } from 'next-intl/navigation'

export default function DashboardPage() {
  const user = useUser({ or: 'redirect' })
  // user is guaranteed non-null here
  return <UserDashboard />
}
```

### Locale-Aware Navigation Replacing onNavigate
```tsx
// Source: next-intl documentation + frontend/src/app/[locale]/layout.tsx patterns
'use client'
import { useRouter } from 'next-intl/navigation'

export function Navbar() {
  const router = useRouter()

  // Instead of: onNavigate('explore')
  router.push('/explore')

  // Instead of: onNavigate('details', id)
  router.push(`/establishments/${id}`)

  // Instead of: onNavigate('dashboard')
  router.push('/dashboard')
}
```

### structlog Configuration for FastAPI
```python
# Source: structlog documentation, app/main.py insertion point
import structlog
import logging
import uuid

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# Replace supabase.py print() calls:
logger = structlog.get_logger()
logger.info("supabase_config", url=settings.SUPABASE_URL, key_prefix=settings.SUPABASE_KEY[:20])
```

### Exclusion Constraint and 409 Handling
```python
# Source: reservations.py create_reservation, to replace bare Exception catch
from postgrest.exceptions import APIError

try:
    response = supabase.table("reservations").insert(data).execute()
except APIError as e:
    if "no_overlapping_reservations" in str(e) or "23P01" in str(e):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked for the selected space."
        )
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

### pytest conftest.py with Supabase Mock
```python
# Source: backend/tests/ — to be created as conftest.py
import os
import pytest
from unittest.mock import patch, MagicMock

# Must set before app import
os.environ.setdefault("SUPABASE_URL", "http://mock-supabase")
os.environ.setdefault("SUPABASE_KEY", "mock-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "mock-service-key")
os.environ.setdefault("STACK_PROJECT_ID", "mock-project-id")
os.environ.setdefault("STACK_SECRET_SERVER_KEY", "mock-secret")

@pytest.fixture(autouse=True)
def mock_supabase_client():
    mock_client = MagicMock()
    with patch("app.core.supabase.get_supabase", return_value=mock_client):
        yield mock_client

@pytest.fixture
def authenticated_headers(mock_supabase_client):
    """Headers + mocked user lookup for authenticated endpoints."""
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "test-user-id", "email": "test@example.com",
        "role": "customer", "coffee_credits": 100,
        "full_name": "Test User", "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    with patch("app.core.stack_auth.verify_stack_auth_token", return_value={"sub": "stack-user-123"}):
        yield {"x-stack-access-token": "mock-token"}
```

---

## State of the Art

| Old Approach | Current Approach | Impact for Phase 12 |
|--------------|------------------|---------------------|
| SPA with `useState<Page>` | App Router with file-based routes | UX-03: replace home-client.tsx |
| `onNavigate('explore')` | `router.push('/explore')` via next-intl | All 10 components with `onNavigate` |
| python-jose custom JWT | Stack Auth JWKS (already done for backend) | AUTH-05: delete 3 files |
| geopy in Python | PostGIS ST_DWithin in SQL | SEARCH-02: RPC function |
| `print()` statements | structlog JSON | INFRA-02: 2 files + middleware |
| No exclusion constraint | `EXCLUDE USING GIST` + `btree_gist` | INFRA-04: 1 migration |

**Deprecated in this project:**
- `auth.py` router: uses Supabase Auth `sign_up` / `sign_in_with_password` — both wrong now that Stack Auth manages identity
- `auth_enhanced.py` router: CivilDocPro-style custom JWT system — irrelevant after Stack Auth migration
- `security.py` / `auth_simple.py`: duplicate legacy JWT utilities — no callers remain after router deletion
- `home-client.tsx`: entire file deleted after all views get their own routes

---

## Open Questions

1. **`check_space_availability` RPC definition**
   - What we know: called in `reservations.py` line 134; not found in any migration file
   - What's unclear: exact SQL implementation; whether it uses locking
   - Recommendation: Add exclusion constraint regardless — it supersedes any RPC-based check. The RPC can remain as a pre-validation convenience check but is no longer the safety mechanism.

2. **`stack_auth_id` population for existing users (AUTH-09)**
   - What we know: `stack_auth_id` column exists (migration 20260221); no seed script exists
   - What's unclear: whether any real users exist in production who used the legacy auth system and need their ID mapped
   - Recommendation: AUTH-09 is a data migration concern. For a dev/staging environment, existing users can re-register. For production, a script that reads Stack Auth's user list via their management API and matches by email to populate `stack_auth_id` is needed. Include a placeholder script in this phase; mark as manual step if no production users exist yet.

3. **`rating` field on `EstablishmentResponse`**
   - What we know: field referenced in `advanced_search` sort but absent from DB schema
   - What's unclear: whether a `rating` column was added to `establishments` in Supabase directly (not in any migration file visible)
   - Recommendation: Treat as absent. For SEARCH-03 min_rating filter, compute average rating from `reviews` table in the RPC subquery. Remove the `rating` attribute from Python sort in `advanced_search` or replace with `average_rating` computed field.

---

## Sources

### Primary (HIGH confidence — source files read directly)
- `librework/backend/app/main.py` — router registrations, confirmed legacy imports
- `librework/backend/app/core/security.py` — legacy JWT code with python-jose
- `librework/backend/app/core/auth_simple.py` — legacy duplicate
- `librework/backend/app/core/auth_enhanced.py` — legacy CivilDocPro-style system
- `librework/backend/app/core/dependencies.py` — Stack Auth dependency (confirmed correct)
- `librework/backend/app/core/stack_auth.py` — JWKS verification (confirmed correct)
- `librework/backend/app/api/v1/auth.py` — Supabase Auth register/login (to delete)
- `librework/backend/app/api/v1/auth_enhanced.py` — duplicate routes (to delete)
- `librework/backend/app/api/v1/establishments.py` — geopy in-memory filtering (to replace)
- `librework/backend/app/api/v1/reservations.py` — check_space_availability RPC call
- `librework/backend/app/core/config.py` — settings, confirmed no structlog, no logging config
- `librework/backend/app/core/supabase.py` — confirmed print() calls at module level
- `librework/backend/app/schemas/__init__.py` — all schema definitions
- `librework/backend/requirements.txt` — confirmed no python-jose/passlib explicit entries, no structlog
- `librework/backend/tests/test_main.py` — 2 tests only, no mocking
- `librework/frontend/src/app/home-client.tsx` — SPA state machine confirmed
- `librework/frontend/src/app/[locale]/page.tsx` — renders HomeClient, no routes
- `librework/frontend/src/app/[locale]/layout.tsx` — StackProvider + NextIntlClientProvider
- `librework/frontend/src/app/[locale]/login/page.tsx` — uses `<SignIn>` from Stack Auth
- `librework/frontend/src/components/Navbar.tsx` — uses `useUser()` + `onNavigate`
- `librework/frontend/src/hooks/useAuth.tsx` — wraps `useUser()`, only auth hook file present
- `librework/frontend/src/lib/api.ts` — x-stack-access-token interceptor confirmed
- `librework/frontend/src/stack/client.ts` — StackClientApp config
- `librework/frontend/playwright.config.ts` — E2E config confirmed
- `librework/database_schema_replit.sql` — reservations table, location GEOGRAPHY column
- `librework/supabase/migrations/20260221000000_stack_auth_migration.sql` — stack_auth_id column

### Secondary (MEDIUM confidence)
- structlog documentation patterns: standard FastAPI integration approach, well-established
- PostgreSQL `EXCLUDE USING GIST` with `btree_gist`: documented PostgreSQL feature for range overlap prevention
- Stack Auth `useUser({ or: 'redirect' })`: documented in @stackframe/stack API

---

## Metadata

**Confidence breakdown:**
- Auth cleanup: HIGH — all files read, import chains confirmed
- App Router migration: HIGH — SPA code read, `onNavigate` callers enumerated
- Double-booking constraint: HIGH — schema confirmed, btree_gist approach is standard PostgreSQL
- PostGIS search: HIGH — location column confirmed in schema; backfill risk noted
- structlog: HIGH — no logging framework in codebase, structlog is standard FastAPI choice
- Test infrastructure: HIGH — test file read, problem (env vars, no mocking) identified

**Research date:** 2026-03-26
**Valid until:** 2026-04-25 (stable domain — no fast-moving libraries)
