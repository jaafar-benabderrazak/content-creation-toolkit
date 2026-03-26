---
phase: 12
plan: 02
subsystem: backend-db
tags: [double-booking, postgis, spatial-search, exclusion-constraint, filters]
dependency_graph:
  requires: []
  provides: [INFRA-04, SEARCH-02, SEARCH-03, SEARCH-04]
  affects: [backend/app/api/v1/reservations.py, backend/app/api/v1/establishments.py]
tech_stack:
  added: []
  patterns:
    - PostgreSQL exclusion constraint via btree_gist for double-booking prevention
    - PostGIS ST_DWithin + ST_Distance via Supabase RPC for spatial search
    - Location column backfill + sync trigger pattern
    - Python-side open_now filter using pytz timezone-aware datetime
key_files:
  created:
    - supabase/migrations/20260326000000_double_booking_constraint.sql
    - supabase/migrations/20260326000001_postgis_search_rpc.sql
  modified:
    - backend/app/api/v1/reservations.py
    - backend/app/api/v1/establishments.py
decisions:
  - "Half-open tstzrange '[)' allows back-to-back bookings; only pending/confirmed reservations participate in exclusion constraint"
  - "establishments_within_radius RPC pushes capacity and price filters to DB via EXISTS subqueries on spaces table; amenities and open_now filtered in Python"
  - "geopy kept in requirements.txt because reservations.py still uses it in the find_soonest_available endpoint — removal scoped only to establishments.py per plan"
  - "Location backfill runs once at migration time; sync_location_from_latlng trigger maintains geography column on INSERT/UPDATE going forward"
metrics:
  duration: 4min
  completed: 2026-03-26
  tasks_completed: 2
  files_created_or_modified: 4
---

# Phase 12 Plan 02: Double-Booking Prevention and PostGIS Search Filters Summary

**One-liner:** PostgreSQL exclusion constraint (btree_gist) prevents concurrent double-bookings; PostGIS ST_DWithin RPC replaces geopy in-memory distance filtering with open_now/price/capacity/amenity filters added to advanced_search.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Double-booking exclusion constraint migration + reservations.py 409 handler | 1e33ca2 | supabase/migrations/20260326000000_double_booking_constraint.sql, backend/app/api/v1/reservations.py |
| 2 | PostGIS RPC migration (backfill + trigger + function) + establishments.py rewrite | 324600c (via 12-01 agent) | supabase/migrations/20260326000001_postgis_search_rpc.sql, backend/app/api/v1/establishments.py |

## What Was Built

### Task 1: Double-Booking Exclusion Constraint

`supabase/migrations/20260326000000_double_booking_constraint.sql` installs `btree_gist` and adds:

```sql
ALTER TABLE reservations
ADD CONSTRAINT no_overlapping_reservations
EXCLUDE USING GIST (
    space_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (status IN ('pending', 'confirmed'));
```

The half-open `[)` range means back-to-back bookings (09:00–10:00 and 10:00–11:00) are allowed. Cancelled and completed reservations are excluded from the constraint via the `WHERE` clause.

`reservations.py` `create_reservation` now wraps the insert in a try/except that checks for PostgreSQL error code `23P01` or the constraint name `no_overlapping_reservations` and raises `HTTP 409 Conflict` instead of a generic 400. The existing `check_space_availability` RPC pre-check is retained as fast feedback.

### Task 2: PostGIS Search RPC and Filters

`supabase/migrations/20260326000001_postgis_search_rpc.sql`:
- Backfills `location` column from `latitude`/`longitude` for rows where it is NULL
- Creates `sync_location_from_latlng()` trigger function and `trg_sync_location` trigger (BEFORE INSERT OR UPDATE OF latitude, longitude) to keep the geography column in sync
- Creates `establishments_within_radius(lat, lng, radius_meters, min_capacity, min_price, max_price)` Postgres function using `ST_DWithin` for radius filtering and `ST_Distance` for sorting; capacity/price filters use `EXISTS` subqueries on the `spaces` table

`establishments.py`:
- `list_establishments` and `get_nearest_establishments` now call `supabase.rpc('establishments_within_radius', ...)` instead of fetching all rows and filtering with geopy
- `advanced_search` endpoint gains `open_now: bool`, `min_price: Optional[float]`, `max_price: Optional[float]`, `min_capacity: Optional[int]`, `amenities: Optional[str]` (comma-separated) query parameters
- `is_open_now(opening_hours, timezone)` helper function added — timezone-aware check using pytz against the `{"monday": {"open": "09:00", "close": "18:00"}}` JSONB format
- geopy import removed from this file entirely

## Deviations from Plan

### Incidental

**Task 2 files committed by prior agent (12-01)**

- **Found during:** Task 2 staging
- **Issue:** `establishments.py` and `20260326000001_postgis_search_rpc.sql` were already committed at HEAD by the 12-01 plan agent in commit `324600c`. The `git add` succeeded but `git commit` reported "nothing to commit."
- **Resolution:** Content is correct and committed. This plan's Task 1 commit (`1e33ca2`) is the primary new work. Task 2 content exists at the correct state.
- **Impact:** None — all artifacts present and verified.

## Self-Check

### Files Exist

- supabase/migrations/20260326000000_double_booking_constraint.sql: FOUND
- supabase/migrations/20260326000001_postgis_search_rpc.sql: FOUND
- backend/app/api/v1/reservations.py (contains 23P01 check): FOUND
- backend/app/api/v1/establishments.py (contains establishments_within_radius, is_open_now): FOUND

### Commits Exist

- 1e33ca2: feat(12-02): add double-booking exclusion constraint and 409 handler — FOUND
- 324600c: Task 2 content committed (by 12-01 agent) — FOUND

## Self-Check: PASSED
