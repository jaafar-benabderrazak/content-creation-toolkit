---
phase: 10-add-more-features
plan: "03"
subsystem: owner-analytics, explore-map
tags: [recharts, analytics, geolocation, leaflet, fastapi]
dependency_graph:
  requires: []
  provides: [owner-analytics-timeseries, explore-geolocation-centering]
  affects: [OwnerDashboard, ExplorePage, MapView, owner.py]
tech_stack:
  added: []
  patterns: [time-series-api, recharts-charts, browser-geolocation-api]
key_files:
  created: []
  modified:
    - librework/backend/app/api/v1/owner.py
    - librework/frontend/src/components/OwnerDashboard.tsx
    - librework/frontend/src/components/ExplorePage.tsx
    - librework/frontend/src/components/MapView.tsx
decisions:
  - "Added center prop to MapView (optional, defaults to Paris) to support external centering without breaking existing usages"
  - "Occupancy stored as 0-1 float on backend, converted to 0-100% in frontend before charting"
  - "Period selector uses inline button group instead of shadcn Select to keep header compact"
metrics:
  duration: 15min
  completed: 2026-03-22
  tasks_completed: 2
  files_modified: 4
---

# Phase 10 Plan 03: Owner Analytics Charts and Explore Geolocation Summary

One-liner: Revenue LineChart and occupancy BarChart with live time-series data from FastAPI, plus geolocation-centered Leaflet map with "Center on me" button.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add time-series analytics endpoints and enhance OwnerDashboard | 6ff3dff | owner.py, OwnerDashboard.tsx |
| 2 | Add user-location centering to Explore map | 7576dc6 | ExplorePage.tsx, MapView.tsx |

## What Was Built

### Task 1: Owner Analytics (Backend + Frontend)

**Backend (`owner.py`):**
- `GET /owner/analytics/revenue?period=week|month|quarter` — queries all non-cancelled reservations for the owner's establishments in the period, groups by `created_at` date, returns `[{date, revenue}]` time-series with zeros for missing days
- `GET /owner/analytics/occupancy?period=week|month` — counts confirmed reservations per day divided by total_spaces count, returns `[{date, occupancy}]` (0.0–1.0, capped at 1.0)
- Both endpoints use `Depends(get_current_owner)` for auth
- Added `Query`, `datetime`, `timedelta`, `date`, `Dict`, `Any` imports

**Frontend (`OwnerDashboard.tsx`):**
- Imports `LineChart`, `Line`, `BarChart`, `Bar`, `Legend` from recharts (already installed)
- Two `useEffect` hooks fetch from `/owner/analytics/revenue` and `/owner/analytics/occupancy` when period changes
- Period selectors: revenue supports week/month/quarter; occupancy supports week/month
- Revenue chart: `LineChart` with brand color `#F9AB18`, `dot={false}` for clean trend line
- Occupancy chart: `BarChart` with domain [0,100] and `%` unit on Y-axis
- Charts in `grid-cols-1 lg:grid-cols-2` layout below stats cards
- Loading spinner, "Unable to load" error state, and "No data" empty state for each chart

### Task 2: Explore Geolocation

**`ExplorePage.tsx`:**
- `requestGeolocation` callback calls `navigator.geolocation.getCurrentPosition` with `{ enableHighAccuracy: false, timeout: 5000 }`
- `useEffect` on mount fires `requestGeolocation()`
- On success: sets `userCenter` state `{ lat, lng }`
- On error/denial: silently keeps `userCenter` as `null`, falling back to `DEFAULT_CENTER` (Paris)
- "Center on me" button with `LocateFixed` icon (lucide-react) in top-right of map area, uses `z-[1000]` to sit above Leaflet tiles
- `userCenter` passed as `center` prop to `MapView`; also used as the fetch center for `fetchNearbyEstablishments`
- "Showing results near your location" indicator appears when `userCenter` is set

**`MapView.tsx` (Rule 2 auto-fix — missing prop support):**
- Added optional `center?: { lat, lng }` prop
- `useEffect` watching `center` calls `map.setView` when center changes (recenter on "Center on me" click)
- Initial map view uses `center ?? DEFAULT_CENTER` instead of hardcoded Paris

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] MapView lacked center prop**
- **Found during:** Task 2
- **Issue:** Plan said to "update the Map component's center prop" but MapView had no such prop; passing it without support would silently do nothing
- **Fix:** Added optional `center` prop to MapView interface and a `useEffect` that calls `map.setView` when it changes
- **Files modified:** `librework/frontend/src/components/MapView.tsx`
- **Commit:** 7576dc6

## Self-Check: PASSED
