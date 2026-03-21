---
phase: 09-fix-select-visibility-issues-and-integrate-google-maps-open-data
plan: "02"
subsystem: frontend/explore
tags: [google-maps, places-api, react, typescript, leaflet]
dependency_graph:
  requires: []
  provides:
    - googlePlaces.ts fetchNearbyEstablishments utility
    - Establishment.coordinates optional field
    - APIProvider conditional wrapper in providers.tsx
  affects:
    - ExplorePage.tsx (data source, loading state)
    - MapView.tsx (coordinate resolution)
    - providers.tsx (Google Maps API loading)
tech_stack:
  added:
    - "@vis.gl/react-google-maps ^1.x — APIProvider for Maps JS API loading"
    - "@types/google.maps ^3.x — TypeScript types for google.maps.places.Place"
  patterns:
    - "google.maps.importLibrary('places') inside async function (requires APIProvider mounted)"
    - "Conditional APIProvider: only wraps children when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is defined"
    - "Mock data fallback: liveEstablishments.length > 0 ? liveEstablishments : establishments"
key_files:
  created:
    - librework/frontend/src/lib/googlePlaces.ts
  modified:
    - librework/frontend/src/lib/mockData.ts
    - librework/frontend/src/components/providers.tsx
    - librework/frontend/src/components/ExplorePage.tsx
    - librework/frontend/src/components/MapView.tsx
    - librework/frontend/package.json
decisions:
  - "Used --legacy-peer-deps for npm install: pre-existing react-leaflet@5/React18 conflict unrelated to this plan"
  - "Excluded openingHours from Places API fields to stay on Essentials SKU (10K free/month vs 5K for Pro)"
  - "APIProvider conditional on env var presence so app runs without any Google key configured"
metrics:
  duration: "4 minutes"
  completed_date: "2026-03-21"
  tasks_completed: 2
  tasks_total: 3
  files_created: 1
  files_modified: 5
---

# Phase 9 Plan 02: Google Maps Places API Integration Summary

**One-liner:** Google Places API (New) integration via @vis.gl/react-google-maps with Leaflet map markers using real GPS coordinates and mock data fallback when API key absent.

## What Was Built

Task 1 and Task 2 of 3 are complete. Task 3 is a human-verify checkpoint awaiting visual confirmation.

### Task 1 — Install dependencies, extend Establishment interface, create Places fetch utility

- Installed `@vis.gl/react-google-maps` and `@types/google.maps` with `--legacy-peer-deps` (pre-existing react-leaflet@5/React18 peer conflict).
- Added optional `coordinates?: { lat: number; lng: number }` field to `Establishment` interface in `mockData.ts`.
- Populated `coordinates` on all 5 mock establishments using the values previously hardcoded in `MapView.tsx`'s `COORDS` record.
- Created `librework/frontend/src/lib/googlePlaces.ts` exporting `fetchNearbyEstablishments(center, radiusMeters?)`:
  - Iterates over place types: `cafe`, `coworking_space`, `library`
  - Uses `Place.searchNearby` with Essentials SKU fields only (`displayName`, `formattedAddress`, `location`, `rating`, `userRatingCount`, `photos`, `types`, `businessStatus`)
  - Maps each `google.maps.places.Place` to `Establishment` interface
  - Full try/catch returning `[]` on error

Commit: `07ac562`

### Task 2 — Add APIProvider to providers, wire ExplorePage and MapView to use real data

- `providers.tsx`: imports `APIProvider` from `@vis.gl/react-google-maps`; conditionally wraps children only when `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is set in env — app works without any key.
- `ExplorePage.tsx`:
  - Imports `fetchNearbyEstablishments` from `@/lib/googlePlaces`
  - Adds `liveEstablishments` and `isLoading` state
  - `useEffect` on mount: fetches real places from Paris center (48.8566, 2.3522) when API key is configured; silently falls back to mock data on error
  - Uses `liveEstablishments.length > 0 ? liveEstablishments : establishments` as data source
  - Shows spinner during load; hides results grid while loading
  - Shows "Contact to book" badge on establishment cards when `spaces.length === 0` (covers Google-sourced establishments)
  - Handles empty `distance` field gracefully (only shows separator when distance is non-empty)
- `MapView.tsx`:
  - Removed hardcoded `COORDS` record
  - Uses `est.coordinates` for marker placement; skips marker when coordinates absent
  - Fits bounds using `establishments.filter(e => e.coordinates)` — no unsafe `COORDS[est.id]` lookup

Build passes, TypeScript clean.

Commit: `76fc139`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] npm install required --legacy-peer-deps**
- **Found during:** Task 1
- **Issue:** `react-leaflet@5.0.0` requires `react@^19.0.0` but project uses `react@18.3.1`. This is a pre-existing conflict present before this plan.
- **Fix:** Added `--legacy-peer-deps` flag to npm install command.
- **Files modified:** None beyond package-lock.json (same packages installed)
- **Commit:** `07ac562`

## Self-Check

To be run after human-verify checkpoint completes. Auto tasks verified:
- `librework/frontend/src/lib/googlePlaces.ts` — created
- `librework/frontend/src/lib/mockData.ts` — coordinates added to 5 establishments
- `librework/frontend/src/components/providers.tsx` — APIProvider conditional wrap
- `librework/frontend/src/components/ExplorePage.tsx` — live fetch + fallback
- `librework/frontend/src/components/MapView.tsx` — COORDS removed, est.coordinates used
- Commits `07ac562` and `76fc139` — exist in submodule git log
- TypeScript: clean
- Build: passes

## Self-Check: PASSED
