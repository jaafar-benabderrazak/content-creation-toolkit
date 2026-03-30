---
phase: 08-the-compilation-via-remotion-should-be-top-notch
plan: "02"
subsystem: remotion
tags: [remotion, transitions, spring-physics, profile-system, video-composition]
dependency_graph:
  requires: ["08-01"]
  provides: ["08-03", "08-04"]
  affects: ["remotion/src/StudyVideo.tsx", "remotion/src/Root.tsx"]
tech_stack:
  added: ["@remotion/transitions", "@remotion/transitions/fade", "@remotion/transitions/wipe", "@remotion/transitions/slide"]
  patterns: ["TransitionSeries", "spring() physics", "calculateMetadata", "profile-driven rendering"]
key_files:
  created: []
  modified:
    - remotion/src/StudyVideo.tsx
    - remotion/src/Root.tsx
decisions:
  - "Used `as any` return type for getPresentation() to avoid TypeScript union narrowing rejection across wipe/slide/fade presentation types — a Remotion API limitation, not a design flaw"
  - "calculateMetadata uses Record<string, unknown> prop type due to Remotion's LooseComponentType constraint on Composition — cast props internally"
  - "Font imports converted to side-effect-only import (`import './fonts/index'`) since font loading is triggered by module evaluation, not variable access"
metrics:
  duration: "2 min"
  completed: "2026-03-28"
  tasks_completed: 2
  files_modified: 2
---

# Phase 8 Plan 02: StudyVideo Refactor — TransitionSeries, Spring Physics, calculateMetadata Summary

StudyVideo refactored to use TransitionSeries for profile-driven inter-scene transitions (fade/wipe/slide), spring() physics for all motion (parallax, zoom, timer pop-in), and Root.tsx updated with calculateMetadata() that derives durationInFrames from sceneDurations array minus transition overlap — eliminating the hardcoded 120-minute constant.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Refactor StudyVideo.tsx — TransitionSeries, spring physics, profile system | ca50337 | remotion/src/StudyVideo.tsx |
| 2 | Update Root.tsx — calculateMetadata for StudyVideo, sceneDurations defaultProp | 3dc2138 | remotion/src/Root.tsx |

## What Was Built

### StudyVideo.tsx
- Replaced `images.map(...Sequence)` with `TransitionSeries` — each scene is a `TransitionSeries.Sequence`, transitions inserted between them via `TransitionSeries.Transition`
- Profile selects transition presentation: `fade()` (lofi-study), `wipe()` (cinematic), `slide()` (tech-tutorial) via `getPresentation(profileConfig.transition)`
- `springTiming({ config: { damping: 200 } })` used for transition timing — smooth, physics-based
- Scene parallax rewritten: `spring()` drives a `parallaxProgress` [0,1] value, then `interpolate` maps to `[-20,20]px` / `[-10,10]px` — organic feel vs. old linear pan
- Scene zoom rewritten: `spring({ damping: 20, stiffness: 60 })` drives `[1.05, 1.12]` scale
- Timer gains spring pop-in: `spring({ damping: 10, stiffness: 200 })` drives `scale(${popIn})`
- Timer uses `profileConfig.fontFamily` instead of hardcoded `"monospace"`
- Particles gated on `profileConfig.particleDensity > 0` (not just `enableParticles`)
- `Vignette` replaces inline radial gradient, strength from `profileConfig.vignetteStrength`
- `FilmGrain` rendered only when `profileConfig.grainIntensity > 0`
- `AudioVisualizer` rendered in bottom-left footer when `audioFile && profile === "lofi-study"`
- New props: `profile?: string`, `sceneDurations?: number[]`

### Root.tsx
- Added `import { getProfile } from "./profiles/index"`
- StudyVideo Composition: removed `durationInFrames={30 * 60 * 120}`, added `calculateMetadata`
- `calculateMetadata` logic:
  1. Resolves `sceneDurations` from props (falls back to `Array(images.length).fill(sceneDuration)`)
  2. Sums scene frames: `sceneDurations.reduce((sum, dur) => sum + Math.round(dur * fps), 0)`
  3. Computes transition overlap: `(n - 1) * profile.transitionDuration`
  4. Returns `Math.max(totalSceneFrames - transitionFrames, 1)` — never zero
- defaultProps gains `sceneDurations: []` and `profile: "lofi-study"`
- TechTutorial Composition: `durationInFrames={30 * 60}` preserved, defaultProps gains `profile: "tech-tutorial"` for Plan 03 readiness

## Verification Results

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | Exit 0 — clean |
| `grep -c "TransitionSeries" src/StudyVideo.tsx` | 7 (import + 6 JSX usages) |
| `grep -c "spring(" src/StudyVideo.tsx` | 3 (parallax, zoom, pop-in) |
| `grep "interpolate(frame, [0," src/StudyVideo.tsx"` | 0 — all linear entrances replaced |
| `grep "30 * 60 * 120" src/Root.tsx` | 0 — hardcoded duration gone |
| `grep "calculateMetadata" src/Root.tsx` | Present |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TransitionSeries.Transition presentation union type rejection**
- **Found during:** Task 1 TypeScript check
- **Issue:** `getPresentation()` inferred return type as `TransitionPresentation<WipeProps> | TransitionPresentation<SlideProps> | TransitionPresentation<FadeProps>`, but `TransitionSeries.Transition` expects `TransitionPresentation<WipeProps> | undefined` — Remotion's API types the prop narrowly
- **Fix:** Added `: any` return type annotation to `getPresentation()` with eslint-disable comment
- **Files modified:** remotion/src/StudyVideo.tsx
- **Commit:** ca50337

**2. [Rule 1 - Bug] calculateMetadata props type incompatibility in Root.tsx**
- **Found during:** Task 2 — existing `component={StudyVideo}` already had `as any` cast from linter (pre-existing), but calculateMetadata's `props` parameter needed explicit `Record<string, unknown>` type annotation to avoid inference failures
- **Fix:** Typed `({ props }: { props: Record<string, unknown> })` in calculateMetadata signature, cast prop accesses internally
- **Files modified:** remotion/src/Root.tsx
- **Commit:** 3dc2138

**3. [Rule 2 - Missing functionality] Font side-effect import**
- **Found during:** Task 1 — `spaceGrotesk` and `jetBrainsMono` named exports would show as unused variables
- **Fix:** Converted `import { spaceGrotesk, jetBrainsMono } from "./fonts/index"` to `import "./fonts/index"` — fonts load on module evaluation; named exports not needed in this file
- **Files modified:** remotion/src/StudyVideo.tsx
- **Commit:** ca50337

## Self-Check: PASSED

| Item | Status |
| ---- | ------ |
| remotion/src/StudyVideo.tsx | FOUND |
| remotion/src/Root.tsx | FOUND |
| 08-02-SUMMARY.md | FOUND |
| commit ca50337 (Task 1) | FOUND |
| commit 3dc2138 (Task 2) | FOUND |
