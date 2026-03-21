---
phase: 09-fix-select-visibility-issues-and-integrate-google-maps-open-data
plan: "01"
subsystem: frontend/styling
tags: [css, tailwind, shadcn, fix, globals]
dependency_graph:
  requires: []
  provides: [correct-tailwind-color-tokens]
  affects: [all-shadcn-components, select-dropdowns, popovers, cards, sidebar]
tech_stack:
  added: []
  patterns: [HSL triple CSS variables for Tailwind v3 hsl() wrapping]
key_files:
  created: []
  modified:
    - librework/frontend/src/app/globals.css
decisions:
  - "Keep --input-background and --switch-background as hex values since they are used directly via var() not wrapped in hsl()"
  - "Chart variables converted to HSL triples for consistency with tailwind color token pattern"
  - "Dead @theme inline block removed entirely — Tailwind v4 syntax with no effect under v3"
  - "@custom-variant dark removed — Tailwind v4 syntax, project already uses darkMode: ['class'] in tailwind.config.ts"
metrics:
  duration: "5 minutes"
  completed: "2026-03-21"
  tasks_completed: 1
  files_modified: 1
---

# Phase 09 Plan 01: Fix Select/Dropdown Visibility — CSS Variable HSL Conversion Summary

Fix CSS variable format mismatch: all Tailwind color tokens now use bare HSL triples compatible with `hsl(var(--X))` wrapping in tailwind.config.ts.

## What Was Done

All color variables in `:root` and `.dark` blocks that are consumed by `tailwind.config.ts` via `hsl(var(--X))` were converted from hex values to bare HSL triples (format: `H S% L%`).

**Root cause:** `tailwind.config.ts` wraps every CSS variable as `hsl(var(--X))`. When globals.css defined `--popover: #ffffff`, the resolved value was `hsl(#ffffff)` — an invalid CSS color, which browsers render as transparent. This caused all Select dropdowns, Popovers, Cards, and other shadcn components to have transparent or invisible backgrounds.

**Two blocks of dead code removed:**
1. `@theme inline { ... }` (54 lines) — Tailwind v4 syntax, completely inert under Tailwind v3
2. `@custom-variant dark (&:is(.dark *));` — Tailwind v4 syntax, superseded by `darkMode: ["class"]` already in tailwind.config.ts

**Variables left as hex (correct — not consumed via hsl() wrapping):**
- `--input-background`, `--switch-background` — used directly as `var()` in components
- `--primary-500`, `--primary-600`, `--primary-100` — brand color vars used as direct `var()` references
- `--gray-*`, `--success`, `--warning`, `--error` — custom vars referenced directly

## Deviations from Plan

None - plan executed exactly as written.

## Verification

Build: `npm run build` passes cleanly (pre-existing stackframe/stack-ui `CircleAlert` warning is unrelated to this change and pre-dates it).

All variables consumed by tailwind.config.ts via `hsl(var(--X))` now resolve to valid CSS colors:
- `--popover: 0 0% 100%` → `hsl(0 0% 100%)` = `rgb(255, 255, 255)` (opaque white)
- `--card: 0 0% 100%` → `hsl(0 0% 100%)` = `rgb(255, 255, 255)` (opaque white)
- All dark mode variables resolve to correct dark grays

## Self-Check: PASSED

- `librework/frontend/src/app/globals.css` exists and contains HSL triples
- Commit `341643e` exists in submodule repo
