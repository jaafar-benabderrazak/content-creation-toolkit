---
phase: "08-the-compilation-via-remotion-should-be-top-notch"
plan: "03"
subsystem: "remotion"
tags: ["remotion", "animation", "spring", "profile-system", "TechTutorial"]
dependency_graph:
  requires:
    - "08-01"  # profiles, fonts, TextReveal, FilmGrain, Vignette
  provides:
    - "TechTutorial.tsx refactored with spring/TextReveal/profile"
  affects:
    - "remotion/src/TechTutorial.tsx"
    - "remotion/src/Root.tsx"
tech_stack:
  added: []
  patterns:
    - "spring() for entrance animations instead of linear interpolate"
    - "TextReveal component for per-word stagger on bullet points"
    - "Profile-gated effects (FilmGrain, Vignette, cssColorFilter)"
    - "Easing.out(Easing.cubic) for fade-out overlays"
key_files:
  created: []
  modified:
    - "remotion/src/TechTutorial.tsx"
    - "remotion/src/Root.tsx"
    - "remotion/src/StudyVideo.tsx"
decisions:
  - "Cast component props to `any` in Root.tsx — Remotion's LooseComponentType does not accept typed FC props; this is the idiomatic fix"
  - "Cast getPresentation return to `any` in StudyVideo.tsx — union of TransitionPresentation types is not assignable to a single typed slot"
metrics:
  duration: "2 min"
  completed: "2026-03-28"
  tasks_completed: 1
  files_modified: 3
---

# Phase 08 Plan 03: TechTutorial Refactor Summary

Spring-based title entrance and per-word TextReveal bullets in TechTutorial using the shared profile system from Plan 01.

## What Was Built

`TechTutorial.tsx` was rewritten to consume all shared components from Plan 01:

- **Profile resolution**: `getProfile(profile ?? "tech-tutorial")` at component root; fontFamily derived from profile.
- **Title entrance**: `spring({ frame, fps, config: profileConfig.springConfig, durationInFrames: 25 })` replaces the previous `interpolate(frame, [0, 30], [0, 1])` linear fade.
- **Bullet animations**: Each bullet rendered as `<TextReveal text={bullet} startFrame={60 + i*45} staggerFrames={4} springConfig={...} />` — old `bullets.map` with per-bullet `interpolate` on opacity/translateX removed entirely.
- **Background filter**: `filter: profileConfig.cssColorFilter` on the `<Img>` element.
- **Vignette**: `<Vignette strength={profileConfig.vignetteStrength} />` after content card.
- **FilmGrain**: Conditional — `{profileConfig.grainIntensity > 0 && <FilmGrain .../>}`. tech-tutorial profile has grainIntensity=0 so it never renders for that profile.
- **Fade-out**: `Easing.out(Easing.cubic)` easing option in interpolate replaces the bare `{ extrapolateLeft, extrapolateRight }` only version.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pre-existing Root.tsx TypeScript errors blocking clean compile**
- **Found during:** Task 1 verification
- **Issue:** Root.tsx was missing `import React from "react"` and had TS2322 errors on `component={StudyVideo}` and `component={TechTutorial}` due to Remotion's `LooseComponentType<Record<string, unknown>>` not accepting typed FC props.
- **Fix:** Added React import, cast both components to `any`, added `profile: "tech-tutorial"` to TechTutorial defaultProps.
- **Files modified:** `remotion/src/Root.tsx`
- **Commit:** a876e2a

**2. [Rule 3 - Blocking] Fixed pre-existing StudyVideo.tsx TS2322 on presentation union type**
- **Found during:** Task 1 verification
- **Issue:** `getPresentation()` returned `TransitionPresentation<WipeProps> | TransitionPresentation<SlideProps> | TransitionPresentation<FadeProps>` but `presentation` prop expects a single concrete type. TypeScript rejected the union assignment.
- **Fix:** Added `: any` return type annotation to `getPresentation`. The linter had partially addressed this (added eslint-disable comment) but the type annotation was missing.
- **Files modified:** `remotion/src/StudyVideo.tsx`
- **Commit:** a876e2a

## Verification Results

All verification commands passed:
1. `npx tsc --noEmit` — zero output (clean)
2. `grep "TextReveal" src/TechTutorial.tsx` — 3 matches (import, comment, JSX usage)
3. `grep "spring(" src/TechTutorial.tsx` — 1 match (titleSpring)
4. `grep 'interpolate(frame, \[start' src/TechTutorial.tsx` — no output (old bullet logic removed)
5. `grep "Vignette" src/TechTutorial.tsx` — 2 matches (import, JSX)

## Self-Check: PASSED

- `remotion/src/TechTutorial.tsx` — FOUND
- `remotion/src/Root.tsx` — FOUND
- Commit a876e2a — FOUND
