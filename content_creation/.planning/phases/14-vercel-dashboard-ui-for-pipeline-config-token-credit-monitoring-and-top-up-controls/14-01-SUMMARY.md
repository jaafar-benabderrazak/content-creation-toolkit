---
phase: 14-vercel-dashboard-ui-for-pipeline-config-token-credit-monitoring-and-top-up-controls
plan: "01"
subsystem: dashboard
tags: [nextjs, shadcn-ui, tailwind, vercel, dashboard]
dependency_graph:
  requires: []
  provides: [dashboard/package.json, dashboard/src/app/layout.tsx, dashboard/src/app/page.tsx, dashboard/vercel.json, dashboard/.env.example]
  affects: []
tech_stack:
  added: [next@16.2.1, react@19, tailwindcss@3, shadcn/ui, class-variance-authority, clsx, tailwind-merge, tailwindcss-animate, autoprefixer]
  patterns: [Next.js App Router, shadcn/ui component library, Tailwind CSS variables for theming]
key_files:
  created:
    - dashboard/package.json
    - dashboard/tsconfig.json
    - dashboard/next.config.ts
    - dashboard/tailwind.config.ts
    - dashboard/postcss.config.js
    - dashboard/components.json
    - dashboard/src/app/globals.css
    - dashboard/src/app/layout.tsx
    - dashboard/src/app/page.tsx
    - dashboard/src/lib/utils.ts
    - dashboard/src/components/ui/button.tsx
    - dashboard/src/components/ui/card.tsx
    - dashboard/src/components/ui/badge.tsx
    - dashboard/src/components/ui/separator.tsx
    - dashboard/vercel.json
    - dashboard/.env.example
    - dashboard/.gitignore
  modified: []
decisions:
  - "Next.js 16.2.1 used instead of 15.x — 15.2.4 had active CVE-2025-66478 security vulnerability; upgraded immediately on detection"
  - "autoprefixer added as devDependency — Turbopack build requires it explicitly even though Tailwind implies it"
  - "src/lib tracked with git add -f — root .gitignore has a lib/ exclusion pattern that collides with dashboard/src/lib; force-add is the correct override for a nested project"
  - "shadcn/ui components written manually instead of via CLI — npx shadcn@latest init triggered interactive TTY prompts incompatible with non-interactive execution"
metrics:
  duration: "18 min"
  completed: "2026-03-28"
  tasks_completed: 2
  files_created: 17
---

# Phase 14 Plan 01: Next.js Dashboard Scaffold Summary

Next.js 16 App Router shell with shadcn/ui sidebar navigation, Tailwind CSS theming, and Vercel deployment config deployed to dashboard/ directory.

## Tasks Completed

| # | Name | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Initialize Next.js 15 project with shadcn/ui and Tailwind | 91dd8ce | package.json, layout.tsx, page.tsx, globals.css, 4 UI components |
| 2 | Configure Vercel deployment and environment variables | ae9a83a | vercel.json, .env.example, .gitignore |

## What Was Built

- `dashboard/` directory at the repo root, alongside `generators/`, `shared/`, `config/`
- Next.js 16.2.1 with Turbopack, TypeScript strict mode, App Router, `@/*` import alias
- Persistent left sidebar (w-56, border-r, bg-muted/40) with three NavLink items: Config Editor, Credits, Status
- Root homepage with three Card components linking to /config, /credits, /status sections
- shadcn/ui slate theme with CSS variables for full dark mode support
- `vercel.json` targeting cdg1 (Paris) region, framework=nextjs
- `.env.example` documenting 7 environment variables across all future plans

## Success Criteria Verification

- `npm run build` exits 0 — confirmed (Next.js 16.2.1 Turbopack, 3 static pages generated)
- TypeScript strict mode passes — confirmed (no type errors)
- Sidebar navigation with Config Editor, Credits, Status — confirmed in layout.tsx
- `.env.example` documents SUNO_API_KEY, REPLICATE_API_TOKEN, OPENAI_API_KEY, PIPELINE_WEBHOOK_SECRET, PIPELINE_TRIGGER_URL — confirmed
- `vercel.json` framework=nextjs — confirmed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Security] Upgraded Next.js from 15.2.4 to 16.2.1**
- **Found during:** Task 1 (npm install output)
- **Issue:** Next.js 15.2.4 has active CVE-2025-66478 security vulnerability; npm warned on install
- **Fix:** `npm install next@latest` — resolved to 16.2.1 with 0 vulnerabilities
- **Files modified:** dashboard/package.json, dashboard/package-lock.json
- **Commit:** ae9a83a (included in Task 2 commit)

**2. [Rule 3 - Blocking] Added missing autoprefixer devDependency**
- **Found during:** Task 1 build verification
- **Issue:** `npm run build` failed — Turbopack could not resolve `autoprefixer` module required by postcss.config.js
- **Fix:** `npm install -D autoprefixer`
- **Files modified:** dashboard/package.json, dashboard/package-lock.json
- **Commit:** 91dd8ce

**3. [Rule 3 - Blocking] Wrote shadcn/ui components manually instead of CLI**
- **Found during:** Task 1 execution
- **Issue:** `npx shadcn@latest init` triggered interactive TTY prompts ("Would you like to use React Compiler?") incompatible with non-interactive shell execution
- **Fix:** Wrote all required shadcn/ui components (Button, Card, Badge, Separator) and globals.css manually matching the shadcn/ui default/slate theme spec
- **Files created:** button.tsx, card.tsx, badge.tsx, separator.tsx, globals.css, components.json

**4. [Rule 3 - Blocking] Force-added dashboard/src/lib/utils.ts**
- **Found during:** Task 1 commit staging
- **Issue:** Root `.gitignore` contains a `lib/` exclusion pattern (CRLF line-count mismatch causes git to see line 13 as `lib/`); git refused to add dashboard/src/lib/
- **Fix:** `git add -f dashboard/src/lib/utils.ts` — force-add for nested project path that should not be excluded
- **Commit:** 91dd8ce

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| dashboard/package.json | FOUND |
| dashboard/src/app/layout.tsx | FOUND |
| dashboard/.env.example | FOUND |
| dashboard/vercel.json | FOUND |
| dashboard/src/lib/utils.ts | FOUND |
| commit 91dd8ce | FOUND |
| commit ae9a83a | FOUND |
| npm run build | PASSED (Turbopack, 0 errors) |
