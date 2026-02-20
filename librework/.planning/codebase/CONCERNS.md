# Codebase Concerns

**Analysis Date:** 2025-02-20

## Tech Debt

**Dual Authentication Systems:**
- Issue: Project runs two auth routers with overlapping paths; legacy Supabase Auth (`librework/backend/app/api/v1/auth.py`) and enhanced custom JWT (`librework/backend/app/api/v1/auth_enhanced.py`) both register `/auth/register`, `/auth/login`. FastAPI uses last-registered route, so enhanced auth wins. Legacy auth remains in codebase as dead weight.
- Files: `librework/backend/app/main.py`, `librework/backend/app/api/v1/auth.py`, `librework/backend/app/api/v1/auth_enhanced.py`
- Impact: Confusion, maintenance burden, risk of accidentally re-enabling Supabase Auth.
- Fix approach: Remove legacy `auth.router` and `librework/backend/app/api/v1/auth.py` when migration is complete.

**Auth Provider vs. Project Requirement:**
- Issue: Project should use https://app.stack-auth.com/ per requirements, but codebase uses custom JWT + Supabase/custom bcrypt. No Stack Auth SDK or integration exists.
- Files: `librework/backend/app/core/auth_enhanced.py`, `librework/backend/app/core/security.py`, `librework/frontend/package.json` (no `@stackframe/stack` or similar)
- Impact: Misalignment with stated architecture; no SSO, social login, or managed auth features.
- Fix approach: Migrate to Stack Auth: add `@stackframe/stack` (or equivalent SDK), configure project in Stack Auth dashboard, replace custom JWT endpoints with Stack Auth callbacks, update `librework/frontend/src/hooks/useAuth.tsx` and backend verification to use Stack Auth tokens.

**Inconsistent get_current_user Sources:**
- Issue: `librework/backend/app/core/dependencies.py` (security.decode_access_token) is used by establishments, users, owner. `librework/backend/app/core/auth_enhanced.py` (auth_enhanced.get_current_user) is used by rbac, admin_audit. Both decode JWTs the same way but return different shapes (UserResponse vs. dict).
- Files: `librework/backend/app/core/dependencies.py`, `librework/backend/app/core/auth_enhanced.py`, `librework/backend/app/api/v1/establishments.py`, `librework/backend/app/api/v1/rbac.py`
- Impact: Subtle bugs if one path expects UserResponse and receives dict, or vice versa.
- Fix approach: Unify on a single auth dependency module; migrate all routers to use one `get_current_user` returning a shared type.

**Password Column Naming Inconsistency:**
- Issue: Enhanced auth and main migration use `hashed_password`; older scripts and docs use `password_hash`. SQL scripts like `librework/supabase/SAFE_REBUILD_AUTH.sql`, `librework/supabase/diagnostic_check.sql` reference `password_hash`.
- Files: `librework/supabase/migrations/20240201000000_enhanced_auth_system.sql` (hashed_password), `librework/supabase/SAFE_REBUILD_AUTH.sql` (password_hash), `librework/docs/AUTH_DEBUG_STATUS.md`, `librework/database_schema_replit.sql`
- Impact: Schema drift if wrong migration/script is run; users may not authenticate if column name is wrong.
- Fix approach: Standardize on `hashed_password`; update all SQL scripts and docs; add migration to rename `password_hash` to `hashed_password` if it exists.

**Multiple Auth Hooks with No Single Source of Truth:**
- Issue: Frontend has `useAuth.tsx`, `useSimpleAuth.ts`, `useAuth_replit.ts`. Different pages/hosts use different hooks. No central AuthProvider consistently wrapping the app for all routes.
- Files: `librework/frontend/src/hooks/useAuth.tsx`, `librework/frontend/src/hooks/useSimpleAuth.ts`, `librework/frontend/src/hooks/useAuth_replit.ts`
- Impact: Inconsistent auth state across pages; different token/key usage.
- Fix approach: Consolidate to one `useAuth` and one `AuthProvider`; remove `useSimpleAuth` and `useAuth_replit` or alias them to the main hook.

## Known Bugs

**Navbar Never Shows Authenticated State:**
- Symptoms: Navbar always shows "Log in" / "Sign up" even when user is logged in.
- Files: `librework/frontend/src/components/Navbar.tsx` (line 20)
- Trigger: `isAuthenticated` is hardcoded to `false` with TODO "Get from auth context".
- Workaround: None; users cannot see their logged-in state in navbar.

**Owner Components Use Wrong Token Key:**
- Symptoms: Owner dashboard, reservations, loyalty features fail with 401 when user is logged in.
- Files: `librework/frontend/src/components/owner/OwnerReservationsTable.tsx`, `librework/frontend/src/components/owner/EnhancedOwnerDashboard.tsx`, `librework/frontend/src/components/owner/OwnerLoyaltyManager.tsx`
- Trigger: These components use `localStorage.getItem('token')` while `useAuth` and `librework/frontend/src/lib/api.ts` store/use `access_token`. Key mismatch.
- Workaround: Manually set `localStorage.setItem('token', access_token)` on login (fragile); proper fix is to use `access_token` or centralize token access via api client.

**Password Reset Emails Not Sent:**
- Symptoms: Password reset request returns success but no email is sent; token is printed to server console.
- Files: `librework/backend/app/api/v1/auth_enhanced.py` (lines 448–457)
- Trigger: `request_password_reset` has TODO "Implement actual email sending"; uses `print()` for token.
- Workaround: User must obtain reset token from server logs (insecure); implement SMTP/email provider.

## Security Considerations

**Token Storage in localStorage:**
- Risk: XSS can steal tokens from localStorage.
- Files: `librework/frontend/src/hooks/useAuth.tsx`, `librework/frontend/src/lib/api.ts`
- Current mitigation: None; tokens stored in localStorage.
- Recommendations: Prefer httpOnly cookies for access/refresh tokens; or ensure strict CSP and XSS hardening if localStorage must be used.

**Password Reset Token Printed to Console:**
- Risk: Reset tokens leak via logs; could be captured in log aggregation or screenshots.
- Files: `librework/backend/app/api/v1/auth_enhanced.py` (line 449)
- Current mitigation: None.
- Recommendations: Remove `print()`; implement real email delivery; never log sensitive tokens.

**Stack Auth Not Used:**
- Risk: Custom auth increases risk of misconfigurations (JWT expiry, secret rotation, token binding).
- Files: Entire auth stack.
- Current mitigation: bcrypt, JWT with type claim, refresh flow.
- Recommendations: Migrate to Stack Auth (https://app.stack-auth.com/) for managed security, SSO, and reduced custom code.

**CORS and Credentials:**
- Risk: Broad CORS with `allow_credentials=True` can enable cross-origin credentialed requests.
- Files: `librework/backend/app/main.py`
- Current mitigation: Origins controlled via `settings.CORS_ORIGINS`.
- Recommendations: Ensure `CORS_ORIGINS` is restrictive in production; avoid `["*"]` with credentials.

## Performance Bottlenecks

**Nearest Establishments Without PostGIS:**
- Problem: `get_nearest_establishments` fetches extra rows and filters in Python instead of using spatial index.
- Files: `librework/backend/app/api/v1/establishments.py` (lines 57–91)
- Cause: Comment notes "use PostGIS in production" but implementation uses in-memory distance calc.
- Improvement path: Add PostGIS extension, spatial index on `establishments`, use `ST_DWithin` or equivalent for radius queries.

**Advanced Search open_now Filter Unimplemented:**
- Problem: `open_now` filter in `advanced_search` does nothing (pass).
- Files: `librework/backend/app/api/v1/establishments.py` (lines 284–286)
- Cause: TODO "Implement with actual opening hours".
- Improvement path: Add `opening_hours` to schema if missing; implement time-window check against current time.

## Fragile Areas

**RBAC Permission Resolution:**
- Files: `librework/backend/app/core/rbac.py`
- Why fragile: `resolve_user_permissions` returns `{}` when user not found; `has_permission` depends on Supabase response shape. Nested `custom_roles` structure can break if schema changes.
- Safe modification: Add explicit null checks; document expected Supabase response shape; add integration tests.
- Test coverage: No dedicated RBAC tests in `librework/backend/tests/`.

**Reservation and Owner Endpoints Returning Empty on Error:**
- Files: `librework/backend/app/api/v1/reservations.py` (line 319), `librework/backend/app/api/v1/owner.py` (line 140), `librework/backend/app/api/v1/groups.py` (line 143)
- Why fragile: Some paths return `[]` on failure instead of raising HTTPException; callers may treat empty as valid.
- Safe modification: Prefer raising 404/500 with clear messages; avoid silent empty returns.
- Test coverage: Minimal; `librework/backend/tests/test_main.py` only tests root/health.

**SessionProvider vs. Custom Auth:**
- Files: `librework/frontend/src/app/providers.tsx` (SessionProvider from next-auth), `librework/frontend/package.json` (next-auth)
- Why fragile: next-auth is included but auth flow uses custom JWT and `useAuth`. Unclear if any routes use next-auth sessions.
- Safe modification: Either wire next-auth fully or remove it to avoid confusion and unused deps.
- Test coverage: None for auth flow.

## Scaling Limits

**Spatial Queries:**
- Current capacity: In-memory distance filtering; works for hundreds of establishments.
- Limit: Degrades with thousands of establishments; no pagination on nearest.
- Scaling path: Add PostGIS, spatial index, and cursor-based pagination.

**Audit Logs:**
- Current: Stored in `audit_logs` table without apparent retention/archival strategy.
- Limit: Unbounded growth can slow queries and increase storage.
- Scaling path: Add retention policy, archival to cold storage, partitioning by date.

## Dependencies at Risk

**next-auth:**
- Risk: Likely unused or partially configured; adds bundle size and maintenance.
- Impact: Confusion; possible version drift with Next.js.
- Migration plan: Remove if unused; or document and complete integration.

**Multiple Supabase Auth Paths:**
- Risk: Legacy auth still references `supabase.auth.sign_up` and `sign_in_with_password`.
- Impact: If legacy router is re-enabled, Supabase Auth becomes critical path.
- Migration plan: Complete migration to enhanced/custom auth or Stack Auth; delete legacy auth.

## Missing Critical Features

**Email Delivery:**
- Problem: Password reset and likely other notifications (e.g. reservation confirmations) have no email backend.
- Blocks: Password reset flow is unusable in production; user notifications incomplete.
- Files: `librework/backend/app/api/v1/auth_enhanced.py`, notification-related code.

**Group Invitation Notifications:**
- Problem: Group invite logic has TODO "Send invitation notification".
- Blocks: Users not informed of group invites.
- Files: `librework/backend/app/api/v1/groups.py` (line 124).

## Test Coverage Gaps

**Auth Flow:**
- What's not tested: Enhanced auth registration, login, refresh, password reset, token validation.
- Files: `librework/backend/app/api/v1/auth_enhanced.py`, `librework/backend/app/core/auth_enhanced.py`
- Risk: Auth regressions go unnoticed; migration to Stack Auth would need new tests.
- Priority: High.

**RBAC:**
- What's not tested: Permission resolution, `require_permission`, `check_establishment_access`.
- Files: `librework/backend/app/core/rbac.py`, `librework/backend/app/api/v1/rbac.py`
- Risk: Permission bugs could expose admin features or block valid users.
- Priority: High.

**Owner and Reservation APIs:**
- What's not tested: Establishment CRUD, reservation check-in/cancel, owner endpoints.
- Files: `librework/backend/app/api/v1/establishments.py`, `librework/backend/app/api/v1/reservations.py`, `librework/backend/app/api/v1/owner.py`
- Risk: Business logic changes can break core flows.
- Priority: Medium.

**Frontend Auth Integration:**
- What's not tested: AuthProvider, useAuth, token refresh, protected routes.
- Files: `librework/frontend/src/hooks/useAuth.tsx`, `librework/frontend/src/lib/api.ts`
- Risk: Token/key bugs (e.g. `token` vs `access_token`) not caught.
- Priority: High.

---

*Concerns audit: 2025-02-20*
