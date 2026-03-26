---
phase: 01-auth-migration
plan: 02
subsystem: auth
tags: [stack-auth, react, next.js, axios, frontend]

requires:
  - phase: 01-auth-migration plan 01
    provides: Stack Auth backend JWT verification and DB migration
provides:
  - StackClientApp configuration and provider wrapping
  - Stack Auth handler route for sign-in/sign-up/sign-out
  - Navbar with useUser() auth state integration
  - API client with x-stack-access-token interceptor
affects: [01-auth-migration plan 03, 01-auth-migration plan 04, 01-auth-migration plan 05]

tech-stack:
  added: ["@stackframe/stack"]
  patterns: ["StackProvider as outermost provider in layout.tsx", "useUser() hook for auth state in components", "async axios interceptor for Stack Auth tokens"]

key-files:
  created:
    - "librework/frontend/src/stack/client.ts"
    - "librework/frontend/src/app/handler/[...stack]/page.tsx"
  modified:
    - "librework/frontend/package.json"
    - "librework/frontend/package-lock.json"
    - "librework/frontend/src/app/layout.tsx"
    - "librework/frontend/src/components/providers.tsx"
    - "librework/frontend/src/components/Navbar.tsx"
    - "librework/frontend/src/lib/api.ts"
    - "librework/frontend/.env.local.example"

key-decisions:
  - "StackProvider placed outside all other providers in layout.tsx for broadest scope"
  - "Owner Dashboard menu gated by clientReadOnlyMetadata.role check"
  - "Async axios interceptor calls stackClientApp.getUser() on each request"

patterns-established:
  - "StackProvider wrapping: always outermost in layout.tsx"
  - "Auth state via useUser() hook: returns null when unauthenticated, user object when authenticated"
  - "API token header: x-stack-access-token set via async interceptor"

requirements-completed: [AUTH-01, AUTH-02, AUTH-06, AUTH-07]

duration: 35min
completed: 2026-02-21
---

# Phase 1 Plan 2: Frontend Stack Auth Setup Summary

**Stack Auth SDK with StackProvider, catch-all handler route, useUser() Navbar integration, and async token interceptor replacing next-auth and localStorage**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-02-21T00:37:45Z
- **Completed:** 2026-02-21T01:13:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Installed @stackframe/stack SDK and removed next-auth completely
- Created StackClientApp config and catch-all handler route for /handler/sign-in, /handler/sign-up, etc.
- StackProvider wraps the entire app as outermost provider in layout.tsx
- Navbar uses useUser() for auth state with role-based owner menu items
- API client uses async interceptor with x-stack-access-token header, replacing all localStorage token logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Stack Auth SDK + configure provider + handler route** - `0d69ff7` (feat)
2. **Task 2: Update Navbar + API client for Stack Auth** - `d3f2286` (feat)

## Files Created/Modified
- `frontend/src/stack/client.ts` - StackClientApp configuration with project credentials and redirect URLs
- `frontend/src/app/handler/[...stack]/page.tsx` - Catch-all route for Stack Auth sign-in/sign-up/sign-out pages
- `frontend/package.json` - Added @stackframe/stack, removed next-auth
- `frontend/src/app/layout.tsx` - StackProvider and StackTheme wrapping the app
- `frontend/src/components/providers.tsx` - Removed SessionProvider from next-auth
- `frontend/src/components/Navbar.tsx` - useUser() for auth state, role-based menu, Stack Auth links
- `frontend/src/lib/api.ts` - Async interceptor with x-stack-access-token, removed localStorage logic
- `frontend/.env.local.example` - Added NEXT_PUBLIC_STACK_PROJECT_ID and NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY

## Decisions Made
- StackProvider placed as outermost provider in layout.tsx (outside QueryClientProvider and Toaster)
- Owner Dashboard menu item gated by `clientReadOnlyMetadata.role` check instead of always showing
- Used `user.signOut()` for logout which redirects via the afterSignOut URL in client config

## Deviations from Plan

None - plan executed exactly as written.

## User Setup Required

**External services require manual configuration.** Stack Auth project credentials needed:
- `NEXT_PUBLIC_STACK_PROJECT_ID` - from Stack Auth Dashboard -> Project Settings -> Project ID
- `NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY` - from Stack Auth Dashboard -> API Keys -> Publishable Client Key

## Issues Encountered
None

## Next Phase Readiness
- Frontend auth foundation complete with Stack Auth SDK
- Ready for Plan 03 (backend auth middleware) and Plan 04 (hook migration across all pages)
- All components using useUser() pattern established for future pages

---
*Phase: 01-auth-migration*
*Completed: 2026-02-21*
