---
phase: 11-real-map-data-mobile-responsive-polish-and-playwright-e2e-testing
plan: 01
subsystem: ui
tags: [leaflet, react, google-maps, geolocation, haversine]

# Dependency graph
requires:
  - phase: 09-fix-select-visibility-issues-and-integrate-google-maps-open-data
    provides: MapView component with Leaflet, fetchNearbyEstablishments, Places API integration
provides:
  - MapView with LayerGroup-based marker lifecycle (no duplicates on prop change)
  - moveend event handler firing onBoundsChange callback with map center
  - Debounced handleBoundsChange in ExplorePage re-fetching on map drag
  - computeDistance Haversine export populating distance field on all live establishments
affects: [11-02, 11-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LayerGroup for marker lifecycle: clearLayers() on prop change prevents duplicates"
    - "Ref-based stale closure avoidance: onSelectRef and onBoundsChangeRef updated in sync effects"
    - "Separate mount-only init effect from data-update effect to prevent map re-creation"
    - "Debounce via useRef<ReturnType<typeof setTimeout>> for map moveend re-fetch"

key-files:
  created: []
  modified:
    - librework/frontend/src/components/MapView.tsx
    - librework/frontend/src/components/ExplorePage.tsx
    - librework/frontend/src/lib/googlePlaces.ts

key-decisions:
  - "LayerGroup used instead of direct map.addLayer to allow clearLayers() without destroying the map instance"
  - "onSelectRef and onBoundsChangeRef pattern used to avoid registering stale closures in Leaflet event handlers"
  - "Init effect depends only on [] (mount-only); establishments update effect is separate — this is the correct fix for the full-map-recreation bug"
  - "computeDistance returns metres below 1000 ('850 m'), kilometres above ('1.2 km') for human readability"
  - "handleBoundsChange uses 500ms debounce to avoid spamming Places API during fast panning"

patterns-established:
  - "Leaflet marker management: always use LayerGroup.clearLayers() before re-adding markers"
  - "Event handler stale closures in Leaflet: store callback in useRef, update via sync useEffect"

requirements-completed: [SEARCH-01]

# Metrics
duration: 4min
completed: 2026-03-26
---

# Phase 11 Plan 01: MapView Marker Fix and Search-by-Area Summary

**Leaflet LayerGroup marker lifecycle fix, moveend-driven search-by-area with 500ms debounce, and Haversine distance strings on all establishment cards**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-26T~14:58Z
- **Completed:** 2026-03-26T~15:02Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Fixed marker duplication bug: markers now live in a LayerGroup cleared on each prop change instead of being added directly to the map
- Map drag fires `onBoundsChange` via `moveend` handler; ExplorePage debounces re-fetch to 500ms, loading new establishments for the panned area
- `computeDistance` (Haversine) exported from googlePlaces.ts; distance string ("1.2 km" / "850 m") populated on every live establishment returned from the Places API

## Task Commits

1. **Task 1: Fix marker layer management bug and add onBoundsChange callback** - `34a974a` (feat)
2. **Task 2: Wire search-by-area in ExplorePage and add distance calculation** - `d035416` (feat)

## Files Created/Modified
- `librework/frontend/src/components/MapView.tsx` - LayerGroup marker lifecycle, mount-only init effect, moveend handler, ref-based stale closure avoidance
- `librework/frontend/src/components/ExplorePage.tsx` - useRef import, moveDebounceRef, handleBoundsChange, onBoundsChange prop wired, userCenter passed to fetchNearbyEstablishments
- `librework/frontend/src/lib/googlePlaces.ts` - computeDistance export (Haversine), mapPlaceToEstablishment accepts optional userCenter, fetchNearbyEstablishments accepts optional userCenter

## Decisions Made
- LayerGroup chosen over direct map markers so `clearLayers()` can reset without touching the map instance
- Separate mount-only init effect (`[]`) from establishments update effect (`[establishments]`) — the root cause of the duplication bug was the original init effect depending on `establishments`, causing full map re-creation on every establishments prop change
- Stale closure pattern: `onSelectRef` and `onBoundsChangeRef` updated via dedicated sync `useEffect`s, keeping Leaflet event handlers always current without re-registering

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `git add librework/frontend/src/lib/googlePlaces.ts` triggered a `.gitignore` warning because the root `.gitignore` has a `lib/` rule. The file was already tracked by git (pre-existing), so it staged correctly despite the advisory warning. Commit succeeded.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MapView marker lifecycle is now correct and extensible
- Search-by-area (map drag) is live and wired end-to-end
- Distance display is ready; marker popups already render `est.distance`
- Plan 02 (mobile responsive polish) and Plan 03 (Playwright E2E) can proceed

---
*Phase: 11-real-map-data-mobile-responsive-polish-and-playwright-e2e-testing*
*Completed: 2026-03-26*

## Self-Check: PASSED

- FOUND: `.planning/phases/11-real-map-data-mobile-responsive-polish-and-playwright-e2e-testing/11-01-SUMMARY.md`
- FOUND: `librework/frontend/src/components/MapView.tsx`
- FOUND: `librework/frontend/src/components/ExplorePage.tsx`
- FOUND: `librework/frontend/src/lib/googlePlaces.ts`
- FOUND commit: `34a974a` (Task 1)
- FOUND commit: `d035416` (Task 2)
