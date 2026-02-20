# Phase 1: Auth Migration - Research

**Researched:** 2026-02-21
**Domain:** Authentication, Authorization, Identity Management
**Confidence:** HIGH

## Summary

Stack Auth replaces the entire custom JWT + Supabase Auth system with a managed authentication provider. The frontend migration is straightforward: Stack Auth's Next.js SDK provides `useUser()`, `<SignIn>`, `<SignUp>`, and `<UserButton>` components that replace all three custom hooks and login/register pages. The backend migration requires more care: Stack Auth's JWT uses ES256 (not HS256) and is verified via a JWKS endpoint, replacing `python-jose` with `PyJWT[crypto]`. Custom user metadata (roles) is NOT included in Stack Auth's JWT claims — the backend must look up the user's role from the local Supabase `users` table after verifying the JWT. The most critical technical risk is the user ID format change: Stack Auth user IDs are strings (not UUIDs), while the existing `users.id` is a UUID with foreign keys across 8+ tables.

**Primary recommendation:** Verify Stack Auth JWTs locally via JWKS (fast, no network call per request). Store roles in Stack Auth's `clientReadOnlyMetadata` as the source of truth, synced to the local `users` table via webhook. Keep the existing UUID primary key on `users` and add a `stack_auth_id TEXT` column for mapping.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Roles (customer/owner/admin) live in **Stack Auth only** as user metadata, exposed via token claims. Backend reads roles from the JWT — no separate Supabase role lookup.
- **3 fixed roles** (customer, owner, admin) — the existing `custom_roles` table and fine-grained per-establishment permissions are removed/simplified. Custom roles are not needed for v1.
- A user becomes an **owner via self-service** — they click "Become an owner" and get the role immediately. No admin approval needed at this stage (approval workflow is deferred to v2).
- Admin access is managed through **Stack Auth's admin dashboard** — no hardcoded email lists.
- Multi-device: **Allow concurrent sessions** — user can be logged in on phone and laptop simultaneously.
- Logout: **Redirect to login page** after logout.
- Protected routes: **Redirect to login page with return URL** — after successful login, redirect back to the originally requested page.

### Claude's Discretion
- Session duration / token refresh strategy — use Stack Auth's default configuration
- User migration approach (force re-registration vs progressive re-auth vs bulk import) — pick the most practical approach given Stack Auth's capabilities
- Cutover approach (big-bang vs parallel period) — decide based on implementation complexity

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | User can sign up and log in via Stack Auth (email/password), replacing all custom JWT auth | Stack Auth SDK provides `<SignIn>`, `<SignUp>` components and `useUser()` hook; backend verifies via JWKS (ES256) |
| AUTH-02 | User session is managed by Stack Auth SDK; frontend uses `useUser()` instead of custom hooks | `useUser({ or: "redirect" })` replaces all 3 hooks; `StackProvider` wraps app in root layout |
| AUTH-03 | Backend verifies Stack Auth JWTs via JWKS (RS256→ES256, cached) instead of custom `decode_access_token()` | JWKS endpoint at `https://api.stack-auth.com/api/v1/projects/{id}/.well-known/jwks.json`; PyJWT[crypto] for verification |
| AUTH-04 | All three frontend auth hooks replaced by Stack Auth's hook | `useAuth.tsx`, `useSimpleAuth.ts`, `useAuth_replit.ts` all removed; replaced by `useUser()` from `@stackframe/stack` |
| AUTH-05 | Legacy auth code is removed (Supabase Auth router, next-auth, python-jose, passlib) | Remove `auth.py` router, `auth_enhanced.py` endpoints, `security.py`, `auth_simple.py`; uninstall `next-auth`, `python-jose`, `passlib` |
| AUTH-06 | Navbar correctly shows authenticated/unauthenticated state | Currently hardcoded `isAuthenticated = false`; replace with `useUser()` — returns user or null |
| AUTH-07 | Owner components use correct token source | Owner components use `localStorage.getItem('token')` vs `access_token`; Stack Auth eliminates this — SDK manages tokens internally |
| AUTH-08 | RBAC roles (customer, owner, admin) work with Stack Auth user metadata | Store role in `clientReadOnlyMetadata`; sync to local `users` table via webhook; backend reads from local DB after JWT verification |
| AUTH-09 | Existing user accounts are migrated or re-created in Stack Auth | Recommend force re-registration (clean slate); existing bcrypt hashes cannot be imported into Stack Auth |
| INFRA-03 | Password column naming standardized to `hashed_password` | Column becomes irrelevant after migration (Stack Auth handles passwords); rename in migration for cleanup, then drop in final migration |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@stackframe/stack` | ^2.8.68 | Frontend: Auth SDK — hooks, components, provider | Official Stack Auth Next.js SDK; replaces all 3 custom auth hooks with single `useUser()` |
| `PyJWT[crypto]` | ^2.9.0 | Backend: JWT verification via JWKS (ES256) | Stack Auth JWTs use ES256 algorithm; PyJWT supports JWKS/ES256; recommended by Stack Auth Python backend docs |
| `httpx` | ^0.28.1 (upgrade from 0.27.2) | Backend: Async HTTP for REST API calls to Stack Auth | Already in requirements.txt at 0.27.2; upgrade for latest fixes; used for webhook handling and fallback user lookups |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `requests` | (already installed) | Backend: Sync HTTP for JWKS client initialization | PyJWT's `PyJWKClient` uses `requests` internally; already in requirements.txt |
| `cachetools` | ^5.5.0 | Backend: Cache JWKS keys and user lookups | Avoid fetching JWKS keys on every request; TTL cache for user role lookups |

### Packages to REMOVE

| Package | Side | Why Remove |
|---------|------|------------|
| `next-auth` (^4.24) | Frontend | Stack Auth replaces it entirely; currently only `SessionProvider` is used in `providers.tsx` |
| `python-jose[cryptography]` (3.3) | Backend | Stack Auth uses ES256; PyJWT handles verification; python-jose is HS256-only in practice |
| `passlib[bcrypt]` (1.7) | Backend | Stack Auth manages password hashing; backend no longer stores/verifies passwords |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JWT verification (JWKS) | REST API verification (`/api/v1/users/me`) | REST API gives full user profile but adds ~100ms latency per request; JWT is local, ~1ms |
| `PyJWT[crypto]` | `python-jose` | python-jose doesn't support ES256 JWKS well; PyJWT is recommended by Stack Auth docs |
| `clientReadOnlyMetadata` for roles | `serverMetadata` for roles | serverMetadata not readable from client — frontend can't check role without extra API call |

**Installation:**

```bash
# Frontend
npm install @stackframe/stack
npm uninstall next-auth

# Backend
pip install "PyJWT[crypto]" cachetools
pip uninstall python-jose passlib
# httpx already installed, update version in requirements.txt
```

## Architecture Patterns

### Recommended Project Structure Changes

```
librework/
├── frontend/src/
│   ├── stack/
│   │   ├── client.ts            # NEW: StackClientApp config
│   │   └── server.ts            # NEW: StackServerApp config (if using server components)
│   ├── app/
│   │   ├── handler/
│   │   │   └── [...stack]/
│   │   │       └── page.tsx     # NEW: Stack Auth handler (sign-in, sign-up, etc.)
│   │   ├── layout.tsx           # MODIFY: Add StackProvider + StackTheme
│   │   ├── loading.tsx          # NEW: Suspense boundary for Stack's async hooks
│   │   ├── login/page.tsx       # REMOVE: Stack Auth provides sign-in page
│   │   └── register/page.tsx    # REMOVE: Stack Auth provides sign-up page
│   ├── components/
│   │   ├── providers.tsx        # MODIFY: Remove SessionProvider, add StackProvider
│   │   └── Navbar.tsx           # MODIFY: Use useUser() + UserButton
│   ├── hooks/
│   │   ├── useAuth.tsx          # REMOVE
│   │   ├── useSimpleAuth.ts     # REMOVE
│   │   └── useAuth_replit.ts    # REMOVE
│   └── lib/
│       └── api.ts               # MODIFY: Change interceptor to use Stack Auth access token
├── backend/app/
│   ├── core/
│   │   ├── stack_auth.py        # NEW: Stack Auth JWT verification + user lookup
│   │   ├── dependencies.py      # MODIFY: Single get_current_user using Stack Auth
│   │   ├── rbac.py              # SIMPLIFY: Remove custom_roles, keep DEFAULT_ROLE_PERMISSIONS
│   │   ├── auth_enhanced.py     # REMOVE
│   │   ├── auth_simple.py       # REMOVE (if exists)
│   │   └── security.py          # REMOVE
│   ├── api/v1/
│   │   ├── auth.py              # REMOVE (legacy Supabase Auth router)
│   │   └── auth_enhanced.py     # REMOVE (custom JWT router)
│   └── main.py                  # MODIFY: Remove auth routers, update CORS
```

### Pattern 1: Frontend — Stack Auth Provider Setup

**What:** Wrap the app with `StackProvider` and `StackTheme` in the root layout.
**When to use:** Once, during initial setup.

```typescript
// stack/client.ts
import { StackClientApp } from "@stackframe/stack";

export const stackClientApp = new StackClientApp({
  projectId: process.env.NEXT_PUBLIC_STACK_PROJECT_ID!,
  publishableClientKey: process.env.NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY!,
  urls: {
    afterSignIn: "/",
    afterSignUp: "/",
    afterSignOut: "/handler/sign-in",
  },
});
```

```tsx
// app/layout.tsx
import { StackProvider, StackTheme } from "@stackframe/stack";
import { stackClientApp } from "@/stack/client";

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <StackProvider app={stackClientApp}>
          <StackTheme>
            <Providers>{children}</Providers>
          </StackTheme>
        </StackProvider>
      </body>
    </html>
  );
}
```

Source: https://docs.stack-auth.com/next/getting-started/setup (verified 2026-02-21)

### Pattern 2: Frontend — Replace Auth Hooks with useUser()

**What:** Replace all 3 custom hooks with Stack Auth's `useUser()`.
**When to use:** Every component that needs auth state.

```typescript
// Before (3 different hooks):
// import { useAuth } from '@/hooks/useAuth'          // Context-based
// import { useAuth } from '@/hooks/useSimpleAuth'    // Zustand-based
// import { useAuth } from '@/hooks/useAuth_replit'   // Zustand-based (identical)

// After (one hook):
import { useUser } from "@stackframe/stack";

function MyComponent() {
  const user = useUser(); // null if not signed in
  // or:
  const user = useUser({ or: "redirect" }); // redirects to sign-in if not signed in
}
```

Source: https://docs.stack-auth.com/docs/sdk/hooks/use-user (verified 2026-02-21)

### Pattern 3: Frontend — Sending Access Token to Backend

**What:** Get the Stack Auth access token and send it to the FastAPI backend.
**When to use:** Every API call from frontend to backend.

```typescript
// lib/api.ts — Updated interceptor
import { stackClientApp } from "@/stack/client";

api.interceptors.request.use(async (config) => {
  const user = await stackClientApp.getUser();
  if (user) {
    const { accessToken } = await user.getAuthJson();
    config.headers["x-stack-access-token"] = accessToken;
  }
  return config;
});
```

Source: https://docs.stack-auth.com/concepts/backend-integration (verified 2026-02-21, GitHub raw source)

### Pattern 4: Backend — JWT Verification via JWKS (Recommended)

**What:** Verify Stack Auth access tokens locally using the JWKS endpoint. Fast (~1ms), no network call per request.
**When to use:** Primary verification method for all protected endpoints.

```python
# app/core/stack_auth.py
import jwt
from jwt import PyJWKClient
from functools import lru_cache
from app.core.config import settings

@lru_cache()
def get_jwks_client():
    return PyJWKClient(
        f"https://api.stack-auth.com/api/v1/projects/{settings.STACK_PROJECT_ID}/.well-known/jwks.json"
    )

def verify_stack_auth_token(access_token: str) -> dict:
    """Verify a Stack Auth access token via JWKS. Returns JWT payload."""
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(access_token)
    payload = jwt.decode(
        access_token,
        signing_key.key,
        algorithms=["ES256"],
        audience=settings.STACK_PROJECT_ID,
    )
    return payload  # Contains: sub, email, name, email_verified, etc.
```

Source: https://docs.stack-auth.com/concepts/backend-integration (verified 2026-02-21, GitHub raw source)

### Pattern 5: Backend — FastAPI Dependency for Auth

**What:** Single `get_current_user` dependency that verifies token + looks up user in local DB.
**When to use:** Replaces BOTH `dependencies.get_current_user` AND `auth_enhanced.get_current_user`.

```python
# app/core/dependencies.py (rewritten)
from fastapi import Depends, HTTPException, status, Request
from app.core.stack_auth import verify_stack_auth_token
from app.core.supabase import get_supabase
from app.schemas import UserResponse

async def get_current_user(request: Request) -> UserResponse:
    """Get the current authenticated user from Stack Auth token."""
    token = request.headers.get("x-stack-access-token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")

    try:
        payload = verify_stack_auth_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    stack_auth_id = payload.get("sub")
    if not stack_auth_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    supabase = get_supabase()
    response = supabase.table("users").select("*").eq("stack_auth_id", stack_auth_id).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="User not found in database")

    return UserResponse(**response.data[0])
```

### Pattern 6: Role Storage and Retrieval

**What:** Store role in Stack Auth `clientReadOnlyMetadata`, sync to local DB via webhook.
**When to use:** Role assignment, role checking.

**IMPORTANT FINDING:** Stack Auth's JWT does NOT contain custom metadata. The JWT only has standard claims (`sub`, `email`, `name`, `email_verified`, `role` which is always `"authenticated"`). Custom metadata (`clientMetadata`, `serverMetadata`, `clientReadOnlyMetadata`) is only available via the SDK's `user` object (frontend) or REST API (backend).

**Implication for the "roles in token claims" user decision:** Roles cannot literally be in JWT claims. The practical implementation is:
1. Store role in `clientReadOnlyMetadata` in Stack Auth (e.g., `{ role: "owner" }`)
2. Frontend reads role via `user.clientReadOnlyMetadata.role` (immediate, no extra call)
3. Backend reads role from local `users` table (synced via webhook, no extra API call)
4. Webhook keeps Stack Auth and local DB in sync

```typescript
// Frontend: reading role
const user = useUser({ or: "redirect" });
const role = user.clientReadOnlyMetadata?.role || "customer";

// Server-side: setting role (owner self-promotion)
const serverUser = await stackServerApp.getUser(userId);
await serverUser.update({
  clientReadOnlyMetadata: { ...serverUser.clientReadOnlyMetadata, role: "owner" },
});
```

### Anti-Patterns to Avoid

- **Don't store auth tokens in localStorage:** Stack Auth SDK manages tokens internally via httpOnly cookies. The current `localStorage.setItem('access_token', ...)` pattern is eliminated.
- **Don't decode JWT on frontend for role checks:** Use `user.clientReadOnlyMetadata.role` instead. JWT payload is an implementation detail.
- **Don't call Stack Auth REST API per request for role checks:** Verify JWT locally (JWKS), look up role from local `users` table. REST API is for admin operations and webhooks only.
- **Don't keep two auth dependency implementations:** The current codebase has `dependencies.get_current_user` (returns `UserResponse`) and `auth_enhanced.get_current_user` (returns dict). Unify to ONE dependency returning ONE type.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sign-in/sign-up UI | Custom login/register pages | Stack Auth `<SignIn>`, `<SignUp>` components or `/handler/[...stack]` | Handles email verification, error states, social login (future), password strength, CSRF |
| Token refresh | Custom refresh interceptor in `api.ts` | Stack Auth SDK auto-refresh | SDK refreshes tokens before expiry (default 10 min); handles race conditions |
| Password hashing | `passlib[bcrypt]` in `auth_enhanced.py` | Stack Auth handles passwords | Eliminates liability of storing password hashes; Stack Auth manages salt, rounds, hash migration |
| JWT creation | `create_access_token()` / `create_refresh_token()` | Stack Auth issues JWTs | ES256 with proper key rotation; no need to manage JWT_SECRET_KEY |
| Session management | Custom localStorage + refresh token logic | Stack Auth session management | Handles multi-device, expiry, refresh, logout across devices |
| JWKS key fetching | Manual key download + caching | `PyJWKClient` from PyJWT | Handles key rotation, caching, retries automatically |

**Key insight:** Stack Auth eliminates ~500 lines of custom auth code across 6 backend files and 3 frontend files. The entire `auth_enhanced.py` (306 lines), `security.py` (72 lines), `auth_simple.py` (if separate), and most of `dependencies.py` become unnecessary.

## Common Pitfalls

### Pitfall 1: User ID Format Mismatch

**What goes wrong:** Stack Auth user IDs are strings (e.g., format like `usr_...` or UUIDs — format varies), while the existing `users.id` column is `UUID PRIMARY KEY REFERENCES auth.users(id)`. Direct replacement breaks all foreign keys.
**Why it happens:** Assuming Stack Auth user IDs are UUIDs because the existing system uses UUIDs.
**How to avoid:** Add a `stack_auth_id TEXT UNIQUE` column to the `users` table. Keep the existing UUID `id` as primary key. All foreign keys remain unchanged. Backend looks up users by `stack_auth_id` after JWT verification.
**Warning signs:** Foreign key constraint violations when inserting users; "invalid input syntax for type uuid" errors.

### Pitfall 2: Forgetting to Drop auth.users Foreign Key

**What goes wrong:** The `users` table has `REFERENCES auth.users(id) ON DELETE CASCADE`. After migration, new users are in Stack Auth (not Supabase Auth). The FK constraint prevents inserting new user rows because their IDs don't exist in `auth.users`.
**Why it happens:** The FK to Supabase's internal `auth.users` table is easy to overlook.
**How to avoid:** Migration MUST: `ALTER TABLE users DROP CONSTRAINT users_id_fkey;` (or whatever the constraint name is). This is a prerequisite for creating any new users post-migration.
**Warning signs:** "insert or update on table 'users' violates foreign key constraint" errors.

### Pitfall 3: JWT Role Claim Misunderstanding

**What goes wrong:** Assuming Stack Auth JWT contains custom role claims (like `"role": "owner"`). The JWT `role` field is always `"authenticated"` — it's a Stack Auth internal field, not a custom role.
**Why it happens:** The user decision says "exposed via token claims" but Stack Auth JWTs only contain standard claims.
**How to avoid:** Read role from `clientReadOnlyMetadata` (frontend) or local `users` table (backend). Never rely on JWT `role` field for business logic.
**Warning signs:** All users appear to have the same role; RBAC checks fail or pass incorrectly.

### Pitfall 4: Token Header Name Mismatch

**What goes wrong:** Backend expects `Authorization: Bearer <token>` but Stack Auth frontend sends `x-stack-access-token: <token>`.
**Why it happens:** Keeping the old `HTTPBearer` security scheme in FastAPI which expects the `Authorization` header.
**How to avoid:** Update the FastAPI dependency to extract the token from the `x-stack-access-token` header (or standardize on `Authorization: Bearer` in the axios interceptor — either works, but be consistent).
**Warning signs:** 401 errors on every authenticated request despite valid token.

### Pitfall 5: Dual Auth During Migration

**What goes wrong:** Having both old and new auth active simultaneously causes ambiguous behavior — some endpoints accept old JWT, others accept Stack Auth JWT, users get confused by two login systems.
**Why it happens:** Trying to run parallel auth systems for a "gradual" migration.
**How to avoid:** Big-bang cutover is recommended for this codebase. The app has few active users (pre-launch). Switch all endpoints at once, require re-registration. Simpler, less code, less risk.
**Warning signs:** "Works on some pages, not others"; inconsistent token formats across endpoints.

### Pitfall 6: Forgetting to Update All Router Imports

**What goes wrong:** Some API routers still import `get_current_user` from the old location (`auth_enhanced` or `dependencies`), causing import errors or using stale auth logic.
**Why it happens:** 15+ router files import auth dependencies from 2 different modules (see grep results below).
**How to avoid:** After rewriting `dependencies.py`, update ALL imports. Systematic approach: grep for all `from app.core.auth_enhanced import` and `from app.core.dependencies import` across `api/v1/`.
**Warning signs:** Import errors on startup; specific endpoints failing with unexpected auth errors.

**Import map (current state):**
- `auth_enhanced.get_current_user` used by: `rbac.py`, `admin_audit.py`, `auth_enhanced.py` (router)
- `dependencies.get_current_user` used by: `users.py`, `reservations.py`, `reviews.py`, `spaces.py`, `notifications.py`, `owner.py`, `loyalty.py`, `establishments.py`, `favorites.py`, `groups.py`, `credits.py`, `auth.py`, `calendar.py`, `activity.py`

## Code Examples

### Stack Auth JWKS Endpoint and JWT Structure

```
JWKS URL: https://api.stack-auth.com/api/v1/projects/{PROJECT_ID}/.well-known/jwks.json

JWT Claims (ES256 signed):
{
  "iss": "https://api.stack-auth.com/api/v1/projects/{PROJECT_ID}",
  "sub": "{STACK_AUTH_USER_ID}",           // The user ID
  "aud": "{PROJECT_ID}",                    // Audience = your project
  "exp": 1735689600,                        // Expiration (default: 10 min)
  "iat": 1735603200,                        // Issued at
  "project_id": "{PROJECT_ID}",
  "role": "authenticated",                  // Always "authenticated" — NOT custom role
  "name": "John Doe",                       // Display name (nullable)
  "email": "john@example.com",              // Primary email (nullable)
  "email_verified": true,
  "selected_team_id": null,                 // Team context (nullable)
  "is_anonymous": false
}
```

Source: https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/concepts/jwt.mdx (verified 2026-02-21)

### REST API Verification (Fallback/Admin Use)

```python
# Only for admin operations or when full user profile is needed
import httpx

async def get_stack_auth_user(access_token: str) -> dict:
    """Get full user profile from Stack Auth REST API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.stack-auth.com/api/v1/users/me",
            headers={
                "x-stack-access-type": "server",
                "x-stack-project-id": settings.STACK_PROJECT_ID,
                "x-stack-secret-server-key": settings.STACK_SECRET_SERVER_KEY,
                "x-stack-access-token": access_token,
            },
        )
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=401, detail="Invalid token")
```

Source: https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/concepts/backend-integration.mdx (verified 2026-02-21)

### Database Migration Example

```sql
-- Step 1: Drop FK to Supabase auth.users (CRITICAL)
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey CASCADE;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_id_fkey;

-- Step 2: Re-add PK without FK to auth.users
ALTER TABLE users ADD PRIMARY KEY (id);

-- Step 3: Add Stack Auth user ID column
ALTER TABLE users ADD COLUMN IF NOT EXISTS stack_auth_id TEXT UNIQUE;

-- Step 4: Standardize password column (INFRA-03) then drop
-- (password no longer needed — Stack Auth manages passwords)
ALTER TABLE users DROP COLUMN IF EXISTS hashed_password;
ALTER TABLE users DROP COLUMN IF EXISTS reset_token;
ALTER TABLE users DROP COLUMN IF EXISTS reset_token_hash;
ALTER TABLE users DROP COLUMN IF EXISTS reset_token_expires;

-- Step 5: Drop custom_roles table and FK (3 fixed roles only)
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_custom_role;
ALTER TABLE users DROP COLUMN IF EXISTS custom_role_id;
DROP TABLE IF EXISTS custom_roles;

-- Step 6: Create index for Stack Auth ID lookups
CREATE INDEX IF NOT EXISTS idx_users_stack_auth_id ON users(stack_auth_id);
```

### Owner Self-Promotion (Next.js Server Action or API Route)

```typescript
// app/api/become-owner/route.ts
import { stackServerApp } from "@/stack/server";

export async function POST() {
  const user = await stackServerApp.getUser({ or: "redirect" });

  await user.update({
    clientReadOnlyMetadata: {
      ...user.clientReadOnlyMetadata,
      role: "owner",
    },
  });

  // Also update local DB (or let webhook handle it)
  return Response.json({ success: true });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `python-jose` HS256 symmetric JWT | `PyJWT[crypto]` ES256 asymmetric JWT via JWKS | Stack Auth uses ES256 since launch | No shared secret needed; public key verification only |
| `passlib[bcrypt]` local password storage | Stack Auth managed passwords | This migration | Backend no longer stores/handles passwords |
| `localStorage` token storage | Stack Auth SDK httpOnly cookies | Stack Auth default behavior | Eliminates XSS token theft risk |
| `next-auth` SessionProvider | Stack Auth `StackProvider` | This migration | Purpose-built for Stack Auth; no dead code |
| Custom refresh token interceptor | Stack Auth automatic refresh | SDK handles internally | Token refresh before expiry (10 min default); no 401 retry logic needed |

**Deprecated/outdated after migration:**
- `auth_enhanced.py` (entire file): Custom JWT auth replaced by Stack Auth
- `security.py` (entire file): JWT encode/decode replaced by Stack Auth
- `auth_simple.py`: Redundant auth module
- `auth.py` API router: Supabase Auth endpoints
- `auth_enhanced.py` API router: Custom JWT endpoints (register, login, refresh, password reset)
- `rbac.py` custom roles section: `custom_roles` table, `create_custom_role`, `update_custom_role`, `delete_custom_role`, `assign_role_to_user`

## Open Questions

1. **Stack Auth User ID Format**
   - What we know: JWT `sub` field contains the user ID; example shows `"user_123456"` but this may be a placeholder
   - What's unclear: Whether Stack Auth user IDs are UUIDs, prefixed strings, or another format
   - Recommendation: Add `stack_auth_id TEXT` column regardless — works with any format. Validate during implementation by creating a test user in Stack Auth dashboard.

2. **Webhook Delivery Reliability**
   - What we know: Stack Auth fires `user.created` and `user.updated` webhooks; these are needed to sync role changes to local DB
   - What's unclear: Retry policy, delivery guarantees, latency between role change and webhook delivery
   - Recommendation: Implement webhook endpoint with idempotent handling. Also have the backend update local DB role directly when processing owner self-promotion (don't rely solely on webhook for real-time role changes).

3. **Existing User Data Preservation**
   - What we know: Current users have reservations, reviews, favorites, credits linked by `user_id` FK
   - What's unclear: How many active users exist; whether data loss from re-registration is acceptable
   - Recommendation: Force re-registration (cleanest). When new Stack Auth user signs up, create a new `users` row. If user data preservation is critical, provide a one-time "link account" flow that matches by email and assigns the old UUID row a new `stack_auth_id`.

4. **Stack Auth Default Session Duration**
   - What we know: JWT expiry is 10 minutes (configurable via `STACK_ACCESS_TOKEN_EXPIRATION_TIME`); SDK auto-refreshes
   - What's unclear: Default refresh token lifetime; whether it matches the "30 days" mentioned in STACK.md
   - Recommendation: Use defaults (builder's discretion). The 10-minute access token with auto-refresh provides good security without user friction.

## Sources

### Primary (HIGH confidence)
- Stack Auth backend integration docs (GitHub raw): `https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/concepts/backend-integration.mdx` — JWT verification (ES256, JWKS), REST API verification, Python example code
- Stack Auth JWT docs (GitHub raw): `https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/concepts/jwt.mdx` — JWT structure, claims, ES256, JWKS endpoint, security best practices
- Stack Auth custom user data docs (GitHub raw): `https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/concepts/custom-user-data.mdx` — `clientMetadata`, `serverMetadata`, `clientReadOnlyMetadata`
- Stack Auth REST API overview (GitHub raw): `https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/rest-api/overview.mdx` — All header names, auth patterns, access types
- Stack Auth setup docs (GitHub raw): `https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/getting-started/setup.mdx` — init wizard, provider setup, file structure
- Stack Auth user management docs (GitHub raw): `https://raw.githubusercontent.com/stack-auth/stack-auth/main/docs/content/docs/(guides)/getting-started/users.mdx` — useUser(), protecting pages, signOut, user.update()

### Secondary (MEDIUM confidence)
- Stack Auth docs site (WebSearch verified): https://docs.stack-auth.com — Confirmed `clientReadOnlyMetadata` for role storage, teams/permissions model, `useUser()` hook API
- npm `@stackframe/stack` package: ^2.8.68 — Verified active maintenance (Feb 2026), Next.js App Router support

### Tertiary (LOW confidence)
- Stack Auth user ID format: Example `"user_123456"` seen in JWT docs — may be placeholder; actual format needs validation during implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries verified from official docs and GitHub source
- Architecture: HIGH — Backend integration patterns verified with Python code examples from official docs
- Pitfalls: HIGH — Based on direct codebase analysis (6 files read, 15+ router imports traced) and verified JWT structure
- Role storage: MEDIUM — `clientReadOnlyMetadata` pattern verified, but user decision says "token claims" which is technically impossible; recommendation is a practical interpretation
- User ID format: LOW — Placeholder example only; needs validation

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (Stack Auth actively maintained; API stable)
