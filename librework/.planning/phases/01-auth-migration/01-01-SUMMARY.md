---
phase: 01-auth-migration
plan: 01
subsystem: auth
tags: [jwt, es256, jwks, pyjwt, stack-auth, rbac, supabase, fastapi]

requires: []
provides:
  - "JWKS-based JWT verification for Stack Auth ES256 tokens (stack_auth.py)"
  - "Unified get_current_user/get_current_owner/get_current_admin FastAPI dependencies using x-stack-access-token header"
  - "Simplified RBAC with 3 fixed roles (customer/owner/admin), no custom_roles table"
  - "Database migration: stack_auth_id column, dropped auth.users FK, dropped custom_roles, dropped password columns"
  - "Config settings for STACK_PROJECT_ID and STACK_SECRET_SERVER_KEY"
affects: [01-auth-migration, 02-frontend-auth, api-routers]

tech-stack:
  added: [PyJWT[crypto], cachetools]
  removed: [python-jose, passlib]
  patterns: [JWKS verification via PyJWKClient with lru_cache, x-stack-access-token header extraction, stack_auth_id user lookup]

key-files:
  created:
    - "librework/backend/app/core/stack_auth.py"
    - "librework/supabase/migrations/20260221000000_stack_auth_migration.sql"
  modified:
    - "librework/backend/app/core/dependencies.py"
    - "librework/backend/app/core/rbac.py"
    - "librework/backend/app/core/config.py"
    - "librework/backend/requirements.txt"

key-decisions:
  - "Made JWT_SECRET_KEY optional (default empty string) to avoid breaking startup before Stack Auth env vars are configured"
  - "Kept verify_establishment_owner() in dependencies.py for backward compatibility with existing routers"
  - "Kept get_current_active_user() as alias in dependencies.py for backward compatibility"
  - "Simplified resolve_user_permissions() to use role string directly instead of DB lookup (no more custom_roles join)"
  - "Changed require_permission/require_role checkers to accept Request instead of Depends(get_current_user) to match new auth pattern"

patterns-established:
  - "Stack Auth token verification: extract x-stack-access-token header -> verify via JWKS -> lookup user by stack_auth_id"
  - "Role-based auth: 3 fixed roles in DEFAULT_ROLE_PERMISSIONS dict, no DB-stored custom roles"
  - "Permission dependencies: all RBAC checkers call get_current_user(request) internally"

requirements-completed: [AUTH-03, AUTH-08, INFRA-03]

duration: 12min
completed: 2026-02-21
---

# Phase 1 Plan 01: Backend Auth Foundation Summary

**JWKS-based Stack Auth JWT verification with unified FastAPI auth dependencies and simplified 3-role RBAC**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-02-21T00:38:31Z
- **Completed:** 2026-02-21T00:50:00Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments
- Created `stack_auth.py` with ES256 JWT verification via JWKS endpoint using PyJWKClient
- Rewrote `dependencies.py` to extract `x-stack-access-token` header, verify via JWKS, and lookup users by `stack_auth_id`
- Simplified `rbac.py` to 3 fixed roles — removed all custom_roles references, updated imports from `auth_enhanced` to `dependencies`
- Created database migration dropping auth.users FK, adding stack_auth_id column, dropping custom_roles table, dropping password columns
- Updated requirements.txt: added PyJWT[crypto] and cachetools, removed python-jose and passlib
- Added STACK_PROJECT_ID and STACK_SECRET_SERVER_KEY to config settings

## Task Commits

Each task was committed atomically:

1. **Task 1: Database migration + config + requirements** - `73065a2` (feat)
2. **Task 2: Stack Auth verification module + rewrite dependencies + simplify RBAC** - `87bbb8a` (feat)

## Files Created/Modified
- `backend/app/core/stack_auth.py` - NEW: JWKS-based ES256 JWT verification for Stack Auth tokens
- `backend/app/core/dependencies.py` - REWRITE: Unified auth dependencies using Stack Auth tokens and stack_auth_id lookup
- `backend/app/core/rbac.py` - SIMPLIFY: 3 fixed roles only, removed custom_roles, updated imports
- `backend/app/core/config.py` - ADD: STACK_PROJECT_ID and STACK_SECRET_SERVER_KEY settings
- `backend/requirements.txt` - UPDATE: PyJWT[crypto], cachetools in; python-jose, passlib out
- `supabase/migrations/20260221000000_stack_auth_migration.sql` - NEW: Schema migration for Stack Auth

## Decisions Made
- Made `JWT_SECRET_KEY` default to empty string so the app can start without legacy JWT config during migration
- Kept `verify_establishment_owner()` and `get_current_active_user()` as compatibility shims for existing routers
- Changed RBAC dependency checkers to accept `Request` directly (matching the new `get_current_user(request)` signature)
- Simplified `resolve_user_permissions()` to a pure function taking a role string instead of querying the DB for custom_roles

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Git repo structure: the source code lives in a nested git repo at `librework/librework/` (not the workspace-root `.git`). Required adjusting commit working directory.

## User Setup Required

**External services require manual configuration.** The following env vars must be set before backend will authenticate:
- `STACK_PROJECT_ID` - from Stack Auth Dashboard -> Project Settings -> Project ID
- `STACK_SECRET_SERVER_KEY` - from Stack Auth Dashboard -> Project Settings -> Server Keys

## Next Phase Readiness
- Backend auth foundation complete — all subsequent plans can import from `app.core.dependencies` and `app.core.stack_auth`
- Plans 01-02 through 01-05 can proceed: frontend SDK setup, router import updates, legacy code removal, E2E testing
- **Note:** Existing routers still import `get_current_user` from `app.core.dependencies` (same module path) so most routers won't need import changes — but routers importing from `auth_enhanced` will need updating (handled in plan 01-03)

## Self-Check: PASSED

All created files verified to exist. Both commits verified in git log.

---
*Phase: 01-auth-migration*
*Completed: 2026-02-21*
