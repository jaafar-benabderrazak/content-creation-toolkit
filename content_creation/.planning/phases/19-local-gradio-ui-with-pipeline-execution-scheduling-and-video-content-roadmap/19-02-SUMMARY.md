---
phase: 19-local-gradio-ui-with-pipeline-execution-scheduling-and-video-content-roadmap
plan: "02"
subsystem: roadmap
tags: [python, dataclasses, json, persistence, crud]
dependency_graph:
  requires: []
  provides: [roadmap.py, VideoRoadmap, RoadmapEntry, get_roadmap]
  affects: [plan-19-03]
tech_stack:
  added: []
  patterns: [atomic-json-write, dataclass-crud, lazy-singleton]
key_files:
  created:
    - roadmap.py
  modified: []
decisions:
  - "Atomic save via .tmp + Path.replace — prevents corrupt JSON on crash"
  - "status validation raises ValueError inline in update_status — fast fail at mutation point"
  - "Module-level get_roadmap() lazy singleton — zero overhead on import; safe for multi-call UI code"
  - "_load returns [] on FileNotFoundError or bad JSON — VideoRoadmap() is always safe to instantiate"
metrics:
  duration: "1 min"
  completed_date: "2026-03-28"
  tasks_completed: 2
  files_created: 1
  files_modified: 0
---

# Phase 19 Plan 02: VideoRoadmap Backend Summary

**One-liner:** JSON-persisted VideoRoadmap class with full CRUD, ordering, and status filtering for the Gradio Content Roadmap tab.

## What Was Built

`roadmap.py` — a self-contained module with no third-party dependencies that Plan 03 will import as a thin backend for the Gradio UI.

### RoadmapEntry dataclass

Fields: `id` (uuid4 hex), `title`, `tags` (comma-separated), `profile`, `notes`, `status` (planned/producing/published), `created_at`, `updated_at` (ISO 8601).

### VideoRoadmap class

| Method | Description |
| --- | --- |
| `add_entry(title, tags, profile, notes)` | Creates entry with uuid4 id, status=planned, timestamps now |
| `update_status(entry_id, status)` | Validates status in set; raises ValueError on invalid; returns bool |
| `update_entry(entry_id, **kwargs)` | Updates any non-None fields; sets updated_at |
| `delete_entry(entry_id)` | Removes by id; returns bool |
| `move_up(entry_id)` | Swaps with predecessor; returns bool |
| `move_down(entry_id)` | Swaps with successor; returns bool |
| `list_entries(status_filter)` | Returns copy; filters by status if provided |
| `_save()` | Atomic write via .tmp + Path.replace |
| `_load()` | Reads JSON; returns [] on FileNotFoundError or decode error |

### Module-level singleton

`get_roadmap()` returns a lazy-initialized global `VideoRoadmap()` instance.

## Tasks Completed

| Task | Name | Commit | Files |
| --- | --- | --- | --- |
| 1 | Build roadmap.py with RoadmapEntry and VideoRoadmap | 4c08166 | roadmap.py (created) |
| 2 | Smoke test full CRUD lifecycle | (no file changes) | — |

## Verification Results

- Import: `from roadmap import VideoRoadmap, RoadmapEntry, get_roadmap` — OK
- `VideoRoadmap()` creates `video_roadmap.json` with `[]` — OK
- Full CRUD cycle (add, status update, edit, move_down, move_up, filter, delete, reload) — PASS
- Status validation rejects invalid value with ValueError — PASS
- Persistence confirmed via reload into fresh `VideoRoadmap` instance — PASS

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- FOUND: roadmap.py
- FOUND: commit 4c08166
- FOUND: 19-02-SUMMARY.md
