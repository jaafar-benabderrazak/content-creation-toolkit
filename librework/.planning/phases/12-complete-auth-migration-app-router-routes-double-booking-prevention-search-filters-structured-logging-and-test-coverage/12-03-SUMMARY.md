---
phase: 12
plan: 03
subsystem: frontend-routing
tags: [app-router, next-intl, navigation, spa-removal]
dependency_graph:
  requires: [12-01]
  provides: [url-based-routing, bookmarkable-pages, auth-guarded-routes]
  affects: [frontend-navigation, playwright-tests]
tech_stack:
  added: []
  patterns: [next-intl useRouter, useParams from next/navigation, useUser({ or: 'redirect' })]
key_files:
  created:
    - frontend/src/app/[locale]/explore/page.tsx
    - frontend/src/app/[locale]/establishments/[id]/page.tsx
    - frontend/src/app/[locale]/dashboard/page.tsx
    - frontend/src/app/[locale]/owner/dashboard/page.tsx
    - frontend/src/app/[locale]/owner/admin/page.tsx
  modified:
    - frontend/src/app/[locale]/page.tsx
    - frontend/src/components/Navbar.tsx
    - frontend/src/components/HomePage.tsx
    - frontend/src/components/ExplorePage.tsx
    - frontend/src/components/EstablishmentDetails.tsx
    - frontend/src/components/UserDashboard.tsx
    - frontend/src/components/OwnerDashboard.tsx
    - frontend/src/components/OwnerAdminPage.tsx
    - frontend/src/components/UserProfileComponent.tsx
    - frontend/src/components/OwnerDashboardEnhanced.tsx
    - frontend/src/components/owner/EnhancedOwnerDashboard.tsx
  deleted:
    - frontend/src/app/home-client.tsx
decisions:
  - "useParams from next/navigation (not next-intl) used in establishments/[id]/page.tsx — params are route-level and locale-agnostic"
  - "OwnerDashboardEnhanced.tsx updated despite not being imported anywhere — eliminates stale onNavigate references from codebase search"
  - "EnhancedOwnerDashboard activeView=management renders OwnerAdminPage directly instead of navigating; avoids double-route for same component"
metrics:
  duration: 7min
  completed: 2026-03-26
  tasks_completed: 2
  files_changed: 12
---

# Phase 12 Plan 03: App Router Route Extraction Summary

6 SPA views extracted from home-client.tsx state machine into proper Next.js App Router routes with URL-based navigation using next-intl useRouter throughout.

## Tasks Completed

### Task 1: Create App Router route pages for all 6 views

Created 5 new route files and updated the root locale page:

- `[locale]/page.tsx` — renders `<HomePage />` directly (removed HomeClient/Suspense wrapper)
- `[locale]/explore/page.tsx` — `<ExplorePage />`, no auth guard
- `[locale]/establishments/[id]/page.tsx` — `<EstablishmentDetails>` with `useParams()` for dynamic id
- `[locale]/dashboard/page.tsx` — `<UserDashboard />` behind `useUser({ or: 'redirect' })`
- `[locale]/owner/dashboard/page.tsx` — `<OwnerDashboard />` behind `useUser({ or: 'redirect' })`
- `[locale]/owner/admin/page.tsx` — `<OwnerAdminPage />` behind `useUser({ or: 'redirect' })`

**Commit:** `900e2b5`

### Task 2: Remove onNavigate from all components, use router.push, delete home-client.tsx

Updated all 10 components:

- **Navbar**: removed `currentPage`+`onNavigate` props; added `usePathname` for active link highlighting; all navigation via `router.push`
- **HomePage**: removed `onNavigate` prop; `router.push('/explore')`, `router.push('/dashboard')`, `router.push('/establishments/${id}')`
- **ExplorePage**: removed `onNavigate` prop; map onSelect and card onClick use `router.push('/establishments/${id}')`
- **EstablishmentDetails**: removed `onNavigate` prop; back button uses `router.push('/explore')`; confirmation dialog uses `router.push('/dashboard')`
- **UserDashboard**: removed `onNavigate` prop; empty state uses `router.push('/explore')`
- **OwnerDashboard**: removed `onNavigate` prop; Manage Spaces buttons use `router.push('/owner/admin')`
- **OwnerAdminPage**: removed `onNavigate` prop; back button uses `router.push('/owner/dashboard')`
- **UserProfileComponent**: removed `onNavigate` prop; two explore links use `router.push('/explore')`
- **OwnerDashboardEnhanced**: removed `onNavigate` prop (unused file); all calls use `router.push('/owner/admin')`
- **EnhancedOwnerDashboard**: removed `onNavigate` prop; home button uses `router.push('/')`, empty state uses `router.push('/owner/admin')`

Deleted `home-client.tsx` — the SPA useState page state machine is no longer needed.

**Commit:** `724b06d` (bundled with 12-04 auth consolidation work)

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written.

### Additional Context

The `OwnerDashboardEnhanced.tsx` file was not in the original plan's file list but contained `onNavigate` references and was found via grep scan. Updated as Rule 2 (would fail the zero-onNavigate verification criterion).

The Task 2 changes were committed inside the `724b06d feat(12-04)` commit because those files had already been modified by an earlier 12-04 pass before this executor ran. The 12-03 route page creation (Task 1) has its own clean commit `900e2b5`.

## Verification Results

- `grep -rn "onNavigate" frontend/src/` — zero matches
- `home-client.tsx` — does not exist
- `grep -rn "home-client" frontend/src/` — zero matches
- All 5 new route files confirmed present
- Protected routes (`/dashboard`, `/owner/dashboard`, `/owner/admin`) call `useUser({ or: 'redirect' })`
- All navigation uses `useRouter` from `next-intl/navigation` (locale-aware)

## Self-Check

### Created files:
- `[locale]/explore/page.tsx` — FOUND
- `[locale]/establishments/[id]/page.tsx` — FOUND
- `[locale]/dashboard/page.tsx` — FOUND
- `[locale]/owner/dashboard/page.tsx` — FOUND
- `[locale]/owner/admin/page.tsx` — FOUND

### Commits:
- `900e2b5` — FOUND (Task 1: route pages)
- `724b06d` — FOUND (Task 2: onNavigate removal + home-client.tsx deletion)

## Self-Check: PASSED
