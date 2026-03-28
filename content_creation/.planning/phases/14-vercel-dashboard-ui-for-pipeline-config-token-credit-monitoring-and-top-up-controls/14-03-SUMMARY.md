---
phase: 14-vercel-dashboard-ui-for-pipeline-config-token-credit-monitoring-and-top-up-controls
plan: "03"
subsystem: dashboard/credits
tags: [nextjs, api-routes, credit-monitoring, shadcn-ui, react]
dependency_graph:
  requires: ["14-01"]
  provides: ["credit-monitoring-ui", "credit-api-routes"]
  affects: ["dashboard/src/app/credits", "dashboard/src/app/api/credits"]
tech_stack:
  added: []
  patterns:
    - "Next.js App Router API routes with nodejs runtime and revalidate=0"
    - "CreditResponse shared type exported from suno route, imported by siblings"
    - "Promise.allSettled for parallel multi-provider fetch with per-slot error handling"
    - "useCallback + useEffect for mount fetch with refresh button"
key_files:
  created:
    - dashboard/src/app/api/credits/suno/route.ts
    - dashboard/src/app/api/credits/replicate/route.ts
    - dashboard/src/app/api/credits/openai/route.ts
    - dashboard/src/app/api/credits/youtube/route.ts
    - dashboard/src/components/credits/CreditCard.tsx
    - dashboard/src/components/ui/skeleton.tsx
    - dashboard/src/app/credits/page.tsx
  modified: []
decisions:
  - "CreditResponse type exported from suno/route.ts and imported by replicate, openai, youtube — single source of truth for the shared shape"
  - "YouTube quota reads from YOUTUBE_QUOTA_USED env var — no API call possible without user OAuth; pipeline must update env var after each upload run"
  - "Replicate returns value: null with error message — balance not available via their public API as of 2026"
  - "Skeleton component written manually (same pattern as other shadcn components) — interactive CLI not available in non-TTY context"
  - "Promise.allSettled used so one failing fetch does not block the other three cards from rendering"
metrics:
  duration: "2 min"
  completed: "2026-03-28"
  tasks_completed: 2
  files_created: 7
  files_modified: 0
---

# Phase 14 Plan 03: Credit/Quota Monitoring — API Routes and Credits Page Summary

Four credit API routes and a Credits page that shows live balances for Suno (kie.ai), Replicate, OpenAI, and YouTube quota in a responsive grid with top-up buttons.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Credit balance API routes for all four providers | ac57754 | suno/route.ts, replicate/route.ts, openai/route.ts, youtube/route.ts |
| 2 | Credits page with CreditCard components and refresh | 84ad945 | CreditCard.tsx, skeleton.tsx, credits/page.tsx |

## What Was Built

**API Routes** (`/api/credits/{provider}`) — all return `CreditResponse`:
- `suno`: calls `GET https://api.kie.ai/api/v1/account/credits`; falls back to `/account` on 404; returns `configured: false` when `SUNO_API_KEY` is absent
- `replicate`: validates token via `GET https://api.replicate.com/v1/account`; returns `value: null` with "Balance not available via API" since Replicate does not expose balance in their public API
- `openai`: calls `GET https://api.openai.com/dashboard/billing/credit_grants`; handles 404 for usage-based orgs; `value` is `total_available` in USD
- `youtube`: reads `YOUTUBE_QUOTA_USED` env var; computes `10000 - used`; flags stale data when `YOUTUBE_QUOTA_DATE` does not match today

All routes: `runtime = "nodejs"`, `revalidate = 0`, never return 500 on missing keys.

**UI Components**:
- `CreditCard`: shadcn Card with Skeleton loading shimmer, balance display, "Not configured" badge, error text, and Top Up button linking to provider billing page
- `Skeleton`: shadcn-pattern component with `animate-pulse`
- `/credits` page: parallel `Promise.allSettled` fetch on mount, Refresh button, responsive `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` layout

## Verification

- `npm run build` exits 0
- All four routes appear as `ƒ` (dynamic) in build output
- `/credits` renders as `○` (static shell, client-fetches on hydration)
- TypeScript check passes with zero errors

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `dashboard/src/app/api/credits/suno/route.ts` — FOUND
- `dashboard/src/app/api/credits/replicate/route.ts` — FOUND
- `dashboard/src/app/api/credits/openai/route.ts` — FOUND
- `dashboard/src/app/api/credits/youtube/route.ts` — FOUND
- `dashboard/src/components/credits/CreditCard.tsx` — FOUND
- `dashboard/src/components/ui/skeleton.tsx` — FOUND
- `dashboard/src/app/credits/page.tsx` — FOUND
- Commit ac57754 — FOUND
- Commit 84ad945 — FOUND
