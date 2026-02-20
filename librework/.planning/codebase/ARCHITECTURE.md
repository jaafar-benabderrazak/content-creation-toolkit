# Architecture

**Analysis Date:** 2025-02-20

## Pattern Overview

**Overall:** Full-stack monorepo with separated frontend (Next.js) and backend (FastAPI) services, using Supabase as database and storage. SPA-style frontend with conditional page rendering on a single route. Custom JWT authentication with RBAC and audit logging.

**Key Characteristics:**
- Backend and frontend run as separate processes; frontend calls backend API
- No ORM: backend uses Supabase Python client directly for database access
- Two parallel auth subsystems: legacy (`app.core.dependencies`) and enhanced (`app.core.auth_enhanced`)
- Frontend uses localStorage for tokens; axios interceptors attach Bearer token and handle refresh
- **Auth target:** The project is intended to use [Stack Auth](https://app.stack-auth.com/) for authentication. Current implementation uses custom JWT + Supabase. Migration to Stack Auth will affect auth layers and data flows below.

## Layers

**Backend API:**
- Purpose: HTTP API, request routing, validation
- Location: `librework/backend/app/`
- Contains: `main.py`, `api/v1/*.py`, `schemas/`
- Depends on: `app.core`, `app.schemas`
- Used by: Frontend via `NEXT_PUBLIC_API_URL/api/v1`

**Backend Core:**
- Purpose: Config, auth, database client, RBAC, audit
- Location: `librework/backend/app/core/`
- Contains: `config.py`, `auth_enhanced.py`, `auth_simple.py`, `security.py`, `dependencies.py`, `supabase.py`, `rbac.py`, `audit.py`, `email.py`
- Depends on: `pydantic-settings`, `jose`, `passlib`, `supabase`
- Used by: API routers via `Depends()`

**Frontend App:**
- Purpose: Pages, routing, layout
- Location: `librework/frontend/src/app/`
- Contains: `layout.tsx`, `page.tsx`, `login/`, `register/`, `globals.css`
- Depends on: `@/components`, `@/lib`, `@/hooks`
- Used by: Next.js App Router

**Frontend Components:**
- Purpose: Reusable UI and feature components
- Location: `librework/frontend/src/components/`
- Contains: `HomePage.tsx`, `ExplorePage.tsx`, `UserDashboard.tsx`, `OwnerDashboard.tsx`, `Navbar.tsx`, `owner/*`, `ui/*` (shadcn)
- Depends on: `@/lib`, `@/hooks`, `@/types`
- Used by: `app/page.tsx`, layout

**Frontend Lib:**
- Purpose: API client, utilities, Supabase client
- Location: `librework/frontend/src/lib/`
- Contains: `api.ts`, `supabase.ts`, `utils.ts`, `mockData.ts`
- Depends on: `axios`, `@supabase/supabase-js`
- Used by: Components, hooks

**Database (Supabase):**
- Purpose: PostgreSQL persistence, RLS
- Location: `librework/supabase/migrations/`
- Schema: `20240101000000_initial_schema.sql`, `20240201000000_enhanced_auth_system.sql`, others
- Used by: Backend via Supabase client

## Data Flow

**Authentication (current):**

1. User submits email/password to `/api/v1/auth/login` (enhanced) or legacy auth router
2. Backend validates credentials via `authenticate_user()` in `auth_enhanced.py`, fetches user from Supabase `users` table
3. Backend returns `access_token` and `refresh_token` (JWT)
4. Frontend stores tokens in localStorage; axios interceptor adds `Authorization: Bearer <token>`
5. On 401, interceptor calls `/api/v1/auth/refresh` with refresh token; retries request with new access token
6. Protected routes use `Depends(get_current_user)` or `Depends(get_current_admin)` to validate JWT and load user

**Note:** When migrating to Stack Auth (https://app.stack-auth.com/), the auth flow will change. Stack Auth typically issues and validates its own tokens; backend will need to verify Stack Auth tokens instead of custom JWTs.

**API request flow:**

1. Component calls `api.get('/reservations')` or similar from `lib/lib/api.ts`
2. Axios interceptor adds `Authorization: Bearer ${localStorage.access_token}`
3. FastAPI receives request, router runs `Depends(get_current_user)` → `decode_access_token()` → fetch user from Supabase
4. Router calls `get_supabase()` and queries tables
5. Response returned as JSON

**State management:**
- Server state: React Query (TanStack Query) in `Providers`
- Auth state: `useAuth` hook with `AuthContext` (`hooks/useAuth.tsx`) or `useSimpleAuth` (Zustand)
- Session: `SessionProvider` (next-auth) wraps app but auth flows use custom backend; mixed usage

## Key Abstractions

**FastAPI Dependencies:**
- Purpose: Inject current user, enforce RBAC
- Examples: `backend/app/core/dependencies.py`, `backend/app/core/auth_enhanced.py`
- Pattern: `Depends(security)` for Bearer extraction; `get_current_user`, `get_current_owner`, `get_current_admin` for role checks
- Two implementations: `dependencies.get_current_user` (returns `UserResponse`, uses `security.decode_access_token`) vs `auth_enhanced.get_current_user` (returns raw dict, used by rbac/admin_audit/auth_enhanced)

**API Routers:**
- Purpose: Group endpoints by domain
- Examples: `backend/app/api/v1/reservations.py`, `backend/app/api/v1/auth_enhanced.py`, `backend/app/api/v1/rbac.py`
- Pattern: `APIRouter(prefix="/reservations", tags=["Reservations"])`; all mounted under `settings.API_V1_PREFIX` in `main.py`

**RBAC:**
- Purpose: Module/action permissions, custom roles, establishment access
- Location: `backend/app/core/rbac.py`
- Pattern: `require_permission(module, action)`, `require_establishment_access()`, `check_reservation_access()`
- Roles: `customer`, `owner`, `admin`; custom roles via `custom_roles` table

**Axios API client:**
- Purpose: Centralized HTTP client with auth and refresh
- Location: `frontend/src/lib/api.ts`
- Pattern: `baseURL: ${NEXT_PUBLIC_API_URL}/api/v1`; interceptors for Bearer and refresh-on-401

## Entry Points

**Backend:**
- Location: `librework/backend/app/main.py`
- Triggers: `uvicorn run app.main:app` or `python -m app.main`
- Responsibilities: Create FastAPI app, CORS, mount all routers at `/api/v1`

**Frontend:**
- Location: `librework/frontend/src/app/layout.tsx`, `librework/frontend/src/app/page.tsx`
- Triggers: Next.js dev/build
- Responsibilities: Root layout with Providers; `page.tsx` renders Navbar + conditional page components (home, explore, details, dashboard, owner-dashboard, owner-admin)

**App Router routes:**
- `librework/frontend/src/app/page.tsx` – SPA main page (conditional view switching)
- `librework/frontend/src/app/login/page.tsx` – Login
- `librework/frontend/src/app/register/page.tsx` – Registration

## Error Handling

**Strategy:** HTTP exceptions for API errors; frontend catches axios errors.

**Patterns:**
- Backend: `raise HTTPException(status_code=404, detail="...")`; `decode_access_token` raises 401 on invalid token
- Frontend: Axios interceptor handles 401 via refresh; components use `try/catch` or React Query error state

## Cross-Cutting Concerns

**Logging:** Print statements in `supabase.py`; no structured logging framework detected.

**Validation:** Pydantic schemas in `backend/app/schemas/`; request/response models per endpoint.

**Authentication:**
- Current: Custom JWT (jose, passlib) in `auth_enhanced.py`, `auth_simple.py`, `security.py`
- Intended: Stack Auth (https://app.stack-auth.com/) – not yet implemented

---

*Architecture analysis: 2025-02-20*
