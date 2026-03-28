---
phase: 08-the-compilation-via-remotion-should-be-top-notch
plan: "01"
subsystem: remotion
tags: [remotion, profiles, components, fonts, film-grain, text-reveal, audio-visualizer]
dependency_graph:
  requires: []
  provides:
    - remotion/src/profiles/index.ts (ProfileName, ProfileConfig, profiles, getProfile)
    - remotion/src/profiles/lofi-study.ts (lofiStudyProfile)
    - remotion/src/profiles/tech-tutorial.ts (techTutorialProfile)
    - remotion/src/profiles/cinematic.ts (cinematicProfile)
    - remotion/src/fonts/index.ts (spaceGrotesk, jetBrainsMono)
    - remotion/src/components/FilmGrain.tsx (FilmGrain)
    - remotion/src/components/Vignette.tsx (Vignette)
    - remotion/src/components/TextReveal.tsx (TextReveal)
    - remotion/src/components/AudioVisualizer.tsx (AudioVisualizer)
  affects:
    - Plans 02 and 03 (composition refactors import all of the above)
tech_stack:
  added:
    - "@remotion/transitions@4.0.441"
    - "@remotion/google-fonts@4.0.441"
    - "@remotion/media-utils@4.0.441"
  patterns:
    - "Profile system: typed interface + Record<ProfileName, ProfileConfig> + getProfile() selector with fallback"
    - "SVG grain with per-frame seed for animated noise"
    - "useWindowedAudioData with {src, frame, fps, windowInSeconds} options object (not raw string)"
key_files:
  created:
    - remotion/src/profiles/lofi-study.ts
    - remotion/src/profiles/tech-tutorial.ts
    - remotion/src/profiles/cinematic.ts
    - remotion/src/profiles/index.ts
    - remotion/src/fonts/index.ts
    - remotion/src/components/FilmGrain.tsx
    - remotion/src/components/Vignette.tsx
    - remotion/src/components/TextReveal.tsx
    - remotion/src/components/AudioVisualizer.tsx
  modified:
    - remotion/package.json
    - remotion/package-lock.json
decisions:
  - "ProfileConfig uses an explicit interface with union types for transition/x264Preset rather than typeof lofiStudyProfile — prevents TS narrowing rejecting slide and wipe profiles"
  - "useWindowedAudioData API changed in 4.0.441: takes options object {src,frame,fps,windowInSeconds}, returns {audioData, dataOffsetInSeconds} — updated AudioVisualizer accordingly"
  - "windowInSeconds=1 default chosen for AudioVisualizer — sufficient for bar visualization at 30fps without excess memory overhead"
metrics:
  duration: "~5 minutes"
  completed: "2026-03-28"
  tasks_completed: 3
  tasks_total: 3
  files_created: 9
  files_modified: 2
---

# Phase 08 Plan 01: Remotion Building Blocks — Profiles, Fonts, and Shared Components Summary

One-liner: Pinned six @remotion/* packages at 4.0.441, built a three-profile system (lofi-study/tech-tutorial/cinematic) with typed getProfile() selector, and created four shared components (FilmGrain, Vignette, TextReveal, AudioVisualizer) plus Google Fonts loading — the zero-dependency building blocks for Plans 02 and 03.

## What Was Built

### Task 1: Package installation and version pinning

Installed `@remotion/transitions`, `@remotion/google-fonts`, and `@remotion/media-utils` all at 4.0.441. Removed `^` carets from all six remotion-related package.json entries to prevent version drift (the bundler throws a mismatch error if any @remotion/* packages differ at render time).

### Task 2: Profile system (4 files)

- `lofi-study`: fade transition, grain 0.05, vignette 0.35, timerVisible true, particleDensity 20, crf 18
- `tech-tutorial`: slide transition, overshootClamping spring, grainIntensity 0, crf 18
- `cinematic`: wipe transition, grain 0.12, vignette 0.55, crf 16, x264Preset slow
- `index.ts`: `ProfileName` union type, `ProfileConfig` interface, `profiles` record, `getProfile()` selector (falls back to lofi-study for unknown names from Python PipelineConfig)

### Task 3: Fonts and shared components (5 files)

- `fonts/index.ts`: `spaceGrotesk` and `jetBrainsMono` exported font family strings via @remotion/google-fonts automatic delayRender/continueRender
- `FilmGrain`: AbsoluteFill SVG feTurbulence with `seed={frame}` for animated noise, instance-scoped filter ID to prevent collisions with multiple instances
- `Vignette`: configurable strength radial-gradient overlay, pointer-events none
- `TextReveal`: per-word spring opacity+translateY with configurable staggerFrames (default 5) and springConfig
- `AudioVisualizer`: `useWindowedAudioData` with correct options shape; passes `dataOffsetInSeconds` to `visualizeAudio` for accurate windowed playback

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ProfileConfig type too narrow using typeof lofiStudyProfile**
- Found during: Task 2 verification
- Issue: `ProfileConfig = typeof lofiStudyProfile` locked the `transition` field to literal `"fade"`, causing TS2322 when assigning tech-tutorial (transition "slide") and cinematic (transition "wipe") to the profiles Record
- Fix: Replaced with an explicit `ProfileConfig` interface with `transition: "fade" | "slide" | "wipe"` union and a complete `x264Preset` union type
- Files modified: `remotion/src/profiles/index.ts`
- Commit: e68d07b

**2. [Rule 1 - Bug] useWindowedAudioData API changed in 4.0.441**
- Found during: Task 3 verification
- Issue: The plan assumed `useWindowedAudioData(src: string)` returning `MediaUtilsAudioData | null`. Actual API at 4.0.441 takes `UseWindowedAudioDataOptions = {src, frame, fps, windowInSeconds}` and returns `{audioData, dataOffsetInSeconds}`
- Fix: Updated AudioVisualizer to pass the options object and destructure the return value; also passes `dataOffsetInSeconds` to `visualizeAudio` for correct audio windowing
- Files modified: `remotion/src/components/AudioVisualizer.tsx`
- Commit: e9fcc20

### Out-of-Scope Items Deferred

Pre-existing `Root.tsx` TypeScript errors (TS2322 — component prop type mismatch with `LooseComponentType`) were present before this plan and are not caused by any changes here. These will be addressed in Plan 02 or 03 when compositions are refactored.

## Self-Check: PASSED

All 9 created files confirmed on disk. All 3 task commits confirmed in git log (1c9adf5, e68d07b, e9fcc20).
